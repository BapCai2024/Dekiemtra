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

# --- IMPORT DỮ LIỆU CỨNG (Nếu có) ---
try:
    from data_matrices import SAMPLE_MATRICES
except ImportError:
    SAMPLE_MATRICES = {}

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🏫", layout="wide")

# --- QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = ''
if 'selected_color' not in st.session_state: st.session_state.selected_color = ''
if 'topic_df' not in st.session_state: st.session_state.topic_df = None 
if 'auto_config' not in st.session_state: st.session_state.auto_config = {}

# --- CSS GIAO DIỆN ---
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

# --- CÁC HÀM XỬ LÝ (WORD, AI, PDF) ---
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
    
    # Title
    title = doc.add_paragraph()
    run_title = title.add_run(str(exam_name).upper())
    run_title.bold = True
    run_title.font.size = Pt(14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Info
    info = doc.add_paragraph()
    info.add_run("Họ và tên học sinh: ..................................................................................... ").bold = False
    info.add_run(f"Lớp: {student_info.get('grade', '...')}.....")
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph() 
    
    # Score Table
    score_table = doc.add_table(rows=2, cols=2)
    score_table.style = 'Table Grid'
    score_table.cell(0, 0).text = "Điểm"
    score_table.cell(0, 1).text = "Lời nhận xét của giáo viên"
    score_table.cell(0,0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.cell(0,1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.rows[1].height = Cm(2.5)
    doc.add_paragraph() 
    doc.add_paragraph("------------------------------------------------------------------------------------------------------")
    
    # Body
    clean_body = clean_text_for_word(content_body)
    for line in clean_body.split('\n'):
        line = line.strip()
        if not line: continue
        para = doc.add_paragraph()
        if re.match(r"^(Câu|PHẦN|Bài|Phần) \d+|^(Câu|PHẦN|Bài|Phần) [IVX]+", line, re.IGNORECASE):
            para.add_run(line).bold = True
        else: para.add_run(line)
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    # Answer Key
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

def extract_topics_json(api_key, text):
    if not api_key: return []
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())
    prompt = f"""
    Phân tích văn bản kế hoạch dạy học dưới đây.
    Hãy trích xuất danh sách các "Bài học" hoặc "Chủ đề" cùng với "Số tiết" (nếu có).
    OUTPUT: JSON List of Objects. Format: [{{"topic": "Tên bài", "periods": 2}}].
    Văn bản: {text[:15000]} 
    """
    try:
        response = model.generate_content(prompt)
        content = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return data
    except Exception as e: return []

def generate_exam_content(api_key, subject_plan, matrix_content, config, info, selected_data):
    if not api_key: return None, None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())

    practical_prompt = ""
    if config.get('has_practical'):
        practical_prompt = f"""
        C. PHẦN THỰC HÀNH ({config['prac_point']} điểm):
           - Mức 1: {config['prac_lv1']}, Mức 2: {config['prac_lv2']}, Mức 3: {config['prac_lv3']} yêu cầu.
        """
    
    topics_instruction = ""
    if selected_data:
        topics_str = ", ".join([f"{item['topic']} ({item['periods']} tiết)" for item in selected_data])
        topics_instruction = f"PHẠM VI KIẾN THỨC CHỈ NẰM TRONG: {topics_str}"

    prompt = f"""
    Bạn là chuyên gia khảo thí Tiểu học. Hãy soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    Tuân thủ Thông tư 27, Thông tư 32.
    
    {topics_instruction}
    
    CẤU TRÚC ĐỀ (Bắt buộc theo cấu hình):
    1. PHẦN TRẮC NGHIỆM (Tổng {config['mcq_total']} câu):
       - Dạng: {config['q_abcd']} ABCD (0.5đ), {config['q_tf']} Đ/S (0.5đ), {config['q_match']} Nối (1.0đ), {config['q_fill']} Điền (1.0đ).
       - Mức độ: Biết {config['mcq_lv1']}, Hiểu {config['mcq_lv2']}, Vận dụng {config['mcq_lv3']}.
    
    2. PHẦN TỰ LUẬN ({config['essay_total']} câu - {config['essay_point']} điểm/câu):
       - Mức độ: Biết {config['essay_lv1']}, Hiểu {config['essay_lv2']}, Vận dụng {config['essay_lv3']}.
    
    {practical_prompt}
    
    DỮ LIỆU NGUỒN:
    1. Nội dung dạy học: {subject_plan}
    2. Ma trận tham chiếu: {matrix_content}
    
    OUTPUT:
    - KHÔNG lời dẫn. Tách đáp án bằng: ###TÁCH_Ở_ĐÂY###
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
    except: return ""

# ==================== GIAO DIỆN CHÍNH ====================
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
                st.session_state.topic_df = None
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

    col_left, col_right = st.columns([1.2, 1])

    # === CỘT TRÁI ===
    with col_left:
        st.info("1️⃣ Thiết lập Ma trận & Nội dung")
        grade = st.selectbox("Khối lớp:", ["Lớp 3", "Lớp 4", "Lớp 5"])
        
        file_plan = st.file_uploader("📂 Kế hoạch dạy học (Bắt buộc):", type=['docx', 'pdf', 'txt'])
        plan_text_content = ""
        if file_plan: plan_text_content = read_input_file(file_plan)

        # Quét chủ đề
        if file_plan:
            if st.session_state.topic_df is None:
                if st.button("🔍 Phân tích & Tạo Ma trận Chủ đề"):
                    if not api_key: st.error("Cần nhập API Key.")
                    else:
                        with st.spinner("Đang phân tích bài học..."):
                            topics_data = extract_topics_json(api_key, plan_text_content)
                            if topics_data:
                                df = pd.DataFrame(topics_data)
                                df.insert(0, "Chọn", False)
                                df.rename(columns={"topic": "Tên bài/Chủ đề", "periods": "Số tiết"}, inplace=True)
                                st.session_state.topic_df = df
                            else: st.error("Không tìm thấy chủ đề.")
            
            if st.session_state.topic_df is not None:
                st.write("📋 **Bảng Ma trận Chủ đề (Tích chọn bài cần ra đề):**")
                edited_df = st.data_editor(
                    st.session_state.topic_df,
                    column_config={
                        "Chọn": st.column_config.CheckboxColumn("Chọn", default=False),
                        "Số tiết": st.column_config.NumberColumn("Số tiết", min_value=1, max_value=10, step=1),
                    },
                    disabled=["Tên bài/Chủ đề"],
                    hide_index=True,
                    use_container_width=True
                )
                selected_rows = edited_df[edited_df["Chọn"] == True]
                if not selected_rows.empty:
                    st.success(f"✅ Đã chọn: {len(selected_rows)} bài - {selected_rows['Số tiết'].sum()} tiết")
                    selected_data_for_ai = []
                    for index, row in selected_rows.iterrows():
                        selected_data_for_ai.append({"topic": row["Tên bài/Chủ đề"], "periods": row["Số tiết"]})
                else:
                    st.warning("Vui lòng tích chọn bài.")
                    selected_data_for_ai = []
            else: selected_data_for_ai = []

        st.write("---")
        st.write("📊 **Khung Ma trận (Cấu trúc điểm):**")
        matrix_source = st.radio("Nguồn:", ["Upload file mới", "Dùng Mẫu có sẵn"], horizontal=True)
        matrix_text_final = ""
        
        if matrix_source == "Upload file mới":
            file_matrix = st.file_uploader("Upload:", type=['xlsx', 'xls', 'csv', 'pdf'], label_visibility="collapsed")
            if file_matrix:
                matrix_text_final = read_input_file(file_matrix)
                try:
                    if file_matrix.name.endswith(('.xlsx', '.xls')): st.dataframe(pd.read_excel(file_matrix), height=150)
                    elif file_matrix.name.endswith('.csv'): st.dataframe(pd.read_csv(file_matrix), height=150)
                except: pass
        else:
            if SAMPLE_MATRICES:
                selected_sample = st.selectbox("Chọn mẫu:", list(SAMPLE_MATRICES.keys()))
                if selected_sample:
                    data_obj = SAMPLE_MATRICES[selected_sample]
                    st.dataframe(pd.DataFrame(data_obj["data"]), height=150)
                    matrix_text_final = pd.DataFrame(data_obj["data"]).to_string()
                    if st.button("🔄 Áp dụng Cấu hình từ Mẫu"):
                        st.session_state.auto_config = data_obj["config"]
                        st.rerun()

    # === CỘT PHẢI: CẤU HÌNH ===
    with col_right:
        st.success("2️⃣ Cấu trúc Đề thi")
        ac = st.session_state.auto_config
        def_mcq_pt = ac.get("mcq_point", 0.5)
        def_essay_pt = ac.get("essay_point", 1.0)
        
        tabs = st.tabs(["🅰️ Trắc Nghiệm", "🅱️ Tự Luận"])

        with tabs[0]:
            st.markdown(f"**Lưu ý:** ABCD & Đ/S tính **{def_mcq_pt}đ**. Nối & Điền tính **1.0đ**.")
            c1, c2, c3 = st.columns(3)
            mcq_lv1 = c1.number_input("Biết (TN):", 0, 20, 3)
            mcq_lv2 = c2.number_input("Hiểu (TN):", 0, 20, 2)
            mcq_lv3 = c3.number_input("Vận dụng (TN):", 0, 20, 1)
            
            # SỬA LỖI Ở ĐÂY: Viết đầy đủ dòng lệnh
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

        # Tính điểm
        score_tn_basic = (q_abcd + q_tf) * def_mcq_pt
        score_tn_adv = (q_match + q_fill) * 1.0 
        score_essay = essay_total * essay_point
        total_score = score_tn_basic + score_tn_adv + score_essay

        st.markdown("---")
        if total_score == 10:
            st.markdown(f"<div style='background:#d4edda; color:#155724; padding:10px; border-radius:5px; text-align:center;'>✅ TỔNG ĐIỂM: 10/10</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#f8d7da; color:#721c24; padding:10px; border-radius:5px; text-align:center;'>⚠️ TỔNG: {total_score}</div>", unsafe_allow_html=True)

        if st.button("🚀 TẠO ĐỀ & TẢI FILE", type="primary", use_container_width=True):
            if not api_key: st.error("Thiếu API Key.")
            elif not plan_text_content or (matrix_source == "Upload file mới" and not matrix_text_final):
                 st.error("Thiếu dữ liệu nguồn.")
            elif not selected_data_for_ai:
                 st.error("Vui lòng tích chọn bài học ở bảng bên trái.")
            else:
                with st.spinner("Đang xử lý..."):
                    config = {
                        "mcq_total": mcq_total, "mcq_point": def_mcq_pt,
                        "mcq_lv1": mcq_lv1, "mcq_lv2": mcq_lv2, "mcq_lv3": mcq_lv3,
                        "q_abcd": q_abcd, "q_tf": q_tf, "q_fill": q_fill, "q_match": q_match,
                        "essay_total": essay_total, "essay_point": essay_point,
                        "essay_lv1": essay_lv1, "essay_lv2": essay_lv2, "essay_lv3": essay_lv3,
                        "has_practical": False
                    }
                    info = {"subject": subject, "grade": grade}
                    
                    exam_body, answer_key = generate_exam_content(api_key, plan_text_content, matrix_text_final, config, info, selected_data_for_ai)
                    
                    if exam_body and "Lỗi" not in exam_body:
                        docx = create_docx_file(school_name, exam_name, info, exam_body, answer_key)
                        st.download_button("📥 Tải File Word", docx, f"De_{subject}_{grade}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    else: st.error(exam_body)
