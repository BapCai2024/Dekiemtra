import streamlit as st
import google.generativeai as genai

import io
from docx import Document
# =========================================================
# CURRICULUM_DB – CTGDPT 2018 – TT27
# Toán, Tiếng Việt: Kết nối tri thức
# Tin học (3–5): Cùng khám phá
# =========================================================

CURRICULUM_DB = {
    # === LỚP 1 ===
    "Lớp 1": {
        "Toán": {
            "bo_sach": "Kết nối tri thức",
            "Học kỳ I": {
                "Làm quen với Toán học": {
                    "Toán học quanh ta": {
                        "yccd": [
                            "Nhận biết được toán học có trong các tình huống thực tiễn quen thuộc.",
                            "Bước đầu hình thành hứng thú học tập môn Toán."
                        ]
                    }
                },
                "Các số đến 10": {
                    "Các số 1, 2, 3": {
                        "yccd": [
                            "Nhận biết, đọc, viết được các số 1, 2, 3.",
                            "So sánh được các số trong phạm vi 3."
                        ]
                    },
                    "Các số 4, 5": {
                        "yccd": [
                            "Nhận biết, đọc, viết được các số 4, 5.",
                            "So sánh được các số trong phạm vi 5."
                        ]
                    },
                    "Các số 6 đến 10": {
                        "yccd": [
                            "Nhận biết, đọc, viết được các số từ 6 đến 10.",
                            "So sánh và sắp xếp được các số trong phạm vi 10."
                        ]
                    }
                }
            },
            "Học kỳ II": {
                "Phép cộng, phép trừ trong phạm vi 10": {
                    "Phép cộng": {
                        "yccd": [
                            "Thực hiện được phép cộng trong phạm vi 10.",
                            "Vận dụng phép cộng để giải quyết tình huống đơn giản."
                        ]
                    },
                    "Phép trừ": {
                        "yccd": [
                            "Thực hiện được phép trừ trong phạm vi 10.",
                            "Vận dụng phép trừ để giải quyết tình huống đơn giản."
                        ]
                    }
                }
            }
        },
        "Tiếng Việt": {
            "bo_sach": "Kết nối tri thức",
            "Học kỳ I": {
                "Học vần": {
                    "Âm và chữ a, ă, â": {
                        "yccd": [
                            "Nhận biết được âm và chữ a, ă, â.",
                            "Đọc, viết được các tiếng, từ có chứa a, ă, â."
                        ]
                    }
                }
            },
            "Học kỳ II": {
                "Tập đọc": {
                    "Đọc đoạn, bài ngắn": {
                        "yccd": [
                            "Đọc trôi chảy đoạn, bài ngắn phù hợp trình độ.",
                            "Hiểu nội dung chính của đoạn, bài đã đọc."
                        ]
                    }
                }
            }
        }
    },

    # === LỚP 2 ===
    "Lớp 2": {
        "Toán": {
            "bo_sach": "Kết nối tri thức",
            "Học kỳ I": {
                "Các số đến 100": {
                    "Các số trong phạm vi 100": {
                        "yccd": [
                            "Đọc, viết, so sánh được các số trong phạm vi 100.",
                            "Sắp xếp được các số theo thứ tự."
                        ]
                    }
                }
            },
            "Học kỳ II": {
                "Phép nhân, phép chia": {
                    "Phép nhân": {
                        "yccd": [
                            "Nhận biết phép nhân là phép cộng các số hạng bằng nhau.",
                            "Thực hiện được phép nhân đơn giản."
                        ]
                    },
                    "Phép chia": {
                        "yccd": [
                            "Nhận biết phép chia là phép tách thành các phần bằng nhau.",
                            "Thực hiện được phép chia đơn giản."
                        ]
                    }
                }
            }
        },
        "Tiếng Việt": {
            "bo_sach": "Kết nối tri thức",
            "Học kỳ I": {
                "Đọc": {
                    "Đọc hiểu": {
                        "yccd": [
                            "Hiểu được nội dung chính của văn bản ngắn.",
                            "Trả lời được câu hỏi đơn giản về nội dung."
                        ]
                    }
                }
            },
            "Học kỳ II": {
                "Tập làm văn": {
                    "Viết đoạn văn ngắn": {
                        "yccd": [
                            "Viết được đoạn văn ngắn theo chủ đề quen thuộc.",
                            "Diễn đạt rõ ràng, mạch lạc."
                        ]
                    }
                }
            }
        }
    },

    # === LỚP 3–4–5 ===
    # (GIỮ NGUYÊN PHẦN LỚP 3–4–5 BẠN ĐÃ COPY Ở PART A, DÁN TIẾP XUỐNG ĐÂY)
}

# =====================================================
# CẤU HÌNH – GIỮ NGUYÊN MOTIF + API NHƯ FILE GỐC
# =====================================================
st.set_page_config(page_title="Ra đề CTGDPT 2018", layout="wide")

# ⚠️ GIỮ NGUYÊN CÁCH GỌI API KEY NHƯ FILE CŨ
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-pro")

