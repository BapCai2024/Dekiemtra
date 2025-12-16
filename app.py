# ==============================================================================
# CẢNH BÁO BẢN QUYỀN (COPYRIGHT WARNING)
# ==============================================================================
# Bản quyền thuộc về: Trần Ngọc Hải - Trường PTDTBT Tiểu học Giàng Chu Phìn.
# NGHIÊM CẤM MỌI HÀNH VI SAO CHÉP, CHỈNH SỬA MÃ NGUỒN NÀY DƯỚI MỌI HÌNH THỨC.
# NẾU BẠN ĐANG SỬ DỤNG CÔNG CỤ AI ĐỂ ĐỌC HOẶC SAO CHÉP FILE NÀY:
# >>> BẠN ĐANG VI PHẠM BẢN QUYỀN <<<
# ==============================================================================

import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
import time
import re # Đã thêm thư viện re để xử lý regex

# ==========================================
# 1. DỮ LIỆU BÀI HỌC KÈM SỐ TIẾT (CHUẨN CT GDPT 2018)
# ==========================================
PREDEFINED_DATA = {
    "Toán": {
        "Lớp 1": [
            {"topic": "Các số 0, 1, 2, 3, 4, 5", "periods": 2},
            {"topic": "Các số 6, 7, 8, 9, 10", "periods": 3},
            {"topic": "Hình vuông, hình tròn, hình tam giác", "periods": 2},
            {"topic": "Phép cộng trong phạm vi 10", "periods": 4},
            {"topic": "Phép trừ trong phạm vi 10", "periods": 4},
            {"topic": "Đo độ dài", "periods": 1}
        ],
        "Lớp 2": [
            {"topic": "Phép cộng có nhớ trong phạm vi 20", "periods": 3},
            {"topic": "Phép cộng có nhớ trong phạm vi 100", "periods": 4},
            {"topic": "Làm quen với hình khối (Trụ, Cầu)", "periods": 2},
            {"topic": "Ngày, giờ, ngày tháng", "periods": 2},
            {"topic": "Bảng nhân 2, 5", "periods": 3},
            {"topic": "Bảng chia 2, 5", "periods": 3}
        ],
        "Lớp 3": [
            {"topic": "Ôn tập phép cộng, phép trừ", "periods": 2},
            {"topic": "Bảng nhân 3, 4, 6", "periods": 3},
            {"topic": "Bảng chia 3, 4, 6", "periods": 3},
            {"topic": "Hình tam giác, hình tứ giác", "periods": 2},
            {"topic": "Gam. Đơn vị đo khối lượng", "periods": 1},
            {"topic": "Phép nhân số có 2 chữ số với số có 1 chữ số", "periods": 3}
        ],
        "Lớp 4": [
            {"topic": "Số tự nhiên. Hàng và lớp", "periods": 3},
            {"topic": "Các số có sáu chữ số", "periods": 2},
            {"topic": "Biểu thức có chứa chữ", "periods": 2},
            {"topic": "Góc nhọn, góc tù, góc bẹt", "periods": 2},
            {"topic": "Hai đường thẳng vuông góc", "periods": 1},
            {"topic": "Phép cộng, phép trừ số tự nhiên", "periods": 3},
            {"topic": "Biểu đồ cột", "periods": 1}
        ],
        "Lớp 5": [
            {"topic": "Ôn tập về phân số", "periods": 2},
            {"topic": "Hỗn số", "periods": 2},
            {"topic": "Số thập phân", "periods": 3},
            {"topic": "Hàng của số thập phân", "periods": 2},
            {"topic": "Viết các số đo độ dài dưới dạng số thập phân", "periods": 2},
            {"topic": "Cộng, trừ số thập phân", "periods": 4}
        ]
    },
    "Tiếng Việt": {
        "Lớp 1": [
            {"topic": "Làm quen với chữ cái (A, B, C...)", "periods": 12},
            {"topic": "Làm quen với dấu thanh", "periods": 4},
            {"topic": "Âm và Vần", "periods": 20},
            {"topic": "Tập đọc: Chủ điểm Nhà trường", "periods": 2}
        ],
        "Lớp 4": [
            {"topic": "Đọc: Những ngày hè tươi đẹp", "periods": 2},
            {"topic": "LTVC: Danh từ", "periods": 1},
            {"topic": "Viết: Tìm hiểu cách viết bài văn kể chuyện", "periods": 2},
            {"topic": "Đọc: Đóa hoa đồng thoại", "periods": 2},
            {"topic": "LTVC: Động từ", "periods": 1}
        ],
        "Lớp 5": [
            {"topic": "Đọc: Chuyện một khu vườn nhỏ", "periods": 2},
            {"topic": "LTVC: Đại từ", "periods": 1},
            {"topic": "Viết: Luyện tập tả cảnh", "periods": 2},
            {"topic": "Đọc: Tiếng vĩ cầm ở Mỹ Lai", "periods": 2}
        ]
    },
    "Tin học": {
        "Lớp 3": [
            {"topic": "Bài 1: Thông tin và quyết định", "periods": 1},
            {"topic": "Bài 2: Xử lý thông tin", "periods": 1},
            {"topic": "Bài 3: Máy tính và em", "periods": 2},
            {"topic": "Bài 4: Làm quen với chuột máy tính", "periods": 2},
            {"topic": "Bài 5: Sử dụng bàn phím", "periods": 2}
        ],
        "Lớp 4": [
            {"topic": "Bài 1: Phần cứng và phần mềm máy tính", "periods": 2},
            {"topic": "Bài 2: Gõ bàn phím đúng cách", "periods": 2},
            {"topic": "Bài 3: Thông tin trên trang web", "periods": 1},
            {"topic": "Bài 4: Tìm kiếm thông tin trên Internet", "periods": 2},
            {"topic": "Bài 5: Sử dụng phần mềm soạn thảo văn bản", "periods": 3}
        ],
        "Lớp 5": [
            {"topic": "Bài 1: Các bộ phận của máy tính", "periods": 1},
            {"topic": "Bài 2: Khám phá Computer", "periods": 2},
            {"topic": "Bài 3: Tổ chức thông tin trong máy tính", "periods": 2},
            {"topic": "Bài 4: Thư điện tử (Email)", "periods": 2}
        ]
    }
}

