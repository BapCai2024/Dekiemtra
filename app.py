import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import time
import re

# ==========================================
# 1. CẤU HÌNH MÔN HỌC THEO LỚP (CHUẨN THÔNG TƯ 27)
# ==========================================
# Thông tư 27: Chỉ các môn có bài kiểm tra định kỳ bằng điểm số mới cần ra đề.
VALID_SUBJECTS = {
    "Lớp 1": ["Toán", "Tiếng Việt"],
    "Lớp 2": ["Toán", "Tiếng Việt"],
    "Lớp 3": ["Toán", "Tiếng Việt", "Tin học", "Công nghệ", "Tiếng Anh"],
    "Lớp 4": ["Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí", "Tin học", "Công nghệ", "Tiếng Anh"],
    "Lớp 5": ["Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí", "Tin học", "Công nghệ", "Tiếng Anh"]
}

SUBJECT_META = {
    "Toán": {"icon": "📐", "color": "#3498db"},
    "Tiếng Việt": {"icon": "📚", "color": "#e74c3c"},
    "Tin học": {"icon": "💻", "color": "#9b59b6"},
    "Khoa học": {"icon": "🌱", "color": "#2ecc71"},
    "Lịch sử & Địa lí": {"icon": "🌏", "color": "#e67e22"},
    "Công nghệ": {"icon": "🛠️", "color": "#1abc9c"},
    "Tiếng Anh": {"icon": "abc", "color": "#f1c40f"}
}

# ==========================================
# 2. DỮ LIỆU CHI TIẾT 3 BỘ SÁCH (MẪU FULL LỚP 1)
# ==========================================
DATA_DB = {
    "Toán": {
        "Lớp 1": {
            "Kết nối tri thức": {
                "Chủ đề 1: Các số từ 0 đến 10": [
                    {"topic": "Bài 1: Các số 0, 1, 2, 3, 4, 5", "periods": 3},
                    {"topic": "Bài 2: Các số 6, 7, 8, 9, 10", "periods": 4},
                    {"topic": "Bài 3: Nhiều hơn, ít hơn, bằng nhau", "periods": 2},
                    {"topic": "Bài 4: So sánh số", "periods": 2},
                    {"topic": "Bài 5: Mấy và mấy", "periods": 2}
                ],
                "Chủ đề 2: Làm quen với một số hình phẳng": [
                    {"topic": "Bài 6: Hình vuông, hình tròn, hình tam giác, hình chữ nhật", "periods": 3},
                    {"topic": "Bài 7: Thực hành lắp ghép hình", "periods": 2}
                ],
                "Chủ đề 3: Phép cộng, phép trừ trong phạm vi 10": [
                    {"topic": "Bài 8: Phép cộng trong phạm vi 10", "periods": 4},
                    {"topic": "Bài 9: Phép trừ trong phạm vi 10", "periods": 4},
                    {"topic": "Bài 10: Luyện tập chung", "periods": 2}
                ]
            },
            "Chân trời sáng tạo": {
                "Chủ đề 1: Làm quen với một số hình": [
                    {"topic": "Vị trí", "periods": 1},
                    {"topic": "Khối hộp chữ nhật, Khối lập phương", "periods": 2},
                    {"topic": "Hình tròn, Hình tam giác, Hình vuông, Hình chữ nhật", "periods": 2}
                ],
                "Chủ đề 2: Các số đến 10": [
                    {"topic": "Các số 1, 2, 3, 4, 5", "periods": 3},
                    {"topic": "Các số 6, 7, 8, 9", "periods": 3},
                    {"topic": "Số 0", "periods": 1},
                    {"topic": "Số 10", "periods": 1}
                ],
                "Chủ đề 3: Phép cộng, phép trừ trong phạm vi 10": [
                    {"topic": "Phép cộng", "periods": 4},
                    {"topic": "Phép trừ", "periods": 4},
                    {"topic": "Em làm được những gì?", "periods": 2}
                ]
            },
            "Cánh Diều": {
                "Chương 1: Các số đến 10": [
                    {"topic": "Các số 1, 2, 3", "periods": 1},
                    {"topic": "Các số 4, 5, 6", "periods": 1},
                    {"topic": "Các số 7, 8, 9", "periods": 1},
                    {"topic": "Số 0", "periods": 1},
                    {"topic": "Số 10", "periods": 1},
                    {"topic": "Luyện tập chung", "periods": 2}
                ],
                "Chương 2: Phép cộng, phép trừ trong phạm vi 10": [
                    {"topic": "Phép cộng trong phạm vi 6", "periods": 2},
                    {"topic": "Phép trừ trong phạm vi 6", "periods": 2},
                    {"topic": "Phép cộng trong phạm vi 10", "periods": 3},
                    {"topic": "Phép trừ trong phạm vi 10", "periods": 3}
                ]
            }
        },
        # Dữ liệu mẫu các lớp khác (Bạn có thể bổ sung thêm tương tự Lớp 1)
        "Lớp 4": {
             "Kết nối tri thức": {
                "Chủ đề 1: Số tự nhiên": [{"topic": "Bài 1: Ôn tập các số đến 100 000", "periods": 1}],
                "Chủ đề 2: Các phép tính với số tự nhiên": [{"topic": "Bài 5: Phép cộng, phép trừ", "periods": 2}]
            }
        }
    },
    "Tiếng Việt": {
        "Lớp 1": {
            "Kết nối tri thức": {
                "Chủ đề 1: Những bài học đầu tiên": [
                    {"topic": "Bài 1: A, a", "periods": 2},
                    {"topic": "Bài 2: B, b, dấu huyền", "periods": 2},
                    {"topic": "Bài 3: C, c, dấu sắc", "periods": 2}
                ],
                "Chủ đề 2: Đi học": [
                     {"topic": "Bài 6: O, o, dấu hỏi", "periods": 2},
                     {"topic": "Bài 7: Ô, ô, dấu nặng", "periods": 2}
                ]
            },
            "Chân trời sáng tạo": {
                "Tuần 1: Chủ đề Em là búp măng non": [
                    {"topic": "Bài 1: A a", "periods": 2},
                    {"topic": "Bài 2: B b", "periods": 2}
                ],
                "Tuần 2: Chủ đề Bé và Bà": [
                    {"topic": "Bài 1: Ơ ơ, dấu nặng", "periods": 2}
                ]
            },
             "Cánh Diều": {
                "Bài 1: A, C": [{"topic": "Làm quen chữ cái A, C", "periods": 2}],
                "Bài 2: B, Bễ": [{"topic": "Làm quen chữ cái B", "periods": 2}]
            }
        }
    }
}

