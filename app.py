# ======================= IMPORT =======================
import streamlit as st
import pandas as pd
import random
import re
import os
from io import BytesIO
from docx import Document

# PDF
import pypdf

# ======================= CẤU HÌNH =======================
st.set_page_config(
    page_title="Hệ thống sinh đề TT27",
    layout="wide"
)

DATA_DIR = "data_pdf"
IMAGE_DIR = "images"

SUBJECTS = [
    "Toán",
    "Tiếng Việt",
    "Tin học",
    "Công nghệ",
    "Khoa học",
    "Lịch sử - Địa lí"
]

# Nguồn đọc hiểu ngoài SGK – Tiếng Việt
TV_EXTERNAL_TEXTS = {
    1: ["Bé Na dậy sớm. Bé chào bố mẹ rồi đi học cùng các bạn."],
    2: ["Buổi sáng, sân trường đông vui. Các bạn cùng nhau quét lớp."],
    3: ["Quê hương em có cánh đồng lúa xanh mát trải dài."],
    4: ["Dòng sông quê hương gắn liền với tuổi thơ của em."],
    5: ["Tinh thần vượt khó giúp con người thành công trong cuộc sống."]
}

# ======================= HÀM AN TOÀN =======================
def safe_int(value):
    try:
        if value is None or pd.isna(value):
            return 0
        if isinstance(value, str):
            nums = re.findall(r"\d+", value)
            return int(nums[0]) if nums else 0
        return int(float(value))
    except:
        return 0

# ======================= ĐỌC FILE =======================
def read_matrix(uploaded_file):
    df = pd.read_excel(uploaded_file, header=None)
    return df.dropna(how="all")

def read_pdf_folder(folder):
    texts = []
    if not os.path.exists(folder):
        return ""
    for f in os.listdir(folder):
        if f.lower().endswith(".pdf"):
            reader = pypdf.PdfReader(os.path.join(folder, f))
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    texts.append(txt)
    return "\n".join(texts)

# ======================= SINH CÂU HỎI =======================
def gen_question(bank, level, qtype, idx):
    base = random.choice(bank) if bank else "Nội dung kiến thức phù hợp"
    if qtype == "TN":
        return f"Câu {idx}. ({level}) {base}\nA. ...\nB. ...\nC. ...\nD. ..."
    if qtype == "DK":
        return f"Câu {idx}. ({level}) {base}: ________"
    return f"Câu {idx}. ({level}) {base}."

def generate_exam(df, grade, subject, shuffle=True):
    questions, answers = [], []
    idx = 1

    # Nguồn nội dung
    if subject == "Tiếng Việt":
        bank = TV_EXTERNAL_TEXTS.get(grade, [])
    else:
        pdf_text = read_pdf_folder(f"{DATA_DIR}/K{grade}/{subject}")
        sentences = re.split(r"[.\n]", pdf_text)
        bank = [s.strip() for s in sentences if len(s.strip()) > 30]

    for i in range(len(df)):
        for qtype, cols in [
            ("TN", [6, 7, 8]),
            ("DK", [9, 10, 11]),
            ("TL", [12, 13, 14])
        ]:
            for level, col in zip(["NB", "TH", "VD"], cols):
                if col >= len(df.columns):
                    continue
                num_q = safe_int(df.iloc[i, col])
                for _ in range(num_q):
                    questions.append(gen_question(bank, level, qtype, idx))
                    answers.append(f"Câu {idx}: ({level})")
                    idx += 1

    if shuffle:
        qa = list(zip(questions, answers))
        random.shuffle(qa)
        questions, answers = zip(*qa) if qa else ([], [])

    return list(questions), list(answers)

# ======================= XUẤT WORD =======================
def export_word(qs, ans, grade, subject, code):
    doc = Document()
    doc.add_heading(f"ĐỀ KIỂM TRA – MÃ {code}", level=1)
    doc.add_paragraph(f"Môn: {subject} – Khối {grade}")
    doc.add_paragraph("Theo Thông tư 27/2020/TT-BGDĐT")

    if subject == "Tiếng Việt" and grade in [1, 2]:
        img_path = os.path.join(IMAGE_DIR, f"tv_k{grade}.png")
        if os.path.exists(img_path):
            doc.add_picture(img_path)

    for q in qs:
        doc.add_paragraph(q)

    doc.add_page_break()
    doc.add_heading("ĐÁP ÁN", level=1)
    for a in ans:
        doc.add_paragraph(a)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ======================= GIAO DIỆN =======================
st.title("🏫 HỆ THỐNG SINH ĐỀ ĐÁNH GIÁ ĐỊNH KÌ (TT27)")

tab1, tab2, tab3 = st.tabs([
    "📘 Tab 1 – Sinh đề",
    "🤖 Tab 2 – Chức năng mở rộng",
    "⚙️ Tab 3 – Quản trị"
])

# ======================= TAB 1 =======================
with tab1:
    st.subheader("Sinh đề từ ma trận Excel")

    matrix_file = st.file_uploader(
        "Upload file ma trận (.xlsx)",
        type=["xlsx"]
    )

    if matrix_file:
        df = read_matrix(matrix_file)
        st.success("Đọc ma trận thành công")

        col1, col2, col3 = st.columns(3)
        with col1:
            grade = st.selectbox("Khối lớp", [1, 2, 3, 4, 5])
        with col2:
            subject = st.selectbox("Môn học", SUBJECTS)
        with col3:
            num_codes = st.selectbox("Số mã đề", [1, 2, 3])

        shuffle = st.checkbox("Trộn câu hỏi", value=True)

        if st.button("🚀 Sinh đề"):
            for i in range(num_codes):
                code = chr(65 + i)
                qs, ans = generate_exam(df, grade, subject, shuffle)
                word = export_word(qs, ans, grade, subject, code)

                st.download_button(
                    f"⬇️ Tải đề mã {code}",
                    data=word,
                    file_name=f"De_{subject}_K{grade}_Ma_{code}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# ======================= TAB 2 =======================
with tab2:
    st.subheader("Tab 2 – Chức năng mở rộng")
    st.info(
        "Tab này giữ chỗ để ghép nguyên logic cũ của bạn "
        "(AI, Gemini, xử lý nâng cao…). "
        "KHÔNG ảnh hưởng Tab 1."
    )

# ======================= TAB 3 =======================
with tab3:
    st.subheader("Tab 3 – Quản trị / Cấu hình")
    st.info(
        "Tab quản trị hệ thống. "
        "Bạn có thể dán nguyên code Tab 3 cũ vào đây."
    )
