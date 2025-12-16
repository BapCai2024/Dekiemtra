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
# 1. DỮ LIỆU CẤP ĐỘ 4 LỚP: MÔN -> LỚP -> BỘ SÁCH -> CHỦ ĐỀ -> BÀI
# ==========================================
# Lưu ý: Đây là dữ liệu mẫu mô phỏng chính xác cấu trúc mục lục của các bộ sách hiện hành.
# Bạn có thể mở rộng thêm dữ liệu này.

PREDEFINED_DATA = {
    "Toán": {
        "Lớp 1": {
            "Kết nối tri thức": {
                "Chủ đề 1: Các số từ 0 đến 10": [
                    {"topic": "Các số 0, 1, 2, 3, 4, 5", "periods": 2},
                    {"topic": "Các số 6, 7, 8, 9, 10", "periods": 3}
                ],
                "Chủ đề 2: Làm quen với một số hình phẳng": [
                    {"topic": "Hình vuông, hình tròn, hình tam giác", "periods": 2}
                ],
                "Chủ đề 3: Phép cộng, phép trừ trong phạm vi 10": [
                    {"topic": "Phép cộng trong phạm vi 10", "periods": 4},
                    {"topic": "Phép trừ trong phạm vi 10", "periods": 4}
                ]
            },
            "Cánh Diều": {
                "Chương 1: Các số đến 10": [
                    {"topic": "Các số 1, 2, 3", "periods": 1},
                    {"topic": "Các số 4, 5, 6", "periods": 1},
                    {"topic": "Các số 7, 8, 9", "periods": 1},
                    {"topic": "Số 0", "periods": 1},
                    {"topic": "Số 10", "periods": 1}
                ],
                "Chương 2: Phép cộng, phép trừ trong phạm vi 10": [
                    {"topic": "Phép cộng trong phạm vi 6", "periods": 2},
                    {"topic": "Phép trừ trong phạm vi 6", "periods": 2}
                ]
            },
            "Chân trời sáng tạo": {
                "Chủ đề: Các số đến 10": [
                    {"topic": "Các số 1, 2, 3, 4, 5", "periods": 2},
                    {"topic": "Các số 6, 7, 8, 9, 10", "periods": 3}
                ],
                "Chủ đề: Phép cộng, phép trừ trong phạm vi 10": [
                    {"topic": "Phép cộng", "periods": 2},
                    {"topic": "Phép trừ", "periods": 2}
                ]
            }
        },
        "Lớp 4": {
            "Kết nối tri thức": {
                "Chủ đề 1: Số tự nhiên": [
                    {"topic": "Bài 1: Ôn tập các số đến 100 000", "periods": 1},
                    {"topic": "Bài 2: Các số có nhiều chữ số", "periods": 2},
                    {"topic": "Bài 3: Dãy số tự nhiên", "periods": 1}
                ],
                "Chủ đề 2: Các phép tính với số tự nhiên": [
                    {"topic": "Bài 4: Phép cộng, phép trừ", "periods": 2},
                    {"topic": "Bài 5: Phép nhân, phép chia", "periods": 3}
                ]
            },
            "Chân trời sáng tạo": {
                "Chủ đề 1: Ôn tập và bổ sung": [
                    {"topic": "Bài 1: Ôn tập các số đến 100 000", "periods": 1},
                    {"topic": "Bài 2: Biểu thức có chứa chữ", "periods": 2}
                ],
                "Chủ đề 2: Số tự nhiên": [
                    {"topic": "Bài 6: Các số có nhiều chữ số", "periods": 2},
                    {"topic": "Bài 7: Hàng và lớp", "periods": 1}
                ]
            }
        }
    },
    "Tiếng Việt": {
        "Lớp 4": {
            "Kết nối tri thức": {
                "Chủ điểm: Mỗi người một vẻ": [
                    {"topic": "Đọc: Điều kì diệu", "periods": 2},
                    {"topic": "LTVC: Danh từ", "periods": 1},
                    {"topic": "Viết: Tìm hiểu đoạn văn và bài văn kể chuyện", "periods": 2}
                ],
                "Chủ điểm: Trải nghiệm và Khám phá": [
                    {"topic": "Đọc: Tờ báo tường của tôi", "periods": 2},
                    {"topic": "LTVC: Động từ", "periods": 1}
                ]
            },
            "Cánh Diều": {
                "Bài 1: Chân dung của em": [
                    {"topic": "Đọc: Tuổi Ngựa", "periods": 2},
                    {"topic": "LTVC: Danh từ", "periods": 1},
                    {"topic": "Viết: Viết đoạn văn về một nhân vật", "periods": 2}
                ],
                "Bài 2: Chăm học, chăm làm": [
                    {"topic": "Đọc: Văn hay chữ tốt", "periods": 2},
                    {"topic": "LTVC: Động từ", "periods": 1}
                ]
            }
        }
    }
}