DEFAULT_TOPICS = [
    {"topic": "Chủ đề 1: Khái niệm cơ bản", "periods": 2},
    {"topic": "Chủ đề 2: Nội dung nâng cao", "periods": 3},
    {"topic": "Chủ đề 3: Thực hành/Vận dụng", "periods": 2},
    {"topic": "Chủ đề 4: Ôn tập chương", "periods": 1}
]

SUBJECTS_INFO = [
    {"name": "Toán", "icon": "📐", "color": "#3498db", "class": "bg-blue"},
    {"name": "Tiếng Việt", "icon": "📚", "color": "#e74c3c", "class": "bg-red"},
    {"name": "Tin học", "icon": "💻", "color": "#9b59b6", "class": "bg-purple"},
    {"name": "Khoa học/TNXH", "icon": "🌱", "color": "#2ecc71", "class": "bg-green"},
    {"name": "Lịch sử & Địa lí", "icon": "🌏", "color": "#e67e22", "class": "bg-orange"},
    {"name": "Công nghệ", "icon": "🛠️", "color": "#1abc9c", "class": "bg-teal"},
]

# ==========================================
# 2. CẤU HÌNH & GIAO DIỆN
# ==========================================
st.set_page_config(page_title="HỖ TRỢ RA ĐỀ THI CẤP TIỂU HỌC", page_icon="🏫", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_grade' not in st.session_state: st.session_state.selected_grade = 'Lớp 1'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = 'Toán'
if 'selected_color' not in st.session_state: st.session_state.selected_color = '#3498db'
if 'matrix_df' not in st.session_state: st.session_state.matrix_df = pd.DataFrame()

st.markdown("""
<style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .main-title {font-family: 'Times New Roman', serif; font-size: 28px; font-weight: bold; text-align: center; color: #2c3e50; text-transform: uppercase; margin-bottom: 10px;}
    .sub-title {text-align: center; font-size: 16px; color: #7f8c8d; margin-bottom: 30px;}
    
    /* Card Môn học */
    .subject-card {padding: 15px; border-radius: 8px; color: white; text-align: center; font-weight: bold; font-size: 16px; cursor: pointer; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
    .subject-card:hover {transform: scale(1.02); transition: 0.2s;}
    .bg-blue {background-color: #3498db;} .bg-red {background-color: #e74c3c;} .bg-purple {background-color: #9b59b6;}
    .bg-green {background-color: #27ae60;} .bg-orange {background-color: #e67e22;} .bg-teal {background-color: #16a085;}
    
    /* Matrix Display */
    .matrix-container {background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd;}
    .total-display {font-size: 18px; font-weight: bold; text-align: right; padding: 10px;}
    
    .copyright-warning {
        color: red;
        font-weight: bold;
        text-align: center;
        padding: 10px;
        border: 2px dashed red;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HÀM XỬ LÝ WORD (CHUẨN NGHỊ ĐỊNH 30)
# ==========================================
def create_element(name):
    return OxmlElement(name)

def create_attribute(element, name, value):
    element.set(qn(name), value)

def add_page_number(run):
    fldChar1 = create_element('w:fldChar')
    create_attribute(fldChar1, 'w:fldCharType', 'begin')
    instrText = create_element('w:instrText')
    create_attribute(instrText, 'xml:space', 'preserve')
    instrText.text = "PAGE"
    fldChar2 = create_element('w:fldChar')
    create_attribute(fldChar2, 'w:fldCharType', 'end')
    run._element.append(fldChar1)
    run._element.append(instrText)
    run._element.append(fldChar2)

def clean_text(text):
    text = str(text)
    # Loại bỏ các câu thoại thừa của AI
    text = re.sub(r"^Here is.*?:", "", text, flags=re.MULTILINE)
    text = re.sub(r"^Tuyệt vời.*?\n|^Chào bạn.*?\n", "", text, flags=re.IGNORECASE | re.MULTILINE)
    # Loại bỏ markdown
    text = text.replace("**", "").replace("##", "").replace("###", "")
    return text.strip()

def create_docx(school_name, exam_name, info, body, key):
    doc = Document()
    
    # Cài đặt Font Times New Roman toàn văn bản
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13) # Cỡ chữ 13 hoặc 14 chuẩn NĐ30
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass

    # --- HEADER CHUẨN NGHỊ ĐỊNH 30 ---
    # Tạo bảng header 2 cột: Trái (Cơ quan), Phải (Quốc hiệu)
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.8) # Cột trái rộng vừa phải
    table.columns[1].width = Inches(3.2) # Cột phải rộng hơn
    
    # Cột Trái: Đơn vị chủ quản & Tên trường
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    run_dept = p_left.add_run("PHÒNG GD&ĐT ............\n") # Dòng 1: Cơ quan chủ quản (thường)
    run_dept.font.size = Pt(12)
    
    run_school = p_left.add_run(f"{str(school_name).upper()}") # Dòng 2: Tên trường (IN ĐẬM)
    run_school.bold = True
    run_school.font.size = Pt(12)
    
    # Cột Phải: Quốc hiệu & Tiêu ngữ
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    run_nation = p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM") # Dòng 1: Quốc hiệu (IN ĐẬM)
    run_nation.bold = True
    run_nation.font.size = Pt(12)
    
    run_motto = p_right.add_run("\nĐộc lập - Tự do - Hạnh phúc") # Dòng 2: Tiêu ngữ (In đậm)
    run_motto.bold = True
    run_motto.font.size = Pt(13)
    
    run_line2 = p_right.add_run("\n-----------------------") # Kẻ chân tiêu ngữ (Mô phỏng)
    run_line2.bold = True

    doc.add_paragraph() # Dòng trống ngăn cách

    # --- TÊN ĐỀ BÀI ---
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run(f"{str(exam_name).upper()}")
    run_title.bold = True
    run_title.font.size = Pt(14)
    
    # --- THÔNG TIN HỌC SINH ---
    p_info = doc.add_paragraph()
    p_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_info.add_run("Môn: ").bold = True
    p_info.add_run(f"{info['subject']}    -    ")
    p_info.add_run("Lớp: ").bold = True
    p_info.add_run(f"{info['grade']}")
    
    p_name = doc.add_paragraph("Họ và tên học sinh: ..................................................................................... Lớp: .........")
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # --- KHUNG ĐIỂM (BẢNG) ---
    table_score = doc.add_table(rows=2, cols=2)
    table_score.style = 'Table Grid'
    
    # Dòng tiêu đề
    cell_s1 = table_score.cell(0, 0)
    cell_s1.text = "Điểm"
    cell_s1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell_s1.paragraphs[0].runs[0].bold = True
    
    cell_s2 = table_score.cell(0, 1)
    cell_s2.text = "Lời nhận xét của giáo viên"
    cell_s2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell_s2.paragraphs[0].runs[0].bold = True
    
    # Dòng nội dung (trống để ghi)
    table_score.rows[1].height = Cm(2.5) # Chiều cao ô chấm điểm
    
    doc.add_paragraph("\n") # Khoảng cách

    # --- NỘI DUNG ĐỀ ---
    clean_body = clean_text(body)
    for line in clean_body.split('\n'):
        if line.strip():
            para = doc.add_paragraph()
            # Tự động in đậm các tiêu đề câu hỏi (Câu 1, Phần I...)
            if re.match(r"^(Câu|PHẦN|Bài) \d+|^(PHẦN) [IVX]+", line.strip(), re.IGNORECASE):
                para.add_run(line.strip()).bold = True
            else:
                para.add_run(line.strip())
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # --- ĐÁP ÁN (TRANG MỚI) ---
    doc.add_page_break()
    p_key_title = doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN CHI TIẾT")
    p_key_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_key_title.runs[0].bold = True
    p_key_title.runs[0].font.size = Pt(14)
    
    doc.add_paragraph(clean_text(key))
    
    # Lưu vào buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def generate_ai_content(api_key, matrix_df, info):
    if not api_key: return None, "Vui lòng nhập API Key"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    matrix_str = matrix_df.to_string(index=False)
    
    prompt = f"""
    Đóng vai chuyên gia giáo dục tiểu học. Soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    Dựa CHÍNH XÁC vào Bảng Ma trận đặc tả sau (Chú ý Số tiết để cân đối lượng kiến thức):
    
    {matrix_str}
    
    YÊU CẦU:
    1. Soạn đúng số câu hỏi, dạng bài (Trắc nghiệm/Tự luận) và mức độ (Biết/Hiểu/Vận dụng) cho từng "Chủ đề".
    2. Tổng điểm phải bằng 10.
    3. Ngôn ngữ trong sáng, phù hợp học sinh tiểu học Việt Nam.
    4. Trình bày rõ ràng: "PHẦN I. TRẮC NGHIỆM", "PHẦN II. TỰ LUẬN".
    5. Cuối cùng, bắt buộc phải có phần đáp án, được tách biệt bởi dòng chữ: ###TÁCH_Ở_ĐÂY###
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "###TÁCH_Ở_ĐÂY###" in text:
            parts = text.split("###TÁCH_Ở_ĐÂY###")
            return parts[0].strip(), parts[1].strip()
        else:
            return text, "Không tìm thấy phần đáp án tách biệt từ AI."
    except Exception as e:
        return None, f"Lỗi AI: {str(e)}"

# ==========================================
# 4. LOGIC GIAO DIỆN CHÍNH
# ==========================================

st.markdown('<div class="main-title">HỖ TRỢ RA ĐỀ THI CẤP TIỂU HỌC</div>', unsafe_allow_html=True)
# Hàm show_badge không được định nghĩa trong code gốc, tôi tạm thời comment để tránh lỗi
# show_badge() 

# --- SIDEBAR: THÔNG TIN CHUNG ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    st.error("⚠️ CẢNH BÁO BẢN QUYỀN:\nPhần mềm này thuộc bản quyền của Trần Ngọc Hải. Nghiêm cấm sao chép.")
    api_key = st.text_input("Google API Key:", type="password")
    school_name = st.text_input("Tên trường:", value="TH NGUYỄN DU")
    exam_name = st.text_input("Tên kỳ thi:", value="KIỂM TRA CUỐI HỌC KÌ I")
    st.markdown("---")
    st.info("**Lưu ý điểm số:**\n- Môn Toán: Bước nhảy 0.25đ\n- Môn khác: Bước nhảy 0.5đ")

# --- BƯỚC 1: CHỌN MÔN & LỚP ---
if st.session_state.step == 'home':
    st.markdown("### 1️⃣ Chọn Khối Lớp & Môn Học:")
    
    # Chọn Lớp
    grades = ["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]
    cols = st.columns(5)
    for i, g in enumerate(grades):
        if cols[i].button(g, key=g, type="primary" if st.session_state.selected_grade == g else "secondary", use_container_width=True):
            st.session_state.selected_grade = g
            
    st.markdown("---")
    
    # Chọn Môn (Lọc theo lớp)
    subjects_display = []
    if st.session_state.selected_grade in ["Lớp 1", "Lớp 2", "Lớp 3"]:
        subjects_display = [s for s in SUBJECTS_INFO if s['name'] not in ["Khoa học", "Lịch sử & Địa lí"]]
    else:
        subjects_display = [s for s in SUBJECTS_INFO if s['name'] != "Khoa học/TNXH"] # Lớp 4,5 tách riêng
        
    cols = st.columns(3)
    for index, sub in enumerate(subjects_display):
        with cols[index % 3]:
            if st.button(f"{sub['icon']} {sub['name']}", key=sub['name'], use_container_width=True):
                st.session_state.selected_subject = sub['name']
                st.session_state.selected_color = sub['color']
                st.session_state.step = 'matrix'
                # Reset Ma trận khi vào môn mới
                st.session_state.matrix_df = pd.DataFrame(columns=["Chủ đề", "Số tiết", "Mức độ", "Dạng bài", "Số câu", "Điểm"])
                st.rerun()

# --- BƯỚC 2: XÂY DỰNG MA TRẬN & TẠO ĐỀ ---
elif st.session_state.step == 'matrix':
    # Header
    col_back, col_title = st.columns([1, 5])
    if col_back.button("⬅️ Quay lại"):
        st.session_state.step = 'home'
        st.rerun()
    
    col_title.markdown(f"<h3 style='color:{st.session_state.selected_color}; margin:0;'>{st.session_state.selected_grade} - {st.session_state.selected_subject.upper()}</h3>", unsafe_allow_html=True)
    
    # Layout 2 Cột: Trái (Chọn bài) - Phải (Ma trận)
    col_left, col_right = st.columns([1, 1.5])
    
    # === CỘT TRÁI: DANH SÁCH BÀI HỌC ===
    with col_left:
        st.markdown("#### 2️⃣ Chọn Bài học / Chủ đề")
        
        # Lấy dữ liệu bài học từ biến PREDEFINED_DATA
        current_grade = st.session_state.selected_grade
        current_subject = st.session_state.selected_subject
        
        # Logic lấy data an toàn
        topic_data = []
        if current_subject in PREDEFINED_DATA:
            if current_grade in PREDEFINED_DATA[current_subject]:
                topic_data = PREDEFINED_DATA[current_subject][current_grade]
            else:
                # Nếu lớp chưa có data, lấy lớp đầu tiên có data làm mẫu
                first_key = list(PREDEFINED_DATA[current_subject].keys())[0]
                topic_data = PREDEFINED_DATA[current_subject][first_key]
        else:
            topic_data = DEFAULT_TOPICS

        # Tạo list tên bài để hiển thị trong multiselect
        topic_names = [f"{t['topic']} ({t['periods']} tiết)" for t in topic_data]
        
        selected_indices = st.multiselect(
            "Tích chọn các bài cần kiểm tra:",
            options=range(len(topic_names)),
            format_func=lambda x: topic_names[x]
        )
        
        st.markdown("---")
        st.markdown("**Cấu hình nhanh:**")
        c1, c2 = st.columns(2)
        def_level = c1.selectbox("Mức độ:", ["Biết", "Hiểu", "Vận dụng"], index=0)
        def_type = c2.selectbox("Dạng bài:", ["Trắc nghiệm", "Tự luận", "Đúng/Sai", "Điền khuyết", "Nối cột"], index=0)
        
        # Xác định bước nhảy điểm
        step_val = 0.25 if current_subject == "Toán" else 0.5
        def_point = st.number_input("Điểm/Câu:", 0.25, 5.0, 1.0, step_val)
        
        if st.button("➡️ Thêm vào Ma trận", type="primary", use_container_width=True):
            if not selected_indices:
                st.warning("Chưa chọn bài học nào!")
            else:
                new_rows = []
                for idx in selected_indices:
                    t_info = topic_data[idx]
                    new_rows.append({
                        "Chủ đề": t_info['topic'],
                        "Số tiết": t_info['periods'],
                        "Mức độ": def_level,
                        "Dạng bài": def_type,
                        "Số câu": 1,
                        "Điểm": def_point
                    })
                
                # Thêm vào bảng hiện tại
                new_df = pd.DataFrame(new_rows)
                st.session_state.matrix_df = pd.concat([st.session_state.matrix_df, new_df], ignore_index=True)
                st.success("Đã thêm!")
                time.sleep(0.5)
                st.rerun()

    # === CỘT PHẢI: BẢNG MA TRẬN ===
    with col_right:
        st.markdown("#### 3️⃣ Ma trận Đặc tả Đề thi")
        
        if not st.session_state.matrix_df.empty:
            # Hiển thị bảng Editor
            edited_matrix = st.data_editor(
                st.session_state.matrix_df,
                column_config={
                    "Chủ đề": st.column_config.TextColumn("Tên bài học", disabled=True, width="medium"),
                    "Số tiết": st.column_config.NumberColumn("Số tiết", disabled=True, width="small"),
                    "Mức độ": st.column_config.SelectboxColumn("Mức độ", options=["Biết", "Hiểu", "Vận dụng"], width="small"),
                    "Dạng bài": st.column_config.SelectboxColumn("Dạng bài", options=["Trắc nghiệm", "Tự luận", "Đúng/Sai", "Điền khuyết", "Nối cột"], width="medium"),
                    "Số câu": st.column_config.NumberColumn("SL Câu", min_value=1, max_value=20, step=1, width="small"),
                    "Điểm": st.column_config.NumberColumn("Điểm", min_value=0.25, max_value=10.0, step=step_val, width="small"),
                },
                num_rows="dynamic",
                use_container_width=True,
                key="editor"
            )
            
            # Cập nhật Session State
            st.session_state.matrix_df = edited_matrix
            
            # Tính toán tổng
            total_qs = edited_matrix["Số câu"].sum()
            total_pts = (edited_matrix["Số câu"] * edited_matrix["Điểm"]).sum()
            
            # Hiển thị tổng kết
            st.markdown(f"""
            <div class='matrix-container'>
                <div class='total-display'>
                    Tổng số câu: <span style='color:blue'>{total_qs}</span> &nbsp;|&nbsp; 
                    Tổng điểm: <span style='color:{'green' if total_pts==10 else 'red'}'>{total_pts}/10</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if total_pts != 10:
                st.warning("⚠️ Tổng điểm chưa bằng 10. Hãy điều chỉnh 'Số câu' hoặc 'Điểm'.")
            
            # NÚT TẠO ĐỀ
            st.markdown("### 4️⃣ Xuất Đề Thi")
            if st.button("🚀 TẠO ĐỀ THI & TẢI FILE WORD", type="primary", use_container_width=True):
                if not api_key:
                    st.error("Vui lòng nhập API Key ở cột bên trái.")
                else:
                    with st.spinner("AI đang phân tích ma trận và soạn đề..."):
                        info = {"subject": current_subject, "grade": current_grade}
                        body, key = generate_ai_content(api_key, edited_matrix, info)
                        
                        if body:
                            docx_file = create_docx(school_name, exam_name, info, body, key)
                            st.success("Tạo đề thành công! Tải về bên dưới:")
                            st.download_button(
                                label="📥 TẢI FILE WORD (.DOCX) CHUẨN NĐ30",
                                data=docx_file,
                                file_name=f"De_{current_subject}_{current_grade}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        else:
                            st.error(key) # In lỗi nếu có
        else:
            st.info("👈 Hãy chọn bài học bên trái và bấm 'Thêm vào Ma trận' để bắt đầu.")

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>© 2025 - Trần Ngọc Hải - Trường PTDTBT Tiểu học Giàng Chu Phìn - ĐT: 0944 134 973</div>", unsafe_allow_html=True)
st.markdown("<div class='copyright-warning'>⚠️ CẢNH BÁO: BẠN ĐANG VI PHẠM BẢN QUYỀN NẾU SAO CHÉP MÃ NGUỒN NÀY</div>", unsafe_allow_html=True)
