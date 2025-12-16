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
import requests
import json
import PyPDF2

# ==========================================
# 1. CẤU HÌNH & HÀM HỖ TRỢ
# ==========================================
st.set_page_config(page_title="HỆ THỐNG RA ĐỀ TIỂU HỌC CHUẨN GDPT 2018", page_icon="🏫", layout="wide")

# CSS Tùy chỉnh
st.markdown("""
<style>
    .block-container {max-width: 95% !important;}
    .step-label {font-weight: bold; font-size: 1.1em; color: #2c3e50; margin-top: 10px;}
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f8f9fa; color: #333; text-align: center;
        padding: 10px; font-weight: bold; border-top: 1px solid #ddd; z-index: 999;
        font-size: 14px;
    }
    .main-content {margin-bottom: 60px;}
    .upload-box {border: 2px dashed #3498db; padding: 20px; border-radius: 10px; text-align: center; background-color: #f0f8ff;}
</style>
""", unsafe_allow_html=True)

# Link dữ liệu JSON
INTERNAL_DATA_URL = "https://raw.githubusercontent.com/tranngochai/tieuhoc_db/main/data.json" # Ví dụ link (Thay bằng link thật của bạn)

# Môn học
VALID_SUBJECTS = {
    "Lớp 1": ["Toán", "Tiếng Việt", "Đạo đức", "TN&XH", "Âm nhạc", "Mĩ thuật", "GDTC", "HĐTN"],
    "Lớp 2": ["Toán", "Tiếng Việt", "Đạo đức", "TN&XH", "Âm nhạc", "Mĩ thuật", "GDTC", "HĐTN"],
    "Lớp 3": ["Toán", "Tiếng Việt", "Tin học", "Công nghệ", "Tiếng Anh", "Đạo đức", "TN&XH", "Âm nhạc", "Mĩ thuật", "GDTC", "HĐTN"],
    "Lớp 4": ["Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí", "Tin học", "Công nghệ", "Tiếng Anh", "Đạo đức", "Âm nhạc", "Mĩ thuật", "GDTC", "HĐTN"],
    "Lớp 5": ["Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí", "Tin học", "Công nghệ", "Tiếng Anh", "Đạo đức", "Âm nhạc", "Mĩ thuật", "GDTC", "HĐTN"]
}

SUBJECT_META = {
    "Toán": {"icon": "📐"}, "Tiếng Việt": {"icon": "📚"}, "Tin học": {"icon": "💻"},
    "Khoa học": {"icon": "🌱"}, "Lịch sử & Địa lí": {"icon": "🌏"}, "Công nghệ": {"icon": "🛠️"}, 
    "Tiếng Anh": {"icon": "🔤"}, "Đạo đức": {"icon": "❤️"}, "TN&XH": {"icon": "🌳"},
    "Âm nhạc": {"icon": "🎵"}, "Mĩ thuật": {"icon": "🎨"}, "GDTC": {"icon": "⚽"}, "HĐTN": {"icon": "🌟"}
}

# Dữ liệu dự phòng
DATA_FALLBACK = {
  "Toán": {
    "Lớp 1": {
      "Kết nối tri thức": {
        "Chủ đề 1": [{"topic": "Các số 0-10", "periods": 3}]
      }
    }
  }
}

# --- CÁC HÀM XỬ LÝ ---

@st.cache_data
def load_data():
    try:
        response = requests.get(INTERNAL_DATA_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return DATA_FALLBACK

def get_data_safe(data_source, subj, grade):
    return data_source.get(subj, {}).get(grade, {})

def read_uploaded_file(uploaded_file):
    """Đọc nội dung file upload (PDF/Word/Excel)"""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in reader.pages])
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            return df.to_string()
    except Exception as e:
        return f"Lỗi đọc file: {str(e)}"
    return ""

