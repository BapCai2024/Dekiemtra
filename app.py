import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import pypdf
import re

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🏫", layout="wide")

# --- QUẢN LÝ SESSION ---
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = ''
if 'selected_color' not in st.session_state: st.session_state.selected_color = ''

# --- CSS TÙY CHỈNH GIAO DIỆN (QUAN TRỌNG) ---
st.markdown("""
<style>
    /* 1. ẨN MENU MẶC ĐỊNH CỦA STREAMLIT (Manage App, Deploy...) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 2. Style cho giao diện chính */
    .main-title {font-family: 'Times New Roman', serif; font-size: 30px; font-weight: bold; text-align: center; text-transform: uppercase; color: #2c3e50; margin-bottom: 20px;}
    
    /* Style thẻ môn học */
    .subject-card {padding: 20px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 18px; cursor: pointer; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;}
    .subject-card:hover {transform: scale(1.05);}
    
    /* Màu sắc */
    .bg-blue {background-color: #3498db;} .bg-green {background-color: #2ecc71;} .bg-red {background-color: #e74c3c;}
    .bg-purple {background-color: #9b59b6;} .bg-orange {background-color: #e67e22;} .bg-teal {background-color: #1abc9c;}
    
    /* Style cho Profile Tác giả */
    .author-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
    }
    .author-name {font-weight: bold; font-size: 18px; color: #2d3436; margin-top: 10px;}
    .author-role {font-size: 13px; color: #636e72; margin-bottom: 10px;}
    .home-btn {
        background-color: #0984e3; color: white !important; 
        padding: 8px 15px; border-radius: 5px; text-decoration: none; 
        font-weight: bold; font-size: 14px; display: inline-block;
        transition: 0.3s;
    }
    .home-btn:hover {background-color: #74b9ff;}
</style>
""", unsafe_allow_html=True)

SUBJECTS_DATA = [
    {"name": "Toán", "icon": "📐", "color": "#3498db", "class": "bg-blue"},
    {"name": "Tiếng Việt", "icon": "📚", "color": "#e74c3c", "class": "bg-red"},
    {"name": "Tin học", "icon": "💻", "color": "#9b59b6", "class": "bg-purple"},
    {"name": "Khoa học", "icon": "🔬", "color": "#2ecc71", "class": "bg-green"},
    {"name": "Lịch sử & Địa lí", "icon": "🌏", "color": "#e67e22", "class": "bg-orange"},
    {"name": "Công nghệ", "icon": "🛠️", "color": "#1abc9c", "class": "bg-teal"},
]

# --- HÀM PROFILE TÁC GIẢ (SIDEBAR) ---
def show_author_profile():
    # Sử dụng API DiceBear để tạo Avatar ngẫu nhiên đẹp mắt theo tên
    st.sidebar.markdown("""
    <div class="author-card">
        <img src="https://api.dicebear.com/9.x/avataaars/svg?seed=BapCai&backgroundColor=b6e3f4" width="80" style="border-radius: 50%;">
        <div class="author-name">BapCai</div>
        <div class="author-role">Chuyên gia Giáo dục Tiểu học</div>
        <a href="https://www.google.com" target="_blank" class="home-btn">
            🏠 Trang Chủ Tác Giả
        </a>
    </div>
    """, unsafe_allow_html=True)

