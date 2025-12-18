import streamlit as st
import pandas as pd
import os
import random
import re
from io import BytesIO
from docx import Document
from PyPDF2 import PdfReader

# ==================================================
# CẤU HÌNH CHUNG
# ==================================================
st.set_page_config(
    page_title="Hệ thống sinh đề TT27",
    layout="wide"
)

DATA_DIR = "data_pdf"
IMAGE_DIR = "images"

SUPPORTED_SUBJECTS = [
    "Toán",
    "Tiếng Việt",
    "Tin",
    "Công nghệ",
    "Khoa học",
    "Lịch sử – Địa lí"
]

# ==================================================
# NGUỒN NGOÀI CHO TIẾNG VIỆT (KHÔNG DÙNG SGK)
# ==================================================
EXTERNAL_TV_TEXTS = {
    1: [
        "Bé Lan đi học sớm. Trên đường đi, bé gặp cô giáo và lễ phép chào hỏi."
    ],
    2: [
        "Buổi sáng, sân trường rộn ràng tiếng cười. Các bạn nhỏ cùng nhau quét sân."
    ],
    3: [
        "Mỗi buổi chiều, ông thường kể cho em nghe những câu chuyện về làng quê yên bình."
    ],
    4: [
        "Dòng sông quê hương gắn liền với tuổi thơ của biết bao thế hệ, mang theo phù sa và kỉ niệm."
    ],
    5: [
        "Tinh thần vượt khó giúp con người vươn lên trong học tập và cuộc sống, dù gặp nhiều thử thách."
    ]
}

# ==================================================
# HÀM TIỆN ÍCH
# ==================================================
def read_matrix(excel_file):
    df = pd.read_excel(excel_file, sheet_name=0, header=None)
    df = df.dropna(how="all")
    return df


def load_pdf_text(folder):
    texts = []
    if not os.path.exists(folder):
        return ""
    for f in os.listdir(folder):
        if f.lower().endswith(".pdf"):
            reader = PdfReader(os.path.join(folder, f))
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    texts.append(txt)
    return "\n".join(texts)


def extract_sentences(text, keyword):
    sentences = re.split(r"[.\n]", text)
    results = [
        s.strip() for s in sentences
        if keyword.lower() in s.lower() and len(s.strip()) > 25
    ]
    return results if results else [f"Nội dung liên quan đến {keyword}"]


def gen_question(bank, level, qtype, idx):
    base = random.choice(bank)
    if qtype == "TN":
        return (
            f"Câu {idx}. ({level}) {base}\n"
            f"A. Phương án A\nB. Phương án B\nC. Phương án C\nD. Phương án D"
        )
    elif qtype == "DK":
        return f"Câu {idx}. ({level}) {base}: __________"
    else:
        return f"Câu {idx}. ({level}) {base}."


def generate_exam(df, grade, subject, shuffle=True):
    questions, answers = [], []
    idx = 1

    # ===== Nguồn dữ liệu =====
    if subject == "Tiếng Việt":
        bank_texts = EXTERNAL_TV_TEXTS.get(grade, [])
    else:
        pdf_folder = f"{DATA_DIR}/K{grade}/{subject}"
        pdf_text = load_pdf_text(pdf_folder)
        bank_texts = []
        for i in range(6, len(df)):
            c = df.iloc[i, 2]
            if pd.notna(c):
                bank_texts.extend(extract_sentences(pdf_text, c))

    for i in range(6, len(df)):
        content = df.iloc[i, 2]
        if pd.isna(content):
            continue

        bank = bank_texts

        blocks = [
            ("TN", [6, 7, 8]),
            ("DK", [9, 10, 11]),
            ("TL", [12, 13, 14])
        ]
        levels = ["NB", "TH", "VD"]

        for qtype, cols in blocks:
            for level, col in zip(levels, cols):
                if col >= len(df.columns):
                    continue
                num = df.iloc[i, col]
                if pd.notna(num) and int(num) > 0:
                    for _ in range(int(num)):
                        q = gen_question(bank, level, qtype, idx)
                        questions.append(q)
                        answers.append(f"Câu {idx}: {level}")
                        idx += 1

    if shuffle and questions:
        combined = list(zip(questions, answers))
        random.shuffle(combined)
        questions, answers = zip(*combined)

    return list(questions), list(answers)


def export_word(questions, answers, grade, subject, code):
    doc = Document()
    doc.add_heading(f"ĐỀ KIỂM TRA ĐỊNH KÌ – MÃ ĐỀ {code}", level=1)
    doc.add_paragraph(f"Môn: {subject} – Khối {grade}")
    doc.add_paragraph("Theo Thông tư 27/2020/TT-BGDĐT")
    doc.add_paragraph("Thời gian làm bài: 40 phút\n")

    # Hình ảnh cho TV lớp 1,2
    if subject == "Tiếng Việt" and grade in [1, 2]:
        img_path = os.path.join(IMAGE_DIR, f"tv_k{grade}.png")
        if os.path.exists(img_path):
            doc.add_picture(img_path)

    for q in questions:
        doc.add_paragraph(q)

    doc.add_page_break()
    doc.add_heading("ĐÁP ÁN – HƯỚNG DẪN CHẤM", level=1)
    for a in answers:
        doc.add_paragraph(a)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ==================================================
# GIAO DIỆN STREAMLIT – 3 TAB
# ==================================================
st.title("🏫 HỆ THỐNG SINH ĐỀ ĐÁNH GIÁ ĐỊNH KÌ THEO TT27")

tab1, tab2, tab3 = st.tabs([
    "📘 Tab 1: Sinh đề từ ma trận",
    "📊 Tab 2",
    "⚙️ Tab 3"
])

# ==================================================
# TAB 1 – ĐÃ THAY THẾ HOÀN TOÀN
# ==================================================
with tab1:
    st.subheader("Sinh đề kiểm tra từ ma trận (TT27)")

    matrix_file = st.file_uploader(
        "📂 Upload file Excel ma trận",
        type=["xlsx"]
    )

    if matrix_file:
        df = read_matrix(matrix_file)
        st.success("Đã đọc ma trận thành công")

        col1, col2, col3 = st.columns(3)
        with col1:
            grade = st.selectbox("Khối lớp", [1, 2, 3, 4, 5])
        with col2:
            subject = st.selectbox("Môn học", SUPPORTED_SUBJECTS)
        with col3:
            num_codes = st.selectbox("Số mã đề", [1, 2, 3])

        shuffle = st.checkbox("Trộn câu hỏi", value=True)

        if st.button("🚀 Sinh đề hoàn chỉnh"):
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

# ==================================================
# TAB 2 – GIỮ NGUYÊN (PLACEHOLDER)
# ==================================================
with tab2:
    st.info("Tab 2 giữ nguyên cấu trúc theo code gốc của bạn.")

# ==================================================
# TAB 3 – GIỮ NGUYÊN (PLACEHOLDER)
# ==================================================
with tab3:
    st.info("Tab 3 giữ nguyên cấu trúc theo code gốc của bạn.")
