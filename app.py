import streamlit as st
import pandas as pd
from io import BytesIO
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Ra Đề Thi Tiểu Học (TT27)", layout="wide", page_icon="🏫")

# --- DỮ LIỆU MÔN HỌC THEO THÔNG TƯ 27 ---
# Thông tư 27 quy định đánh giá định kỳ các môn khác nhau tùy khối lớp
DATA_MON_HOC = {
    "Lớp 1": ["Tiếng Việt", "Toán"],
    "Lớp 2": ["Tiếng Việt", "Toán"],
    "Lớp 3": ["Tiếng Việt", "Toán", "Tiếng Anh", "Tin học và Công nghệ"],
    "Lớp 4": ["Tiếng Việt", "Toán", "Tiếng Anh", "Lịch sử và Địa lí", "Khoa học", "Tin học", "Công nghệ"],
    "Lớp 5": ["Tiếng Việt", "Toán", "Tiếng Anh", "Lịch sử và Địa lí", "Khoa học", "Tin học", "Công nghệ"]
}

# --- HÀM XỬ LÝ ĐỌC FILE ---
def read_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        elif uploaded_file.name.endswith('.docx') or uploaded_file.name.endswith('.doc'):
            import docx
            doc = docx.Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file)
            return df.to_string()
        else:
            return "Định dạng file không hỗ trợ đọc nội dung trực tiếp."
    except Exception as e:
        return f"Lỗi khi đọc file: {str(e)}"

# --- HÀM GIẢ LẬP GỌI AI (MOCKUP) ---
# Trong thực tế, bạn sẽ thay thế hàm này bằng lệnh gọi OpenAI/Gemini API
def generate_exam_ai(api_key, grade, subject, matrix_content):
    if not api_key:
        return "⚠️ Vui lòng nhập API Key để bắt đầu."
    
    # Giả lập độ trễ khi AI suy nghĩ
    time.sleep(2) 
    
    # Prompt giả định gửi cho AI
    prompt = f"""
    Đóng vai trò là giáo viên tiểu học có kinh nghiệm.
    Hãy ra đề thi môn {subject} cho học sinh {grade} theo chuẩn Thông tư 27.
    Dựa vào ma trận/đặc tả sau:
    {matrix_content[:500]}... (nội dung file tải lên)
    
    Yêu cầu:
    1. Đảm bảo 3 mức độ nhận thức (Mức 1, Mức 2, Mức 3).
    2. Cấu trúc đề thi rõ ràng, có trắc nghiệm và tự luận.
    3. Ngôn ngữ phù hợp với lứa tuổi tiểu học.
    """
    
    # Nội dung trả về mẫu (Demo)
    return f"""
# ĐỀ KIỂM TRA ĐỊNH KỲ CUỐI KỲ I
**Môn: {subject} - {grade}**
*Thời gian làm bài: 40 phút*
---

### A. PHẦN TRẮC NGHIỆM (4 điểm)
*Khoanh tròn vào chữ cái đặt trước câu trả lời đúng*

**Câu 1 (Mức 1):** (Nội dung được tạo dựa trên ma trận file upload)...
A. Đáp án 1
B. Đáp án 2
C. Đáp án 3

**Câu 2 (Mức 2):** ...

### B. PHẦN TỰ LUẬN (6 điểm)

**Câu 3 (Mức 2):** Đặt tính rồi tính:
a) 123 + 456
b) 789 - 123

**Câu 4 (Mức 3):** Giải bài toán có lời văn:
(Nội dung bài toán vận dụng cao dựa trên đặc tả...)

---
*Ghi chú: Đề thi này được tạo tự động bởi AI dựa trên hướng dẫn Thông tư 27.*
    """

# --- GIAO DIỆN CHÍNH ---

