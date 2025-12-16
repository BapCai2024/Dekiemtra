import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
import time
import re

# ==========================================
# 1. CẤU HÌNH & DỮ LIỆU
# ==========================================
st.set_page_config(page_title="HỆ THỐNG RA ĐỀ CHUẨN MA TRẬN MỚI", page_icon="📝", layout="wide")

# Cấu hình điểm số mặc định theo File PDF 
SCORE_CONFIG = {
    "MCQ": 0.5,      # Nhiều lựa chọn
    "TF": 0.5,       # Đúng/Sai
    "MATCH": 1.0,    # Nối cột
    "FILL": 1.0,     # Điền khuyết
    "ESSAY": 1.0     # Tự luận (Mặc định 1đ, có thể chỉnh)
}

# DỮ LIỆU MÔN HỌC (DATA_DB) - GIỮ NGUYÊN TỪ PHIÊN BẢN TRƯỚC
# (Để tiết kiệm không gian hiển thị, tôi rút gọn phần này,
# bạn hãy giữ lại phần DATA_DB đầy đủ ở câu trả lời trước nhé)
DATA_DB = {
    "Toán": {
        "Lớp 1": {
            "Kết nối tri thức": {
                "Chủ đề 1: Các số từ 0 đến 10": [{"topic": "Bài 1: Các số 0, 1, 2, 3, 4, 5", "periods": 3}, {"topic": "Bài 2: Các số 6, 7, 8, 9, 10", "periods": 4}],
                "Chủ đề 2: Làm quen với một số hình phẳng": [{"topic": "Bài 6: Hình vuông, tròn, tam giác", "periods": 3}],
                "Chủ đề 3: Phép cộng, trừ phạm vi 10": [{"topic": "Bài 10: Phép cộng trong phạm vi 10", "periods": 4}]
            },
            "Chân trời sáng tạo": {
                "Chủ đề 1: Các số đến 10": [{"topic": "Các số 1, 2, 3, 4, 5", "periods": 3}],
            },
            "Cánh Diều": {
                "Chương 1: Các số đến 10": [{"topic": "Các số 1, 2, 3", "periods": 1}],
            }
        },
        "Lớp 4": {
            "Kết nối tri thức": {
                "Chủ đề 1: Số tự nhiên": [{"topic": "Bài 1: Ôn tập các số đến 100 000", "periods": 1}],
                "Chủ đề 2: Các phép tính số tự nhiên": [{"topic": "Bài 5: Phép cộng, phép trừ", "periods": 2}]
            }
        }
    },
    "Tiếng Việt": {
        "Lớp 1": {
            "Kết nối tri thức": {
                "Chủ đề 1: Những bài học đầu tiên": [{"topic": "Bài 1: A, a", "periods": 2}],
            }
        }
    }
    # ... (Bạn vui lòng paste thêm phần dữ liệu đầy đủ các môn khác vào đây)
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

# CSS tùy chỉnh để bảng nhập liệu rộng hơn
st.markdown("""
<style>
    .block-container {max-width: 95% !important;}
    .step-label {font-weight: bold; font-size: 1.1em; color: #2c3e50; margin-top: 10px;}
</style>
""", unsafe_allow_html=True)

def set_cell_border(cell, **kwargs):
    """
    Hàm hỗ trợ kẻ khung cho ô trong Word
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for border_name in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), '000000')
        tcPr.append(border)

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

    # --- MA TRẬN ĐẶC TẢ (Complex Table) ---
    doc.add_paragraph("\nI. MA TRẬN ĐỀ KIỂM TRA:").bold = True
    
    # Số cột: TT(1) + Chủ đề(1) + Nội dung(1) + Tiết(1) + Tỉ lệ(1) + Điểm(1) + 
    # MCQ(3) + TF(3) + Match(3) + Fill(3) + Essay(3) = 21 cột
    table = doc.add_table(rows=4, cols=21)
    table.style = 'Table Grid'
    table.autofit = False 
    
    # Set độ rộng cột (tương đối)
    for row in table.rows:
        for i in range(6): row.cells[i].width = Inches(0.4) # Metadata
        for i in range(6, 21): row.cells[i].width = Inches(0.3) # Các ô điểm số nhỏ
    
    # --- HEADER ROW 1: TRẮC NGHIỆM & TỰ LUẬN ---
    # Merge các ô tiêu đề lớn
    # Cột 0-5: Merge theo chiều dọc sau này
    # Cột 6-17: Trắc nghiệm
    c_tn = table.cell(0, 6)
    c_tn.merge(table.cell(0, 17))
    c_tn.text = "Trắc nghiệm"
    c_tn.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_tn.paragraphs[0].runs[0].bold = True

    # Cột 18-20: Tự luận
    c_tl = table.cell(0, 18)
    c_tl.merge(table.cell(0, 20))
    c_tl.text = "Tự luận"
    c_tl.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_tl.paragraphs[0].runs[0].bold = True

    # --- HEADER ROW 2: DẠNG BÀI ---
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

    # --- HEADER ROW 3: MỨC ĐỘ (B-H-V) ---
    levels = ["Biết", "Hiểu", "VD"] * 5
    for i, txt in enumerate(levels):
        c = table.cell(2, 6 + i)
        c.text = txt
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].font.size = Pt(9)

    # --- MERGE CỘT THÔNG TIN CHUNG (TT, Chủ đề...) ---
    headers = ["TT", "Chương/\nChủ đề", "Nội dung/\nĐơn vị KT", "Số\ntiết", "Tỉ\nlệ %", "Số\nđiểm"]
    for i, txt in enumerate(headers):
        c = table.cell(0, i)
        c.merge(table.cell(2, i))
        c.text = txt
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].runs[0].font.size = Pt(10)

    # --- FILL DATA ---
    current_row_idx = 3 # Bắt đầu từ dòng 4 (index 3)
    
    # Duyệt qua DataFrame
    total_q_types = [0] * 15 # Để tính tổng dòng cuối
    
    stt = 1
    for index, row in matrix_df.iterrows():
        # Thêm
