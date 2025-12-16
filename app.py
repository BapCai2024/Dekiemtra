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
st.set_page_config(page_title="HỆ THỐNG RA ĐỀ TIỂU HỌC", page_icon="📝", layout="wide")

# CSS Tùy chỉnh
st.markdown("""
<style>
    .block-container {max-width: 95% !important;}
    .step-label {font-weight: bold; font-size: 1.1em; color: #2c3e50; margin-top: 10px;}
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #333; text-align: center;
        padding: 10px; font-weight: bold; border-top: 1px solid #ccc; z-index: 100;
        font-size: 14px;
    }
    .main-footer {margin-bottom: 50px;}
</style>
""", unsafe_allow_html=True)

# Link dữ liệu mặc định (Bạn hãy thay link raw JSON của bạn vào đây)
DEFAULT_JSON_URL = "https://raw.githubusercontent.com/username/repo/main/data.json"

# Cấu hình môn học
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
    "Tiếng Anh": {"icon": "🔤"}, "Đạo đức": {"icon": "heart"}, "TN&XH": {"icon": "tree"},
    "Âm nhạc": {"icon": "🎵"}, "Mĩ thuật": {"icon": "🎨"}, "GDTC": {"icon": "🏃"}, "HĐTN": {"icon": "🌟"}
}

