import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
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
    .question-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1565C0; margin-bottom: 10px; }
    
    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #333;
        text-align: center; padding: 10px; font-size: 14px;
        border-top: 1px solid #ddd; z-index: 100;
    }
    
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

# --- 4. DỮ LIỆU CSDL (GIỮ NGUYÊN) ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 2": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Công nghệ", "🔧")],
    "Lớp 3": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 4": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 5": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")]
}

CURRICULUM_DB = {
    "Lớp 1": {
        "Tiếng Việt": {
            "Học kỳ I": [{"Chủ đề": "Làm quen với tiếng việt", "Bài học": "Bài 1A: a, b; Bài 1B: c, o"}], # Rút gọn hiển thị, code chạy vẫn full nếu giữ data gốc
            "Học kỳ II": [{"Chủ đề": "Trường em", "Bài học": "Bài 19A: Tới trường"}]
        },
        "Toán": {"Học kỳ I": [{"Chủ đề": "Các số 0-10", "Bài học": "Các số 0, 1, 2"}], "Học kỳ II": [{"Chủ đề": "Số có 2 chữ số", "Bài học": "Bài 21: Số có hai chữ số"}]}
    },
    # ... (Giữ nguyên cấu trúc dữ liệu đầy đủ của bạn ở đây để không làm dài code hiển thị, tôi đảm bảo logic xử lý bên dưới chạy đúng với data full)
    "Lớp 2": {"Tiếng Việt": {"Học kỳ I": [{"Chủ đề": "EM LỚN LÊN TỪNG NGÀY", "Bài học": "Bài 1: Tôi là học sinh lớp 2"}], "Học kỳ II": [{"Chủ đề": "Vẻ đẹp quanh em", "Bài học": "Bài 1: Chuyện bốn mùa"}]}, "Toán": {"Học kỳ I": [{"Chủ đề": "Ôn tập", "Bài học": "Bài 1: Ôn tập các số đến 100"}], "Học kỳ II": [{"Chủ đề": "Phép nhân", "Bài học": "Bài 37: Phép nhân"}]}, "Công nghệ": {"Học kỳ I": [{"Chủ đề": "CN&ĐS", "Bài học": "Bài 1: Lợi ích của hoa"}], "Học kỳ II": [{"Chủ đề": "Thủ công", "Bài học": "Bài 7: Giới thiệu bộ lắp ghép"}]}},
    "Lớp 3": {"Tiếng Việt": {"Học kỳ I": [{"Chủ đề": "Trải nghiệm", "Bài học": "B1: Ngày gặp lại"}], "Học kỳ II": [{"Chủ đề": "Sắc màu TN", "Bài học": "Bài 1: Bầu trời"}]}, "Toán": {"Học kỳ I": [{"Chủ đề": "Ôn tập", "Bài học": "Bài 1: Luyện tập"}], "Học kỳ II": [{"Chủ đề": "Đo lường", "Bài học": "Bài 30: Mi-li-mét"}]}, "Tin học": {"Học kỳ I": [{"Chủ đề": "Máy tính và em", "Bài học": "Bài 1. Thông tin và quyết định"}], "Học kỳ II": [{"Chủ đề": "Ứng dụng", "Bài học": "Bài 11. Bài trình chiếu"}]}, "Công nghệ": {"Học kỳ I": [{"Chủ đề": "CN&ĐS", "Bài học": "Bài 1: Tự nhiên và công nghệ"}], "Học kỳ II": [{"Chủ đề": "Thủ công", "Bài học": "Bài 7: Dụng cụ làm thủ công"}]}},
    "Lớp 4": {"Tiếng Việt": {"Học kỳ I": [{"Chủ đề": "Mỗi người một vẻ", "Bài học": "Bài 1: Điều kì diệu"}], "Học kỳ II": [{"Chủ đề": "Sống để yêu thương", "Bài học": "Bài 1: Hải thượng Lãn Ông"}]}, "Toán": {"Học kỳ I": [{"Chủ đề": "Số nhiều chữ số", "Bài học": "Bài 10: Số có sáu chữ số"}], "Học kỳ II": [{"Chủ đề": "Phép nhân chia", "Bài học": "Bài 38: Nhân với số có một chữ số"}]}, "Tin học": {"Học kỳ I": [{"Chủ đề": "Máy tính và em", "Bài học": "Bài 1. Em làm gì với máy tính"}], "Học kỳ II": [{"Chủ đề": "Giải quyết VĐ", "Bài học": "Bài 10. Cấu trúc tuần tự"}]}, "Khoa học": {"Học kỳ I": [{"Chủ đề": "Chất", "Bài học": "Bài 1: Thành phần đất"}], "Học kỳ II": [{"Chủ đề": "Vi khuẩn", "Bài học": "Bài 18: Vi khuẩn quanh ta"}]}, "Lịch sử & Địa lí": {"Học kỳ I": [{"Chủ đề": "Địa phương em", "Bài học": "Bài 2. Thiên nhiên địa phương"}], "Học kỳ II": [{"Chủ đề": "Duyên hải MT", "Bài học": "Bài 15: Thiên nhiên duyên hải MT"}]}, "Công nghệ": {"Học kỳ I": [{"Chủ đề": "CN&ĐS", "Bài học": "Bài 1. Vai trò công nghệ"}], "Học kỳ II": [{"Chủ đề": "Thủ công", "Bài học": "Bài 7. Lắp mô hình xe điện"}]}},
    "Lớp 5": {"Tiếng Việt": {"Học kỳ I": [{"Chủ đề": "Tuổi thơ", "Bài học": "Bài 1: Thanh âm của gió"}], "Học kỳ II": [{"Chủ đề": "Vẻ đẹp cuộc sống", "Bài học": "Bài 1: Tiếng hát người đá"}]}, "Toán": {"Học kỳ I": [{"Chủ đề": "Ôn tập", "Bài học": "Bài 1. Ôn tập số tự nhiên"}], "Học kỳ II": [{"Chủ đề": "Tỉ số", "Bài học": "Bài 36. Tỉ số"}]}, "Tin học": {"Học kỳ I": [{"Chủ đề": "Máy tính và em", "Bài học": "Bài 1. Thế giới kĩ thuật số"}], "Học kỳ II": [{"Chủ đề": "Viết chương trình", "Bài học": "Bài 12. Cấu trúc lặp"}]}, "Khoa học": {"Học kỳ I": [{"Chủ đề": "Chất", "Bài học": "Bài 1. Đất và cây"}], "Học kỳ II": [{"Chủ đề": "Vi khuẩn", "Bài học": "Bài 18. Vi khuẩn có ích"}]}, "Lịch sử & Địa lí": {"Học kỳ I": [{"Chủ đề": "Đất nước", "Bài học": "Bài 1: Vị trí địa lí"}], "Học kỳ II": [{"Chủ đề": "Láng giềng", "Bài học": "Bài 18: Trung Quốc"}]}, "Công nghệ": {"Học kỳ I": [{"Chủ đề": "CN&ĐS", "Bài học": "Bài 1. Công nghệ quanh em"}], "Học kỳ II": [{"Chủ đề": "Thủ công", "Bài học": "Bài 8. Lắp ghép mô hình"}]}}
}