# Fallback cho các môn chưa nhập liệu hết
DEFAULT_STRUCT = {
    "Chủ đề chung (Chưa cập nhật)": [{"topic": "Bài 1: Nội dung mẫu", "periods": 1}]
}

# ==========================================
# 3. HÀM XỬ LÝ (GIỮ NGUYÊN TỪ PHIÊN BẢN TRƯỚC)
# ==========================================
st.set_page_config(page_title="HỆ THỐNG RA ĐỀ CHUẨN TT27", page_icon="📝", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_grade' not in st.session_state: st.session_state.selected_grade = 'Lớp 1'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = 'Toán'
if 'matrix_df' not in st.session_state: st.session_state.matrix_df = pd.DataFrame()

# CSS làm đẹp
st.markdown("""
<style>
    .step-label {font-weight: bold; font-size: 1.1em; color: #2c3e50; margin-top: 10px;}
    .stat-box {background: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 4px solid #3498db;}
</style>
""", unsafe_allow_html=True)

def create_docx(school, exam, info, body, key, matrix):
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
    tbl.columns[0].width = Inches(2.8)
    tbl.columns[1].width = Inches(3.2)
    
    c1 = tbl.cell(0,0)
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.add_run("PHÒNG GD&ĐT ............\n").font.size = Pt(12)
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

    # Ma trận
    doc.add_paragraph("\nI. MA TRẬN ĐỀ THI:").bold = True
    if not matrix.empty:
        t = doc.add_table(rows=1, cols=len(matrix.columns))
        t.style = 'Table Grid'
        # Header
        for i, col in enumerate(matrix.columns):
            t.cell(0, i).text = str(col)
        # Body
        for i, row in matrix.iterrows():
            row_cells = t.add_row().cells
            for j, val in enumerate(row):
                row_cells[j].text = str(val)
    
    doc.add_page_break()
    
    # Nội dung
    doc.add_paragraph("II. ĐỀ BÀI:").bold = True
    doc.add_paragraph("Họ và tên: .............................................................. Lớp: ..........")
    
    for line in str(body).split('\n'):
        if line.strip():
            p = doc.add_paragraph()
            if re.match(r"^(Câu|PHẦN|Bài) \d+|^(PHẦN) [IVX]+", line.strip(), re.IGNORECASE):
                p.add_run(line.strip()).bold = True
            else:
                p.add_run(line.strip())
                
    # Đáp án
    doc.add_page_break()
    doc.add_paragraph("HƯỚNG DẪN CHẤM").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(str(key))
    
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def call_ai(api_key, matrix, info):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Soạn đề kiểm tra môn {info['subj']} {info['grade']} - Bộ sách {info['book']}.
    Dựa vào ma trận sau:
    {matrix.to_string(index=False)}
    
    Yêu cầu:
    1. Tổng điểm 10.
    2. Chia phần Trắc nghiệm / Tự luận rõ ràng.
    3. Nội dung bám sát sách giáo khoa.
    4. Cuối cùng phải có phần đáp án, ngăn cách bởi dòng: ###TACH_DAP_AN###
    """
    try:
        resp = model.generate_content(prompt)
        txt = resp.text
        if "###TACH_DAP_AN###" in txt:
            return txt.split("###TACH_DAP_AN###")
        return txt, "Không tìm thấy đáp án tách biệt."
    except Exception as e:
        return None, str(e)

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================

st.markdown('<h2 style="text-align:center; color:#2c3e50;">HỆ THỐNG RA ĐỀ TIỂU HỌC (CHUẨN TT27)</h2>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔧 Cấu hình")
    api_key = st.text_input("Google API Key:", type="password")
    school_name = st.text_input("Trường:", "TH NGUYỄN DU")
    exam_name = st.text_input("Kỳ thi:", "KIỂM TRA CUỐI HỌC KÌ I")
    st.divider()
    st.info("⚠️ Hệ thống tự động lọc môn học theo quy định của Thông tư 27.")

# --- BƯỚC 1: CHỌN LỚP ---
if st.session_state.step == 'home':
    st.markdown("#### 1️⃣ Chọn Lớp")
    cols = st.columns(5)
    grades = ["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]
    
    for i, g in enumerate(grades):
        if cols[i].button(g, type="primary" if st.session_state.selected_grade == g else "secondary", use_container_width=True):
            st.session_state.selected_grade = g
            # Reset lại môn khi đổi lớp để tránh lỗi môn không tồn tại ở lớp mới
            st.session_state.selected_subject = None 
            
    st.divider()
    
    # --- BƯỚC 2: CHỌN MÔN (ĐÃ LỌC) ---
    st.markdown(f"#### 2️⃣ Chọn Môn học ({st.session_state.selected_grade})")
    
    # Lấy danh sách môn hợp lệ cho lớp đã chọn
    valid_subs = VALID_SUBJECTS.get(st.session_state.selected_grade, [])
    
    if not valid_subs:
        st.error("Không có dữ liệu môn học cho lớp này.")
    else:
        # Hiển thị dạng lưới
        c_sub = st.columns(4)
        for idx, s_name in enumerate(valid_subs):
            meta = SUBJECT_META.get(s_name, {"icon": "📘", "color": "#95a5a6"})
            with c_sub[idx % 4]:
                if st.button(f"{meta['icon']} {s_name}", key=s_name, use_container_width=True):
                    st.session_state.selected_subject = s_name
                    st.session_state.matrix_df = pd.DataFrame(columns=["Bộ sách", "Chủ đề", "Bài học", "Mức độ", "Dạng", "Số câu", "Điểm"])
                    st.session_state.step = 'matrix'
                    st.rerun()

# --- BƯỚC 3: XÂY DỰNG MA TRẬN ---
elif st.session_state.step == 'matrix':
    c1, c2 = st.columns([1,5])
    if c1.button("⬅️ Quay lại"):
        st.session_state.step = 'home'
        st.rerun()
    
    grade = st.session_state.selected_grade
    subj = st.session_state.selected_subject
    
    c2.markdown(f"### 🚩 Đang soạn: {grade} - {subj}")
    
    left, right = st.columns([1, 1.5])
    
    with left:
        st.markdown('<p class="step-label">A. Chọn Bộ Sách & Nội dung:</p>', unsafe_allow_html=True)
        
        # 1. Logic lấy data
        # Kiểm tra xem có data chi tiết không, nếu không dùng data mẫu
        db_grade = DATA_DB.get(subj, {}).get(grade, {})
        
        if db_grade:
            books = list(db_grade.keys())
        else:
            books = ["Kết nối tri thức", "Chân trời sáng tạo", "Cánh Diều"]
            # Tạo data giả lập nếu chưa nhập liệu
            db_grade = {b: DEFAULT_STRUCT for b in books}

        sel_book = st.selectbox("Bộ sách:", books)
        
        # Lấy chủ đề từ sách đã chọn
        book_content = db_grade.get(sel_book, {})
        topics = list(book_content.keys())
        sel_topic = st.selectbox("Chủ đề:", topics)
        
        # Lấy bài học
        lessons = book_content.get(sel_topic, [])
        lesson_opts = [f"{l['topic']} ({l['periods']} tiết)" for l in lessons]
        sel_lessons = st.multiselect("Bài học:", lesson_opts)
        
        st.divider()
        
        # 2. Cấu hình câu hỏi
        st.markdown('<p class="step-label">B. Cấu hình câu hỏi:</p>', unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        lvl = cc1.selectbox("Mức độ", ["Biết", "Hiểu", "Vận dụng"])
        type_q = cc2.selectbox("Dạng", ["Trắc nghiệm", "Tự luận", "Đ/S"])
        
        pt = st.number_input("Điểm/Câu:", 0.25, 5.0, 1.0, 0.25)
        
        if st.button("⬇️ Thêm vào Ma trận", type="primary", use_container_width=True):
            if not sel_lessons:
                st.warning("Chọn ít nhất 1 bài học!")
            else:
                rows = []
                for l in sel_lessons:
                    # Tách tên bài và số tiết để lưu cho đẹp
                    clean_name = l.split(" (")[0]
                    rows.append({
                        "Bộ sách": sel_book,
                        "Chủ đề": sel_topic,
                        "Bài học": clean_name,
                        "Mức độ": lvl,
                        "Dạng": type_q,
                        "Số câu": 1,
                        "Điểm": pt
                    })
                st.session_state.matrix_df = pd.concat([st.session_state.matrix_df, pd.DataFrame(rows)], ignore_index=True)
                st.success("Đã thêm!")
                time.sleep(0.5)
                st.rerun()
                
    with right:
        st.markdown("#### 📋 Ma trận đề thi")
        if not st.session_state.matrix_df.empty:
            edited = st.data_editor(st.session_state.matrix_df, use_container_width=True, num_rows="dynamic", height=300)
            st.session_state.matrix_df = edited
            
            # Thống kê
            t_q = edited["Số câu"].sum()
            t_p = (edited["Số câu"] * edited["Điểm"]).sum()
            
            st.markdown(f"""
            <div class="stat-box">
                Tổng câu: <b>{t_q}</b> &nbsp;|&nbsp; 
                Tổng điểm: <b style="color: {'green' if t_p==10 else 'red'}">{t_p}/10</b>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            if st.button("🚀 TẠO ĐỀ THI (.DOCX)", type="primary", use_container_width=True):
                if not api_key:
                    st.error("Chưa nhập API Key!")
                else:
                    with st.spinner("AI đang soạn đề..."):
                        info = {"subj": subj, "grade": grade, "book": sel_book}
                        body, key = call_ai(api_key, edited, info)
                        if body:
                            f = create_docx(school_name, exam_name, info, body, key, edited)
                            st.download_button("📥 Tải về máy", f, f"DeThi_{subj}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                        else:
                            st.error(key)
        else:
            st.info("👈 Vui lòng chọn dữ liệu bên trái để bắt đầu.")

st.markdown("---")
st.caption("© 2025 - Hỗ trợ Giáo viên Tiểu học - Dữ liệu chuẩn GDPT 2018")