# 1. SIDEBAR: HƯỚNG DẪN API
with st.sidebar:
    st.header("🔑 Cấu hình AI")
    api_key = st.text_input("Nhập API Key (OpenAI/Gemini):", type="password")
    
    st.markdown("---")
    with st.expander("📚 Hướng dẫn lấy API Key"):
        st.markdown("""
        **Để AI hoạt động, bạn cần có API Key:**
        1. **OpenAI (ChatGPT):**
           - Truy cập [platform.openai.com](https://platform.openai.com).
           - Đăng ký/Đăng nhập -> Chọn "API Keys".
           - Tạo key mới và copy vào ô bên trên.
        2. **Google Gemini:**
           - Truy cập [aistudio.google.com](https://aistudio.google.com).
           - Chọn "Get API key".
        
        *Lưu ý: API key của bạn được bảo mật và không lưu trên hệ thống.*
        """)
    st.info("Hệ thống hỗ trợ tạo đề theo 3 mức độ nhận thức của TT27.")

# 2. HEADER & CHỌN LỚP/MÔN
st.title("🏫 Hệ Thống Ra Đề Thi Tiểu Học (TT27)")
st.markdown("---")

# Tạo hàng chọn Lớp
col_grade_select = st.container()
with col_grade_select:
    st.subheader("1. Chọn Khối Lớp & Môn Học")
    c1, c2 = st.columns(2)
    
    with c1:
        selected_grade = st.selectbox("Chọn Khối Lớp:", list(DATA_MON_HOC.keys()))
    
    with c2:
        # Môn học thay đổi dựa trên Lớp đã chọn
        subjects = DATA_MON_HOC[selected_grade]
        selected_subject = st.selectbox("Chọn Môn Học:", subjects)

st.markdown("---")

# 3. KHUNG LÀM VIỆC CHÍNH (2 CỘT)
col_left, col_right = st.columns([1, 1], gap="large")

# --- CỘT PHẢI: UPLOAD & CẤU HÌNH ---
with col_right:
    st.subheader("2. Dữ liệu đầu vào (Ma trận/Đặc tả)")
    st.write("Tải lên file Ma trận đề thi, Bảng đặc tả hoặc nội dung ôn tập.")
    
    uploaded_file = st.file_uploader(
        "Upload file (PDF, DOCX, EXCEL, DOC)", 
        type=['pdf', 'docx', 'doc', 'xlsx', 'xls']
    )
    
    matrix_content = ""
    if uploaded_file is not None:
        with st.spinner("Đang đọc nội dung file..."):
            matrix_content = read_uploaded_file(uploaded_file)
            st.success(f"Đã đọc xong file: {uploaded_file.name}")
            with st.expander("Xem nội dung file đã đọc"):
                st.text(matrix_content[:500] + "...")
    
    st.markdown("### 3. Tác vụ")
    btn_generate = st.button("✨ TẠO ĐỀ THI BẰNG AI", type="primary", use_container_width=True)

# --- CỘT TRÁI: HIỂN THỊ ĐỀ THI ---
with col_left:
    st.subheader("4. Đề thi do AI tạo ra")
    
    # Sử dụng session_state để lưu đề thi khi render lại trang
    if "exam_content" not in st.session_state:
        st.session_state.exam_content = ""

    if btn_generate:
        if not uploaded_file and not matrix_content:
            st.warning("Vui lòng upload ma trận hoặc đặc tả trước khi tạo đề.")
        else:
            with st.spinner("AI đang phân tích ma trận và soạn đề theo TT27..."):
                # Gọi hàm tạo đề
                result = generate_exam_ai(api_key, selected_grade, selected_subject, matrix_content)
                st.session_state.exam_content = result

    # Khu vực hiển thị nội dung
    text_area = st.text_area(
        "Nội dung đề thi (Có thể chỉnh sửa):", 
        value=st.session_state.exam_content, 
        height=500
    )

    # Nút xuất file
    if st.session_state.exam_content:
        st.download_button(
            label="📥 Xuất file Đề thi (.txt)",
            data=st.session_state.exam_content,
            file_name=f"De_thi_{selected_subject}_{selected_grade}.txt",
            mime="text/plain"
        )
        st.caption("Sau khi tải về, bạn có thể copy nội dung vào Word để căn chỉnh font chữ.")
