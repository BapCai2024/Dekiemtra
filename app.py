import streamlit as st
import pandas as pd
import google.generativeai as genai
import re
from io import BytesIO
from docx import Document

# ================== CẤU HÌNH ==================
st.set_page_config(page_title="AI Ra đề theo ma trận TT27", layout="wide")

# ================== API GEMINI ==================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = genai.GenerativeModel("gemini-1.5-pro")

# ================== TT27 ==================
SUBJECTS_BY_GRADE = {
    1: ["Toán", "Tiếng Việt"],
    2: ["Toán", "Tiếng Việt"],
    3: ["Toán", "Tiếng Việt", "Tin học", "Công nghệ"],
    4: ["Toán", "Tiếng Việt", "Tin học", "Công nghệ", "Khoa học", "Lịch sử - Địa lí"],
    5: ["Toán", "Tiếng Việt", "Tin học", "Công nghệ", "Khoa học", "Lịch sử - Địa lí"],
}

# ================== TIỆN ÍCH ==================
def safe_int(v):
    if pd.isna(v):
        return 0
    nums = re.findall(r"\d+", str(v))
    return int(nums[0]) if nums else 0

# ================== ĐỌC MA TRẬN ==================
def read_matrix(file):
    df = pd.read_excel(file, header=None)
    return df.dropna(how="all")

# ================== PROMPT CAO CẤP ==================
def build_prompt(df, grade, subject):
    matrix = []
    for i in range(len(df)):
        matrix.append(
            f"""
Chủ đề {i+1}:
- Trắc nghiệm: NB {safe_int(df.iloc[i,6])}, TH {safe_int(df.iloc[i,7])}, VD {safe_int(df.iloc[i,8])}
- Điền khuyết: NB {safe_int(df.iloc[i,9])}, TH {safe_int(df.iloc[i,10])}, VD {safe_int(df.iloc[i,11])}
- Tự luận: NB {safe_int(df.iloc[i,12])}, TH {safe_int(df.iloc[i,13])}, VD {safe_int(df.iloc[i,14])}
"""
        )

    return f"""
Bạn là CHUYÊN GIA RA ĐỀ KIỂM TRA TIỂU HỌC VIỆT NAM.

NHIỆM VỤ:
Tạo đề kiểm tra định kì theo Thông tư 27.

RÀNG BUỘC TUYỆT ĐỐI:
- Không thay đổi số câu trong ma trận
- Không gộp câu
- Không sinh câu giả
- Ngôn ngữ tiểu học
- Tiếng Việt: KHÔNG dùng bài đọc SGK

THÔNG TIN:
- Khối: {grade}
- Môn: {subject}

MA TRẬN:
{''.join(matrix)}

ĐỊNH DẠNG:
Câu 1. (NB/TN) ...
A. ...
B. ...
C. ...
D. ...

--- ĐÁP ÁN ---
Câu 1: A
...

--- THANG ĐIỂM ---
"""

# ================== AI ==================
def ai_generate(prompt):
    res = MODEL.generate_content(prompt)
    return res.text

# ================== WORD ==================
def export_word(text, grade, subject):
    doc = Document()
    doc.add_heading("ĐỀ KIỂM TRA ĐỊNH KÌ", 1)
    doc.add_paragraph(f"Môn: {subject} – Khối {grade}")
    doc.add_paragraph("Theo Thông tư 27/2020/TT-BGDĐT")
    doc.add_paragraph("")

    for line in text.split("\n"):
        doc.add_paragraph(line)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# ================== UI ==================
st.title("🤖 AI RA ĐỀ THEO MA TRẬN – MỨC CAO NHẤT")

matrix_file = st.file_uploader("📂 Upload ma trận Excel", type=["xlsx"])

if matrix_file:
    df = read_matrix(matrix_file)
    grade = st.selectbox("Khối lớp", [1,2,3,4,5])
    subject = st.selectbox("Môn học", SUBJECTS_BY_GRADE[grade])

    if st.button("🚀 AI tạo đề hoàn chỉnh"):
        with st.spinner("AI đang làm việc ở mức cao nhất..."):
            prompt = build_prompt(df, grade, subject)
            exam = ai_generate(prompt)
            word = export_word(exam, grade, subject)

            st.download_button(
                "⬇️ Tải đề Word hoàn chỉnh",
                word,
                file_name=f"De_AI_TT27_{subject}_K{grade}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
