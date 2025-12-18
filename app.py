import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
import io

# ==================================================
# CẤU HÌNH
# ==================================================
st.set_page_config(layout="wide", page_title="RA ĐỀ CTGDPT 2018")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ==================================================
# CURRICULUM_DB – ĐỦ 5 KHỐI – GẮN YCCĐ – ĐÚNG BỘ SÁCH
# ==================================================

CURRICULUM_DB = {
    "Lớp 1": {
        "Toán": {
            "Bộ sách": "Kết nối tri thức",
            "Học kỳ I": {
                "Các số đến 10": {
                    "Số 1, 2, 3": [
                        "Nhận biết và đọc, viết được các số 1, 2, 3.",
                        "So sánh được các số trong phạm vi 3."
                    ],
                    "Số 4, 5": [
                        "Nhận biết và đọc, viết được các số 4, 5.",
                        "Thực hiện được so sánh các số trong phạm vi 5."
                    ]
                }
            },
            "Học kỳ II": {
                "Các số đến 100": {
                    "Các số đến 20": [
                        "Nhận biết và đọc, viết được các số đến 20.",
                        "So sánh được các số trong phạm vi 20."
                    ]
                }
            }
        },
        "Tin học": {
            "Bộ sách": "Cùng khám phá",
            "Học kỳ I": {
                "Làm quen máy tính": {
                    "Thông tin quanh ta": [
                        "Nhận biết được thông tin trong đời sống hằng ngày.",
                        "Nêu được ví dụ về thông tin."
                    ]
                }
            },
            "Học kỳ II": {
                "Thực hành": {
                    "Làm quen chuột": [
                        "Thực hiện được thao tác cầm và di chuyển chuột.",
                        "Nháy chuột đúng cách."
                    ]
                }
            }
        }
    },

    "Lớp 2": {
        "Toán": {
            "Bộ sách": "Kết nối tri thức",
            "Học kỳ I": {
                "Các số đến 100": {
                    "So sánh số": [
                        "So sánh được các số trong phạm vi 100.",
                        "Sắp xếp được các số theo thứ tự."
                    ]
                }
            }
        },
        "Tin học": {
            "Bộ sách": "Cùng khám phá",
            "Học kỳ I": {
                "Máy tính và em": {
                    "Các bộ phận máy tính": [
                        "Nhận biết được các bộ phận chính của máy tính.",
                        "Nêu được chức năng cơ bản của từng bộ phận."
                    ]
                }
            }
        }
    },

    "Lớp 3": {
        "Tin học": {
            "Bộ sách": "Cùng khám phá",
            "Học kỳ I": {
                "Máy tính và em": {
                    "Thông tin và quyết định": [
                        "Nhận biết được vai trò của thông tin trong quyết định.",
                        "Lấy được ví dụ minh họa."
                    ]
                }
            }
        }
    },

    "Lớp 4": {
        "Tin học": {
            "Bộ sách": "Cùng khám phá",
            "Học kỳ I": {
                "Soạn thảo văn bản": {
                    "Soạn thảo văn bản đơn giản": [
                        "Soạn thảo được đoạn văn bản ngắn.",
                        "Định dạng được chữ trong văn bản."
                    ]
                }
            }
        }
    },

    "Lớp 5": {
        "Tin học": {
            "Bộ sách": "Cùng khám phá",
            "Học kỳ I": {
                "Lập trình": {
                    "Lệnh lặp": [
                        "Nhận biết được lệnh lặp.",
                        "Sử dụng được lệnh lặp trong chương trình đơn giản."
                    ]
                }
            }
        }
    }
}

# ==================================================
# AI FUNCTIONS – BỊ KHÓA THEO YCCĐ
# ==================================================

def generate_question_from_yccd(yccd, qtype, level, score):
    prompt = f"""
Bạn là giáo viên tiểu học dạy theo CTGDPT 2018, TT27.

CHỈ được ra câu hỏi đo đúng các YCCĐ sau:
{chr(10).join(yccd)}

Ràng buộc:
- Dạng câu hỏi: {qtype}
- Mức độ: {level}
- Điểm: {score}
- Không dùng từ "em"

PHẢI TRẢ VỀ:
CÂU HỎI:
...
ĐÁP ÁN:
...
"""
    model = genai.GenerativeModel("gemini-1.5-pro")
    return model.generate_content(prompt).text.strip()

# ==================================================
# SESSION
# ==================================================
st.session_state.setdefault("questions", [])
st.session_state.setdefault("question", "")

# ==================================================
# SIDEBAR – CHỌN ĐÚNG CHƯƠNG TRÌNH
# ==================================================
with st.sidebar:
    grade = st.selectbox("Lớp", CURRICULUM_DB.keys())
    subject = st.selectbox("Môn học", CURRICULUM_DB[grade].keys())
    semester = st.selectbox("Học kỳ", CURRICULUM_DB[grade][subject].keys() - {"Bộ sách"})

    topics = CURRICULUM_DB[grade][subject][semester]
    topic = st.selectbox("Chủ đề", topics.keys())

    lessons = topics[topic]
    lesson = st.selectbox("Bài học", lessons.keys())

    yccd = lessons[lesson]

# ==================================================
# MAIN
# ==================================================
st.title("HỆ THỐNG RA ĐỀ – CTGDPT 2018")

tab1, tab2 = st.tabs(["Soạn từng câu", "Đề thi"])

with tab1:
    st.write("### Yêu cầu cần đạt")
    st.write(yccd)

    qtype = st.selectbox("Dạng câu hỏi", ["Trắc nghiệm", "Tự luận", "Đúng/Sai"])
    level = st.selectbox("Mức độ", ["Biết", "Hiểu", "Vận dụng"])
    score = st.number_input("Điểm", 0.25, 10.0, 1.0, 0.25)

    if st.button("Tạo câu hỏi"):
        st.session_state.question = generate_question_from_yccd(
            yccd, qtype, level, score
        )

    st.text_area("Câu hỏi + Đáp án", st.session_state.question, height=250)

    if st.button("Thêm vào đề"):
        st.session_state.questions.append(st.session_state.question)

with tab2:
    content = ""
    for i, q in enumerate(st.session_state.questions):
        content += f"Câu {i+1}:\n{q}\n\n"
    st.text_area("Đề thi", content, height=400)
