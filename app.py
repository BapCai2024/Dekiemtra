import streamlit as st
import pandas as pd
import google.generativeai as genai
import re
from io import BytesIO
from docx import Document

# ================= CẤU HÌNH APP =================
st.set_page_config(
    page_title="AI Sinh đề theo ma trận TT27",
    layout="wide"
)

# ================= KIỂM TRA API KEY =================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ Chưa cấu hình GEMINI_API_KEY trong Streamlit Secrets")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# MODEL ỔN ĐỊNH NHẤT
MODEL = genai.GenerativeModel("gemini-1.5-flash")

GEN_CONFIG = genai.types.GenerationConfig(
    temperature=0.4,
    top_p=0.9,
    max_output_tokens=2048
)

# ================= TT27 – MÔN THEO KHỐI =================
SUBJECTS_BY_GRADE = {
    1: ["Toán", "Tiếng Việt"],
    2: ["Toán", "Tiếng Việt"],
    3: ["Toán", "Tiếng Việt", "Tin học", "Công nghệ"],
    4: ["Toán", "Tiếng Việt", "Tin học", "Công nghệ", "Khoa học", "Lịch sử - Địa lí"],
    5: ["Toán", "Tiếng Việt", "Tin học", "Công nghệ", "Khoa học", "Lịch sử - Địa lí"],
}

# ================= HÀM TIỆN ÍCH =================
def safe_int(v):
    if pd.isna(v):
        return 0
    nums = re.findall(r"\d+", str(v))
    return int(nums[0]) if nums else 0

def read_matrix(file):
    df = pd.read_excel(file, header=None)
    return df.dropna(how="all")

# ================= PROMPT AI (ĐÃ GIẢM & ỔN ĐỊNH) =================
def build_prompt(df, grade, subject):
    matrix_text = ""
    for i in range(len(df)):
        matrix_text += (
            f"Chủ đề {i+1}: "
            f"TN(NB {safe_int(df.iloc[i,6])}, TH {safe_int(df.iloc[i,7])}, VD {safe_int(df.iloc[i,8])}); "
            f"DK(NB {safe_int(df.iloc[i,9])}, TH {safe_int(df.iloc[i,10])}, VD {safe_int(df.iloc[i,11])}); "
            f"TL(NB {safe_int(df.iloc[i,12])}, TH {safe_int(df.iloc[i,13])}, VD {safe_int(df.iloc[i,14])})\n"
        )

    return f"""
Hãy tạo đề kiểm tra định kì tiểu học theo Thông tư 27.

Thông tin:
- Khối: {grade}
- Môn: {subject}

Yêu cầu:
- Đúng tuyệt đối số câu theo ma trận
- Ngôn ngữ phù hợp học sinh tiểu học
- Tiếng Việt: KHÔNG dùng bài đọc trong SGK
- Trắc nghiệm có 4 phương án rõ ràng
- Có đáp án và thang điểm

Ma trận:
{matrix_text}

Định dạng:
Câu 1. (TN/NB) ...
A. ...
B. ...
C. ...
D. ...

--- ĐÁP ÁN ---
Câu 1: A

--- THANG ĐIỂM ---
"""

# ================= GỌI GEMINI (CHỐNG LỖI) =================
def ai_generate(prompt):
    try:
        response = MODEL.generate_content(
            prompt,
            generation_config=GEN_CONFIG
        )

        if not response or not response.text:
            raise ValueError("AI không trả về nội dung")

        return response.text

    except Exception as e:
        st.error("❌ AI Gemini không tạo được đề")
        st.error(str(e))
        st.stop()

# ================= XUẤT WORD =================
def export_word(text, grade, subject):
    doc = Document()
    doc.add_heading("ĐỀ KIỂM TRA ĐỊNH KÌ", level=1)
    doc.add_paragraph(f"Môn: {subject} – Khối {grade}")
    doc.add_paragraph("Theo Thông tư 27/2020/TT-BGDĐT")
    doc.add_paragraph("")

    for line in text.split("\n"):
        doc.add_paragraph(line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ================= GIAO DIỆN =================
st.title("🤖 AI SINH ĐỀ THEO MA TRẬN TT27 (BẢN ỔN ĐỊNH)")

matrix_file = st.file_uploader(
    "📂 Upload file ma trận Excel",
    type=["xlsx"]
)

if matrix_file:
    df = read_matrix(matrix_file)
    st.success("✔ Đã đọc ma trận")

    col1, col2 = st.columns(2)
    with col1:
        grade = st.selectbox("Khối lớp", [1,2,3,4,5])
    with col2:
        subject = st.selectbox("Môn học", SUBJECTS_BY_GRADE[grade])

    if st.button("🚀 AI sinh đề"):
        with st.spinner("AI đang tạo đề..."):
            prompt = build_prompt(df, grade, subject)
            exam_text = ai_generate(prompt)
            word = export_word(exam_text, grade, subject)

            st.download_button(
                "⬇️ Tải đề Word",
                data=word,
                file_name=f"De_TT27_{subject}_K{grade}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
