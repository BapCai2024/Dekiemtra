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
import re

# ==========================================
# 1. DỮ LIỆU & CẤU HÌNH
# ==========================================
st.set_page_config(page_title="HỆ THỐNG RA ĐỀ TIỂU HỌC", page_icon="📝", layout="wide")

# CSS tùy chỉnh giao diện và Footer
st.markdown("""
<style>
    .block-container {max-width: 95% !important;}
    .step-label {font-weight: bold; font-size: 1.1em; color: #2c3e50; margin-top: 10px;}
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #333; text-align: center;
        padding: 10px; font-weight: bold; border-top: 1px solid #ccc; z-index: 100;
    }
    .preview-box {border: 2px solid #3498db; padding: 15px; border-radius: 5px; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

# Danh sách môn học theo TT27
VALID_SUBJECTS = {
    "Lớp 1": ["Toán", "Tiếng Việt"],
    "Lớp 2": ["Toán", "Tiếng Việt"],
    "Lớp 3": ["Toán", "Tiếng Việt", "Tin học", "Công nghệ", "Tiếng Anh"],
    "Lớp 4": ["Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí", "Tin học", "Công nghệ", "Tiếng Anh"],
    "Lớp 5": ["Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí", "Tin học", "Công nghệ", "Tiếng Anh"]
}

SUBJECT_META = {
    "Toán": {"icon": "📐"}, "Tiếng Việt": {"icon": "📚"}, "Tin học": {"icon": "💻"},
    "Khoa học": {"icon": "🌱"}, "Lịch sử & Địa lí": {"icon": "🌏"}, "Công nghệ": {"icon": "🛠️"}, "Tiếng Anh": {"icon": "🔤"}
}

# Dữ liệu mẫu (Cần bổ sung thêm dữ liệu thực tế vào đây)
DATA_DB = {
    "Toán": {
        "Lớp 1": {
            "Kết nối tri thức": {
                "Chủ đề 1: Các số 0-10": [{"topic": "Bài 1: Các số 0-5", "periods": 3}, {"topic": "Bài 2: Các số 6-10", "periods": 4}],
                "Chủ đề 2: Hình phẳng": [{"topic": "Bài 6: Hình vuông, tròn...", "periods": 3}]
            },
            "Chân trời sáng tạo": {
                "Chủ đề 1: Các số đến 10": [{"topic": "Bài 1: Các số 1-5", "periods": 3}, {"topic": "Bài 2: Số 0", "periods": 1}],
                "Chủ đề 2: Phép cộng trừ": [{"topic": "Bài 5: Phép cộng", "periods": 4}]
            },
            "Cánh Diều": {
                "Chương 1: Các số đến 10": [{"topic": "Các số 1, 2, 3", "periods": 1}, {"topic": "Số 0", "periods": 1}]
            }
        },
        "Lớp 4": {
            "Kết nối tri thức": {
                "Chủ đề 1: Số tự nhiên": [{"topic": "Bài 1: Ôn tập số đến 100.000", "periods": 1}],
                "Chủ đề 2: Phép tính": [{"topic": "Bài 5: Phép cộng, trừ", "periods": 2}]
            },
            "Chân trời sáng tạo": {
                "Chủ đề 1: Ôn tập": [{"topic": "Bài 1: Ôn tập các số", "periods": 1}]
            },
            "Cánh Diều": {
                "Chủ đề: Số tự nhiên": [{"topic": "Bài 1: Số có nhiều chữ số", "periods": 2}]
            }
        }
        # ... (Thêm các môn và lớp khác tương tự)
    }
}
# Hàm fallback để tránh lỗi nếu thiếu data
def get_data(subj, grade):
    d = DATA_DB.get(subj, {}).get(grade, {})
    if not d:
        return {
            "Kết nối tri thức": {"Chủ đề mẫu": [{"topic": "Bài học mẫu", "periods": 1}]},
            "Chân trời sáng tạo": {"Chủ đề mẫu": [{"topic": "Bài học mẫu", "periods": 1}]},
            "Cánh Diều": {"Chủ đề mẫu": [{"topic": "Bài học mẫu", "periods": 1}]}
        }
    return d

# ==========================================
# 2. HÀM XỬ LÝ WORD (GỘP Ô CHUẨN)
# ==========================================
def create_docx_final(school, exam, info, body, key, matrix_df, score_cfg):
    doc = Document()
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(11)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass
    
    # Header
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False
    tbl.columns[0].width = Inches(2.8)
    tbl.columns[1].width = Inches(4.0)
    
    c1 = tbl.cell(0,0)
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.add_run(f"PHÒNG GD&ĐT ............\n").font.size = Pt(11)
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
    doc.add_paragraph(f"Môn: {info['subj']} - {info['grade']} ({info['book']})").alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # MA TRẬN
    doc.add_paragraph("\nI. MA TRẬN ĐỀ KIỂM TRA:").bold = True
    table = doc.add_table(rows=4, cols=21)
    table.style = 'Table Grid'
    table.autofit = False 
    
    for row in table.rows:
        for i in range(6): row.cells[i].width = Inches(0.4) 
        for i in range(6, 21): row.cells[i].width = Inches(0.3) 
    
    # Header Row 1
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

    # Header Row 2
    types_map = [(6, 8, "Nhiều lựa chọn"), (9, 11, "Đúng - Sai"), (12, 14, "Nối cột"), (15, 17, "Điền khuyết"), (18, 20, "Tự luận")]
    for start, end, text in types_map:
        c = table.cell(1, start)
        c.merge(table.cell(1, end))
        c.text = text
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].font.size = Pt(9)
        c.paragraphs[0].runs[0].bold = True

    # Header Row 3
    levels = ["Biết", "Hiểu", "VD"] * 5
    for i, txt in enumerate(levels):
        c = table.cell(2, 6 + i)
        c.text = txt
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].font.size = Pt(9)

    # Merge Meta Columns
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
    total_q_types = [0] * 15
    stt = 1
    total_matrix_score = 0
    
    for index, row in matrix_df.iterrows():
        if current_row_idx >= len(table.rows): table.add_row()
        cells = table.rows[current_row_idx].cells
        
        cells[0].text = str(stt)
        cells[1].text = str(row["Chủ đề"])
        cells[2].text = str(row["Nội dung"])
        cells[3].text = str(row["Số tiết"])
        
        col_keys = [
            "MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V",
            "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V",
            "TL_B", "TL_H", "TL_V"
        ]
        
        row_score = 0
        for i, key in enumerate(col_keys):
            val = int(row.get(key, 0))
            if val > 0:
                cells[6 + i].text = str(val)
                cells[6 + i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                total_q_types[i] += val
                
                if "MCQ" in key: row_score += val * score_cfg["MCQ"]
                elif "TF" in key: row_score += val * score_cfg["TF"]
                elif "MAT" in key: row_score += val * score_cfg["MAT"]
                elif "FILL" in key: row_score += val * score_cfg["FILL"]
                elif "TL" in key: row_score += val * score_cfg["TL"]

        cells[5].text = str(row_score)
        total_matrix_score += row_score
        stt += 1
        current_row_idx += 1
        
    # Tính tỉ lệ % sau khi có tổng điểm
    if total_matrix_score > 0:
        for r_idx in range(3, current_row_idx):
            try:
                r_score = float(table.rows[r_idx].cells[5].text)
                percent = (r_score / total_matrix_score) * 100
                table.rows[r_idx].cells[4].text = f"{percent:.1f}%"
            except: pass

    # Tổng kết
    row_total = table.add_row()
    row_total.cells[0].merge(row_total.cells[2])
    row_total.cells[0].text = "Tổng số câu"
    row_total.cells[0].paragraphs[0].runs[0].bold = True
    for i, val in enumerate(total_q_types):
        row_total.cells[6+i].text = str(val)
        row_total.cells[6+i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        row_total.cells[6+i].paragraphs[0].runs[0].bold = True

    doc.add_page_break()
    
    # NỘI DUNG ĐỀ
    doc.add_paragraph("II. NỘI DUNG ĐỀ KIỂM TRA:").bold = True
    doc.add_paragraph("Họ và tên học sinh: ................................................................. Lớp: .........")
    tbl_sc = doc.add_table(rows=2, cols=2)
    tbl_sc.style = 'Table Grid'
    tbl_sc.cell(0,0).text = "Điểm"
    tbl_sc.cell(0,1).text = "Lời nhận xét của giáo viên"
    tbl_sc.rows[1].height = Cm(2.5)
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

def call_ai_generate(api_key, matrix_df, info, score_cfg):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    matrix_desc = ""
    for _, row in matrix_df.iterrows():
        matrix_desc += f"\n- {row['Chủ đề']} ({row['Nội dung']}):"
        if row['MCQ_B']>0: matrix_desc += f" {row['MCQ_B']} câu TN(Biết);"
        if row['MCQ_H']>0: matrix_desc += f" {row['MCQ_H']} câu TN(Hiểu);"
        if row['MCQ_V']>0: matrix_desc += f" {row['MCQ_V']} câu TN(VD);"
        if row['TF_B']>0: matrix_desc += f" {row['TF_B']} ý Đ/S(Biết);"
        if row['TF_H']>0: matrix_desc += f" {row['TF_H']} ý Đ/S(Hiểu);"
        if row['MAT_B']>0: matrix_desc += f" {row['MAT_B']} câu Nối(Biết);"
        if row['FILL_B']>0: matrix_desc += f" {row['FILL_B']} câu Điền(Biết);"
        if row['TL_B']>0: matrix_desc += f" {row['TL_B']} câu TL(Biết);"
        if row['TL_H']>0: matrix_desc += f" {row['TL_H']} câu TL(Hiểu);"
        if row['TL_V']>0: matrix_desc += f" {row['TL_V']} câu TL(VD);"

    prompt = f"""
    Soạn đề kiểm tra môn {info['subj']} {info['grade']} - Sách {info['book']}.
    
    CẤU TRÚC:
    {matrix_desc}
    
    ĐIỂM SỐ:
    - Trắc nghiệm 4 lựa chọn: {score_cfg['MCQ']} điểm/câu
    - Đúng/Sai: {score_cfg['TF']} điểm/ý
    - Nối cột: {score_cfg['MAT']} điểm/câu
    - Điền khuyết: {score_cfg['FILL']} điểm/câu
    - Tự luận: {score_cfg['TL']} điểm/câu
    
    YÊU CẦU:
    1. Nội dung chuẩn kiến thức tiểu học.
    2. Trắc nghiệm: 4 đáp án A,B,C,D.
    3. Đúng/Sai: Các nhận định.
    4. Nối cột: Cột A nối Cột B.
    5. Điền khuyết: Đoạn văn/câu có chỗ trống.
    6. Tách riêng phần ĐỀ BÀI và phần ĐÁP ÁN (Hướng dẫn chấm chi tiết).
    7. Giữa ĐỀ và ĐÁP ÁN phải có dòng chữ duy nhất: ###TACH_DAP_AN###
    """
    try:
        resp = model.generate_content(prompt)
        txt = resp.text
        if "###TACH_DAP_AN###" in txt:
            return txt.split("###TACH_DAP_AN###")
        return txt, "Không tìm thấy dấu tách đáp án."
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'matrix_df' not in st.session_state:
    cols = ["TT", "Chủ đề", "Nội dung", "Số tiết", 
            "MCQ_B", "MCQ_H", "MCQ_V", 
            "TF_B", "TF_H", "TF_V", 
            "MAT_B", "MAT_H", "MAT_V", 
            "FILL_B", "FILL_H", "FILL_V", 
            "TL_B", "TL_H", "TL_V"]
    st.session_state.matrix_df = pd.DataFrame(columns=cols)
if 'preview_body' not in st.session_state: st.session_state.preview_body = ""
if 'preview_key' not in st.session_state: st.session_state.preview_key = ""

st.markdown('<h2 style="text-align:center;">HỆ THỐNG RA ĐỀ TIỂU HỌC CHUẨN MA TRẬN MỚI</h2>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔧 Cài đặt")
    st.markdown("""<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Lấy API Key tại đây</a>""", unsafe_allow_html=True)
    api_key = st.text_input("Google API Key:", type="password")
    school_name = st.text_input("Trường:", "TH NGUYỄN DU")
    exam_name = st.text_input("Kỳ thi:", "KIỂM TRA CUỐI HỌC KÌ I")
    
    st.divider()
    
    # CẤU HÌNH ĐIỂM SỐ (Vấn đề 1 đã giải quyết)
    with st.expander("🛠️ Cấu hình điểm số chi tiết", expanded=True):
        s_mcq = st.number_input("Trắc nghiệm (4 lựa chọn):", 0.1, 2.0, 0.5, 0.1)
        s_tf = st.number_input("Đúng / Sai:", 0.1, 2.0, 0.5, 0.1)
        s_mat = st.number_input("Nối cột:", 0.1, 5.0, 1.0, 0.25)
        s_fill = st.number_input("Điền khuyết:", 0.1, 5.0, 1.0, 0.25)
        s_tl = st.number_input("Tự luận:", 0.1, 5.0, 1.0, 0.25)
        
    score_config = {"MCQ": s_mcq, "TF": s_tf, "MAT": s_mat, "FILL": s_fill, "TL": s_tl}

# --- HOME: CHỌN LỚP & MÔN ---
if st.session_state.step == 'home':
    st.markdown("#### 1️⃣ Chọn Lớp & Môn")
    cols = st.columns(5)
    for i, g in enumerate(["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]):
        if cols[i].button(g, type="primary" if st.session_state.get('selected_grade') == g else "secondary", use_container_width=True):
            st.session_state.selected_grade = g
            st.session_state.selected_subject = None
            
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
                    st.session_state.matrix_df = pd.DataFrame(columns=["TT", "Chủ đề", "Nội dung", "Số tiết", "MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V", "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V", "TL_B", "TL_H", "TL_V"])
                    st.session_state.preview_body = ""
                    st.session_state.preview_key = ""
                    st.session_state.step = 'matrix'
                    st.rerun()

# --- MATRIX: CHỌN SÁCH & SOẠN MA TRẬN ---
elif st.session_state.step == 'matrix':
    c1, c2 = st.columns([1, 6])
    if c1.button("⬅️ Quay lại"):
        st.session_state.step = 'home'
        st.rerun()
    
    grade = st.session_state.selected_grade
    subj = st.session_state.selected_subject
    c2.markdown(f"### 🚩 {grade} - {subj}")
    
    left, right = st.columns([1, 2.5])
    
    with left:
        st.info("B1. Chọn nội dung")
        # Lấy data (đã xử lý fallback nếu thiếu)
        db_grade = get_data(subj, grade)
        books = list(db_grade.keys())
        
        sel_book = st.selectbox("Bộ sách:", books)
        book_content = db_grade.get(sel_book, {})
        topics = list(book_content.keys())
        
        sel_topic = st.selectbox("Chủ đề:", topics) if topics else None
        lessons = book_content.get(sel_topic, []) if sel_topic else []
        lesson_opts = [f"{l['topic']} ({l['periods']} tiết)" for l in lessons]
        sel_lessons = st.multiselect("Bài học:", lesson_opts)
        
        if st.button("➕ Thêm vào bảng", type="primary", use_container_width=True):
            if sel_lessons:
                rows = []
                start_tt = len(st.session_state.matrix_df) + 1
                for l in sel_lessons:
                    l_name = l.split(" (")[0]
                    p_str = l.split("(")[1].replace(" tiết)", "")
                    row_data = {
                        "TT": start_tt, "Chủ đề": sel_topic, "Nội dung": l_name, "Số tiết": int(p_str),
                        "MCQ_B": 0, "MCQ_H": 0, "MCQ_V": 0, "TF_B": 0, "TF_H": 0, "TF_V": 0,
                        "MAT_B": 0, "MAT_H": 0, "MAT_V": 0, "FILL_B": 0, "FILL_H": 0, "FILL_V": 0,
                        "TL_B": 0, "TL_H": 0, "TL_V": 0
                    }
                    rows.append(row_data)
                    start_tt += 1
                st.session_state.matrix_df = pd.concat([st.session_state.matrix_df, pd.DataFrame(rows)], ignore_index=True)
                st.rerun()

    with right:
        st.info("B2. Nhập số lượng câu hỏi")
        if not st.session_state.matrix_df.empty:
            col_cfg = {
                "TT": st.column_config.NumberColumn("TT", width=40, disabled=True),
                "Chủ đề": st.column_config.TextColumn("Chủ đề", width=100, disabled=True),
                "Nội dung": st.column_config.TextColumn("Nội dung", width=150, disabled=True),
                "Số tiết": st.column_config.NumberColumn("Tiết", width=50, disabled=True),
                "MCQ_B": st.column_config.NumberColumn("TN-B", width=50), "MCQ_H": st.column_config.NumberColumn("TN-H", width=50), "MCQ_V": st.column_config.NumberColumn("TN-V", width=50),
                "TF_B": st.column_config.NumberColumn("ĐS-B", width=50), "TF_H": st.column_config.NumberColumn("ĐS-H", width=50), "TF_V": st.column_config.NumberColumn("ĐS-V", width=50),
                "MAT_B": st.column_config.NumberColumn("Nối-B", width=50), "MAT_H": st.column_config.NumberColumn("Nối-H", width=50), "MAT_V": st.column_config.NumberColumn("Nối-V", width=50),
                "FILL_B": st.column_config.NumberColumn("Điền-B", width=50), "FILL_H": st.column_config.NumberColumn("Điền-H", width=50), "FILL_V": st.column_config.NumberColumn("Điền-V", width=50),
                "TL_B": st.column_config.NumberColumn("TL-B", width=50), "TL_H": st.column_config.NumberColumn("TL-H", width=50), "TL_V": st.column_config.NumberColumn("TL-V", width=50),
            }
            edited_df = st.data_editor(st.session_state.matrix_df, column_config=col_cfg, hide_index=True, use_container_width=True, height=400)
            st.session_state.matrix_df = edited_df
            
            # Tính điểm Real-time
            t_mcq = edited_df[["MCQ_B", "MCQ_H", "MCQ_V"]].sum().sum() * score_config['MCQ']
            t_tf = edited_df[["TF_B", "TF_H", "TF_V"]].sum().sum() * score_config['TF']
            t_mat = edited_df[["MAT_B", "MAT_H", "MAT_V"]].sum().sum() * score_config['MAT']
            t_fill = edited_df[["FILL_B", "FILL_H", "FILL_V"]].sum().sum() * score_config['FILL']
            t_tl = edited_df[["TL_B", "TL_H", "TL_V"]].sum().sum() * score_config['TL']
            
            total_score = t_mcq + t_tf + t_mat + t_fill + t_tl
            st.success(f"📊 TỔNG ĐIỂM DỰ KIẾN: {total_score} điểm")
            
            if st.button("📝 SOẠN ĐỀ (XEM TRƯỚC)", type="primary"):
                if not api_key:
                    st.error("Thiếu API Key")
                else:
                    with st.spinner("AI đang soạn đề, vui lòng đợi..."):
                        info = {"subj": subj, "grade": grade, "book": sel_book}
                        body, key = call_ai_generate(api_key, edited_df, info, score_config)
                        if body:
                            st.session_state.preview_body = body
                            st.session_state.preview_key = key
                            st.session_state.total_score = total_score
                            st.session_state.info = info
                            st.session_state.step = 'preview'
                            st.rerun()
                        else:
                            st.error(key)

# --- PREVIEW: XEM TRƯỚC VÀ CHỈNH SỬA ---
elif st.session_state.step == 'preview':
    st.button("⬅️ Quay lại chỉnh Ma trận", on_click=lambda: st.session_state.update(step='matrix'))
    st.markdown("### 👁️ XEM TRƯỚC VÀ CHỈNH SỬA")
    st.info("Bạn có thể chỉnh sửa trực tiếp nội dung Đề và Đáp án ở dưới trước khi xuất file Word.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("**Nội dung Đề thi:**")
        new_body = st.text_area("Body", value=st.session_state.preview_body, height=500, label_visibility="collapsed")
    with col_p2:
        st.markdown("**Đáp án:**")
        new_key = st.text_area("Key", value=st.session_state.preview_key, height=500, label_visibility="collapsed")
        
    st.session_state.preview_body = new_body
    st.session_state.preview_key = new_key
    
    if st.button("💾 TẢI FILE WORD (.DOCX)", type="primary", use_container_width=True):
        f = create_docx_final(school_name, exam_name, st.session_state.info, new_body, new_key, st.session_state.matrix_df, score_config)
        st.download_button("Click để tải về", f, "De_Kiem_Tra.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# --- FOOTER ---
st.markdown('<div class="footer">Trần Ngọc Hải - Trường PTDTBT Tiểu học Giàng Chu Phìn - 0944 134 973</div>', unsafe_allow_html=True)
