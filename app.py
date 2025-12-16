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
import os
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🏫", layout="wide")

# --- QUẢN LÝ THƯ MỤC DỮ LIỆU CỨNG ---
DATA_FOLDER = "matrix_data"
# Tạo thư mục an toàn
try:
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
except:
    DATA_FOLDER = "." # Fallback nếu không tạo được thư mục

# --- QUẢN LÝ SESSION (KHỞI TẠO ĐẦY ĐỦ ĐỂ TRÁNH LỖI) ---
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_grade' not in st.session_state: st.session_state.selected_grade = 'Lớp 1' # Quan trọng: Khởi tạo mặc định
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = ''
if 'selected_color' not in st.session_state: st.session_state.selected_color = ''
if 'topic_df' not in st.session_state: st.session_state.topic_df = None 
if 'matrix_df_display' not in st.session_state: st.session_state.matrix_df_display = None
if 'auto_config' not in st.session_state: st.session_state.auto_config = {}

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    /* Ẩn giao diện mặc định */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
    
    /* Thẻ tác giả nổi */
    .floating-author-badge {
        position: fixed; bottom: 20px; right: 20px; background-color: white; padding: 10px 15px;
        border-radius: 50px; box-shadow: 0 4px 15px rgba(0,0,0,0.15); border: 2px solid #0984e3; z-index: 9999;
        display: flex; align-items: center; gap: 12px; transition: transform 0.3s ease;
    }
    .floating-author-badge:hover {transform: scale(1.05);}
    .author-avatar {width: 40px; height: 40px; border-radius: 50%; border: 2px solid #dfe6e9;}
    .author-info {display: flex; flex-direction: column; line-height: 1.2;}
    .author-name {font-weight: bold; color: #2d3436; font-size: 14px;}
    .author-link {font-size: 11px; color: #0984e3; text-decoration: none; font-weight: 600;}

    /* Style chính */
    .main-title {font-family: 'Times New Roman', serif; font-size: 28px; font-weight: bold; text-align: center; text-transform: uppercase; color: #2c3e50; margin-bottom: 20px;}
    .subject-card {padding: 20px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 18px; cursor: pointer; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;}
    .subject-card:hover {transform: scale(1.05);}
    
    /* Màu sắc */
    .bg-blue {background-color: #3498db;} .bg-green {background-color: #2ecc71;} .bg-red {background-color: #e74c3c;}
    .bg-purple {background-color: #9b59b6;} .bg-orange {background-color: #e67e22;} .bg-teal {background-color: #1abc9c;}
    
    .step-box {border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 15px; background-color: #fcfcfc;}
    .step-header {font-weight: bold; color: #2980b9; margin-bottom: 10px; font-size: 16px;}
    
    /* Footer Style */
    .custom-footer {text-align: center; color: #666; font-size: 14px; margin-top: 50px; border-top: 1px solid #ddd; padding-top: 10px;}
</style>
""", unsafe_allow_html=True)

SUBJECTS_DATA = [
    {"name": "Toán", "icon": "📐", "color": "#3498db", "class": "bg-blue"},
    {"name": "Tiếng Việt", "icon": "📚", "color": "#e74c3c", "class": "bg-red"},
    {"name": "Tin học", "icon": "💻", "color": "#9b59b6", "class": "bg-purple"},
    {"name": "Khoa học/TNXH", "icon": "🌱", "color": "#2ecc71", "class": "bg-green"},
    {"name": "Lịch sử & Địa lí", "icon": "🌏", "color": "#e67e22", "class": "bg-orange"},
    {"name": "Công nghệ", "icon": "🛠️", "color": "#1abc9c", "class": "bg-teal"},
]

def show_floating_badge():
    st.markdown("""
    <div class="floating-author-badge">
        <img src="https://api.dicebear.com/9.x/avataaars/svg?seed=BapCai&backgroundColor=b6e3f4" class="author-avatar">
        <div class="author-info">
            <span class="author-name">BapCai</span>
            <a href="#" class="author-link">🌐 Trang chủ tác giả</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- CÁC HÀM HỖ TRỢ XỬ LÝ FILE ---
def save_uploaded_template(uploaded_file):
    if uploaded_file is not None:
        try:
            file_path = os.path.join(DATA_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
            return True
        except Exception: return False
    return False

def delete_matrix_file(filename):
    try:
        file_path = os.path.join(DATA_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception: pass
    return False

def get_matrix_files():
    try:
        if os.path.exists(DATA_FOLDER):
            return [f for f in os.listdir(DATA_FOLDER) if f.endswith(('.xlsx', '.xls', '.docx', '.pdf', '.csv'))]
    except Exception: pass
    return []

def read_file_content(file_obj, is_local=False):
    try:
        if is_local:
            file_path = os.path.join(DATA_FOLDER, file_obj)
            ext = os.path.splitext(file_obj)[1].lower()
            if ext == '.docx': return "\n".join([p.text for p in Document(file_path).paragraphs])
            elif ext == '.pdf': return "\n".join([page.extract_text() for page in pypdf.PdfReader(file_path).pages])
            elif ext in ['.xlsx', '.xls']: return pd.read_excel(file_path).to_string()
            elif ext == '.csv': return pd.read_csv(file_path).to_string()
        else:
            if file_obj.name.endswith('.docx'): return "\n".join([p.text for p in Document(file_obj).paragraphs])
            elif file_obj.name.endswith('.pdf'): return "\n".join([page.extract_text() for page in pypdf.PdfReader(file_obj).pages])
            elif file_obj.name.endswith(('.xlsx', '.xls')): return pd.read_excel(file_obj).to_string()
            elif file_obj.name.endswith('.csv'): return pd.read_csv(file_obj).to_string()
            else: return file_obj.read().decode("utf-8")
    except: return ""

def clean_text_for_word(text):
    if not text: return ""
    text = str(text)
    patterns = [r"^Tuyệt vời.*?\n", r"^Dưới đây là.*?\n", r"^Chắc chắn rồi.*?\n", r"^Chào bạn.*?\n"]
    for p in patterns: text = re.sub(p, "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"(PHÒNG GD|TRƯỜNG|SỞ GIÁO DỤC|CỘNG HÒA XÃ HỘI).*?(Họ và tên|Lớp).*?\n", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.replace("**", "").replace("##", "").replace("###", "").strip()

# --- HÀM TẠO FILE WORD CHUẨN ---
def create_docx_file(school_name, exam_name, student_info, content_body, answer_key):
    doc = Document()
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass
    
    # 1. Header: Chỉ tên trường (In đậm, Căn giữa)
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    run_school = p_left.add_run(f"{str(school_name).upper()}")
    run_school.bold = True
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n").bold = True
    p_right.add_run("Độc lập - Tự do - Hạnh phúc").bold = True
    p_right.add_run("\n-------------------").bold = False
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph() 
    
    # 2. Tên đề
    title = doc.add_paragraph()
    run_title = title.add_run(str(exam_name).upper())
    run_title.bold = True
    run_title.font.size = Pt(14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 3. Thông tin học sinh
    info = doc.add_paragraph()
    info.add_run("Họ và tên học sinh: ..................................................................................... ").bold = False
    info.add_run(f"Lớp: {student_info.get('grade', '...')}.....")
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph() 
    
    # 4. Khung điểm
    score_table = doc.add_table(rows=2, cols=2)
    score_table.style = 'Table Grid'
    score_table.cell(0, 0).text = "Điểm"
    score_table.cell(0, 1).text = "Lời nhận xét của giáo viên"
    score_table.cell(0,0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.cell(0,1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.rows[1].height = Cm(2.5)
    doc.add_paragraph() 
    doc.add_paragraph("------------------------------------------------------------------------------------------------------")
    
    # 5. Nội dung đề
    clean_body = clean_text_for_word(content_body)
    for line in clean_body.split('\n'):
        line = line.strip()
        if not line: continue
        para = doc.add_paragraph()
        if re.match(r"^(Câu|PHẦN|Bài|Phần) \d+|^(Câu|PHẦN|Bài|Phần) [IVX]+", line, re.IGNORECASE):
            para.add_run(line).bold = True
        else: para.add_run(line)
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    # 6. Đáp án
    doc.add_page_break()
    ans_title = doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN")
    ans_title.runs[0].bold = True
    ans_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(clean_text_for_word(answer_key))
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- AI FUNCTIONS ---
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
    Phân tích văn bản kế hoạch dạy học sau.
    Trích xuất danh sách "Bài học" hoặc "Chủ đề" và "Số tiết".
    OUTPUT: JSON List of Objects: [{{"topic": "Tên bài", "periods": 2}}].
    Văn bản: {text[:15000]} 
    """
    try:
        response = model.generate_content(prompt)
        content = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return data
    except: return []

def generate_exam_content(api_key, subject_plan, matrix_content, config, info, selected_data):
    if not api_key: return None, None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())

    practical_prompt = ""
    if config.get('has_practical'):
        practical_prompt = f"C. PHẦN THỰC HÀNH ({config['prac_point']} điểm): Mức 1: {config['prac_lv1']}, Mức 2: {config['prac_lv2']}, Mức 3: {config['prac_lv3']} yêu cầu."
    
    topics_instruction = ""
    if selected_data:
        topics_str = ", ".join([f"{item['topic']} ({item['periods']} tiết)" for item in selected_data])
        topics_instruction = f"PHẠM VI KIẾN THỨC CHỈ NẰM TRONG: {topics_str}"

    prompt = f"""
    Bạn là chuyên gia khảo thí Tiểu học. Hãy soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    Tuân thủ Thông tư 27, Thông tư 32.
    
    {topics_instruction}
    
    CẤU TRÚC ĐỀ (Bắt buộc):
    1. TRẮC NGHIỆM (Tổng {config['mcq_total']} câu):
       - Dạng: {config['q_abcd']} ABCD, {config['q_tf']} Đ/S, {config['q_match']} Nối, {config['q_fill']} Điền.
       - Mức độ: Biết {config['mcq_lv1']}, Hiểu {config['mcq_lv2']}, Vận dụng {config['mcq_lv3']}.
    
    2. TỰ LUẬN ({config['essay_total']} câu):
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

# ==================== MAIN APP ====================
st.markdown('<div class="main-title">HỆ THỐNG HỖ TRỢ RA ĐỀ TIỂU HỌC</div>', unsafe_allow_html=True)
show_floating_badge()

# --- MÀN HÌNH 1: CHỌN LỚP & MÔN ---
if st.session_state.step == 'home':
    st.write("### 1️⃣ Chọn Khối Lớp & Môn Học:")
    
    # Chọn Lớp
    st.markdown('<div class="step-header">Chọn Khối Lớp:</div>', unsafe_allow_html=True)
    grades = ["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]
    cols_grade = st.columns(5)
    for i, g in enumerate(grades):
        if cols_grade[i].button(g, key=f"grade_{g}", use_container_width=True, 
                                type="primary" if st.session_state.selected_grade == g else "secondary"):
            st.session_state.selected_grade = g
    st.info(f"👉 Đang chọn: **{st.session_state.selected_grade}**")
    
    st.markdown("---")
    
    # Chọn Môn
    st.markdown('<div class="step-header">Chọn Môn Học:</div>', unsafe_allow_html=True)
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

# --- MÀN HÌNH 2: CẤU HÌNH CHI TIẾT ---
elif st.session_state.step == 'config':
    if st.button("⬅️ Quay lại chọn môn"):
        st.session_state.step = 'home'
        st.session_state.auto_config = {} 
        st.rerun()

    subject = st.session_state.selected_subject
    grade = st.session_state.selected_grade
    color = st.session_state.selected_color
    st.markdown(f"""<div style="background-color:{color}; padding:10px; border-radius:8px; color:white; margin-bottom:20px; text-align:center;"><h3 style="margin:0;">{grade.upper()} - MÔN: {subject.upper()}</h3></div>""", unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Cài đặt")
        api_key = st.text_input("Mã API Google:", type="password")
        st.subheader("🏫 Thông tin")
        school_name = st.text_input("Tên trường:", value="PTDTBT Tiểu học Giàng Chu Phìn")
        exam_name = st.text_input("Kỳ thi:", value="CUỐI HỌC KÌ I")
        
        st.markdown("---")
        st.markdown("##### 📂 Dữ liệu Ma trận Mẫu")
        st.info("Upload file (PDF, Word, Excel) vào thư mục dữ liệu cứng.")
        uploaded_template = st.file_uploader("Upload file mẫu:", type=['xlsx', 'docx', 'pdf'], label_visibility="collapsed")
        if uploaded_template is not None:
            if save_uploaded_template(uploaded_template):
                st.success(f"✅ Đã thêm: {uploaded_template.name}")
                st.rerun()
        
        # Xóa file
        existing_files = get_matrix_files()
        if existing_files:
            st.markdown("---")
            st.markdown("##### 🗑️ Xóa file mẫu")
            file_to_delete = st.selectbox("Chọn file cần xóa:", ["-- Chọn --"] + existing_files)
            if st.button("Xóa file đã chọn"):
                if file_to_delete != "-- Chọn --":
                    if delete_matrix_file(file_to_delete):
                        st.toast(f"Đã xóa {file_to_delete}", icon="🗑️")
                        time.sleep(1)
                        st.rerun()

    col_matrix_view, col_config = st.columns([1.2, 1])
    
    # --- CỘT TRÁI: VIEW MA TRẬN & CHỦ ĐỀ ---
    with col_matrix_view:
        # 1. CHỦ ĐỀ
        st.markdown('<div class="step-box"><div class="step-header">Bước 1: Chủ đề dạy học</div>', unsafe_allow_html=True)
        file_plan = st.file_uploader("📂 Tải Kế hoạch (Word/PDF):", type=['docx', 'pdf', 'txt'])
        plan_text_content = ""
        selected_data_for_ai = []
        
        if file_plan: 
            plan_text_content = read_input_file(file_plan)
            if st.session_state.topic_df is None:
                if st.button("🔍 Quét Chủ đề"):
                    if not api_key: st.error("Cần API Key.")
                    else:
                        with st.spinner("Đang phân tích..."):
                            topics_data = extract_topics_json(api_key, plan_text_content)
                            if topics_data:
                                df = pd.DataFrame(topics_data)
                                df.insert(0, "Chọn", False)
                                df.rename(columns={"topic": "Tên bài/Chủ đề", "periods": "Số tiết"}, inplace=True)
                                st.session_state.topic_df = df
                            else: st.error("Không tìm thấy chủ đề.")
            
            if st.session_state.topic_df is not None:
                edited_df = st.data_editor(st.session_state.topic_df, column_config={"Chọn": st.column_config.CheckboxColumn(default=False)}, disabled=["Tên bài/Chủ đề"], hide_index=True, use_container_width=True)
                selected_rows = edited_df[edited_df["Chọn"] == True]
                if not selected_rows.empty:
                    st.success(f"Đã chọn: {len(selected_rows)} bài.")
                    for index, row in selected_rows.iterrows():
                        selected_data_for_ai.append({"topic": row["Tên bài/Chủ đề"], "periods": row["Số tiết"]})

        # 2. VIEW MA TRẬN
        st.markdown('<div class="step-box"><div class="step-header">Bước 2: Ma trận tham chiếu</div>', unsafe_allow_html=True)
        matrix_source = st.radio("", ["Upload file mới", "Dùng Mẫu có sẵn (Trong Folder)"], horizontal=True, label_visibility="collapsed")
        matrix_text_final = ""
        
        if matrix_source == "Upload file mới":
            file_matrix = st.file_uploader("Upload MT:", type=['xlsx', 'xls', 'csv', 'pdf'], label_visibility="collapsed")
            if file_matrix:
                matrix_text_final = read_input_file(file_matrix)
                try:
                    if file_matrix.name.endswith(('.xlsx', '.xls')): st.session_state.matrix_df_display = pd.read_excel(file_matrix)
                    elif file_matrix.name.endswith('.csv'): st.session_state.matrix_df_display = pd.read_csv(file_matrix)
                except: pass
        else:
            files_in_folder = get_matrix_files()
            if files_in_folder:
                selected_file = st.selectbox("Chọn file mẫu:", files_in_folder)
                if selected_file:
                    matrix_text_final = read_file_content(selected_file, is_local=True)
                    try:
                        file_path = os.path.join(DATA_FOLDER, selected_file)
                        if selected_file.endswith(('.xlsx', '.xls')): st.session_state.matrix_df_display = pd.read_excel(file_path)
                        elif selected_file.endswith('.csv'): st.session_state.matrix_df_display = pd.read_csv(file_path)
                    except: pass
            else: st.warning("Chưa có file mẫu.")

        if st.session_state.matrix_df_display is not None:
            st.write("👀 **Xem trước Ma trận:**")
            st.dataframe(st.session_state.matrix_df_display, height=250, use_container_width=True)

    # --- CỘT PHẢI: CẤU HÌNH ---
    with col_config:
        st.write("🛠️ **Thiết lập Số câu & Điểm:**")
        ac = st.session_state.auto_config
        def_mcq_pt = ac.get("mcq_point", 0.5)
        def_essay_pt = ac.get("essay_point", 1.0)
        tabs = st.tabs(["🅰️ Trắc Nghiệm", "🅱️ Tự Luận"])

        with tabs[0]:
            c1, c2, c3 = st.columns(3)
            mcq_lv1 = c1.number_input("Biết (TN):", 0, 20, 3)
            mcq_lv2 = c2.number_input("Hiểu (TN):", 0, 20, 2)
            mcq_lv3 = c3.number_input("Vận dụng (TN):", 0, 20, 1)
            mcq_total = mcq_lv1 + mcq_lv2 + mcq_lv3
            st.caption(f"Tổng: {mcq_total} câu TN.")
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

        score_tn_basic = (q_abcd + q_tf) * def_mcq_pt
        score_tn_adv = (q_match + q_fill) * 1.0 
        score_essay = essay_total * essay_point
        total_score = score_tn_basic + score_tn_adv + score_essay

        if total_score == 10: st.success(f"✅ TỔNG ĐIỂM: 10/10")
        else: st.error(f"⚠️ TỔNG: {total_score} (Cần chỉnh lại)")

        if st.button("🚀 TẠO ĐỀ & TẢI FILE", type="primary", use_container_width=True):
            if not api_key: st.error("Thiếu API Key.")
            elif not plan_text_content or (matrix_source == "Upload file mới" and not matrix_text_final):
                 st.error("Thiếu dữ liệu nguồn.")
            elif not selected_data_for_ai:
                 st.error("Vui lòng tích chọn bài học ở BƯỚC 1.")
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

# --- CHÂN TRANG ---
st.markdown("<div class='custom-footer'>© 2025 - Trần Ngọc Hải - Trường PTDTBT Tiểu học Giàng Chu Phìn - ĐT: 0944 134 973</div>", unsafe_allow_html=True)