def create_docx_final(school, exam, info, body, key, matrix_df, score_cfg):
    doc = Document()
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass
    
    # Header
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False
    tbl.columns[0].width = Inches(3.0)
    tbl.columns[1].width = Inches(3.5)
    c1 = tbl.cell(0,0); p1 = c1.paragraphs[0]; p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.add_run(f"PHÒNG GD&ĐT ............\n").font.size = Pt(12)
    p1.add_run(f"{school.upper()}").bold = True
    c2 = tbl.cell(0,1); p2 = c2.paragraphs[0]; p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM").bold = True
    p2.add_run("\nĐộc lập - Tự do - Hạnh phúc").bold = True
    
    doc.add_paragraph()
    p_title = doc.add_paragraph(); p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.add_run(f"{exam.upper()}").bold = True; p_title.font.size = Pt(14)
    doc.add_paragraph(f"Môn: {info['subj']} - Lớp: {info['grade']}").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # I. MA TRẬN (Chỉ vẽ bảng nếu có dữ liệu matrix_df)
    if not matrix_df.empty:
        doc.add_paragraph("\nI. MA TRẬN ĐỀ KIỂM TRA:").bold = True
        table = doc.add_table(rows=4, cols=21)
        table.style = 'Table Grid'
        # ... (Code vẽ bảng Ma trận giữ nguyên như cũ) ...
        # Header Row 1
        c_tn = table.cell(0, 6); c_tn.merge(table.cell(0, 17)); c_tn.text = "Trắc nghiệm"
        c_tl = table.cell(0, 18); c_tl.merge(table.cell(0, 20)); c_tl.text = "Tự luận"
        # ... (Định dạng header) ...
        # Fill Data
        current_row = 3; stt = 1
        col_keys = ["MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V", "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V", "TL_B", "TL_H", "TL_V"]
        for _, row in matrix_df.iterrows():
            if current_row >= len(table.rows): table.add_row()
            cells = table.rows[current_row].cells
            cells[0].text = str(stt)
            cells[1].text = str(row["Chủ đề"])
            cells[2].text = str(row["Nội dung"])
            cells[3].text = str(row["Số tiết"])
            # ... (Điền điểm số) ...
            stt += 1; current_row += 1
    
    doc.add_page_break()
    
    # II. NỘI DUNG ĐỀ
    doc.add_paragraph("II. ĐỀ KIỂM TRA:").bold = True
    doc.add_paragraph("Họ và tên: .............................................................. Lớp: ..........")
    tbl_s = doc.add_table(rows=2, cols=2); tbl_s.style = 'Table Grid'
    tbl_s.cell(0,0).text = "Điểm"; tbl_s.cell(0,1).text = "Lời nhận xét"
    tbl_s.rows[1].height = Cm(2.0)
    doc.add_paragraph("\n")

    for line in str(body).split('\n'):
        if line.strip():
            p = doc.add_paragraph()
            if re.match(r"^(Câu|PHẦN|Bài) \d+|^(PHẦN) [IVX]+", line.strip(), re.IGNORECASE):
                p.add_run(line.strip()).bold = True
            else: p.add_run(line.strip())

    # III. ĐÁP ÁN
    doc.add_page_break()
    doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(str(key))

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def call_ai_generate(api_key, matrix_df, info, score_cfg, uploaded_matrix_content=""):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Xây dựng ngữ cảnh từ 2 nguồn: DataFrame (thủ công) hoặc File Upload
    matrix_context = ""
    
    if uploaded_matrix_content:
        matrix_context = f"""
        NGƯỜI DÙNG ĐÃ TẢI LÊN FILE MA TRẬN / ĐẶC TẢ. HÃY DÙNG NỘI DUNG NÀY ĐỂ RA ĐỀ:
        --- BẮT ĐẦU NỘI DUNG FILE ---
        {uploaded_matrix_content[:20000]}
        --- KẾT THÚC NỘI DUNG FILE ---
        """
    elif not matrix_df.empty:
        desc = ""
        for _, row in matrix_df.iterrows():
            line = f"- {row['Chủ đề']} ({row['Nội dung']}): "
            cols = [('MCQ', 'TN 4 chọn'), ('TF', 'Đúng/Sai'), ('MAT', 'Nối'), ('FILL', 'Điền'), ('TL', 'Tự luận')]
            levels = [('B', 'Biết'), ('H', 'Hiểu'), ('V', 'Vận dụng')]
            has_q = False
            for c, n in cols:
                for l, ln in levels:
                    val = int(row.get(f"{c}_{l}", 0))
                    if val > 0: line += f"{val} câu {n}({ln}); "; has_q = True
            if has_q: desc += line + "\n"
        matrix_context = f"CẤU TRÚC MA TRẬN ĐÃ CHỌN:\n{desc}"
    else:
        matrix_context = "Người dùng chưa cung cấp ma trận cụ thể. Hãy tự xây dựng một đề thi chuẩn theo chương trình GDPT 2018."

    prompt = f"""
    Bạn là chuyên gia giáo dục tiểu học, am hiểu Thông tư 27/2020/TT-BGDĐT.
    Hãy soạn Đề kiểm tra môn {info['subj']} Lớp {info['grade']} - Bộ sách {info.get('book', 'Theo chương trình chuẩn')}.

    1. CĂN CỨ RA ĐỀ:
    {matrix_context}
    
    2. CẤU HÌNH ĐIỂM SỐ (Nếu áp dụng):
    - Trắc nghiệm: {score_cfg['MCQ']}đ/câu
    - Đúng/Sai: {score_cfg['TF']}đ/ý
    - Nối cột: {score_cfg['MAT']}đ/câu
    - Điền khuyết: {score_cfg['FILL']}đ/câu
    - Tự luận: {score_cfg['TL']}đ/câu

    3. YÊU CẦU:
    - Nội dung chuẩn kiến thức GDPT 2018.
    - Truy xuất kiến thức của bạn về các bài học trong ma trận để ra câu hỏi chính xác.
    - Trình bày rõ ràng: PHẦN I (TRẮC NGHIỆM) và PHẦN II (TỰ LUẬN).
    - Cuối cùng là ĐÁP ÁN CHI TIẾT.
    - BẮT BUỘC: Ngăn cách giữa ĐỀ và ĐÁP ÁN bằng dòng chữ: ###TACH_DAP_AN###
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "###TACH_DAP_AN###" in text:
            return text.split("###TACH_DAP_AN###")
        return text, "AI trả về toàn bộ nội dung (Không tìm thấy dấu tách)."
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. GIAO DIỆN CHÍNH (STREAMLIT)
# ==========================================
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'matrix_df' not in st.session_state:
    cols = ["TT", "Chủ đề", "Nội dung", "Số tiết", "MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V", "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V", "TL_B", "TL_H", "TL_V"]
    st.session_state.matrix_df = pd.DataFrame(columns=cols)
if 'uploaded_content' not in st.session_state: st.session_state.uploaded_content = ""

# Load data ngầm
DATA_DB = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    st.markdown("""<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Lấy API Key</a>""", unsafe_allow_html=True)
    api_key = st.text_input("Google API Key:", type="password")
    st.divider()
    school_name = st.text_input("Trường:", "TH PTDTBT GIÀNG CHU PHÌN")
    exam_name = st.text_input("Kỳ thi:", "KIỂM TRA CUỐI HỌC KÌ I")
    st.divider()
    with st.expander("Cấu hình điểm số", expanded=False):
        s_mcq = st.number_input("TN 4 chọn:", 0.1, 2.0, 0.5, 0.1)
        s_tf = st.number_input("Đúng/Sai:", 0.1, 2.0, 0.5, 0.1)
        s_mat = st.number_input("Nối cột:", 0.1, 5.0, 1.0, 0.25)
        s_fill = st.number_input("Điền khuyết:", 0.1, 5.0, 1.0, 0.25)
        s_tl = st.number_input("Tự luận:", 0.1, 5.0, 1.0, 0.25)
    score_config = {"MCQ": s_mcq, "TF": s_tf, "MAT": s_mat, "FILL": s_fill, "TL": s_tl}

# --- BƯỚC 1: CHỌN LỚP & MÔN ---
if st.session_state.step == 'home':
    st.markdown("#### 1️⃣ Chọn Khối Lớp & Môn Học")
    cols = st.columns(5)
    for i, g in enumerate(["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]):
        if cols[i].button(g, type="primary" if st.session_state.get('selected_grade') == g else "secondary", use_container_width=True):
            st.session_state.selected_grade = g
            st.session_state.selected_subject = None
            st.rerun()
            
    if st.session_state.get('selected_grade'):
        st.divider()
        valid_subs = VALID_SUBJECTS.get(st.session_state.selected_grade, [])
        c_sub = st.columns(4)
        for idx, s_name in enumerate(valid_subs):
            meta = SUBJECT_META.get(s_name, {"icon": "📘"})
            with c_sub[idx % 4]:
                if st.button(f"{meta['icon']} {s_name}", key=s_name, use_container_width=True):
                    st.session_state.selected_subject = s_name
                    # Reset
                    cols = ["TT", "Chủ đề", "Nội dung", "Số tiết", "MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V", "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V", "TL_B", "TL_H", "TL_V"]
                    st.session_state.matrix_df = pd.DataFrame(columns=cols)
                    st.session_state.uploaded_content = ""
                    st.session_state.step = 'matrix'
                    st.rerun()

# --- BƯỚC 2: CẤU HÌNH MA TRẬN ---
elif st.session_state.step == 'matrix':
    c1, c2 = st.columns([1, 6])
    if c1.button("⬅️ Quay lại"):
        st.session_state.step = 'home'
        st.rerun()
    
    grade = st.session_state.selected_grade
    subj = st.session_state.selected_subject
    c2.markdown(f"### 🚩 {grade} - {subj}")
    
    # TẠO TABS CHO 2 CÁCH NHẬP LIỆU
    tab_manual, tab_upload = st.tabs(["🛠 Cấu hình Thủ công (Từ Data)", "📂 Tải file Ma trận / Đặc tả có sẵn"])
    
    # --- TAB 1: THỦ CÔNG ---
    with tab_manual:
        col_left, col_right = st.columns([1, 2.5])
        
        with col_left:
            st.info("Chọn Bài học từ dữ liệu")
            db_grade = get_data_safe(DATA_DB, subj, grade)
            if not db_grade:
                st.warning("Dữ liệu chi tiết đang được cập nhật. Bạn có thể dùng Tab 'Tải file' hoặc chọn bộ sách mẫu.")
                books = ["Kết nối tri thức", "Chân trời sáng tạo", "Cánh Diều"]
            else:
                books = list(db_grade.keys())
                
            sel_book = st.selectbox("Bộ sách:", books, key="book_select")
            
            topics = []
            if db_grade and sel_book in db_grade:
                book_content = db_grade[sel_book]
                topics = list(book_content.keys())
            
            sel_topic = st.selectbox("Chủ đề:", topics, key="topic_select") if topics else None
            
            lessons = []
            if sel_topic and db_grade:
                lessons = db_grade[sel_book][sel_topic]
                lesson_opts = [f"{l['topic']} ({l['periods']} tiết)" for l in lessons]
            else:
                lesson_opts = []
                
            sel_lessons = st.multiselect("Bài học:", lesson_opts, key="lesson_select")
            
            if st.button("⬇️ Thêm vào bảng", type="primary", use_container_width=True):
                if sel_lessons:
                    rows = []
                    start_tt = len(st.session_state.matrix_df) + 1
                    for l_str in sel_lessons:
                        if "(" in l_str and " tiết)" in l_str:
                            l_name = l_str.rsplit(" (", 1)[0]
                            try: p_int = int(l_str.rsplit(" (", 1)[1].replace(" tiết)", ""))
                            except: p_int = 1
                        else:
                            l_name = l_str; p_int = 1
                            
                        new_row = {"TT": start_tt, "Chủ đề": sel_topic, "Nội dung": l_name, "Số tiết": p_int}
                        for k in ["MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V", "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V", "TL_B", "TL_H", "TL_V"]:
                            new_row[k] = 0
                        rows.append(new_row)
                        start_tt += 1
                    st.session_state.matrix_df = pd.concat([st.session_state.matrix_df, pd.DataFrame(rows)], ignore_index=True)
                    st.rerun()

        with col_right:
            st.info("Nhập số lượng câu hỏi vào bảng dưới đây:")
            if not st.session_state.matrix_df.empty:
                col_cfg = {
                    "TT": st.column_config.NumberColumn("TT", width=40, disabled=True),
                    "Chủ đề": st.column_config.TextColumn("Chủ đề", width=100, disabled=True),
                    "Nội dung": st.column_config.TextColumn("Nội dung", width=200, disabled=True),
                    "Số tiết": st.column_config.NumberColumn("Tiết", width=50, disabled=True),
                    "MCQ_B": st.column_config.NumberColumn("TN-B", width=50), "MCQ_H": st.column_config.NumberColumn("TN-H", width=50), "MCQ_V": st.column_config.NumberColumn("TN-V", width=50),
                    "TF_B": st.column_config.NumberColumn("ĐS-B", width=50), "TF_H": st.column_config.NumberColumn("ĐS-H", width=50), "TF_V": st.column_config.NumberColumn("ĐS-V", width=50),
                    "MAT_B": st.column_config.NumberColumn("Nối-B", width=50), "MAT_H": st.column_config.NumberColumn("Nối-H", width=50), "MAT_V": st.column_config.NumberColumn("Nối-V", width=50),
                    "FILL_B": st.column_config.NumberColumn("Điền-B", width=50), "FILL_H": st.column_config.NumberColumn("Điền-H", width=50), "FILL_V": st.column_config.NumberColumn("Điền-V", width=50),
                    "TL_B": st.column_config.NumberColumn("TL-B", width=50), "TL_H": st.column_config.NumberColumn("TL-H", width=50), "TL_V": st.column_config.NumberColumn("TL-V", width=50),
                }
                edited_df = st.data_editor(st.session_state.matrix_df, column_config=col_cfg, hide_index=True, use_container_width=True, height=400)
                st.session_state.matrix_df = edited_df
                
                # Tính điểm
                total_score = 0
                for _, r in edited_df.iterrows():
                    total_score += (r['MCQ_B']+r['MCQ_H']+r['MCQ_V'])*score_config['MCQ']
                    total_score += (r['TF_B']+r['TF_H']+r['TF_V'])*score_config['TF']
                    total_score += (r['MAT_B']+r['MAT_H']+r['MAT_V'])*score_config['MAT']
                    total_score += (r['FILL_B']+r['FILL_H']+r['FILL_V'])*score_config['FILL']
                    total_score += (r['TL_B']+r['TL_H']+r['TL_V'])*score_config['TL']
                st.success(f"📊 Tổng điểm dự kiến: {total_score:.2f} điểm")
            else:
                st.info("👈 Hãy chọn bài học ở cột bên trái để thêm vào bảng.")

    # --- TAB 2: UPLOAD FILE ---
    with tab_upload:
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        st.write("Nếu bạn đã có file Ma trận hoặc Bản đặc tả (Word/PDF/Excel), hãy tải lên tại đây. AI sẽ đọc file và ra đề dựa trên nội dung đó.")
        uploaded_file = st.file_uploader("Chọn file...", type=['pdf', 'docx', 'xlsx'])
        if uploaded_file:
            with st.spinner("Đang đọc file..."):
                content = read_uploaded_file(uploaded_file)
                st.session_state.uploaded_content = content
                st.success(f"Đã đọc xong file: {uploaded_file.name}")
                with st.expander("Xem nội dung file đã đọc"):
                    st.text(content[:1000] + "...")
        st.markdown('</div>', unsafe_allow_html=True)

    # NÚT TẠO ĐỀ CHUNG
    st.divider()
    if st.button("📝 SOẠN ĐỀ (XEM TRƯỚC)", type="primary", use_container_width=True):
        if not api_key:
            st.error("Thiếu Google API Key!")
        else:
            # Xác định nguồn dữ liệu để gửi cho AI
            # Ưu tiên file upload nếu có, nếu không thì dùng bảng thủ công
            if st.session_state.uploaded_content:
                source_type = "file"
            elif not st.session_state.matrix_df.empty:
                source_type = "manual"
            else:
                st.warning("Vui lòng xây dựng Ma trận hoặc Tải file lên trước khi tạo đề!")
                st.stop()

            with st.spinner("AI đang truy xuất kiến thức và soạn đề..."):
                info = {"subj": subj, "grade": grade, "book": sel_book if 'sel_book' in locals() else "Theo chương trình"}
                
                body, key = call_ai_generate(
                    api_key, 
                    st.session_state.matrix_df, 
                    info, 
                    score_config, 
                    st.session_state.uploaded_content
                )
                
                if body:
                    st.session_state.preview_body = body
                    st.session_state.preview_key = key
                    st.session_state.info = info
                    st.session_state.step = 'preview'
                    st.rerun()
                else:
                    st.error(key)

# --- BƯỚC 3: XEM TRƯỚC & TẢI ---
elif st.session_state.step == 'preview':
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅️ Quay lại chỉnh sửa", on_click=lambda: st.session_state.update(step='matrix')): pass
    
    c2.markdown("### 👁️ XEM TRƯỚC & CHỈNH SỬA")
    st.info("Bạn có thể chỉnh sửa trực tiếp nội dung bên dưới trước khi xuất file Word.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("**Nội dung Đề thi:**")
        new_body = st.text_area("Body", value=st.session_state.preview_body, height=600, label_visibility="collapsed")
    with col_p2:
        st.markdown("**Đáp án & Hướng dẫn chấm:**")
        new_key = st.text_area("Key", value=st.session_state.preview_key, height=600, label_visibility="collapsed")
        
    st.markdown("---")
    if st.button("💾 TẢI FILE WORD HOÀN CHỈNH (.DOCX)", type="primary", use_container_width=True):
        f = create_docx_final(
            school_name, exam_name, st.session_state.info, 
            new_body, new_key, st.session_state.matrix_df, score_config
        )
        st.download_button(
            label="📥 Click để tải về máy",
            data=f,
            file_name=f"De_{st.session_state.info['subj']}_{st.session_state.info['grade']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# Footer
st.markdown('<div class="main-content"></div>', unsafe_allow_html=True)
st.markdown('<div class="footer">© 2025 - Trần Ngọc Hải - Trường PTDTBT Tiểu học Giàng Chu Phìn - ĐT: 0944 134 973</div>', unsafe_allow_html=True)
