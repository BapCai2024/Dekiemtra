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
# 1. CẤU HÌNH & DỮ LIỆU
# ==========================================
st.set_page_config(page_title="HỆ THỐNG RA ĐỀ CHUẨN MA TRẬN MỚI", page_icon="📝", layout="wide")

# Cấu hình điểm số mặc định
SCORE_CONFIG = {
    "MCQ": 0.5,      # Nhiều lựa chọn
    "TF": 0.5,       # Đúng/Sai
    "MATCH": 1.0,    # Nối cột
    "FILL": 1.0,     # Điền khuyết
    "ESSAY": 1.0     # Tự luận (Mặc định 1đ, có thể chỉnh)
}

# DỮ LIỆU MÔN HỌC (DATA_DB)
DATA_DB = {
    "Toán": {
        "Lớp 1": {
            "Kết nối tri thức": {
                "Chủ đề 1: Các số từ 0 đến 10": [{"topic": "Bài 1: Các số 0, 1, 2, 3, 4, 5", "periods": 3}, {"topic": "Bài 2: Các số 6, 7, 8, 9, 10", "periods": 4}],
                "Chủ đề 2: Hình phẳng": [{"topic": "Bài 6: Hình vuông, tròn, tam giác", "periods": 3}],
                "Chủ đề 3: Phép cộng, trừ phạm vi 10": [{"topic": "Bài 10: Phép cộng trong phạm vi 10", "periods": 4}]
            },
            "Chân trời sáng tạo": {
                "Chủ đề 1: Các số đến 10": [{"topic": "Các số 1, 2, 3, 4, 5", "periods": 3}],
            },
            "Cánh Diều": {
                "Chương 1: Các số đến 10": [{"topic": "Các số 1, 2, 3", "periods": 1}],
            }
        },
        "Lớp 2": {
            "Kết nối tri thức": {
                "Chủ đề 1: Ôn tập và bổ sung": [{"topic": "Ôn tập các số đến 100", "periods": 2}],
            }
        },
        "Lớp 3": {
            "Kết nối tri thức": {
                "Chủ đề 1: Số và phép tính": [{"topic": "Bảng nhân 3, 4, 6", "periods": 3}],
            }
        },
        "Lớp 4": {
            "Kết nối tri thức": {
                "Chủ đề 1: Số tự nhiên": [{"topic": "Bài 1: Ôn tập các số đến 100 000", "periods": 1}],
                "Chủ đề 2: Các phép tính số tự nhiên": [{"topic": "Bài 5: Phép cộng, phép trừ", "periods": 2}]
            }
        },
        "Lớp 5": {
            "Kết nối tri thức": {
                "Chủ đề 1: Số thập phân": [{"topic": "Khái niệm số thập phân", "periods": 2}],
            }
        }
    },
    "Tiếng Việt": {
        "Lớp 1": {
            "Kết nối tri thức": {
                "Chủ đề 1: Những bài học đầu tiên": [{"topic": "Bài 1: A, a", "periods": 2}],
            }
        },
        "Lớp 4": {
            "Kết nối tri thức": {
                "Chủ điểm: Mỗi người một vẻ": [{"topic": "Đọc: Điều kì diệu", "periods": 2}]
            }
        },
         "Lớp 5": {
            "Kết nối tri thức": {
                "Chủ điểm: Thế giới tuổi thơ": [{"topic": "Đọc: Thanh âm của gió", "periods": 2}]
            }
        }
    },
    "Khoa học": {
        "Lớp 4": {
            "Kết nối tri thức": {
                "Chủ đề 1: Chất": [{"topic": "Bài 1: Tính chất của nước", "periods": 2}]
            }
        }
    },
    "Lịch sử & Địa lí": {
        "Lớp 4": {
            "Kết nối tri thức": {
                "Chủ đề 1: Địa phương em": [{"topic": "Bài 1: Làm quen với bản đồ", "periods": 2}]
            }
        }
    },
    "Tin học": {
        "Lớp 3": {
            "Kết nối tri thức": {
                "Chủ đề 1: Máy tính và em": [{"topic": "Thông tin và quyết định", "periods": 1}]
            }
        }
    },
    "Công nghệ": {
        "Lớp 3": {
            "Kết nối tri thức": {
                "Chủ đề 1: Công nghệ và đời sống": [{"topic": "Tự nhiên và Công nghệ", "periods": 1}]
            }
        }
    },
    "Tiếng Anh": {
        "Lớp 3": {
            "Global Success": {
                "Unit 1: Hello": [{"topic": "Lesson 1", "periods": 1}]
            }
        }
    }
}

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
# 2. HÀM XỬ LÝ WORD & UI
# ==========================================