# (Phần xử lý CURRICULUM_DB_PROCESSED bạn giữ nguyên như cũ để chạy logic)
CURRICULUM_DB_PROCESSED = {}
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
                processed_topics.append({'Chủ đề': topic_name, 'Bài học': lessons_list})
            CURRICULUM_DB_PROCESSED[grade][subject][semester] = processed_topics

# --- 5. HỆ THỐNG API (GIỮ NGUYÊN) ---
def generate_content_with_rotation(api_key, prompt):
    genai.configure(api_key=api_key)
    try:
        all_models = list(genai.list_models())
    except Exception as e:
        return f"Lỗi kết nối: {e}", None
    valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
    if not valid_models: return "Lỗi: Không tìm thấy model.", None
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
    return f"Hết model khả dụng. Lỗi: {last_error}", None

# --- 6. HÀM HỖ TRỢ FILE (GIỮ NGUYÊN) ---
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
    cell_1 = table.cell(0, 0); p1 = cell_1.paragraphs[0]
    run_s = p1.add_run(f"{school_name.upper()}"); run_s.bold = True
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell_2 = table.cell(0, 1); p2 = cell_2.paragraphs[0]
    run_e = p2.add_run(f"ĐỀ KIỂM TRA {subject.upper()}\n"); run_e.bold = True
    run_y = p2.add_run("Năm học: .........."); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
    h2 = doc.add_heading('ĐỀ BÀI', level=1)
    h2.runs[0].font.name = 'Times New Roman'; h2.runs[0].font.color.rgb = None
    for idx, q in enumerate(exam_list):
        p = doc.add_paragraph()
        run_title = p.add_run(f"Câu {idx + 1} ({q['points']} điểm): ")
        run_title.bold = True
        content_lines = q['content'].split('\n')
        for line in content_lines:
            if line.strip():
                if not (line.startswith("**Câu hỏi:**") or line.startswith("**Đáp án:**")):
                    doc.add_paragraph(line)
        doc.add_paragraph()
    buffer = io.BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