# --- HÀM XỬ LÝ WORD ---
def clean_text_for_word(text):
    if not text: return ""
    text = str(text)
    patterns = [r"^Tuyệt vời.*?\n", r"^Dưới đây là.*?\n", r"^Chắc chắn rồi.*?\n", r"^Chào bạn.*?\n"]
    for p in patterns: text = re.sub(p, "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"(PHÒNG GD|TRƯỜNG|SỞ GIÁO DỤC|CỘNG HÒA XÃ HỘI).*?(Họ và tên|Lớp).*?\n", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.replace("**", "").replace("##", "").replace("###", "").strip()

def create_docx_file(school_name, exam_name, student_info, content_body, answer_key):
    doc = Document()
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass
    
    # Header
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    p_left.add_run("PHÒNG GD&ĐT ............\n").bold = False
    p_left.add_run(f"{str(school_name).upper()}").bold = True
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n").bold = True
    p_right.add_run("Độc lập - Tự do - Hạnh phúc").bold = True
    p_right.add_run("\n-------------------").bold = False
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() 
    title = doc.add_paragraph()
    run_title = title.add_run(str(exam_name).upper())
    run_title.bold = True
    run_title.font.size = Pt(14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    info = doc.add_paragraph()
    info.add_run("Họ và tên học sinh: ..................................................................................... ").bold = False
    info.add_run(f"Lớp: {student_info.get('grade', '...')}.....")
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph() 

    score_table = doc.add_table(rows=2, cols=2)
    score_table.style = 'Table Grid'
    score_table.cell(0, 0).text = "Điểm"
    score_table.cell(0, 1).text = "Lời nhận xét của giáo viên"
    score_table.cell(0,0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.cell(0,1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.rows[1].height = Cm(2.5)
    
    doc.add_paragraph() 
    doc.add_paragraph("------------------------------------------------------------------------------------------------------")
    
    clean_body = clean_text_for_word(content_body)
    for line in clean_body.split('\n'):
        line = line.strip()
        if not line: continue
        para = doc.add_paragraph()
        if re.match(r"^(Câu|PHẦN|Bài|Phần) \d+|^(Câu|PHẦN|Bài|Phần) [IVX]+", line, re.IGNORECASE):
            para.add_run(line).bold = True
        else:
            para.add_run(line)
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    doc.add_page_break()
    ans_title = doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN")
    ans_title.runs[0].bold = True
    ans_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(clean_text_for_word(answer_key))

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- HÀM AI ---
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in models: return 'gemini-1.5-flash'
        return models[0].replace('models/', '') if models else 'gemini-pro'
    except: return 'gemini-pro'

def generate_exam_content(api_key, subject_plan, matrix_content, config, info):
    if not api_key: return None, None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())

    practical_prompt = ""
    if config.get('has_practical'):
        practical_prompt = f"""
        C. PHẦN THỰC HÀNH ({config['prac_point']} điểm):
           - Mức 1: {config['prac_lv1']}, Mức 2: {config['prac_lv2']}, Mức 3: {config['prac_lv3']} yêu cầu.
        """

    prompt = f"""
    Bạn là chuyên gia khảo thí Tiểu học. Hãy soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    Tuân thủ Thông tư 27 (Đánh giá) và Thông tư 32.
    
    CẤU TRÚC:
    A. TRẮC NGHIỆM ({config['mcq_total']} câu - {config['mcq_point']} điểm/câu):
       - Biết {config['mcq_lv1']}, Hiểu {config['mcq_lv2']}, Vận dụng {config['mcq_lv3']}.
       - Dạng: {config['q_abcd']} ABCD, {config['q_tf']} Đ/S, {config['q_fill']} Điền khuyết, {config['q_match']} Ghép nối.
    
    B. TỰ LUẬN ({config['essay_total']} câu - {config['essay_point']} điểm/câu):
       - Biết {config['essay_lv1']}, Hiểu {config['essay_lv2']}, Vận dụng {config['essay_lv3']}.
    
    {practical_prompt}
    
    DỮ LIỆU NGUỒN (Quan trọng):
    1. Nội dung dạy học: {subject_plan}
    2. Ma trận tham chiếu: {matrix_content}
    
    OUTPUT:
    - KHÔNG viết lời dẫn.
    - KHÔNG dùng markdown.
    - Tách đáp án bằng: ###TÁCH_Ở_ĐÂY###
    """
    
    try:
        response = model.generate_content(prompt)
        full_text = response.text
        if "###TÁCH_Ở_ĐÂY###" in full_text:
            parts = full_text.split("###TÁCH_Ở_ĐÂY###")
            return parts[0].strip(), parts[1].strip()
        else: return full_text, "Không tìm thấy đáp án tách biệt."
    except Exception as e: return f"Lỗi AI: {str(e)}", ""

def read_input_file(uploaded_file):
    if not uploaded_file: return ""
    try:
        if uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages: text += page.extract_text() + "\n"
            return text
        elif uploaded_file.name.endswith(('.xlsx', '.xls')): return pd.read_excel(uploaded_file).to_string()
        elif uploaded_file.name.endswith('.csv'): return pd.read_csv(uploaded_file).to_string()
        else: return uploaded_file.read().decode("utf-8")
    except Exception as e: return f"Lỗi đọc file: {str(e)}"

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================

st.markdown('<div class="main-title">HỆ THỐNG HỖ TRỢ RA ĐỀ TIỂU HỌC</div>', unsafe_allow_html=True)

# Hiển thị Profile Tác giả ở Sidebar mọi lúc
show_author_profile()

# ----------------- HOME SCREEN -----------------
if st.session_state.step == 'home':
    st.write("### 👋 Chọn môn học để bắt đầu:")
    cols = st.columns(3)
    for index, sub in enumerate(SUBJECTS_DATA):
        col_idx = index % 3
        with cols[col_idx]:
            st.markdown(f"""
            <div class="subject-card {sub['class']}">
                <div style="font-size: 30px;">{sub['icon']}</div>
                {sub['name']}
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Soạn {sub['name']}", key=sub['name'], use_container_width=True):
                st.session_state.selected_subject = sub['name']
                st.session_state.selected_color = sub['color']
                st.session_state.step = 'config'
                st.rerun()

# ----------------- CONFIG SCREEN -----------------
elif st.session_state.step == 'config':
    # Nút quay lại
    if st.button("⬅️ Quay lại trang chủ"):
        st.session_state.step = 'home'
        st.rerun()

    subject = st.session_state.selected_subject
    color = st.session_state.selected_color
    
    st.markdown(f"""
    <div style="background-color: {color}; padding: 10px; border-radius: 8px; color: white; margin-bottom: 20px; text-align: center;">
        <h3 style="margin:0;">MÔN: {subject.upper()}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar: Chỉ còn API Key và Thông tin trường (Profile tác giả đã hiện mặc định)
    with st.sidebar:
        st.header("⚙️ Cài đặt")
        api_key = st.text_input("Mã API Google:", type="password")
        st.subheader("🏫 Thông tin")
        school_name = st.text_input("Trường:", value="TH Nguyễn Du")
        exam_name = st.text_input("Kỳ thi:", value="CUỐI HỌC KÌ I")

    col_left, col_right = st.columns([1.1, 1])

    # === CỘT TRÁI: DỮ LIỆU & VIEW MA TRẬN ===
    with col_left:
        st.info("1️⃣ Dữ liệu & Ma trận tham chiếu")
        grade = st.selectbox("Khối lớp:", ["Lớp 3", "Lớp 4", "Lớp 5"])
        
        st.write("📂 **Kế hoạch dạy học:**")
        file_plan = st.file_uploader("Upload KH:", type=['docx', 'pdf', 'txt'], label_visibility="collapsed")

        st.write("📊 **Ma trận đề:** (Upload Excel để xem bảng)")
        file_matrix = st.file_uploader("Upload MT:", type=['xlsx', 'xls', 'csv', 'pdf'], label_visibility="collapsed")
        
        if file_matrix:
            st.markdown("**👁️ Xem trước Ma trận:**")
            try:
                if file_matrix.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_matrix)
                    st.dataframe(df, height=300, use_container_width=True)
                elif file_matrix.name.endswith('.csv'):
                    df = pd.read_csv(file_matrix)
                    st.dataframe(df, height=300, use_container_width=True)
                else: st.warning("File PDF chỉ hỗ trợ đọc nội dung khi tạo đề.")
            except: st.error("Lỗi hiển thị file.")

    # === CỘT PHẢI: CẤU HÌNH ===
    with col_right:
        st.success("2️⃣ Điều chỉnh Cấu trúc Đề")
        has_practical = subject in ["Tin học", "Công nghệ"]
        tabs = st.tabs(["🅰️ Trắc Nghiệm", "🅱️ Tự Luận"] + (["💻 Thực Hành"] if has_practical else []))

        with tabs[0]:
            mcq_point = st.selectbox("Điểm/câu TN:", [0.25, 0.5, 1.0], index=1)
            c1, c2, c3 = st.columns(3)
            mcq_lv1 = c1.number_input("Biết (TN):", 0, 20, 3)
            mcq_lv2 = c2.number_input("Hiểu (TN):", 0, 20, 2)
            mcq_lv3 = c3.number_input("Vận dụng (TN):", 0, 20, 1)
            mcq_total = mcq_lv1 + mcq_lv2 + mcq_lv3
            
            st.caption(f"Tổng: {mcq_total} câu TN. Dạng bài:")
            d1, d2 = st.columns(2)
            q_abcd = d1.number_input("ABCD:", 0, 20, max(0, mcq_total-2))
            q_tf = d1.number_input("Đúng/Sai:", 0, 5, 1)
            q_fill = d2.number_input("Điền khuyết:", 0, 5, 1)
            q_match = d2.number_input("Ghép nối:", 0, 5, 0)

        with tabs[1]:
            essay_point = st.selectbox("Điểm/câu TL:", [1.0, 1.5, 2.0, 2.5, 3.0], index=0)
            e1, e2, e3 = st.columns(3)
            essay_lv1 = e1.number_input("Biết (TL):", 0, 5, 0)
            essay_lv2 = e2.number_input("Hiểu (TL):", 0, 5, 1)
            essay_lv3 = e3.number_input("Vận dụng (TL):", 0, 5, 1)
            essay_total = essay_lv1 + essay_lv2 + essay_lv3

        prac_point = 0
        prac_lv1 = prac_lv2 = prac_lv3 = 0
        if has_practical:
            with tabs[2]:
                prac_point = st.
