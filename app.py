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
import json

# Import dữ liệu cứng (nếu có)
try:
    from data_matrices import SAMPLE_MATRICES
except ImportError:
    SAMPLE_MATRICES = {}

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🏫", layout="wide")

# --- QUẢN LÝ SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = ''
if 'selected_color' not in st.session_state: st.session_state.selected_color = ''
if 'extracted_topics' not in st.session_state: st.session_state.extracted_topics = [] # Lưu danh sách chủ đề đã quét
if 'auto_config' not in st.session_state: st.session_state.auto_config = {}

# --- CSS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .main-title {font-family: 'Times New Roman', serif; font-size: 30px; font-weight: bold; text-align: center; text-transform: uppercase; color: #2c3e50; margin-bottom: 20px;}
    .subject-card {padding: 20px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 18px; cursor: pointer; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;}
    .subject-card:hover {transform: scale(1.05);}
    .bg-blue {background-color: #3498db;} .bg-green {background-color: #2ecc71;} .bg-red {background-color: #e74c3c;}
    .bg-purple {background-color: #9b59b6;} .bg-orange {background-color: #e67e22;} .bg-teal {background-color: #1abc9c;}
    .author-card {background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 20px;}
    .author-name {font-weight: bold; font-size: 18px; color: #2d3436; margin-top: 10px;}
    .home-btn {background-color: #0984e3; color: white !important; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-block;}
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

def show_author_profile():
    st.sidebar.markdown("""
    <div class="author-card">
        <img src="https://api.dicebear.com/9.x/avataaars/svg?seed=BapCai&backgroundColor=b6e3f4" width="80" style="border-radius: 50%;">
        <div class="author-name">BapCai</div>
        <div style="font-size:13px; color:#666; margin-bottom:10px;">Chuyên gia Giáo dục Tiểu học</div>
        <a href="https://www.google.com" target="_blank" class="home-btn">🏠 Trang Chủ Tác Giả</a>
    </div>
    """, unsafe_allow_html=True)

# --- XỬ LÝ WORD CHUẨN THỂ THỨC ---
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
        else: para.add_run(line)
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

def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in models: return 'gemini-1.5-flash'
        return models[0].replace('models/', '') if models else 'gemini-pro'
    except: return 'gemini-pro'

# --- HÀM MỚI: QUÉT CHỦ ĐỀ TỪ NỘI DUNG ---
def extract_topics_from_text(api_key, text):
    if not api_key: return []
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())
    
    prompt = f"""
    Đọc văn bản kế hoạch dạy học dưới đây và trích xuất danh sách Tên các Bài học/Chủ đề chính.
    Chỉ trả về danh sách các tên bài, ngăn cách nhau bởi dấu phẩy. Không thêm lời dẫn.
    Ví dụ: Bài 1: Thông tin, Bài 2: Xử lý thông tin, Bài 3: Máy tính
    
    Văn bản nguồn:
    {text[:10000]} 
    """
    try:
        response = model.generate_content(prompt)
        # Xử lý chuỗi trả về thành list
        topics = response.text.split(',')
        return [t.strip() for t in topics if t.strip()]
    except: return []

def generate_exam_content(api_key, subject_plan, matrix_content, config, info, selected_topics):
    if not api_key: return None, None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())

    practical_prompt = ""
    if config.get('has_practical'):
        practical_prompt = f"""
        C. PHẦN THỰC HÀNH ({config['prac_point']} điểm):
           - Mức 1: {config['prac_lv1']}, Mức 2: {config['prac_lv2']}, Mức 3: {config['prac_lv3']} yêu cầu.
        """
    
    # Thêm chỉ dẫn về chủ đề được chọn
    topics_instruction = ""
    if selected_topics:
        topics_instruction = f"LƯU Ý QUAN TRỌNG: Chỉ ra câu hỏi nằm trong các chủ đề sau đây: {', '.join(selected_topics)}."

    prompt = f"""
    Bạn là chuyên gia khảo thí Tiểu học. Hãy soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    Tuân thủ Thông tư 27, Thông tư 32 và Ma trận đính kèm.
    
    {topics_instruction}
    
    CẤU TRÚC ĐỀ VÀ ĐIỂM SỐ (Bám sát ma trận):
    1. PHẦN TRẮC NGHIỆM ({config['mcq_total']} câu):
       - Trắc nghiệm Nhiều lựa chọn (ABCD): {config['q_abcd']} câu.
       - Trắc nghiệm Đúng/Sai: {config['q_tf']} câu.
       - Nối cột: {config['q_match']} câu.
       - Điền khuyết: {config['q_fill']} câu.
       (Phân bổ mức độ: Biết {config['mcq_lv1']}, Hiểu {config['mcq_lv2']}, Vận dụng {config['mcq_lv3']})
    
    2. PHẦN TỰ LUẬN ({config['essay_total']} câu - {config['essay_point']} điểm/câu):
       - Phân bổ: Biết {config['essay_lv1']}, Hiểu {config['essay_lv2']}, Vận dụng {config['essay_lv3']}.
    
    {practical_prompt}
    
    DỮ LIỆU NGUỒN:
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

# ==================== MAIN APP ====================
st.markdown('<div class="main-title">HỆ THỐNG HỖ TRỢ RA ĐỀ TIỂU HỌC</div>', unsafe_allow_html=True)
show_author_profile()

if st.session_state.step == 'home':
    st.write("### 👋 Chọn môn học để bắt đầu:")
    cols = st.columns(3)
    for index, sub in enumerate(SUBJECTS_DATA):
        col_idx = index % 3
        with cols[col_idx]:
            st.markdown(f"""<div class="subject-card {sub['class']}"><div style="font-size:30px;">{sub['icon']}</div>{sub['name']}</div>""", unsafe_allow_html=True)
            if st.button(f"Soạn {sub['name']}", key=sub['name'], use_container_width=True):
                st.session_state.selected_subject = sub['name']
                st.session_state.selected_color = sub['color']
                st.session_state.step = 'config'
                st.session_state.extracted_topics = [] # Reset chủ đề khi vào môn mới
                st.rerun()

elif st.session_state.step == 'config':
    if st.button("⬅️ Quay lại trang chủ"):
        st.session_state.step = 'home'
        st.session_state.auto_config = {} 
        st.rerun()

    subject = st.session_state.selected_subject
    color = st.session_state.selected_color
    st.markdown(f"""<div style="background-color:{color}; padding:10px; border-radius:8px; color:white; margin-bottom:20px; text-align:center;"><h3 style="margin:0;">MÔN: {subject.upper()}</h3></div>""", unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Cài đặt")
        api_key = st.text_input("Mã API Google:", type="password")
        st.subheader("🏫 Thông tin")
        school_name = st.text_input("Trường:", value="TH Nguyễn Du")
        exam_name = st.text_input("Kỳ thi:", value="CUỐI HỌC KÌ I")

    col_left, col_right = st.columns([1.1, 1])

    # === CỘT TRÁI: DỮ LIỆU ===
    with col_left:
        st.info("1️⃣ Dữ liệu & Chủ đề")
        grade = st.selectbox("Khối lớp:", ["Lớp 3", "Lớp 4", "Lớp 5"])
        
        # --- UPLOAD VÀ PHÂN TÍCH CHỦ ĐỀ ---
        st.write("📂 **Kế hoạch dạy học:**")
        file_plan = st.file_uploader("Upload KH:", type=['docx', 'pdf', 'txt'], label_visibility="collapsed")
        
        # Nút phân tích chủ đề
        plan_text_content = ""
        if file_plan:
            plan_text_content = read_input_file(file_plan)
            if st.button("🔍 Phân tích Chủ đề bài học"):
                if not api_key:
                    st.error("Cần nhập API Key để phân tích.")
                else:
                    with st.spinner("Đang đọc file để tìm bài học..."):
                        topics = extract_topics_from_text(api_key, plan_text_content)
                        st.session_state.extracted_topics = topics
        
        # Hộp chọn chủ đề
        selected_topics = []
        if st.session_state.extracted_topics:
            st.success(f"Tìm thấy {len(st.session_state.extracted_topics)} chủ đề:")
            selected_topics = st.multiselect("👉 Chọn các chủ đề muốn ra đề:", st.session_state.extracted_topics)
        elif file_plan and not st.session_state.extracted_topics:
            st.info("Hãy bấm nút Phân tích để chọn bài học.")

        # --- UPLOAD MA TRẬN ---
        st.write("📊 **Ma trận đề:**")
        matrix_source = st.radio("Nguồn Ma trận:", ["Upload file mới", "Dùng Mẫu có sẵn (Dữ liệu cứng)"], horizontal=True)
        
        matrix_text_final = ""
        ac = st.session_state.auto_config 
        
        if matrix_source == "Upload file mới":
            file_matrix = st.file_uploader("Upload MT:", type=['xlsx', 'xls', 'csv', 'pdf'], label_visibility="collapsed")
            if file_matrix:
                matrix_text_final = read_input_file(file_matrix)
                try:
                    if file_matrix.name.endswith(('.xlsx', '.xls')): st.dataframe(pd.read_excel(file_matrix), height=200)
                    elif file_matrix.name.endswith('.csv'): st.dataframe(pd.read_csv(file_matrix), height=200)
                except: pass
        else:
            if SAMPLE_MATRICES:
                selected_sample = st.selectbox("Chọn mẫu ma trận:", list(SAMPLE_MATRICES.keys()))
                if selected_sample:
                    data_obj = SAMPLE_MATRICES[selected_sample]
                    df_sample = pd.DataFrame(data_obj["data"])
                    st.dataframe(df_sample, height=200)
                    matrix_text_final = df_sample.to_string()
                    if st.button("🔄 Load Config"):
                        st.session_state.auto_config = data_obj["config"]
                        st.rerun()
            else: st.warning("Chưa có dữ liệu mẫu.")

    # === CỘT PHẢI: CẤU HÌNH ===
    with col_right:
        st.success("2️⃣ Cấu trúc Đề (Áp dụng cho các chủ đề đã chọn)")
        
        def_mcq_pt = ac.get("mcq_point", 0.5)
        def_essay_pt = ac.get("essay_point", 1.0)
        
        tabs = st.tabs(["🅰️ Trắc Nghiệm", "🅱️ Tự Luận"])

        with tabs[0]:
            st.markdown(f"**Lưu ý:** ABCD & Đ/S tính **{def_mcq_pt}đ**. Nối & Điền tính **1.0đ**.")
            
            c1, c2, c3 = st.columns(3)
            mcq_lv1 = c1.number_input("Biết (TN):", 0, 20, 3)
            mcq_lv2 = c2.number_input("Hiểu (TN):", 0, 20, 2)
            mcq_lv3 = c3.number_input("Vận dụng (TN):", 0, 20, 1)
            mcq_total = mcq_lv1 + mcq_lv2 + mcq_lv3
            
            st.caption(f"Tổng: {mcq_total} câu TN. Phân dạng:")
            d1, d2 = st.columns(2)
            q_abcd = d1.number_input("ABCD (0.5đ):", 0, 20, max(0, mcq_total-2))
            q_tf = d1.number_input("Đúng/Sai (0.5đ):", 0, 5, 1)
            q_match = d2.number_input("Nối cột (1.0đ):", 0, 5, 0)
            q_fill = d2.number_input("Điền khuyết (1.0đ):", 0, 5, 1)

        with tabs[1]:
            essay_point = st.number_input("Điểm/câu TL:", 0.5, 5.0, def_essay_pt, step=0.5)
            e1, e2, e3 = st.columns(3)
            essay_lv1 = e1.number_input("Biết (TL):", 0, 5, 0)
            essay_lv2 = e2.number_input("Hiểu (TL):", 0, 5, 1)
            essay_lv3 = e3.number_input("Vận dụng (TL):", 0, 5, 1)
            essay_total = essay_lv1 + essay_lv2 + essay_lv3

        # TÍNH TOÁN ĐIỂM SỐ
        score_tn_basic = (q_abcd + q_tf) * def_mcq_pt
        score_tn_adv = (q_match + q_fill) * 1.0 
        score_essay = essay_total * essay_point
        total_score = score_tn_basic