st.markdown("""
<style>
    .block-container {max-width: 95% !important;}
    .step-label {font-weight: bold; font-size: 1.1em; color: #2c3e50; margin-top: 10px;}
</style>
""", unsafe_allow_html=True)

def create_docx_advanced(school, exam, info, body, key, matrix_df, total_score_calc):
    doc = Document()
    # Font settings
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(11)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass
    
    # --- HEADER ---
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
    doc.add_paragraph(f"Thời gian làm bài: 40 phút").alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- MA TRẬN ĐẶC TẢ ---
    doc.add_paragraph("\nI. MA TRẬN ĐỀ KIỂM TRA:").bold = True
    
    # Số cột: TT(1) + Chủ đề(1) + Nội dung(1) + Tiết(1) + Tỉ lệ(1) + Điểm(1) + MCQ(3) + TF(3) + Match(3) + Fill(3) + Essay(3) = 21 cột
    table = doc.add_table(rows=4, cols=21)
    table.style = 'Table Grid'
    table.autofit = False 
    
    # Set độ rộng cột (tương đối)
    for row in table.rows:
        for i in range(6): row.cells[i].width = Inches(0.4) # Metadata
        for i in range(6, 21): row.cells[i].width = Inches(0.3) # Các ô điểm số nhỏ
    
    # --- HEADER ROW 1 ---
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

    # --- HEADER ROW 2 ---
    types_map = [
        (6, 8, "Nhiều lựa chọn"),
        (9, 11, "Đúng - Sai"),
        (12, 14, "Nối cột"),
        (15, 17, "Điền khuyết"),
        (18, 20, "Tự luận")
    ]
    for start, end, text in types_map:
        c = table.cell(1, start)
        c.merge(table.cell(1, end))
        c.text = text
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].font.size = Pt(9)
        c.paragraphs[0].runs[0].bold = True

    # --- HEADER ROW 3 ---
    levels = ["Biết", "Hiểu", "VD"] * 5
    for i, txt in enumerate(levels):
        c = table.cell(2, 6 + i)
        c.text = txt
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].font.size = Pt(9)

    # --- MERGE CỘT THÔNG TIN CHUNG ---
    headers = ["TT", "Chương/\nChủ đề", "Nội dung/\nĐơn vị KT", "Số\ntiết", "Tỉ\nlệ %", "Số\nđiểm"]
    for i, txt in enumerate(headers):
        c = table.cell(0, i)
        c.merge(table.cell(2, i))
        c.text = txt
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].runs[0].font.size = Pt(10)

    # --- FILL DATA ---
    current_row_idx = 3 # Bắt đầu từ dòng 4
    
    total_q_types = [0] * 15 # Để tính tổng dòng cuối
    
    stt = 1
    # BẮT ĐẦU VÒNG LẶP SỬA LỖI Ở ĐÂY
    for index, row in matrix_df.iterrows():
        # Thêm dòng mới nếu bảng hết dòng
        if current_row_idx >= len(table.rows):
            table.add_row()
            
        cells = table.rows[current_row_idx].cells
        
        # 1. Metadata
        cells[0].text = str(stt)
        cells[1].text = str(row["Chủ đề"])
        cells[2].text = str(row["Nội dung"])
        cells[3].text = str(row["Số tiết"])
        
        # 2. Các cột điểm số
        col_keys = [
            "MCQ_B", "MCQ_H", "MCQ_V", 
            "TF_B", "TF_H", "TF_V",
            "MAT_B", "MAT_H", "MAT_V",
            "FILL_B", "FILL_H", "FILL_V",
            "TL_B", "TL_H", "TL_V"
        ]
        
        row_score = 0
        
        for i, key in enumerate(col_keys):
            val = int(row.get(key, 0))
            if val > 0:
                cells[6 + i].text = str(val)
                cells[6 + i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                total_q_types[i] += val
                
                # Tính điểm dòng này
                if "MCQ" in key: row_score += val * SCORE_CONFIG["MCQ"]
                elif "TF" in key: row_score += val * SCORE_CONFIG["TF"]
                elif "MAT" in key: row_score += val * SCORE_CONFIG["MATCH"]
                elif "FILL" in key: row_score += val * SCORE_CONFIG["FILL"]
                elif "TL" in key: row_score += val * SCORE_CONFIG["ESSAY"]

        # Cập nhật Tỉ lệ và Điểm (Cột 4, 5)
        cells[5].text = str(row_score)
        if total_score_calc > 0:
            percent = (row_score / total_score_calc) * 100
            cells[4].text = f"{percent:.1f}%"
        
        stt += 1
        current_row_idx += 1
    # KẾT THÚC VÒNG LẶP

    # --- DÒNG TỔNG KẾT ---
    row_total = table.add_row()
    row_total.cells[0].merge(row_total.cells[2])
    row_total.cells[0].text = "Tổng số câu"
    row_total.cells[0].paragraphs[0].runs[0].bold = True
    
    for i, val in enumerate(total_q_types):
        row_total.cells[6+i].text = str(val)
        row_total.cells[6+i].paragraphs[0].runs[0].bold = True
        row_total.cells[6+i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()
    
    # --- ĐỀ BÀI ---
    doc.add_paragraph("II. NỘI DUNG ĐỀ KIỂM TRA:").bold = True
    doc.add_paragraph("Họ và tên học sinh: ................................................................. Lớp: .........")
    
    # Khung điểm
    tbl_sc = doc.add_table(rows=2, cols=2)
    tbl_sc.style = 'Table Grid'
    tbl_sc.cell(0,0).text = "Điểm"
    tbl_sc.cell(0,1).text = "Lời nhận xét của giáo viên"
    tbl_sc.rows[1].height = Cm(2.5)
    doc.add_paragraph("\n")

    # Nội dung từ AI
    for line in str(body).split('\n'):
        if line.strip():
            p = doc.add_paragraph()
            if re.match(r"^(Câu|PHẦN|Bài) \d+|^(PHẦN) [IVX]+", line.strip(), re.IGNORECASE):
                p.add_run(line.strip()).bold = True
            else:
                p.add_run(line.strip())

    # --- ĐÁP ÁN ---
    doc.add_page_break()
    doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(str(key))

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def call_ai_advanced(api_key, matrix_df, info):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    ai_prompt_data = ""
    for idx, row in matrix_df.iterrows():
        ai_prompt_data += f"\n- Chủ đề: {row['Chủ đề']} ({row['Nội dung']}):\n"
        if row['MCQ_B'] > 0: ai_prompt_data += f"  + Trắc nghiệm (Biết): {row['MCQ_B']} câu\n"
        if row['MCQ_H'] > 0: ai_prompt_data += f"  + Trắc nghiệm (Hiểu): {row['MCQ_H']} câu\n"
        if row['MCQ_V'] > 0: ai_prompt_data += f"  + Trắc nghiệm (Vận dụng): {row['MCQ_V']} câu\n"
        if row['TF_B'] > 0: ai_prompt_data += f"  + Đúng/Sai (Biết): {row['TF_B']} ý\n"
        if row['TF_H'] > 0: ai_prompt_data += f"  + Đúng/Sai (Hiểu): {row['TF_H']} ý\n"
        if row['MAT_B'] > 0: ai_prompt_data += f"  + Nối cột (Biết): {row['MAT_B']} câu\n"
        if row['FILL_B'] > 0: ai_prompt_data += f"  + Điền khuyết (Biết): {row['FILL_B']} câu\n"
        if row['TL_B'] > 0: ai_prompt_data += f"  + Tự luận (Biết): {row['TL_B']} câu\n"
        if row['TL_H'] > 0: ai_prompt_data += f"  + Tự luận (Hiểu): {row['TL_H']} câu\n"
        if row['TL_V'] > 0: ai_prompt_data += f"  + Tự luận (Vận dụng): {row['TL_V']} câu\n"

    prompt = f"""
    Đóng vai chuyên gia giáo dục. Soạn đề kiểm tra môn {info['subj']} {info['grade']} - Sách {info['book']}.
    
    CẤU TRÚC ĐỀ THI YÊU CẦU:
    {ai_prompt_data}
    
    LƯU Ý QUAN TRỌNG:
    1. Trắc nghiệm nhiều lựa chọn: 4 đáp án A,B,C,D.
    2. Dạng Đúng/Sai: Đưa ra nhận định.
    3. Dạng Nối cột: Cột A nối với Cột B.
    4. Dạng Điền khuyết: Đoạn văn có chỗ trống.
    5. Nội dung chuẩn kiến thức tiểu học Việt Nam.
    6. BẮT BUỘC: Phần đáp án chi tiết tách biệt bằng dòng: ###TACH_DAP_AN###
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
# 3. GIAO DIỆN CHÍNH
# ==========================================
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_grade' not in st.session_state: st.session_state.selected_grade = 'Lớp 1'
if 'matrix_df' not in st.session_state: 
    cols = ["TT", "Chủ đề", "Nội dung", "Số tiết", "MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V", "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V", "TL_B", "TL_H", "TL_V"]
    st.session_state.matrix_df = pd.DataFrame(columns=cols)

st.markdown('<h2 style="text-align:center;">HỆ THỐNG RA ĐỀ TIỂU HỌC CHUẨN MA TRẬN MỚI</h2>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔧 Cài đặt")
    api_key = st.text_input("Google API Key:", type="password")
    school_name = st.text_input("Trường:", "TH NGUYỄN DU")
    exam_name = st.text_input("Kỳ thi:", "KIỂM TRA CUỐI HỌC KÌ I")
    st.divider()
    st.markdown("**Cấu hình điểm số:**")
    st.caption("Trắc nghiệm: 0.5đ | Đ/S: 0.5đ | Khác: 1.0đ")

# --- BƯỚC 1: CHỌN LỚP & MÔN ---
if st.session_state.step == 'home':
    st.markdown("#### 1️⃣ Chọn Lớp & Môn")
    cols = st.columns(5)
    for i, g in enumerate(["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]):
        if cols[i].button(g, type="primary" if st.session_state.selected_grade == g else "secondary", use_container_width=True):
            st.session_state.selected_grade = g
            st.session_state.selected_subject = None
            
    st.divider()
    valid_subs = VALID_SUBJECTS.get(st.session_state.selected_grade, [])
    c_sub = st.columns(4)
    for idx, s_name in enumerate(valid_subs):
        meta = SUBJECT_META.get(s_name, {"icon": "📘", "color": "#95a5a6"})
        with c_sub[idx % 4]:
            if st.button(f"{meta['icon']} {s_name}", key=s_name, use_container_width=True):
                st.session_state.selected_subject = s_name
                cols = ["TT", "Chủ đề", "Nội dung", "Số tiết", "MCQ_B", "MCQ_H", "MCQ_V", "TF_B", "TF_H", "TF_V", "MAT_B", "MAT_H", "MAT_V", "FILL_B", "FILL_H", "FILL_V", "TL_B", "TL_H", "TL_V"]
                st.session_state.matrix_df = pd.DataFrame(columns=cols)
                st.session_state.step = 'matrix'
                st.rerun()

# --- BƯỚC 2: NHẬP LIỆU MA TRẬN ---
elif st.session_state.step == 'matrix':
    c1, c2 = st.columns([1,6])
    if c1.button("⬅️ Quay lại"):
        st.session_state.step = 'home'
        st.rerun()
    
    grade = st.session_state.selected_grade
    subj = st.session_state.selected_subject
    c2.markdown(f"### 🚩 {grade} - {subj}")
    
    # === PHẦN CHỌN BÀI HỌC (TRÁI) ===
    left, right = st.columns([1, 2.5])
    
    with left:
        st.info("B1. Chọn nội dung kiến thức")
        db_grade = DATA_DB.get(subj, {}).get(grade, {})
        if not db_grade:
            books = ["Kết nối tri thức", "Chân trời sáng tạo", "Cánh Diều"]
            db_grade = {b: {} for b in books}
        else:
            books = list(db_grade.keys())
            
        sel_book = st.selectbox("Bộ sách:", books)
        book_content = db_grade.get(sel_book, {})
        topics = list(book_content.keys()) if book_content else []
        
        if topics:
            sel_topic = st.selectbox("Chủ đề:", topics)
            lessons = book_content.get(sel_topic, [])
            lesson_opts = [f"{l['topic']} ({l['periods']} tiết)" for l in lessons]
            sel_lessons = st.multiselect("Bài học:", lesson_opts)
            
            if st.button("➕ Thêm vào bảng", type="primary", use_container_width=True):
                if sel_lessons:
                    rows = []
                    start_tt = len(st.session_state.matrix_df) + 1
                    for l in sel_lessons:
                        l_name = l.split(" (")[0]
                        period_str = l.split("(")[1].replace(" tiết)", "")
                        row_data = {
                            "TT": start_tt,
                            "Chủ đề": sel_topic,
                            "Nội dung": l_name,
                            "Số tiết": int(period_str),
                            "MCQ_B": 0, "MCQ_H": 0, "MCQ_V": 0,
                            "TF_B": 0, "TF_H": 0, "TF_V": 0,
                            "MAT_B": 0, "MAT_H": 0, "MAT_V": 0,
                            "FILL_B": 0, "FILL_H": 0, "FILL_V": 0,
                            "TL_B": 0, "TL_H": 0, "TL_V": 0
                        }
                        rows.append(row_data)
                        start_tt += 1
                    st.session_state.matrix_df = pd.concat([st.session_state.matrix_df, pd.DataFrame(rows)], ignore_index=True)
                    st.rerun()
        else:
            st.warning("Chưa có dữ liệu bài học.")

    # === PHẦN BẢNG MA TRẬN (PHẢI) ===
    with right:
        st.info("B2. Nhập số lượng câu hỏi vào ô tương ứng")
        
        if not st.session_state.matrix_df.empty:
            col_cfg = {
                "TT": st.column_config.NumberColumn("TT", width=40, disabled=True),
                "Chủ đề": st.column_config.TextColumn("Chủ đề", width=100, disabled=True),
                "Nội dung": st.column_config.TextColumn("Nội dung", width=150, disabled=True),
                "Số tiết": st.column_config.NumberColumn("Tiết", width=50, disabled=True),
                "MCQ_B": st.column_config.NumberColumn("TN-Biết", width=60),
                "MCQ_H": st.column_config.NumberColumn("TN-Hiểu", width=60),
                "MCQ_V": st.column_config.NumberColumn("TN-VD", width=60),
                "TF_B": st.column_config.NumberColumn("ĐS-Biết", width=60),
                "TF_H": st.column_config.NumberColumn("ĐS-Hiểu", width=60),
                "TF_V": st.column_config.NumberColumn("ĐS-VD", width=60),
                "MAT_B": st.column_config.NumberColumn("Nối-Biết", width=60),
                "MAT_H": st.column_config.NumberColumn("Nối-Hiểu", width=60),
                "MAT_V": st.column_config.NumberColumn("Nối-VD", width=60),
                "FILL_B": st.column_config.NumberColumn("Điền-B", width=60),
                "FILL_H": st.column_config.NumberColumn("Điền-H", width=60),
                "FILL_V": st.column_config.NumberColumn("Điền-V", width=60),
                "TL_B": st.column_config.NumberColumn("TL-Biết", width=60),
                "TL_H": st.column_config.NumberColumn("TL-Hiểu", width=60),
                "TL_V": st.column_config.NumberColumn("TL-VD", width=60),
            }
            
            edited_df = st.data_editor(
                st.session_state.matrix_df, 
                column_config=col_cfg, 
                hide_index=True,
                use_container_width=True,
                height=400
            )
            st.session_state.matrix_df = edited_df
            
            # Tính toán
            total_mcq = edited_df[["MCQ_B", "MCQ_H", "MCQ_V"]].sum().sum()
            total_tf = edited_df[["TF_B", "TF_H", "TF_V"]].sum().sum()
            total_mat = edited_df[["MAT_B", "MAT_H", "MAT_V"]].sum().sum()
            total_fill = edited_df[["FILL_B", "FILL_H", "FILL_V"]].sum().sum()
            total_tl = edited_df[["TL_B", "TL_H", "TL_V"]].sum().sum()
            
            score_mcq = total_mcq * SCORE_CONFIG["MCQ"]
            score_tf = total_tf * SCORE_CONFIG["TF"]
            score_mat = total_mat * SCORE_CONFIG["MATCH"]
            score_fill = total_fill * SCORE_CONFIG["FILL"]
            score_tl = total_tl * SCORE_CONFIG["ESSAY"]
            
            total_score = score_mcq + score_tf + score_mat + score_fill + score_tl
            
            st.success(f"📊 TỔNG ĐIỂM: {total_score}/10")
            
            if st.button("🚀 XUẤT ĐỀ & MA TRẬN WORD", type="primary"):
                if not api_key:
                    st.error("Thiếu API Key")
                else:
                    with st.spinner("Đang xử lý..."):
                        info = {"subj": subj, "grade": grade, "book": sel_book}
                        body, key = call_ai_advanced(api_key, edited_df, info)
                        if body:
                            f = create_docx_advanced(school_name, exam_name, info, body, key, edited_df, total_score)
                            st.download_button("📥 Tải file DOCX", f, "De_Kiem_Tra.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                        else:
                            st.error(key)
        else:
            st.info("👈 Hãy thêm bài học từ cột bên trái.")
