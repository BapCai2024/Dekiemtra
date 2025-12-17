import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
import time
import re
import random

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="HỆ THỐNG RA ĐỀ THI TIỂU HỌC TOÀN DIỆN",
    page_icon="🏫",
    layout="wide"
)

# --- 2. CSS GIAO DIỆN ---
st.markdown("""
<style>
    /* Tab 1 Style */
    .subject-card { padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9; text-align: center; margin-bottom: 10px; }
    .stTextArea textarea { font-family: 'Times New Roman'; font-size: 16px; }
    .success-box { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; margin-bottom: 10px; }
    
    /* Tab 2 Style */
    .question-box { background-color: #fff; padding: 20px; border-radius: 5px; border: 1px solid #e0e0e0; margin-bottom: 15px; font-family: 'Times New Roman'; font-size: 1.1rem; }
    
    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #333;
        text-align: center; padding: 10px; font-size: 14px;
        border-top: 1px solid #ddd; z-index: 100;
    }
    .content-container { padding-bottom: 60px; }
    
    /* Tiêu đề chính */
    .main-header {
        text-align: center; 
        color: #1565C0; 
        font-weight: bold; 
        font-size: 28px; 
        text-transform: uppercase;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. IMPORT AN TOÀN ---
try:
    import pypdf
except ImportError:
    st.error("⚠️ Thiếu thư viện 'pypdf'. Vui lòng cài đặt: pip install pypdf")

# --- 4. CSDL CHƯƠNG TRÌNH HỌC (CẬP NHẬT TỪ KẾ HOẠCH DẠY HỌC K1-K5) ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 2": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Công nghệ", "🔧")],
    "Lớp 3": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 4": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 5": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")]
}

# DỮ LIỆU ĐÃ CẬP NHẬT SỐ TIẾT VÀ TÊN BÀI CHÍNH XÁC TỪ FILE K1-K5
CURRICULUM_DB = {
    "Lớp 1": {
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Làm quen với tiếng việt", "Bài học": "Bài 1A: a, b (2 tiết); Bài 1B: c, o (2 tiết); Bài 1C: ô, ơ (2 tiết); Bài 1D: d, đ (2 tiết); Bài 1E: Ôn tập (2 tiết); Bài 2A: e, ê (2 tiết); Bài 2B: h, i (2 tiết); Bài 2C: g, gh (2 tiết); Bài 2D: k, kh (2 tiết); Bài 2E: Ôn tập (2 tiết); Bài 3A: l, m (2 tiết); Bài 3B: n, nh (2 tiết); Bài 3C: ng, ngh (2 tiết); Bài 3D: u, ư (2 tiết); Bài 3E: Ôn tập (2 tiết)"},
                {"Chủ đề": "Học chữ ghi vần", "Bài học": "Bài 5A: ch , tr (2 tiết); Bài 5B: x , y (2 tiết); Bài 5C: ua , ưa , ia (2 tiết); Bài 5D: Chữ thường và chữ hoa (2 tiết); Bài 5E: Ôn tập (2 tiết); Bài 6A: â , ai , ay , ây (2 tiết); Bài 6B: oi , ôi , ơi (2 tiết); Bài 6C: ui, ưi (2 tiết); Bài 6D: uôi, ươi (2 tiết); Bài 6E: Ôn tập (2 tiết)"}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Trường em", "Bài học": "Bài 19A: Tới trường (3 tiết); Bài 19B: Ở trường thật thú vị (3 tiết); Bài 19C: Đường đến trường (3 tiết); Bài 19D: Ngôi trường mới (3 tiết)"},
                {"Chủ đề": "Em là búp măng non", "Bài học": "Bài 20A: Bạn bè tuổi thơ (3 tiết); Bài 20B: Bạn thích đồ chơi gì? (3 tiết); Bài 20C: Em nói lời hay (3 tiết); Bài 20D: Giúp bạn vượt khó (3 tiết)"}
            ]
        },
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Các số từ 0 đến 10", "Bài học": "Các số 0, 1, 2, 3, 4, 5 (3 tiết); Các số 6, 7, 8, 9, 10 (4 tiết); Nhiều hơn, ít hơn, bằng nhau (2 tiết); So sánh số (3 tiết); Mấy và mấy (2 tiết)"},
                {"Chủ đề": "Phép cộng, phép trừ trong phạm vi 10", "Bài học": "Phép cộng trong phạm vi 10 (3 tiết); Phép trừ trong phạm vi 10 (3 tiết); Bảng cộng, bảng trừ trong phạm vi 10 (4 tiết)"}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Số có hai chữ số", "Bài học": "Bài 21: Số có hai chữ số (2 tiết); Bài 22: So sánh số có hai chữ số (2 tiết); Bài 23: Bảng các số từ 1-100 (2 tiết)"},
                {"Chủ đề": "Thời gian", "Bài học": "Bài 35: Các ngày trong tuần (1 tiết); Bài 36: Thực hành xem lịch và giờ (2 tiết)"}
            ]
        }
    },
    "Lớp 4": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Ôn tập và bổ sung", "Bài học": "Bài 1: Ôn tập các số đến 100 000 (2 tiết); Bài 2: Ôn tập các phép tính trong phạm vi 100 000 (3 tiết); Bài 3: Số chẵn, số lẻ (2 tiết); Bài 4: Biểu thức chứa chữ (3 tiết); Bài 5: Giải bài toán có 3 bước tính (2 tiết); Bài 6: Luyện tập chung (2 tiết)"},
                {"Chủ đề": "Góc và đơn vị đo góc", "Bài học": "Bài 7: Đo góc, đơn vị đo góc (1 tiết); Bài 8: Góc nhọn, góc tù, góc bẹt (3 tiết); Bài 9: Luyện tập chung (2 tiết)"},
                {"Chủ đề": "Số có nhiều chữ số", "Bài học": "Bài 10: Số có sáu chữ số. Số 1 000 000 (3 tiết); Bài 11: Hàng và lớp (3 tiết); Bài 12: Các số trong phạm vi lớp triệu (3 tiết); Bài 13: Làm tròn số đến hàng trăm nghìn (1 tiết); Bài 14: So sánh các số có nhiều chữ số (2 tiết); Bài 15: Làm quen với dãy số tự nhiên (2 tiết); Bài 16: Luyện tập chung (3 tiết)"},
                {"Chủ đề": "Một số đơn vị đo đại lượng", "Bài học": "Bài 17: Yến, tạ, tấn (3 tiết); Bài 18: Đề-xi-mét vuông, mét vuông, mi-li-mét vuông (4 tiết); Bài 19: Giây, thế kỉ (2 tiết); Bài 20: Thực hành và trải nghiệm sử dụng một số đơn vị đo đại lượng (3 tiết)"},
                {"Chủ đề": "Phép cộng và phép trừ", "Bài học": "Bài 22: Phép cộng các số có nhiều chữ số (2 tiết); Bài 23: Phép trừ các số có nhiều chữ số (2 tiết); Bài 24: Tính chất giao hoán và kết hợp của phép cộng (3 tiết); Bài 25: Tìm hai số khi biết tổng và hiệu của hai số đó (2 tiết)"}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phép nhân, phép chia", "Bài học": "Bài 38: Nhân với số có một chữ số (2 tiết); Bài 39: Chia cho số có một chữ số (2 tiết); Bài 40: Tính chất giao hoán và kết hợp của phép nhân (3 tiết); Bài 41: Nhân, chia với 10, 100, 1000... (2 tiết); Bài 42: Tính chất phân phối của phép nhân đối với phép cộng (3 tiết); Bài 43: Nhân với số có hai chữ số (3 tiết); Bài 44: Chia cho số có hai chữ số (3 tiết)"},
                {"Chủ đề": "Phân số", "Bài học": "Bài 53: Khái niệm phân số (2 tiết); Bài 54: Phân số và phép chia số tự nhiên (2 tiết); Bài 55: Tính chất cơ bản của phân số (2 tiết); Bài 56: Rút gọn phân số (2 tiết); Bài 57: Quy đồng mẫu số các phân số (2 tiết); Bài 58: So sánh phân số (3 tiết)"},
                {"Chủ đề": "Các phép tính với phân số", "Bài học": "Bài 60: Phép cộng phân số (4 tiết); Bài 61: Phép trừ phân số (3 tiết); Bài 63: Phép nhân phân số (4 tiết); Bài 64: Phép chia phân số (2 tiết); Bài 65: Tìm phân số của một số (2 tiết)"}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Bài 1: Điều kì diệu (3 tiết); Bài 2: Thi nhạc (4 tiết); Bài 3: Anh em sinh đôi (3 tiết); Bài 4: Công chúa và người dẫn chuyện (4 tiết); Bài 5: Thằn lằn xanh và tắc kè (3 tiết); Bài 6: Nghệ sĩ trống (4 tiết); Bài 7: Những bức chân dung (3 tiết); Bài 8: Đò ngang (4 tiết)"},
                {"Chủ đề": "Trải nghiệm và khám phá", "Bài học": "Bài 9: Bầu trời trong quả trứng (3 tiết); Bài 10: Tiếng nói của cỏ cây (4 tiết); Bài 11: Tập làm văn (3 tiết); Bài 12: Nhà phát minh 6 tuổi (4 tiết); Bài 13: Con vẹt xanh (3 tiết); Bài 14: Chân trời cuối phố (4 tiết); Bài 15: Gặt chữ trên non (3 tiết); Bài 16: Trước ngày xa quê (4 tiết)"}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Sống để yêu thương", "Bài học": "Bài 1: Hải Thượng Lãn Ông (3 tiết); Bài 2: Vệt phấn trên mặt bàn (4 tiết); Bài 3: Ông Bụt đã đến (3 tiết); Bài 4: Quả ngọt cuối mùa (4 tiết)"},
                {"Chủ đề": "Uống nước nhớ nguồn", "Bài học": "Bài 9: Sự tích con Rồng, cháu Tiên (3 tiết); Bài 10: Cảm xúc Trường Sa (4 tiết); Bài 11: Sáng tháng Năm (3 tiết); Bài 12: Chàng trai làng Phù Ủng (4 tiết)"}
            ]
        }
    },
    "Lớp 5": {
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Thế giới tuổi thơ", "Bài học": "Bài 1: Thanh âm của gió (3 tiết); Bài 2: Cánh đồng hoa (4 tiết); Bài 3: Tuổi Ngựa (3 tiết); Bài 4: Bến sông tuổi thơ (4 tiết); Bài 5: Tiếng hạt nảy mầm (3 tiết); Bài 6: Ngôi sao sân cỏ (4 tiết); Bài 7: Bộ sưu tập độc đáo (3 tiết); Bài 8: Hành tinh kì lạ (4 tiết)"},
                {"Chủ đề": "Thiên nhiên kì thú", "Bài học": "Bài 9: Trước cổng trời (3 tiết); Bài 10: Kì diệu rừng xanh (4 tiết); Bài 11: Hang Sơn Đoòng - Những điều kì thú (3 tiết); Bài 12: Những hòn đảo trên vịnh Hạ Long (4 tiết); Bài 13: Mầm non (3 tiết); Bài 14: Những ngọn núi nóng rẫy (4 tiết)"},
                {"Chủ đề": "Trên con đường học tập", "Bài học": "Bài 17: Thư gửi các học sinh (3 tiết); Bài 18: Tấm gương tự học (4 tiết); Bài 19: Trải nghiệm để sáng tạo (3 tiết); Bài 20: Khổ luyện thành tài (4 tiết); Bài 21: Thế giới trong trang sách (3 tiết); Bài 22: Từ những câu chuyện ấu thơ (4 tiết)"}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp cuộc sống", "Bài học": "Bài 1: Tiếng hát của người đá (3 tiết); Bài 2: Khúc hát ru những em bé lớn trên lưng mẹ (4 tiết); Bài 3: Hạt gạo làng ta (3 tiết); Bài 4: Hộp quà màu thiên thanh (4 tiết); Bài 5: Giỏ hoa tháng Năm (3 tiết); Bài 6: Thư của bố (4 tiết)"},
                {"Chủ đề": "Hương sắc trăm miền", "Bài học": "Bài 9: Hội thổi cơm thi ở Đồng Văn (3 tiết); Bài 10: Những búp chè trên cây cổ thụ (4 tiết); Bài 11: Hương cốm mùa thu (3 tiết); Bài 12: Vũ điệu trên tiền thổ cẩm (4 tiết); Bài 13: Đàn t'rưng – tiếng ca đại ngàn (3 tiết)"}
            ]
        },
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Ôn tập và bổ sung", "Bài học": "Bài 1: Ôn tập số tự nhiên (2 tiết); Bài 2: Ôn tập các phép tính với số tự nhiên (2 tiết); Bài 3: Ôn tập phân số (2 tiết); Bài 4: Phân số thập phân (2 tiết); Bài 5: Ôn tập các phép tính với phân số (2 tiết); Bài 6: Cộng, trừ hai phân số khác mẫu số (2 tiết)"},
                {"Chủ đề": "Số thập phân", "Bài học": "Bài 10: Khái niệm số thập phân (2 tiết); Bài 11: So sánh các số thập phân (2 tiết); Bài 12: Viết số đo đại lượng dưới dạng số thập phân (2 tiết)"},
                {"Chủ đề": "Các phép tính với số thập phân", "Bài học": "Bài 19: Phép cộng số thập phân (2 tiết); Bài 20: Phép trừ số thập phân (2 tiết); Bài 21: Phép nhân số thập phân (3 tiết); Bài 22: Phép chia số thập phân (3 tiết)"}
            ]
        }
    }
}

# --- CẤU TRÚC DỮ LIỆU ĐÃ ĐƯỢC CHUẨN HÓA LẠI ĐỂ TẠO LIST BÀI HỌC ---
CURRICULUM_DB_PROCESSED = {}

# Xử lý dữ liệu thô để tách chuỗi bài học thành list
for grade, subjects in CURRICULUM_DB.items():
    CURRICULUM_DB_PROCESSED[grade] = {}
    for subject, semesters in subjects.items():
        CURRICULUM_DB_PROCESSED[grade][subject] = {}
        for semester, content in semesters.items():
            processed_topics = []
            for item in content:
                topic_name = item['Chủ đề']
                raw_lessons_str = item['Bài học']
                lessons_list = [l.strip() for l in raw_lessons_str.split(';') if l.strip()]
                processed_topics.append({
                    'Chủ đề': topic_name,
                    'Bài học': lessons_list
                })
            CURRICULUM_DB_PROCESSED[grade][subject][semester] = processed_topics

# --- 5. HỆ THỐNG API MỚI ---
def generate_content_with_rotation(api_key, prompt):
    genai.configure(api_key=api_key)
    try:
        all_models = list(genai.list_models())
    except Exception as e:
        return f"Lỗi kết nối lấy danh sách model: {e}", None

    valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
    if not valid_models:
        return "Lỗi: Không tìm thấy model nào hỗ trợ tạo văn bản.", None

    priority_order = []
    for m in valid_models:
        if 'flash' in m.lower() and '1.5' in m: priority_order.append(m)
    for m in valid_models:
        if 'pro' in m.lower() and '1.5' in m and m not in priority_order: priority_order.append(m)
    for m in valid_models:
        if m not in priority_order: priority_order.append(m)

    last_error = ""
    for model_name in priority_order:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text, model_name
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue

    return f"Hết model khả dụng. Lỗi cuối cùng: {last_error}", None

# --- 6. HÀM HỖ TRỢ FILE ---
def read_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            return df.to_string()
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif uploaded_file.name.endswith('.pdf'):
            if 'pypdf' in globals():
                reader = pypdf.PdfReader(uploaded_file)
                text = ""
                for page in reader.pages: text += page.extract_text()
                return text
        return None
    except Exception:
        return None

def set_font_style(doc):
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)

def create_word_from_question_list(school_name, subject, exam_list):
    doc = Document()
    set_font_style(doc)
    
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(7)
    table.columns[1].width = Cm(9)
    
    cell_1 = table.cell(0, 0)
    p1 = cell_1.paragraphs[0]
    run_s = p1.add_run(f"{school_name.upper()}")
    run_s.bold = True
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    cell_2 = table.cell(0, 1)
    p2 = cell_2.paragraphs[0]
    run_e = p2.add_run(f"ĐỀ KIỂM TRA {subject.upper()}\n")
    run_e.bold = True
    run_y = p2.add_run("Năm học: ..........")
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    
    h1 = doc.add_heading('I. MA TRẬN ĐỀ THI', level=1)
    h1.runs[0].font.name = 'Times New Roman'
    h1.runs[0].font.color.rgb = None
    
    matrix_table = doc.add_table(rows=1, cols=6)
    matrix_table.style = 'Table Grid'
    hdr_cells = matrix_table.rows[0].cells
    headers = ["STT", "Chủ đề / Bài học", "Dạng bài", "Mức độ", "Điểm", "Ghi chú"]
    for i, text in enumerate(headers):
        hdr_cells[i].text = text
        hdr_cells[i].paragraphs[0].runs[0].font.bold = True
        hdr_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    for idx, q in enumerate(exam_list):
        row_cells = matrix_table.add_row().cells
        row_cells[0].text = str(idx + 1)
        row_cells[1].text = str(q.get('lesson', ''))
        row_cells[2].text = str(q.get('type', ''))
        row_cells[3].text = str(q.get('level', ''))
        row_cells[4].text = str(q.get('points', ''))
        row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        row_cells[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

    h2 = doc.add_heading('II. NỘI DUNG ĐỀ THI', level=1)
    h2.runs[0].font.name = 'Times New Roman'
    h2.runs[0].font.color.rgb = None
    
    for idx, q in enumerate(exam_list):
        p = doc.add_paragraph()
        run_title = p.add_run(f"Câu {idx + 1} ({q['points']} điểm): ")
        run_title.bold = True
        
        content_lines = q['content'].split('\n')
        for line in content_lines:
            if line.strip():
                if line.startswith("**Câu hỏi:**") or line.startswith("**Đáp án:**"):
                    pass 
                else:
                    doc.add_paragraph(line)
        doc.add_paragraph() 

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_matrix_document(exam_list, subject_name, grade_name):
    doc = Document()
    section = doc.sections[0]
    new_width, new_height = section.page_height, section.page_width
    section.page_width = new_width
    section.page_height = new_height
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)
    set_font_style(doc)
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"BẢN ĐẶC TẢ ĐỀ KIỂM TRA MÔN {subject_name.upper()} {grade_name.upper()}")
    run.bold = True
    run.font.size = Pt(14)
    doc.add_paragraph()
    
    table = doc.add_table(rows=2, cols=12)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "STT"
    hdr_cells[1].text = "Chủ đề"
    hdr_cells[2].text = "Bài học"
    hdr_cells[3].text = "Yêu cầu cần đạt"
    hdr_cells[4].text = "Dạng câu hỏi & Mức độ nhận thức"
    hdr_cells[4].merge(hdr_cells[10]) 
    hdr_cells[11].text = "Tổng điểm"

    row2_cells = table.rows[1].cells
    sub_headers = ["TN-Biết", "TN-Hiểu", "TN-VD", "TL-Biết", "TL-Hiểu", "TL-VD", "Khác"]
    for i, title in enumerate(sub_headers):
        row2_cells[i+4].text = title
        
    for i in [0, 1, 2, 3, 11]:
        hdr_cells[i].merge(row2_cells[i])

    grouped_data = {}
    for idx, q in enumerate(exam_list):
        key = (q['topic'], q['lesson'])
        if key not in grouped_data:
            grouped_data[key] = {'yccd': q.get('yccd', ''), 'questions': []}
        grouped_data[key]['questions'].append(q)

    stt = 1
    for (topic, lesson), data in grouped_data.items():
        row_cells = table.add_row().cells
        row_cells[0].text = str(stt)
        row_cells[1].text = topic
        row_cells[2].text = lesson
        row_cells[3].text = data['yccd']
        
        counts = {k: [] for k in sub_headers}
        total_points = 0
        for q in data['questions']:
            q_idx = exam_list.index(q) + 1
            q_type_code = "TN" if "Tự luận" not in q['type'] and "Thực hành" not in q['type'] else "TL"
            q_level_code = "Biết" if "Mức 1" in q['level'] else ("Hiểu" if "Mức 2" in q['level'] else "VD")
            key = f"{q_type_code}-{q_level_code}"
            if key in counts: counts[key].append(str(q_idx))
            else: counts["Khác"].append(str(q_idx))
            total_points += q['points']
            
        for i, key in enumerate(sub_headers):
            if counts[key]:
                row_cells[i+4].text = f"Câu {', '.join(counts[key])}"
        
        row_cells[11].text = str(total_points)
        stt += 1

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_word_file_simple(school_name, exam_name, content):
    doc = Document()
    set_font_style(doc)
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2); section.bottom_margin = Cm(2)
        section.left_margin = Cm(3); section.right_margin = Cm(2)

    table = doc.add_table(rows=1, cols=2); table.autofit = False
    table.columns[0].width = Cm(7); table.columns[1].width = Cm(9)

    cell_1 = table.cell(0, 0); p1 = cell_1.paragraphs[0]
    run_s = p1.add_run(f"{school_name.upper()}"); run_s.bold = True; run_s.font.size = Pt(12)
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    cell_2 = table.cell(0, 1); p2 = cell_2.paragraphs[0]
    run_e = p2.add_run(f"{exam_name.upper()}\n"); run_e.bold = True; run_e.font.size = Pt(12)
    run_y = p2.add_run("Năm học: .........."); run_y.font.size = Pt(13)
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    for line in content.split('\n'):
        if line.strip():
            p = doc.add_paragraph(line); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    buffer = io.BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

def extract_periods(lesson_name):
    match = re.search(r'\((\d+)\s*tiết\)', lesson_name, re.IGNORECASE)
    if match:
        return match.group(1)
    return "-"

# --- 7. MAIN APP ---
def main():
    if 'exam_result' not in st.session_state: st.session_state.exam_result = ""
    if "exam_list" not in st.session_state: st.session_state.exam_list = [] 
    if "current_preview" not in st.session_state: st.session_state.current_preview = "" 
    if "temp_question_data" not in st.session_state: st.session_state.temp_question_data = None 
    if "auto_yccd" not in st.session_state: st.session_state.auto_yccd = ""

    # --- SIDEBAR CHUNG ---
    with st.sidebar:
        st.header("🔑 CẤU HÌNH HỆ THỐNG")
        st.subheader("HỖ TRỢ RA ĐỀ CẤP TIỂU HỌC")
        api_key = st.text_input("Nhập API Key Google:", type="password")
        
        if st.button("🔌 Kiểm tra kết nối API"):
            if not api_key:
                st.warning("Vui lòng nhập API Key trước.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    models = list(genai.list_models())
                    st.success(f"✅ Kết nối thành công! (Tìm thấy {len(models)} models)")
                except Exception as e:
                    st.error(f"❌ Kết nối thất bại: {e}")
        
        st.divider()
        st.markdown("**TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN**")
        st.caption("Hệ thống hỗ trợ chuyên môn")

    if not api_key:
        st.warning("Vui lòng nhập API Key để bắt đầu.")
        return

    st.markdown('<div class="main-header">HỖ TRỢ RA ĐỀ THI CẤP TIỂU HỌC</div>', unsafe_allow_html=True)

    # --- TABS GIAO DIỆN ---
    tab1, tab2, tab3 = st.tabs(["📁 TẠO ĐỀ TỪ FILE (UPLOAD)", "✍️ SOẠN TỪNG CÂU (CSDL)", "📊 MA TRẬN ĐỀ THI"])

    # ========================== TAB 1: UPLOAD & TẠO ĐỀ ==========================
    with tab1:
        st.header("Tạo đề thi từ file Ma trận có sẵn")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("1. Chọn Lớp")
            grade_t1 = st.radio("Khối lớp:", list(SUBJECTS_DB.keys()), key="t1_grade")
        with col2:
            st.subheader("2. Chọn Môn")
            subjects_t1 = SUBJECTS_DB[grade_t1]
            sub_name_t1 = st.selectbox("Môn học:", [s[0] for s in subjects_t1], key="t1_sub")
            icon_t1 = next(i for n, i in subjects_t1 if n == sub_name_t1)
            st.markdown(f"<div class='subject-card'><h3>{icon_t1} {sub_name_t1}</h3></div>", unsafe_allow_html=True)
            exam_term_t1 = st.selectbox("Kỳ thi:", 
                ["ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ I", "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ I",
                "ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ II", "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ II"], key="t1_term")
            school_name_t1 = st.text_input("Tên trường:", value="TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN", key="t1_school")

        st.subheader("3. Upload Ma trận")
        st.info("💡 File upload nên chứa bảng ma trận có các cột: Mạch kiến thức, Mức độ, Số câu, Số điểm.")
        uploaded = st.file_uploader("Chọn file (.xlsx, .docx, .pdf)", type=['xlsx', 'docx', 'pdf'], key="t1_up")

        if uploaded and st.button("🚀 TẠO ĐỀ THI NGAY", type="primary", key="t1_btn"):
            content = read_uploaded_file(uploaded)
            if content:
                with st.spinner("Đang phân tích ma trận và tạo đề..."):
                    prompt = f"""
                    Bạn là chuyên gia giáo dục tiểu học. Nhiệm vụ: Soạn đề thi môn {sub_name_t1} lớp {grade_t1} dựa CHÍNH XÁC vào nội dung file tải lên dưới đây.
                    YÊU CẦU BẮT BUỘC VỀ ĐỊNH DẠNG:
                    1. Tuân thủ tuyệt đối cấu trúc ma trận/bảng đặc tả trong văn bản cung cấp.
                    2. Hiển thị rõ ràng theo định dạng:
                       **Câu [Số thứ tự]** ([Số điểm] đ) - [Mức độ]: [Nội dung câu hỏi]
                       (Xuống dòng) Đáp án: ...
                    3. Đối với TRẮC NGHIỆM: Phải hiển thị các lựa chọn A, B, C, D mỗi lựa chọn một dòng.
                    4. Đối với NỐI CỘT: Phải hiển thị Cột A và Cột B rõ ràng.
                    Dữ liệu đầu vào:
                    {content}
                    """
                    result_text, used_model = generate_content_with_rotation(api_key, prompt)
                    if used_model:
                        st.session_state.exam_result = result_text
                        st.success(f"Đã tạo xong bằng model: {used_model}")
                    else:
                        st.error(result_text)

        if st.session_state.exam_result:
            st.markdown("---")
            edited_text = st.text_area("Sửa nội dung:", value=st.session_state.exam_result, height=500, key="t1_edit")
            st.session_state.exam_result = edited_text 
            docx = create_word_file_simple(school_name_t1, exam_term_t1, edited_text)
            st.download_button("📥 TẢI VỀ FILE WORD (.docx)", docx, file_name=f"De_{sub_name_t1}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")

    # ========================== TAB 2: SOẠN TỪNG CÂU ==========================
    with tab2:
        st.header("Soạn thảo từng câu hỏi theo CSDL")
        col1, col2 = st.columns(2)
        with col1:
            selected_grade = st.selectbox("Chọn Khối Lớp:", list(SUBJECTS_DB.keys()), key="t2_grade")
        with col2:
            subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
            selected_subject_full = st.selectbox("Chọn Môn Học:", subjects_list, key="t2_sub")
            selected_subject = selected_subject_full.split(" ", 1)[1]

        raw_data = CURRICULUM_DB_PROCESSED.get(selected_grade, {}).get(selected_subject, {})

        if not raw_data:
            st.warning("⚠️ Dữ liệu môn này đang cập nhật (Hãy chọn Lớp 1, Lớp 4, Lớp 5 để thấy dữ liệu đầy đủ nhất).")
        else:
            st.markdown("---")
            st.subheader("🛠️ Soạn thảo câu hỏi")
            
            col_a, col_b = st.columns(2)
            with col_a:
                all_terms = list(raw_data.keys())
                selected_term = st.selectbox("Chọn Học kỳ:", all_terms, key="t2_term")
                lessons_in_term = raw_data[selected_term]
                unique_topics = sorted(list(set([l['Chủ đề'] for l in lessons_in_term])))
                selected_topic = st.selectbox("Chọn Chủ đề:", unique_topics, key="t2_topic")

            with col_b:
                filtered_lessons = [l for l in lessons_in_term if l['Chủ đề'] == selected_topic]
                all_lessons_in_topic = []
                for item in filtered_lessons:
                    all_lessons_in_topic.extend(item['Bài học'])
                
                # Hàm callback để tự động lấy YCCĐ
                def on_lesson_change():
                    lesson = st.session_state.t2_lesson
                    with st.spinner("Đang tra cứu YCCĐ chuẩn từ nguồn..."):
                        # Prompt tối ưu để lấy YCCĐ chính xác
                        prompt = f"Trích xuất Yêu cầu cần đạt (YCCĐ) chính xác theo chương trình GDPT 2018 cho bài học: '{lesson}' môn {selected_subject} lớp {selected_grade}. Chỉ trả về nội dung YCCĐ ngắn gọn, không rườm rà."
                        yccd_res, _ = generate_content_with_rotation(api_key, prompt)
                        st.session_state.auto_yccd = yccd_res

                selected_lesson_name = st.selectbox("Chọn Bài học:", all_lessons_in_topic, key="t2_lesson", on_change=on_lesson_change)
                
                # Nếu chưa có YCCĐ (lần đầu load), tự động lấy
                if not st.session_state.auto_yccd:
                     on_lesson_change()

                yccd_input = st.text_area("Yêu cầu cần đạt (YCCĐ):", value=st.session_state.auto_yccd, height=100, key="t2_yccd_input")
                
                current_lesson_data = {
                    "Chủ đề": selected_topic,
                    "Bài học": selected_lesson_name,
                    "YCCĐ": yccd_input
                }

            col_x, col_y, col_z = st.columns(3)
            with col_x:
                question_types = ["Trắc nghiệm nhiều lựa chọn", "Nối cột", "Điền khuyết", "Đúng/Sai", "Tự luận"]
                if selected_subject == "Tin học":
                    question_types.append("Thực hành")
                q_type = st.selectbox("Dạng câu hỏi:", question_types, key="t2_type")
            with col_y:
                level = st.selectbox("Mức độ:", ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"], key="t2_lv")
            with col_z:
                points = st.number_input("Điểm số:", min_value=0.25, max_value=10.0, step=0.25, value=1.0, key="t2_pt")

            def generate_question():
                with st.spinner("AI đang viết câu hỏi chuẩn format..."):
                    random_seed = random.randint(1, 100000)
                    
                    # PROMPT ĐƯỢC CẬP NHẬT ĐỂ ĐẢM BẢO ĐỊNH DẠNG TUYỆT ĐỐI CHÍNH XÁC
                    format_instruction = ""
                    if q_type == "Trắc nghiệm nhiều lựa chọn":
                        format_instruction = """
                        ĐỊNH DẠNG BẮT BUỘC CHO TRẮC NGHIỆM:
                        Nội dung câu hỏi...
                        A. Lựa chọn 1
                        B. Lựa chọn 2
                        C. Lựa chọn 3
                        D. Lựa chọn 4
                        (Xuống dòng) Đáp án: [Chỉ ghi A/B/C/D và nội dung đúng]
                        """
                    elif q_type == "Nối cột":
                        format_instruction = """
                        ĐỊNH DẠNG BẮT BUỘC CHO NỐI CỘT:
                        Hãy tạo bảng hoặc danh sách 2 cột rõ ràng để học sinh nối.
                        Cột A:
                        1. ...
                        2. ...
                        3. ...
                        4. ...
                        Cột B:
                        a. ...
                        b. ...
                        c. ...
                        d. ...
                        (Xuống dòng) Đáp án: [Ví dụ: 1-b, 2-a...]
                        """
                    
                    prompt_q = f"""
                    Đóng vai chuyên gia giáo dục Tiểu học. Soạn **1 CÂU HỎI KIỂM TRA** môn {selected_subject} Lớp {selected_grade}.
                    - Bài học: {current_lesson_data['Bài học']}
                    - YCCĐ: {current_lesson_data['YCCĐ']}
                    - Dạng: {q_type}
                    - Mức độ: {level}
                    - Điểm: {points}
                    {format_instruction}
                    OUTPUT CHỈ GHI NỘI DUNG, KHÔNG CẦN LỜI DẪN THỪA.
                    """
                    preview_content, _ = generate_content_with_rotation(api_key, prompt_q)
                    st.session_state.current_preview = preview_content
                    st.session_state.temp_question_data = {
                        "topic": selected_topic, "lesson": selected_lesson_name,
                        "type": q_type, "level": level, "points": points, "content": preview_content,
                        "yccd": yccd_input, "periods": extract_periods(selected_lesson_name)
                    }

            if st.button("✨ Tạo câu hỏi (Xem trước)", type="primary", key="t2_preview"):
                generate_question()

            if st.session_state.current_preview:
                st.markdown(f"<div class='question-box'>{st.session_state.current_preview}</div>", unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    if st.button("✅ Thêm vào đề thi", key="t2_add"):
                        st.session_state.exam_list.append(st.session_state.temp_question_data)
                        st.session_state.current_preview = ""
                        st.success("Đã thêm vào danh sách!")
                        st.rerun()
                with col_btn2:
                    if st.button("🔄 Tạo câu hỏi khác", key="t2_regen"):
                        generate_question()
                        st.rerun()

            if len(st.session_state.exam_list) > 0:
                st.markdown("---")
                st.subheader(f"📊 Bảng thống kê chi tiết ({len(st.session_state.exam_list)} câu)")
                
                stats_data = []
                for i, q in enumerate(st.session_state.exam_list):
                    stats_data.append({
                        "Thứ tự": f"Câu {i+1}",
                        "Tên bài (Số tiết)": q['lesson'],
                        "Dạng": q['type'],
                        "Điểm": q['points']
                    })
                
                st.dataframe(pd.DataFrame(stats_data), use_container_width=True)

                st.markdown("#### 📝 Chỉnh sửa chi tiết đề thi")
                for i, item in enumerate(st.session_state.exam_list):
                    with st.expander(f"Câu {i+1} ({item['points']} điểm) - {item['type']}"):
                        new_content = st.text_area(f"Nội dung câu {i+1}:", value=item['content'], height=150, key=f"edit_q_{i}")
                        st.session_state.exam_list[i]['content'] = new_content
                        if st.button("🗑️ Xóa câu này", key=f"del_q_{i}"):
                            st.session_state.exam_list.pop(i)
                            st.rerun()

                col_act1, col_act2 = st.columns(2)
                with col_act2:
                     if st.button("❌ Xóa toàn bộ đề", key="t2_clear"):
                        st.session_state.exam_list = []
                        st.rerun()

                docx_file = create_word_from_question_list("TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN", selected_subject, st.session_state.exam_list)
                st.download_button(label="📥 TẢI ĐỀ THI (WORD)", data=docx_file, file_name=f"De_thi_{selected_subject}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")
    
    # ========================== TAB 3: MA TRẬN ĐỀ THI ==========================
    with tab3:
        st.header("📊 BẢNG MA TRẬN ĐỀ THI (BẢN ĐẶC TẢ)")
        st.info("Chỉnh sửa trực tiếp trên bảng và tải về file Word theo mẫu.")
        
        if len(st.session_state.exam_list) == 0:
            st.info("⚠️ Vui lòng soạn câu hỏi ở Tab 2 trước.")
        else:
            matrix_data = []
            for i, q in enumerate(st.session_state.exam_list):
                matrix_data.append({
                    "STT": i + 1,
                    "Chủ đề": q['topic'],
                    "Bài học": q['lesson'],
                    "Yêu cầu cần đạt": q.get('yccd', ''),
                    "Dạng câu hỏi": q['type'],
                    "Mức độ": q['level'],
                    "Số điểm": q['points'],
                    "Ghi chú": ""
                })
            
            df_matrix = pd.DataFrame(matrix_data)
            edited_df = st.data_editor(df_matrix, num_rows="dynamic", use_container_width=True, key="matrix_editor")
            
            if st.button("💾 Cập nhật thay đổi từ Ma trận vào Hệ thống"):
                for index, row in edited_df.iterrows():
                    if index < len(st.session_state.exam_list):
                        st.session_state.exam_list[index]['topic'] = row['Chủ đề']
                        st.session_state.exam_list[index]['lesson'] = row['Bài học']
                        st.session_state.exam_list[index]['type'] = row['Dạng câu hỏi']
                        st.session_state.exam_list[index]['level'] = row['Mức độ']
                        st.session_state.exam_list[index]['points'] = row['Số điểm']
                        st.session_state.exam_list[index]['yccd'] = row['Yêu cầu cần đạt']
                st.success("Đã cập nhật dữ liệu thành công!")
                st.rerun()

            matrix_docx = create_matrix_document(st.session_state.exam_list, selected_subject, selected_grade)
            st.download_button(label="📥 TẢI BẢN ĐẶC TẢ ĐỀ THI (WORD)", data=matrix_docx, file_name=f"Ban_dac_ta_{selected_subject}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")

    # --- FOOTER ---
    st.markdown("""
    <div class="footer">
        <p style="margin: 0; font-weight: bold; color: #2c3e50;">🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