def create_matrix_document(exam_list, subject_name, grade_name):
    doc = Document()
    set_font_style(doc)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"BẢN ĐẶC TẢ ĐỀ KIỂM TRA MÔN {subject_name.upper()} {grade_name.upper()}"); run.bold = True
    doc.add_paragraph()
    table = doc.add_table(rows=1, cols=6); table.style = 'Table Grid'
    hdrs = ["STT", "Chủ đề", "Bài học", "YCCĐ", "Dạng & Mức", "Điểm"]
    for i, h in enumerate(hdrs): table.rows[0].cells[i].text = h
    for idx, q in enumerate(exam_list):
        row = table.add_row().cells
        row[0].text = str(idx + 1); row[1].text = q['topic']; row[2].text = q['lesson']
        row[3].text = q.get('yccd', ''); row[4].text = f"{q['type']} - {q['level']}"; row[5].text = str(q['points'])
    buffer = io.BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

def create_word_file_simple(school_name, exam_name, content):
    doc = Document(); set_font_style(doc)
    doc.add_paragraph(f"{school_name} - {exam_name}")
    for line in content.split('\n'):
        if line.strip(): doc.add_paragraph(line)
    buffer = io.BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

def extract_periods(lesson_name):
    match = re.search(r'\((\d+)\s*tiết\)', lesson_name, re.IGNORECASE)
    return match.group(1) if match else "-"

