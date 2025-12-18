import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
import io

st.set_page_config(layout="wide", page_title="RA ĐỀ CTGDPT 2018")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ==================================================
# CURRICULUM_DB – ĐẦY ĐỦ 5 KHỐI – HIỂN THỊ ĐẦY ĐỦ
# ==================================================

CURRICULUM_DB = {

# ======================= LỚP 1 =======================
"Lớp 1": {
"Toán": {
"Học kỳ I": [
{"Chủ đề": "Các số đến 10", "Bài học": [
"Số 0", "Số 1", "Số 2", "Số 3", "Số 4",
"Số 5", "Số 6", "Số 7", "Số 8", "Số 9", "Số 10",
"So sánh các số", "Cộng trong phạm vi 10", "Trừ trong phạm vi 10"
]}
],
"Học kỳ II": [
{"Chủ đề": "Các số đến 100", "Bài học": [
"Các số đến 20", "Các số đến 50", "Các số đến 100",
"So sánh các số", "Cộng trừ trong phạm vi 100"
]}
]
},
"Tiếng Việt": {
"Học kỳ I": [
{"Chủ đề": "Làm quen chữ cái", "Bài học": [
"a, b, c", "d, đ, e, ê", "g, h, i, k",
"l, m, n, o", "ô, ơ, p, q", "r, s, t",
"u, ư, v, x", "y"
]}
],
"Học kỳ II": [
{"Chủ đề": "Gia đình – Trường học", "Bài học": [
"Gia đình em", "Trường em", "Bạn bè", "Thầy cô"
]}
]
},
"Tin học": {
"Học kỳ I": [
{"Chủ đề": "Làm quen máy tính", "Bài học": [
"Thông tin quanh ta", "Máy tính là gì", "Sử dụng máy tính an toàn"
]}
],
"Học kỳ II": [
{"Chủ đề": "Thực hành", "Bài học": [
"Làm quen chuột", "Làm quen bàn phím"
]}
]
}
},

# ======================= LỚP 2 =======================
"Lớp 2": {
"Toán": {
"Học kỳ I": [
{"Chủ đề": "Các số đến 100", "Bài học": [
"Ôn tập số đến 100", "So sánh số",
"Cộng trừ không nhớ", "Cộng trừ có nhớ"
]}
],
"Học kỳ II": [
{"Chủ đề": "Phép nhân – chia", "Bài học": [
"Phép nhân", "Phép chia", "Bảng nhân 2,3,4,5"
]}
]
},
"Tiếng Việt": {
"Học kỳ I": [
{"Chủ đề": "Em lớn lên từng ngày", "Bài học": [
"Tôi là học sinh lớp 2", "Người bạn mới", "Niềm vui học tập"
]}
],
"Học kỳ II": [
{"Chủ đề": "Vẻ đẹp quanh em", "Bài học": [
"Cây cối", "Dòng sông", "Cánh đồng"
]}
]
},
"Tin học": {
"Học kỳ I": [
{"Chủ đề": "Máy tính và em", "Bài học": [
"Thông tin và máy tính", "Các bộ phận máy tính"
]}
],
"Học kỳ II": [
{"Chủ đề": "Thực hành", "Bài học": [
"Luyện gõ phím", "Soạn thảo đơn giản"
]}
]
}
},

# ======================= LỚP 3 =======================
"Lớp 3": {
"Toán": {
"Học kỳ I": [
{"Chủ đề": "Ôn tập và bổ sung", "Bài học": [
"Số đến 1000", "So sánh số", "Cộng trừ trong phạm vi 1000",
"Bài toán có lời văn"
]}
],
"Học kỳ II": [
{"Chủ đề": "Đo lường", "Bài học": [
"Mi-li-mét", "Xăng-ti-mét", "Mét", "Chu vi"
]}
]
},
"Tin học": {
"Học kỳ I": [
{"Chủ đề": "Máy tính và em", "Bài học": [
"Thông tin và quyết định", "Các dạng thông tin", "Sử dụng máy tính an toàn"
]}
],
"Học kỳ II": [
{"Chủ đề": "Bài trình chiếu", "Bài học": [
"Tạo trang chiếu", "Chèn hình ảnh", "Trình chiếu"
]}
]
}
},

# ======================= LỚP 4 =======================
"Lớp 4": {
"Toán": {
"Học kỳ I": [
{"Chủ đề": "Số và phép tính", "Bài học": [
"Số đến 100 000", "So sánh số", "Cộng trừ số lớn"
]}
],
"Học kỳ II": [
{"Chủ đề": "Phân số", "Bài học": [
"Khái niệm phân số", "So sánh phân số", "Cộng trừ phân số"
]}
]
},
"Tin học": {
"Học kỳ I": [
{"Chủ đề": "Soạn thảo", "Bài học": [
"Soạn thảo văn bản", "Định dạng văn bản"
]}
],
"Học kỳ II": [
{"Chủ đề": "Internet", "Bài học": [
"Tìm kiếm thông tin", "An toàn trên mạng"
]}
]
}
},

# ======================= LỚP 5 =======================
"Lớp 5": {
"Toán": {
"Học kỳ I": [
{"Chủ đề": "Số thập phân", "Bài học": [
"Khái niệm số thập phân", "So sánh số thập phân"
]}
],
"Học kỳ II": [
{"Chủ đề": "Hình học", "Bài học": [
"Hình tam giác", "Hình thang", "Diện tích"
]}
]
},
"Tin học": {
"Học kỳ I": [
{"Chủ đề": "Lập trình", "Bài học": [
"Lệnh tuần tự", "Lệnh lặp"
]}
],
"Học kỳ II": [
{"Chủ đề": "Ứng dụng CNTT", "Bài học": [
"Thiết kế trình chiếu", "Dự án nhỏ"
]}
]
}
}

# ==================================================
# AI FUNCTIONS
# ==================================================

def generate_yccd(grade, subject, topic, lesson):
    prompt = f"""
Viết YÊU CẦU CẦN ĐẠT CTGDPT 2018 cho:
Lớp: {grade}
Môn: {subject}
Chủ đề: {topic}
Bài học: {lesson}

- Gạch đầu dòng
- Không dùng từ "em"
- Phù hợp Thông tư 27
"""
    model = genai.GenerativeModel("gemini-1.5-pro")
    return model.generate_content(prompt).text.strip()

def generate_question(yccd, qtype, level):
    prompt = f"""
Soạn 1 câu hỏi tiểu học.
YCCĐ:
{yccd}
Dạng: {qtype}
Mức độ: {level}
Có đáp án.
"""
    model = genai.GenerativeModel("gemini-1.5-pro")
    return model.generate_content(prompt).text.strip()

# ==================================================
# SESSION
# ==================================================
st.session_state.setdefault("questions", [])
st.session_state.setdefault("yccd", "")
st.session_state.setdefault("question", "")

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    grade = st.selectbox("Lớp", CURRICULUM_DB.keys())
    subject = st.selectbox("Môn học", CURRICULUM_DB[grade].keys())
    semester = st.selectbox("Học kỳ", CURRICULUM_DB[grade][subject].keys())
    topics = CURRICULUM_DB[grade][subject][semester]
    topic = st.selectbox("Chủ đề", [t["Chủ đề"] for t in topics])
    lessons = next(t["Bài học"] for t in topics if t["Chủ đề"] == topic)
    lesson = st.selectbox("Bài học", lessons)

# ==================================================
# MAIN TABS
# ==================================================
st.title("HỆ THỐNG RA ĐỀ CTGDPT 2018")
tab1, tab2, tab3 = st.tabs(["Soạn câu hỏi", "Ma trận", "Đề thi"])

with tab1:
    if st.button("Sinh YCCĐ"):
        st.session_state.yccd = generate_yccd(grade, subject, topic, lesson)

    yccd = st.text_area("YCCĐ", st.session_state.yccd, height=120)
    qtype = st.selectbox("Dạng", ["Trắc nghiệm", "Tự luận", "Đúng/Sai"])
    level = st.selectbox("Mức độ", ["Biết", "Hiểu", "Vận dụng"])
    score = st.number_input("Điểm", 0.25, 10.0, 1.0, 0.25)

    if st.button("Tạo câu hỏi"):
        st.session_state.question = generate_question(yccd, qtype, level)

    question = st.text_area("Câu hỏi", st.session_state.question, height=200)

    if st.button("Thêm vào đề"):
        st.session_state.questions.append({
            "Bài": lesson,
            "YCCĐ": yccd,
            "Dạng": qtype,
            "Mức độ": level,
            "Điểm": score,
            "Nội dung": question
        })

with tab2:
    st.table(st.session_state.questions)

with tab3:
    content = ""
    for i, q in enumerate(st.session_state.questions):
        content += f"Câu {i+1}: {q['Nội dung']}\n\n"
    st.text_area("Đề thi", content, height=400)