# Dữ liệu dự phòng nếu chưa có data chi tiết
DEFAULT_BOOKS = ["Kết nối tri thức", "Chân trời sáng tạo", "Cánh Diều"]
DEFAULT_DATA_STRUCT = {
    "Chủ đề 1 (Mẫu)": [
        {"topic": "Bài 1: Bài học mẫu", "periods": 1},
        {"topic": "Bài 2: Bài học mẫu", "periods": 1}
    ]
}

SUBJECTS_INFO = [
    {"name": "Toán", "icon": "📐", "color": "#3498db"},
    {"name": "Tiếng Việt", "icon": "📚", "color": "#e74c3c"},
    {"name": "Tin học", "icon": "💻", "color": "#9b59b6"},
    {"name": "Khoa học/TNXH", "icon": "🌱", "color": "#2ecc71"},
    {"name": "Lịch sử & Địa lí", "icon": "🌏", "color": "#e67e22"},
    {"name": "Công nghệ", "icon": "🛠️", "color": "#1abc9c"},
]

# ==========================================
# 2. CẤU HÌNH & HÀM XỬ LÝ
# ==========================================
st.set_page_config(page_title="HỖ TRỢ RA ĐỀ THI TIỂU HỌC", page_icon="🏫", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_grade' not in st.session_state: st.session_state.selected_grade = 'Lớp 1'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = 'Toán'
if 'selected_book' not in st.session_state: st.session_state.selected_book = 'Kết nối tri thức'
if 'selected_color' not in st.session_state: st.session_state.selected_color = '#3498db'
if 'matrix_df' not in st.session_state: st.session_state.matrix_df = pd.DataFrame()

# --- CSS Tùy chỉnh ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .main-title {font-family: 'Times New Roman', serif; font-size: 28px; font-weight: bold; text-align: center; color: #2c3e50; text-transform: uppercase; margin-bottom: 10px;}
    .matrix-summary {background-color: #e8f5e9; padding: 15px; border-radius: 8px; text-align: right; font-weight: bold; border: 1px solid #c8e6c9;}
    .step-label {font-weight: bold; font-size: 1.1em; color: #333;}
</style>
""", unsafe_allow_html=True)

def clean_text(text):
    text = str(text)
    text = re.sub(r"^Here is.*?:", "", text, flags=re.MULTILINE)
    text = re.sub(r"^Tuyệt vời.*?\n|^Chào bạn.*?\n", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = text.replace("**", "").replace("##", "").replace("###", "")
    return text.strip()

def create_full_docx(school_name, exam_name, info, body, key, matrix_df):
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
    table.columns[0].width = Inches(2.8)
    table.columns[1].width = Inches(3.2)
    
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_left.add_run("PHÒNG GD&ĐT ............\n").font.size = Pt(12)
    run_school = p_left.add_run(f"{str(school_name).upper()}")
    run_school.bold = True
    
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_nation = p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
    run_nation.bold = True
    run_nation.font.size = Pt(12)
    p_right.add_run("\nĐộc lập - Tự do - Hạnh phúc").bold = True

    doc.add_paragraph()
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run(f"{str(exam_name).upper()}")
    run_title.bold = True
    run_title.font.size = Pt(14)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.add_run(f"Môn: {info['subject']} - {info['grade']} - Bộ sách: {info['book']}")

    # 1. MA TRẬN
    doc.add_paragraph("\nI. MA TRẬN ĐẶC TẢ ĐỀ THI:").bold = True
    if not matrix_df.empty:
        t = doc.add_table(rows=1, cols=len(matrix_df.columns))
        t.style = 'Table Grid'
        hdr_cells = t.rows[0].cells
        for i, col_name in enumerate(matrix_df.columns):
            hdr_cells[i].text = str(col_name)
            hdr_cells[i].paragraphs[0].runs[0].bold = True
            hdr_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for index, row in matrix_df.iterrows():
            row_cells = t.add_row().cells
            for i, item in enumerate(row):
                row_cells[i].text = str(item)
    
    doc.add_page_break()

    # 2. NỘI DUNG ĐỀ
    doc.add_paragraph("II. NỘI DUNG ĐỀ THI:").bold = True
    p_name = doc.add_paragraph("Họ và tên học sinh: ................................................................. Lớp: .........")
    table_score = doc.add_table(rows=2, cols=2)
    table_score.style = 'Table Grid'
    table_score.cell(0,0).text = "Điểm"
    table_score.cell(0,1).text = "Lời nhận xét"
    table_score.rows[1].height = Cm(2.0)
    doc.add_paragraph("\n")
    
    clean_body = clean_text(body)
    for line in clean_body.split('\n'):
        if line.strip():
            para = doc.add_paragraph()
            if re.match(r"^(Câu|PHẦN|Bài) \d+|^(PHẦN) [IVX]+", line.strip(), re.IGNORECASE):
                para.add_run(line.strip()).bold = True
            else:
                para.add_run(line.strip())
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # 3. ĐÁP ÁN
    doc.add_page_break()
    p_key = doc.add_paragraph("HƯỚNG DẪN CHẤM")
    p_key.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_key.runs[0].bold = True
    doc.add_paragraph(clean_text(key))

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def create_matrix_excel(matrix_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        matrix_df.to_excel(writer, index=False, sheet_name='Ma Tran')
        workbook = writer.book
        worksheet = writer.sheets['Ma Tran']
        header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D7E4BC', 'border': 1})
        for col_num, value in enumerate(matrix_df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 20)
    output.seek(0)
    return output

def generate_ai_content(api_key, matrix_df, info):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    matrix_str = matrix_df.to_string(index=False)
    
    prompt = f"""
    Soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']} - BỘ SÁCH: {info['book']}.
    Dựa theo Ma trận sau:
    {matrix_str}
    
    YÊU CẦU:
    1. Tổng điểm = 10.
    2. Nội dung câu hỏi phải BÁM SÁT kiến thức của bộ sách {info['book']}.
    3. Chia rõ: "PHẦN I. TRẮC NGHIỆM", "PHẦN II. TỰ LUẬN".
    4. BẮT BUỘC: Phần đáp án để cuối cùng, tách biệt bằng dòng chữ chính xác là: ###TÁCH_Ở_ĐÂY###
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "###TÁCH_Ở_ĐÂY###" in text:
            parts = text.split("###TÁCH_Ở_ĐÂY###")
            return parts[0].strip(), parts[1].strip()
        else:
            return text, "Lỗi: AI không tạo phần đáp án tách biệt."
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. LOGIC CHÍNH
# ==========================================

st.markdown('<div class="main-title">HỆ THỐNG RA ĐỀ & MA TRẬN TIỂU HỌC</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Cài đặt chung")
    api_key = st.text_input("Google API Key:", type="password")
    st.markdown("""<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Lấy API Key tại đây</a>""", unsafe_allow_html=True)
    school_name = st.text_input("Tên trường:", value="TH NGUYỄN DU")
    exam_name = st.text_input("Tên kỳ thi:", value="KIỂM TRA CUỐI HỌC KÌ I")
    st.divider()
    st.info("💡 Lưu ý: Hãy chọn đúng Bộ sách để có danh sách Chủ đề chính xác.")

# --- STEP 1: CHỌN LỚP & MÔN ---
if st.session_state.step == 'home':
    st.markdown("### 1️⃣ Chọn Khối Lớp & Môn Học")
    
    grades = ["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]
    c_grades = st.columns(5)
    for i, g in enumerate(grades):
        if c_grades[i].button(g, key=g, type="primary" if st.session_state.selected_grade == g else "secondary", use_container_width=True):
            st.session_state.selected_grade = g
    
    st.divider()
    
    subjects = [s for s in SUBJECTS_INFO if not (st.session_state.selected_grade in ["Lớp 1","Lớp 2","Lớp 3"] and s['name'] in ["Khoa học/TNXH", "Lịch sử & Địa lí"])]
    c_sub = st.columns(3)
    for idx, sub in enumerate(subjects):
        with c_sub[idx % 3]:
            if st.button(f"{sub['icon']} {sub['name']}", key=sub['name'], use_container_width=True):
                st.session_state.selected_subject = sub['name']
                st.session_state.selected_color = sub['color']
                st.session_state.step = 'matrix'
                # Reset Ma trận
                st.session_state.matrix_df = pd.DataFrame(columns=["Bộ sách", "Chủ đề", "Bài học", "Mức độ", "Dạng", "Số câu", "Điểm"])
                st.rerun()

# --- STEP 2: CHỌN BỘ SÁCH -> CHỦ ĐỀ -> BÀI HỌC ---
elif st.session_state.step == 'matrix':
    c_back, c_tit = st.columns([1, 5])
    if c_back.button("⬅️ Quay lại"):
        st.session_state.step = 'home'
        st.rerun()
    
    c_tit.markdown(f"<h3 style='color:{st.session_state.selected_color}; margin:0'>{st.session_state.selected_grade} - {st.session_state.selected_subject}</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.4])
    
    # === CỘT TRÁI: LOGIC CHỌN BÀI ===
    with col1:
        st.markdown("#### 2️⃣ Xây dựng Ma trận")
        
        cur_grade = st.session_state.selected_grade
        cur_subj = st.session_state.selected_subject
        
        # 1. LOGIC LẤY DATA BỘ SÁCH
        book_data = {}
        # Kiểm tra xem có dữ liệu của Lớp và Môn này không
        if cur_subj in PREDEFINED_DATA and cur_grade in PREDEFINED_DATA[cur_subj]:
            book_data = PREDEFINED_DATA[cur_subj][cur_grade]
            book_list = list(book_data.keys())
        else:
            book_list = DEFAULT_BOOKS
            book_data = {b: DEFAULT_DATA_STRUCT for b in book_list} # Fake data if missing

        # A. Chọn Bộ Sách
        st.markdown('<p class="step-label">A. Chọn Bộ sách:</p>', unsafe_allow_html=True)
        selected_book = st.selectbox("Bộ sách:", book_list, label_visibility="collapsed")
        
        # B. Chọn Chủ đề (Dựa theo sách)
        st.markdown('<p class="step-label">B. Chọn Chủ đề / Mạch kiến thức:</p>', unsafe_allow_html=True)
        
        current_book_content = book_data.get(selected_book, DEFAULT_DATA_STRUCT)
        categories = list(current_book_content.keys())
        selected_cat = st.selectbox("Chủ đề:", categories, label_visibility="collapsed")
        
        # C. Chọn Bài học (Dựa theo chủ đề)
        st.markdown('<p class="step-label">C. Chọn Bài học cụ thể:</p>', unsafe_allow_html=True)
        lessons_in_cat = current_book_content.get(selected_cat, [])
        lesson_opts = [l['topic'] for l in lessons_in_cat]
        selected_lessons = st.multiselect("Bài học:", lesson_opts, label_visibility="collapsed")
        
        st.markdown("---")
        
        # D. Cấu hình câu hỏi
        c1, c2 = st.columns(2)
        lvl = c1.selectbox("Mức độ", ["Biết", "Hiểu", "Vận dụng"])
        type_q = c2.selectbox("Dạng bài", ["Trắc nghiệm", "Tự luận", "Đúng/Sai", "Điền khuyết"])
        
        step_pt = 0.25 if cur_subj == "Toán" else 0.5
        pt = st.number_input("Điểm/Câu:", 0.25, 5.0, 1.0, step_pt)
        
        if st.button("⬇️ Thêm vào Ma trận", type="primary", use_container_width=True):
            if not selected_lessons:
                st.warning("Vui lòng chọn ít nhất 1 bài học!")
            else:
                new_rows = []
                for l_name in selected_lessons:
                    new_rows.append({
                        "Bộ sách": selected_book,
                        "Chủ đề": selected_cat,
                        "Bài học": l_name,
                        "Mức độ": lvl,
                        "Dạng": type_q,
                        "Số câu": 1,
                        "Điểm": pt
                    })
                new_df = pd.DataFrame(new_rows)
                st.session_state.matrix_df = pd.concat([st.session_state.matrix_df, new_df], ignore_index=True)
                st.success("Đã thêm!")
                time.sleep(0.5)
                st.rerun()

    # === CỘT PHẢI: VIEW & EXPORT ===
    with col2:
        st.markdown("#### 3️⃣ Xem & Xuất Ma trận")
        
        if not st.session_state.matrix_df.empty:
            edited_df = st.data_editor(st.session_state.matrix_df, num_rows="dynamic", use_container_width=True, height=300)
            st.session_state.matrix_df = edited_df
            
            total_q = edited_df["Số câu"].sum()
            total_p = (edited_df["Số câu"] * edited_df["Điểm"]).sum()
            
            st.markdown(f"""
            <div class="matrix-summary">
                SL Câu: {total_q} | Tổng điểm: <span style='color:{'green' if total_p==10 else 'red'}'>{total_p}/10</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Export Buttons
            c_ex1, c_ex2 = st.columns(2)
            excel_data = create_matrix_excel(edited_df)
            c_ex1.download_button("📥 Tải Ma trận (Excel)", excel_data, "MaTran.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            c_ex2.download_button("📥 Tải Ma trận (CSV)", edited_df.to_csv().encode('utf-8'), "MaTran.csv", "text/csv", use_container_width=True)
            
            st.divider()
            
            # Generate AI Button
            st.markdown("#### 4️⃣ Tạo Đề thi (AI)")
            if st.button("🚀 TẠO ĐỀ & MA TRẬN (.DOCX)", type="primary", use_container_width=True):
                if not api_key:
                    st.error("Chưa nhập API Key!")
                else:
                    with st.spinner("Đang kết nối AI..."):
                        info = {"subject": cur_subj, "grade": cur_grade, "book": selected_book}
                        body, key = generate_ai_content(api_key, edited_df, info)
                        if body:
                            docx_file = create_full_docx(school_name, exam_name, info, body, key, edited_df)
                            st.success("Hoàn tất!")
                            st.download_button("📥 Tải về (.DOCX)", docx_file, f"DeThi_{cur_subj}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                        else:
                            st.error(key)
        else:
            st.info("👈 Vui lòng chọn Bộ sách -> Chủ đề -> Bài học để bắt đầu.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>© 2025 - Hỗ trợ Giáo viên Tiểu học</div>", unsafe_allow_html=True)