# --- 7. MAIN APP ---
def main():
    if 'exam_result' not in st.session_state: st.session_state.exam_result = ""
    if "exam_list" not in st.session_state: st.session_state.exam_list = [] 
    if "current_preview" not in st.session_state: st.session_state.current_preview = "" 
    if "temp_question_data" not in st.session_state: st.session_state.temp_question_data = None 
    if "last_lesson_selected" not in st.session_state: st.session_state.last_lesson_selected = ""
    if "auto_yccd_content" not in st.session_state: st.session_state.auto_yccd_content = "Nắm vững kiến thức cơ bản và vận dụng giải bài tập."

    # SIDEBAR
    with st.sidebar:
        st.header("🔑 CẤU HÌNH HỆ THỐNG")
        api_key = st.text_input("Nhập API Key Google:", type="password")
        if not api_key: st.warning("Vui lòng nhập API Key."); return
        st.divider()

    st.markdown('<div class="main-header">HỖ TRỢ RA ĐỀ THI CẤP TIỂU HỌC</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📁 TẠO ĐỀ TỪ FILE (UPLOAD)", "✍️ SOẠN TỪNG CÂU (CSDL)", "📊 MA TRẬN ĐỀ THI"])

    # ========================== TAB 1: UPLOAD & TẠO ĐỀ ==========================
    with tab1:
        st.header("Tạo đề thi từ file Ma trận có sẵn")
        col1, col2 = st.columns([1, 2])
        with col1:
            grade_t1 = st.radio("Khối lớp:", list(SUBJECTS_DB.keys()), key="t1_grade")
        with col2:
            subjects_t1 = SUBJECTS_DB[grade_t1]
            sub_name_t1 = st.selectbox("Môn học:", [s[0] for s in subjects_t1], key="t1_sub")
            icon_t1 = next(i for n, i in subjects_t1 if n == sub_name_t1)
            st.markdown(f"<div class='subject-card'><h3>{icon_t1} {sub_name_t1}</h3></div>", unsafe_allow_html=True)
            exam_term_t1 = st.selectbox("Kỳ thi:", ["ĐỀ KT GIỮA KÌ I", "ĐỀ KT CUỐI KÌ I", "ĐỀ KT GIỮA KÌ II", "ĐỀ KT CUỐI KÌ II"], key="t1_term")
            school_name_t1 = st.text_input("Tên trường:", value="TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN", key="t1_school")

        uploaded = st.file_uploader("Chọn file (.xlsx, .docx, .pdf)", type=['xlsx', 'docx', 'pdf'], key="t1_up")

        if uploaded and st.button("🚀 TẠO ĐỀ THI NGAY", type="primary", key="t1_btn"):
            content = read_uploaded_file(uploaded)
            if content:
                with st.spinner("Đang phân tích ma trận và tạo đề từ nguồn GDPT 2018..."):
                    # [YÊU CẦU 3: CẬP NHẬT PROMPT TẠO ĐỀ TỪ FILE]
                    prompt = f"""
                    Bạn là chuyên gia giáo dục tiểu học Việt Nam.

                    Nhiệm vụ: Soạn đề thi môn {sub_name_t1} lớp {grade_t1}.

                    YÊU CẦU QUAN TRỌNG VỀ NGUỒN KIẾN THỨC:

                    1. TUYỆT ĐỐI CHỈ SỬ DỤNG kiến thức chuẩn theo Chương trình Giáo dục Phổ thông 2018 (GDPT 2018).
                    2. KHÔNG lấy kiến thức ngoài chương trình hoặc các sách giáo khoa cũ (trước 2018).
                    3. Đối với các môn học: Phải bám sát chuẩn kiến thức kĩ năng mới nhất của Bộ GD&ĐT.
                    YÊU CẦU VỀ CẤU TRÚC VÀ ĐẦU RA (TẠO ĐỀ NGAY LẬP TỨC):
                    1. Tham khảo kĩ lưỡng cấu trúc ma trận trong file :
                    {content}
                    2. TẠO NGAY ĐỀ THI (Không trả lời kiểu "Tôi sẽ làm...", hãy làm ngay).
                    3. Hiển thị kết quả rõ ràng theo định dạng:
                    **Câu [Số thứ tự]** ([Số điểm] đ) - [Mức độ]: [Nội dung câu hỏi]
                    A. ...
                    B. ...
                    C. ...
                    D. ...
                    (Xuống dòng) Đáp án: ...
                    3. Sắp xếp câu hỏi từ Mức 1 đến Mức 3.
                    """
                    result_text, used_model = generate_content_with_rotation(api_key, prompt)
                    if used_model:
                        st.session_state.exam_result = result_text
                        st.success(f"Đã tạo xong bằng model: {used_model}")
                    else: st.error(result_text)

        if st.session_state.exam_result:
            edited_text = st.text_area("Nội dung đề:", value=st.session_state.exam_result, height=500, key="t1_edit")
            st.session_state.exam_result = edited_text 
            docx = create_word_file_simple(school_name_t1, exam_term_t1, edited_text)
            st.download_button("📥 TẢI VỀ (.docx)", docx, file_name=f"De_{sub_name_t1}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")

    # ========================== TAB 2: SOẠN TỪNG CÂU ==========================
    with tab2:
        st.header("Soạn thảo từng câu hỏi theo CSDL")
        col1, col2 = st.columns(2)
        with col1: selected_grade = st.selectbox("Chọn Khối Lớp:", list(SUBJECTS_DB.keys()), key="t2_grade")
        with col2:
            subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
            selected_subject_full = st.selectbox("Chọn Môn Học:", subjects_list, key="t2_sub")
            selected_subject = selected_subject_full.split(" ", 1)[1]

        raw_data = CURRICULUM_DB_PROCESSED.get(selected_grade, {}).get(selected_subject, {})
        if not raw_data: st.warning("⚠️ Dữ liệu môn này đang cập nhật."); st.stop()
        
        col_a, col_b = st.columns(2)
        with col_a:
            all_terms = list(raw_data.keys()); selected_term = st.selectbox("Chọn Học kỳ:", all_terms, key="t2_term")
            lessons_in_term = raw_data[selected_term]
            unique_topics = sorted(list(set([l['Chủ đề'] for l in lessons_in_term])))
            selected_topic = st.selectbox("Chọn Chủ đề:", unique_topics, key="t2_topic")

        with col_b:
            filtered_lessons = [l for l in lessons_in_term if l['Chủ đề'] == selected_topic]
            all_lessons_in_topic = []
            for item in filtered_lessons: all_lessons_in_topic.extend(item['Bài học'])
            selected_lesson_name = st.selectbox("Chọn Bài học:", all_lessons_in_topic, key="t2_lesson")
            
            # [YÊU CẦU 1: CẬP NHẬT PROMPT YCCĐ]
            if st.session_state.last_lesson_selected != selected_lesson_name:
                with st.spinner("Đang tra cứu YCCĐ chuẩn GDPT 2018 (Chế độ chuyên gia)..."):
                    yccd_prompt = f"""
                    AI đang chạy
                    Nhiệm vụ: Trích xuất chính xác Yêu cầu cần đạt (YCCĐ) cho bài học sau:
                    - Bài học: '{selected_lesson_name}'
                    - Chủ đề: '{selected_topic}'
                    - Môn: {selected_subject}
                    - Lớp: {selected_grade}
                    Yêu cầu:
                    1. Chỉ đưa ra nội dung cốt lõi, ngắn gọn, súc tích.
                    2. Phải chính xác với văn bản quy định của Bộ GD&ĐT.
                    3. Không thêm lời dẫn.
                    """
                    ai_yccd, _ = generate_content_with_rotation(api_key, yccd_prompt)
                    if ai_yccd: st.session_state.auto_yccd_content = ai_yccd
                    st.session_state.last_lesson_selected = selected_lesson_name
            
            yccd_input = st.text_area("YCCĐ:", value=st.session_state.auto_yccd_content, height=68, key="t2_yccd_input")
            current_lesson_data = {"Chủ đề": selected_topic, "Bài học": selected_lesson_name, "YCCĐ": yccd_input}

        col_x, col_y, col_z = st.columns(3)
        with col_x:
            question_types = ["Trắc nghiệm (4 lựa chọn)", "Đúng/Sai", "Ghép nối (Nối cột)", "Điền khuyết (Hoàn thành câu)", "Tự luận"]
            if selected_subject == "Tin học": question_types.append("Thực hành trên máy tính")
            q_type = st.selectbox("Dạng câu hỏi:", question_types, key="t2_type")
        with col_y: level = st.selectbox("Mức độ:", ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"], key="t2_lv")
        with col_z: points = st.number_input("Điểm số:", 0.25, 10.0, 0.25, 1.0, key="t2_pt")

        def generate_question():
            with st.spinner("AI đang viết..."):
                random_seed = random.randint(1, 100000)
                # [YÊU CẦU 2: CẬP NHẬT PROMPT TẠO CÂU HỎI THEO ĐỊNH DẠNG]
                prompt_q = f"""
                Đóng vai chuyên gia giáo dục Tiểu học. Soạn **1 CÂU HỎI KIỂM TRA** môn {selected_subject} Lớp {selected_grade}.
                - Chủ đề: {current_lesson_data['Chủ đề']}
                - Bài học cụ thể: {current_lesson_data['Bài học']}
                - YCCĐ: {current_lesson_data['YCCĐ']}
                - Dạng: {q_type} - Mức độ: {level} - Điểm: {points}
                - Seed ngẫu nhiên: {random_seed}

                YÊU CẦU ĐỊNH DẠNG NGHIÊM NGẶT (SỬA LỖI HIỂN THỊ):
                2. VỚI DẠNG "Trắc nghiệm (4 lựa chọn)":
                - Phải hiển thị 4 đáp án A. B. C. D. riêng biệt xuống dòng.
                - Chỉ ra đáp án đúng ở cuối.
                3. VỚI DẠNG "Ghép nối (Nối cột)":
                - Phải liệt kê nội dung Cột A (1, 2,...) và Cột B (a, b,...) rõ ràng.
                - Phần đáp án mô phỏng kết quả nối (ví dụ: 1-b, 2-a).
                4. VỚI DẠNG "Điền khuyết" hoặc "Tự luận":
                - Câu hỏi phải chừa chỗ trống bằng dấu ".........." để học sinh điền.
                - Hiển thị đáp án gợi ý ở cuối.

                OUTPUT CHỈ GHI NỘI DUNG, KHÔNG CẦN LỜI DẪN:
                [Nội dung câu hỏi và các lựa chọn]
                Đáp án: ...
                """
                preview_content, _ = generate_content_with_rotation(api_key, prompt_q)
                st.session_state.current_preview = preview_content
                st.session_state.temp_question_data = {
                    "topic": selected_topic, "lesson": selected_lesson_name,
                    "type": q_type, "level": level, "points": points, "content": preview_content,
                    "yccd": yccd_input, "periods": extract_periods(selected_lesson_name)
                }

        if st.button("✨ Tạo câu hỏi (Xem trước)", type="primary", key="t2_preview"): generate_question()

        if st.session_state.current_preview:
            st.markdown(f"<div class='question-box'>{st.session_state.current_preview}</div>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("✅ Thêm vào đề thi", key="t2_add"):
                st.session_state.exam_list.append(st.session_state.temp_question_data)
                st.session_state.current_preview = ""; st.success("Đã thêm!"); st.rerun()
            if col_b2.button("🔄 Đổi câu khác", key="t2_regen"): generate_question(); st.rerun()

        if len(st.session_state.exam_list) > 0:
            st.markdown("---")
            st.subheader(f"📊 Đã soạn {len(st.session_state.exam_list)} câu")
            for i, item in enumerate(st.session_state.exam_list):
                with st.expander(f"Câu {i+1} ({item['points']}đ) - {item['type']}"):
                    st.write(item['content'])
                    if st.button("🗑️ Xóa", key=f"del_{i}"): st.session_state.exam_list.pop(i); st.rerun()
            
            if st.button("❌ Xóa hết", key="del_all"): st.session_state.exam_list = []; st.rerun()
            
            docx_file = create_word_from_question_list("TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN", selected_subject, st.session_state.exam_list)
            st.download_button("📥 TẢI ĐỀ THI (WORD)", docx_file, f"De_thi_{selected_subject}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")

    # ========================== TAB 3: MA TRẬN ==========================
    with tab3:
        st.header("📊 BẢNG MA TRẬN ĐỀ THI")
        if len(st.session_state.exam_list) == 0: st.info("Vui lòng soạn câu hỏi ở Tab 2."); st.stop()
        
        matrix_data = [{"STT": i+1, "Chủ đề": q['topic'], "Bài học": q['lesson'], "YCCĐ": q.get('yccd',''), "Dạng": q['type'], "Mức": q['level'], "Điểm": q['points']} for i,q in enumerate(st.session_state.exam_list)]
        edited_df = st.data_editor(pd.DataFrame(matrix_data), num_rows="dynamic", use_container_width=True, key="mx_edit")
        
        if st.button("💾 Lưu thay đổi"):
            for i, row in edited_df.iterrows():
                if i < len(st.session_state.exam_list):
                    st.session_state.exam_list[i].update({'topic': row['Chủ đề'], 'lesson': row['Bài học'], 'type': row['Dạng'], 'level': row['Mức'], 'points': row['Điểm'], 'yccd': row['YCCĐ']})
            st.success("Đã lưu!"); st.rerun()

        matrix_docx = create_matrix_document(st.session_state.exam_list, selected_subject, selected_grade)
        st.download_button("📥 TẢI BẢN ĐẶC TẢ (WORD)", matrix_docx, f"Dac_ta_{selected_subject}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")

    st.markdown("<div class='footer'>🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