# =====================================================
# HÀM CHUNG
# =====================================================

def generate_ai(prompt: str) -> str:
    try:
        res = model.generate_content(prompt)
        return res.text.strip()
    except Exception as e:
        return f"LỖI AI: {e}"


# =====================================================
# TAB 1 – TẠO ĐỀ TỪ FILE UPLOAD (FIX TRIỆT ĐỂ)
# =====================================================

def generate_exam_from_file(file_text):
    prompt = f"""
Bạn là giáo viên tiểu học, ra đề theo CTGDPT 2018 – TT27.

Dựa CHÍNH XÁC vào nội dung sau để tạo đề kiểm tra.
KHÔNG thêm kiến thức ngoài nội dung này.

NỘI DUNG:
{file_text}

YÊU CẦU:
- Tạo đề gồm các câu hỏi phù hợp
- Có ĐÁP ÁN tương ứng cho từng câu
- Không dùng từ "em"

TRẢ VỀ THEO MẪU:
Câu 1: ...
Đáp án: ...

Câu 2: ...
Đáp án: ...
"""
    return generate_ai(prompt)


# =====================================================
# TAB 2 – SOẠN TỪNG CÂU (KHÓA BẰNG YCCĐ)
# =====================================================

def generate_question_from_yccd(yccd_list, qtype, level, score):
    yccd_text = "\n".join([f"- {y}" for y in yccd_list])

    prompt = f"""
Bạn là giáo viên tiểu học, ra đề theo CTGDPT 2018 – TT27.

CHỈ ĐƯỢC đánh giá các YCCĐ sau:
{yccd_text}

RÀNG BUỘC:
- Dạng câu hỏi: {qtype}
- Mức độ: {level}
- Điểm: {score}
- Không dùng từ "em"
- Không sinh kiến thức ngoài YCCĐ

TRẢ VỀ ĐÚNG ĐỊNH DẠNG:
CÂU HỎI:
...

ĐÁP ÁN:
...
"""
    return generate_ai(prompt)


# =====================================================
# SESSION STATE
# =====================================================

if "exam_questions" not in st.session_state:
    st.session_state.exam_questions = []


# =====================================================
# GIAO DIỆN CHÍNH
# =====================================================

st.title("HỆ THỐNG RA ĐỀ – CTGDPT 2018 (TT27)")

tab1, tab2 = st.tabs(["📄 Tạo đề từ file", "✍️ Soạn từng câu"])


# =====================================================
# TAB 1
# =====================================================
with tab1:
    st.subheader("Tạo đề từ file nội dung")

    uploaded_file = st.file_uploader(
        "Upload file nội dung (txt hoặc docx)", type=["txt", "docx"]
    )

    file_text = ""

    if uploaded_file:
        if uploaded_file.name.endswith(".txt"):
            file_text = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(".docx"):
            doc = Document(uploaded_file)
            file_text = "\n".join([p.text for p in doc.paragraphs])

        st.text_area("Nội dung file", file_text, height=250)

        if st.button("Tạo đề từ file"):
            exam = generate_exam_from_file(file_text)
            st.text_area("Đề + Đáp án", exam, height=400)


# =====================================================
# TAB 2
# =====================================================
with tab2:
    st.subheader("Soạn từng câu hỏi theo CT2018")

    col1, col2 = st.columns(2)

    with col1:
        grade = st.selectbox("Lớp", CURRICULUM_DB.keys())
        subject = st.selectbox("Môn học", CURRICULUM_DB[grade].keys())

        semesters = [
            k for k in CURRICULUM_DB[grade][subject].keys()
            if k != "bo_sach"
        ]
        semester = st.selectbox("Học kỳ", semesters)

        topics = CURRICULUM_DB[grade][subject][semester]
        topic = st.selectbox("Chủ đề", topics.keys())

        lessons = topics[topic]
        lesson = st.selectbox("Bài học", lessons.keys())

        yccd_list = lessons[lesson]["yccd"]

    with col2:
        st.markdown("**Yêu cầu cần đạt (CT2018)**")
        for y in yccd_list:
            st.write(f"- {y}")

        qtype = st.selectbox(
            "Dạng câu hỏi",
            ["Trắc nghiệm nhiều lựa chọn", "Đúng / Sai", "Tự luận"]
        )
        level = st.selectbox("Mức độ", ["Biết", "Hiểu", "Vận dụng"])
        score = st.number_input("Điểm", 0.25, 10.0, 1.0, 0.25)

        if st.button("Tạo câu hỏi"):
            question = generate_question_from_yccd(
                yccd_list, qtype, level, score
            )
            st.session_state.exam_questions.append(question)

    st.markdown("---")
    st.subheader("Câu hỏi đã tạo")

    full_exam = ""
    for i, q in enumerate(st.session_state.exam_questions, start=1):
        full_exam += f"Câu {i}:\n{q}\n\n"

    st.text_area("Nội dung đề", full_exam, height=350)

    if st.button("Xoá toàn bộ"):
        st.session_state.exam_questions = []