# --- HÀM TẢI DATA TỪ GITHUB ---
@st.cache_data(ttl=600)
def load_data_from_github(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

# --- HÀM ĐỌC FILE UPLOAD (PDF, WORD, EXCEL) ---
def read_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            return df.to_string()
        else:
            return "Định dạng file không hỗ trợ."
    except Exception as e:
        return f"Lỗi đọc file: {str(e)}"

# --- HÀM TẠO WORD CHUẨN MẪU ---
def create_docx_final(school, exam, info, body, key, matrix_df, score_cfg):
    doc = Document()
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13) # Cỡ chữ 13 hoặc 14
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass
    
    # Header
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False
    tbl.columns[0].width = Inches(3.0)
    tbl.columns[1].width = Inches(3.5)
    
    c1 = tbl.cell(0,0)
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.add_run(f"PHÒNG GD&ĐT ............\n").font.size = Pt(12)
    p1.add_run(f"{school.upper()}").bold = True
    
    c2 = tbl.cell(0,1)
    p2 = c2.paragraphs[0]
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM").bold = True
    p2.add_run("\nĐộc lập - Tự do - Hạnh phúc").bold = True
    
    doc.add_paragraph()
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.add_run(f"{exam.upper()}").bold = True
    p_title.font.size = Pt(14)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.add_run(f"Môn: {info['subj']} - Lớp: {info['grade']} ({info['book']})")
    
    # MA TRẬN
    doc.add_paragraph("\nI. MA TRẬN ĐỀ KIỂM TRA:").bold = True
    
    # Tạo bảng Ma trận phức hợp
    table = doc.add_table(rows=4, cols=21)
    table.style = 'Table Grid'
    table.autofit = False 
    
    # Header Row 1 (Merge Trắc nghiệm / Tự luận)
    c_tn = table.cell(0, 6)
    c_tn.merge(table.cell(0, 17))
    c_tn.text = "Trắc nghiệm"
    c_tn.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_tn.paragraphs[0].runs[0].bold = True

    c_tl = table.cell(0, 18)
    c_tl.merge(table.cell(0, 20))
    c_tl.text = "Tự luận"
    c_tl.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_tl.paragraphs[0].runs[0].bold = True

    # Header Row 2 (Loại câu hỏi)
    types_map = [(6, 8, "Nhiều lựa chọn"), (9, 11, "Đúng - Sai"), (12, 14, "Nối cột"), (15, 17, "Điền khuyết"), (18, 20, "Tự luận")]
    for start, end, text in types_map:
        c = table.cell(1, start)
        c.merge(table.cell(1, end))
        c.text = text
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].font.size = Pt(9)

    # Header Row 3 (Mức độ)
    levels = ["Biết", "Hiểu", "VD"] * 5
    for i, txt in enumerate(levels):
        c = table.cell(2, 6 + i)
        c.text = txt
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].font.size = Pt(9)

    # Header Columns (TT, Chủ đề...)
    headers = ["TT", "Chương/\nChủ đề", "Nội dung/\nĐơn vị KT", "Số\ntiết", "Tỉ\nlệ %", "Số\nđiểm"]
    for i, txt in enumerate(headers):
        c = table.cell(0, i)
        c.merge(table.cell(2, i))
        c.text = txt
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].runs[0].font.size = Pt(9)

    # Fill Data
    current_row_idx = 3 
    stt = 1
    total_q_types = [0] * 15
    total_score_calc = 0

    for index, row in matrix_df.iterrows():
        if current_row_idx >= len(table.rows): table.add_row()
        cells = table.rows[current_row_idx].cells
        
        cells[0].text = str(stt)
        cells[1].text = str(row["Chủ đề"])
        cells[2].text = str(row["Nội dung"])
        cells[3].text = str(row["Số tiết"])
        
        col_keys = ["MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V", "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V", "TL_B", "TL_H", "TL_V"]
        row_score = 0
        
        for i, key in enumerate(col_keys):
            val = int(row.get(key, 0))
            if val > 0:
                cells[6 + i].text = str(val)
                cells[6 + i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                total_q_types[i] += val
                
                # Tính điểm
                if "MCQ" in key: row_score += val * score_cfg['MCQ']
                elif "TF" in key: row_score += val * score_cfg['TF']
                elif "MAT" in key: row_score += val * score_cfg['MAT']
                elif "FILL" in key: row_score += val * score_cfg['FILL']
                elif "TL" in key: row_score += val * score_cfg['TL']
        
        cells[5].text = str(row_score)
        total_score_calc += row_score
        stt += 1
        current_row_idx += 1

    # Tính %
    if total_score_calc > 0:
        for r in range(3, current_row_idx):
            try:
                s = float(table.rows[r].cells[5].text)
                table.rows[r].cells[4].text = f"{(s/total_score_calc)*100:.0f}%"
            except: pass

    # Tổng kết
    row_total = table.add_row()
    row_total.cells[0].merge(row_total.cells[2])
    row_total.cells[0].text = "Tổng số câu"
    row_total.cells[0].paragraphs[0].runs[0].bold = True
    for i, val in enumerate(total_q_types):
        row_total.cells[6+i].text = str(val)
        row_total.cells[6+i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()
    
    # NỘI DUNG ĐỀ
    doc.add_paragraph("II. ĐỀ BÀI:").bold = True
    doc.add_paragraph("Họ và tên học sinh: .............................................................. Lớp: ..........")
    
    tbl_s = doc.add_table(rows=2, cols=2)
    tbl_s.style = 'Table Grid'
    tbl_s.cell(0,0).text = "Điểm"
    tbl_s.cell(0,1).text = "Lời nhận xét"
    tbl_s.rows[1].height = Cm(2.0)
    doc.add_paragraph("\n")

    for line in str(body).split('\n'):
        if line.strip():
            p = doc.add_paragraph()
            if re.match(r"^(Câu|PHẦN|Bài) \d+|^(PHẦN) [IVX]+", line.strip(), re.IGNORECASE):
                p.add_run(line.strip()).bold = True
            else:
                p.add_run(line.strip())

    # ĐÁP ÁN
    doc.add_page_break()
    doc.add_paragraph("HƯỚNG DẪN CHẤM").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(str(key))

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- GỌI AI ---
def call_ai_generate(api_key, matrix_df, info, score_cfg, ref_content):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Xây dựng mô tả ma trận
    matrix_desc = ""
    for _, row in matrix_df.iterrows():
        line = f"- {row['Chủ đề']} ({row['Nội dung']}): "
        has_q = False
        cols = [('MCQ', 'TN 4 lựa chọn'), ('TF', 'Đúng/Sai'), ('MAT', 'Nối cột'), ('FILL', 'Điền khuyết'), ('TL', 'Tự luận')]
        levels = [('B', 'Biết'), ('H', 'Hiểu'), ('V', 'Vận dụng')]
        
        for c_code, c_name in cols:
            for l_code, l_name in levels:
                key = f"{c_code}_{l_code}"
                val = int(row.get(key, 0))
                if val > 0:
                    line += f"{val} câu {c_name} ({l_name}); "
                    has_q = True
        if has_q:
            matrix_desc += line + "\n"

    # Prompt
    prompt = f"""
    Bạn là chuyên gia giáo dục tiểu học. Hãy soạn đề kiểm tra môn {info['subj']} Lớp {info['grade']} - Bộ sách {info['book']}.
    
    1. CẤU TRÚC ĐỀ THI (Dựa trên Ma trận sau):
    {matrix_desc}
    
    2. QUY ĐỊNH ĐIỂM SỐ:
    - Trắc nghiệm (4 lựa chọn A,B,C,D): {score_cfg['MCQ']} đ/câu
    - Đúng/Sai (Mỗi ý): {score_cfg['TF']} đ/ý
    - Nối cột: {score_cfg['MAT']} đ/câu
    - Điền khuyết: {score_cfg['FILL']} đ/câu
    - Tự luận: {score_cfg['TL']} đ/câu
    
    3. TÀI LIỆU THAM KHẢO/MẪU ĐẶC TẢ (NẾU CÓ):
    Người dùng có cung cấp nội dung tham khảo dưới đây. Hãy ưu tiên sử dụng ngữ liệu, phong cách hoặc cấu trúc từ nội dung này nếu phù hợp:
    --- BẮT ĐẦU TÀI LIỆU ---
    {ref_content[:15000]} 
    --- KẾT THÚC TÀI LIỆU ---
    
    4. YÊU CẦU TRÌNH BÀY:
    - Ngôn ngữ trong sáng, chuẩn mực sư phạm tiểu học Việt Nam.
    - PHẦN I: TRẮC NGHIỆM (Gồm các câu hỏi nhiều lựa chọn, đúng sai, nối, điền).
    - PHẦN II: TỰ LUẬN.
    - Cuối cùng là PHẦN ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM CHI TIẾT.
    - QUAN TRỌNG: Giữa ĐỀ BÀI và ĐÁP ÁN phải có dòng chữ duy nhất: ###TACH_DAP_AN###
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "###TACH_DAP_AN###" in text:
            parts = text.split("###TACH_DAP_AN###")
            return parts[0].strip(), parts[1].strip()
        else:
            return text, "Không tìm thấy dấu tách đáp án. AI đã trả về toàn bộ nội dung."
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. LOGIC GIAO DIỆN CHÍNH
# ==========================================
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'data_db' not in st.session_state: st.session_state.data_db = {}
# Init matrix
cols = ["TT", "Chủ đề", "Nội dung", "Số tiết", "MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V", "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V", "TL_B", "TL_H", "TL_V"]
if 'matrix_df' not in st.session_state: st.session_state.matrix_df = pd.DataFrame(columns=cols)
if 'preview_body' not in st.session_state: st.session_state.preview_body = ""
if 'preview_key' not in st.session_state: st.session_state.preview_key = ""

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    st.markdown("""<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Lấy API Key miễn phí</a>""", unsafe_allow_html=True)
    api_key = st.text_input("Google API Key:", type="password")
    
    st.divider()
    st.subheader("1. Nguồn Dữ liệu (JSON)")
    json_url = st.text_input("Link Github (Raw JSON):", value=DEFAULT_JSON_URL)
    
    # Load Data logic
    if st.button("🔄 Tải/Cập nhật Dữ liệu"):
        data = load_data_from_github(json_url)
        if data:
            st.session_state.data_db = data
            st.success("Đã tải dữ liệu thành công!")
        else:
            st.error("Không tải được. Kiểm tra lại đường dẫn.")
            st.session_state.data_db = {} # Hoặc dùng data mẫu
            
    # Fallback nếu chưa tải
    if not st.session_state.data_db:
        data = load_data_from_github(json_url)
        if data: st.session_state.data_db = data
    
    st.divider()
    st.subheader("2. Thông tin chung")
    school_name = st.text_input("Trường:", "TH PTDTBT GIÀNG CHU PHÌN")
    exam_name = st.text_input("Kỳ thi:", "KIỂM TRA CUỐI HỌC KÌ I")
    
    st.divider()
    st.subheader("3. Cấu hình điểm số")
    with st.expander("Chi tiết điểm từng loại", expanded=False):
        s_mcq = st.number_input("Trắc nghiệm (4 chọn):", 0.1, 2.0, 0.5, 0.1)
        s_tf = st.number_input("Đúng / Sai:", 0.1, 2.0, 0.5, 0.1)
        s_mat = st.number_input("Nối cột:", 0.1, 5.0, 1.0, 0.25)
        s_fill = st.number_input("Điền khuyết:", 0.1, 5.0, 1.0, 0.25)
        s_tl = st.number_input("Tự luận:", 0.1, 5.0, 1.0, 0.25)
    score_config = {"MCQ": s_mcq, "TF": s_tf, "MAT": s_mat, "FILL": s_fill, "TL": s_tl}

# --- GIAO DIỆN CHÍNH ---
st.markdown('<h2 style="text-align:center;">HỆ THỐNG RA ĐỀ TIỂU HỌC CHUẨN MA TRẬN MỚI</h2>', unsafe_allow_html=True)

# BƯỚC 1: CHỌN LỚP & MÔN
if st.session_state.step == 'home':
    st.markdown("#### 1️⃣ Chọn Khối Lớp & Môn Học")
    
    # Chọn Lớp
    cols = st.columns(5)
    for i, g in enumerate(["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]):
        if cols[i].button(g, type="primary" if st.session_state.get('selected_grade') == g else "secondary", use_container_width=True):
            st.session_state.selected_grade = g
            st.session_state.selected_subject = None
            st.rerun()
            
    # Chọn Môn
    if st.session_state.get('selected_grade'):
        st.markdown("---")
        valid_subs = VALID_SUBJECTS.get(st.session_state.selected_grade, [])
        c_sub = st.columns(4)
        for idx, s_name in enumerate(valid_subs):
            meta = SUBJECT_META.get(s_name, {"icon": "📘"})
            with c_sub[idx % 4]:
                if st.button(f"{meta['icon']} {s_name}", key=s_name, use_container_width=True):
                    st.session_state.selected_subject = s_name
                    # Reset Matrix
                    st.session_state.matrix_df = pd.DataFrame(columns=cols)
                    st.session_state.step = 'matrix'
                    st.rerun()

# BƯỚC 2: XÂY DỰNG MA TRẬN
elif st.session_state.step == 'matrix':
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅️ Quay lại"):
        st.session_state.step = 'home'
        st.rerun()
        
    grade = st.session_state.selected_grade
    subj = st.session_state.selected_subject
    c2.markdown(f"### 🚩 Đang soạn: {grade} - {subj}")
    
    # Lấy data từ Session State (đã tải từ JSON)
    db_source = st.session_state.data_db
    
    # An toàn khi truy cập data
    current_data = db_source.get(subj, {}).get(grade, {}) if db_source else {}
    
    col_left, col_right = st.columns([1, 2.5])
    
    # --- CỘT TRÁI: CHỌN NỘI DUNG ---
    with col_left:
        st.info("B1. Chọn nội dung kiến thức")
        
        if not current_data:
            st.warning("Chưa có dữ liệu cho môn này. Vui lòng cập nhật JSON hoặc chọn môn khác.")
            books = []
        else:
            books = list(current_data.keys())
            
        sel_book = st.selectbox("Bộ sách:", books) if books else None
        
        if sel_book:
            book_content = current_data.get(sel_book, {})
            topics = list(book_content.keys())
            sel_topic = st.selectbox("Chủ đề:", topics) if topics else None
            
            lessons = book_content.get(sel_topic, []) if sel_topic else []
            # Hiển thị tên bài kèm số tiết
            lesson_opts = [f"{l['topic']} ({l['periods']} tiết)" for l in lessons]
            sel_lessons = st.multiselect("Bài học:", lesson_opts)
            
            if st.button("⬇️ Thêm vào Ma trận", type="primary", use_container_width=True):
                if sel_lessons:
                    rows = []
                    start_tt = len(st.session_state.matrix_df) + 1
                    for l_str in sel_lessons:
                        # Tách tên và số tiết
                        # Giả định format: "Tên bài (X tiết)"
                        if "(" in l_str and " tiết)" in l_str:
                            l_name = l_str.rsplit(" (", 1)[0]
                            p_str = l_str.rsplit(" (", 1)[1].replace(" tiết)", "")
                        else:
                            l_name = l_str
                            p_str = "1"
                            
                        new_row = {
                            "TT": start_tt, "Chủ đề": sel_topic, "Nội dung": l_name, "Số tiết": int(p_str),
                            "MCQ_B": 0, "MCQ_H": 0, "MCQ_V": 0, 
                            "TF_B": 0, "TF_H": 0, "TF_V": 0,
                            "MAT_B": 0, "MAT_H": 0, "MAT_V": 0,
                            "FILL_B": 0, "FILL_H": 0, "FILL_V": 0,
                            "TL_B": 0, "TL_H": 0, "TL_V": 0
                        }
                        rows.append(new_row)
                        start_tt += 1
                    
                    st.session_state.matrix_df = pd.concat([st.session_state.matrix_df, pd.DataFrame(rows)], ignore_index=True)
                    st.rerun()

    # --- CỘT PHẢI: BẢNG MA TRẬN & TẠO ĐỀ ---
    with col_right:
        st.info("B2. Nhập số lượng câu hỏi vào bảng & Tải file mẫu (nếu có)")
        
        # 1. Bảng nhập liệu
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
            
            edited_df = st.data_editor(
                st.session_state.matrix_df, 
                column_config=col_cfg, 
                hide_index=True, 
                use_container_width=True, 
                height=300
            )
            st.session_state.matrix_df = edited_df
            
            # Tính điểm Real-time
            t_mcq = edited_df[["MCQ_B", "MCQ_H", "MCQ_V"]].sum().sum() * score_config['MCQ']
            t_tf = edited_df[["TF_B", "TF_H", "TF_V"]].sum().sum() * score_config['TF']
            t_mat = edited_df[["MAT_B", "MAT_H", "MAT_V"]].sum().sum() * score_config['MAT']
            t_fill = edited_df[["FILL_B", "FILL_H", "FILL_V"]].sum().sum() * score_config['FILL']
            t_tl = edited_df[["TL_B", "TL_H", "TL_V"]].sum().sum() * score_config['TL']
            total_score = t_mcq + t_tf + t_mat + t_fill + t_tl
            
            st.success(f"📊 TỔNG ĐIỂM DỰ KIẾN: {total_score} điểm")
            
            st.markdown("---")
            
            # 2. Upload file mẫu (Tính năng mới)
            st.markdown("##### 📂 Tải lên Mẫu Ma trận / Đặc tả (Tùy chọn)")
            st.caption("Nếu bạn có file Ma trận hoặc Đặc tả (PDF, Word, Excel), hãy tải lên để AI tham khảo cấu trúc.")
            uploaded_file = st.file_uploader("Chọn file...", type=['pdf', 'docx', 'xlsx'])
            
            ref_content = ""
            if uploaded_file:
                with st.spinner("Đang đọc file..."):
                    ref_content = read_uploaded_file(uploaded_file)
                    st.info(f"Đã đọc xong file: {uploaded_file.name}")
            
            # 3. Nút tạo đề
            if st.button("📝 SOẠN ĐỀ (XEM TRƯỚC)", type="primary", use_container_width=True):
                if not api_key:
                    st.error("Vui lòng nhập Google API Key ở cột bên trái!")
                else:
                    with st.spinner("AI đang phân tích và soạn đề..."):
                        info = {"subj": subj, "grade": grade, "book": sel_book}
                        body, key = call_ai_generate(api_key, edited_df, info, score_config, ref_content)
                        
                        if body:
                            st.session_state.preview_body = body
                            st.session_state.preview_key = key
                            st.session_state.info = info
                            st.session_state.total_score = total_score
                            st.session_state.step = 'preview'
                            st.rerun()
                        else:
                            st.error(key) # Lỗi
        else:
            st.info("👈 Hãy chọn Bài học ở cột bên trái để bắt đầu.")

# BƯỚC 3: XEM TRƯỚC & XUẤT FILE
elif st.session_state.step == 'preview':
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅️ Quay lại"):
        st.session_state.step = 'matrix'
        st.rerun()
        
    c2.markdown("### 👁️ XEM TRƯỚC VÀ CHỈNH SỬA")
    
    with st.container():
        st.info("Bạn có thể chỉnh sửa trực tiếp nội dung bên dưới trước khi xuất file.")
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
            school_name, 
            exam_name, 
            st.session_state.info, 
            new_body, 
            new_key, 
            st.session_state.matrix_df, 
            score_config
        )
        st.download_button(
            label="📥 Click để tải về máy",
            data=f,
            file_name=f"De_{st.session_state.info['subj']}_{st.session_state.info['grade']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# --- FOOTER ---
st.markdown('<div class="main-footer"></div>', unsafe_allow_html=True) # Spacer
st.markdown('<div class="footer">© 2025 - Trần Ngọc Hải - Trường PTDTBT Tiểu học Giàng Chu Phìn - ĐT: 0944 134 973</div>', unsafe_allow_html=True)
