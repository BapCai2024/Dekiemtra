import streamlit as st
import pandas as pd
from io import BytesIO
import time
import base64

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Trợ lý Ra Đề Thi Tiểu Học (TT27)", layout="wide", page_icon="🏫")

# --- DỮ LIỆU MÔN HỌC ---
DATA_MON_HOC = {
    "Lớp 1": ["Tiếng Việt", "Toán"],
    "Lớp 2": ["Tiếng Việt", "Toán"],
    "Lớp 3": ["Tiếng Việt", "Toán", "Tin học", "Công nghệ"], 
    "Lớp 4": ["Tiếng Việt", "Toán", "Lịch sử và Địa lí", "Khoa học", "Tin học", "Công nghệ"],
    "Lớp 5": ["Tiếng Việt", "Toán", "Lịch sử và Địa lí", "Khoa học", "Tin học", "Công nghệ"]
}

# --- DỮ LIỆU CHƯƠNG TRÌNH HỌC (RÚT GỌN ĐỂ DEMO, BẠN CÓ THỂ GIỮ NGUYÊN DATA CỦA BẠN) ---
# Lưu ý: Cấu trúc data của bạn là List chứa Dict
CURRICULUM_DATA = {
    "Lớp 1": {
        "Tiếng Việt": [
            {"Chủ đề": "Làm quen với tiếng việt", "Bài học": "Bài 1A: a, b..."},
            {"Chủ đề": "Học chữ ghi vần", "Bài học": "Bài 5A: ch, tr..."}
        ],
        "Toán": [
            {"Chủ đề": "Các số từ 0 đến 10", "Bài học": "Các số 0, 1, 2..."}
        ]
    }
    # (Bạn có thể dán lại toàn bộ dữ liệu CURRICULUM_DATA đầy đủ của bạn vào đây)
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
                text += page.extract_text() or ""
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

# --- HÀM TẠO NỘI DUNG MA TRẬN ---
def generate_matrix_content(grade, subject):
    matrix_header = (
        "MA TRẬN ĐỀ KIỂM TRA CUỐI HỌC KÌ\n"
        "+ Mức độ đề: 50% Nhận biết; 40% Thông hiểu; 10% Vận dụng\n"
        "TT | Chương/Chủ đề | Nội dung/đơn vị kiến thức | Số tiết | Tỉ lệ | Nhận biết | Thông hiểu | Vận dụng\n"
        "---|---|---|---|---|---|---|---\n"
    )
    
    # Lấy dữ liệu an toàn
    try:
        data_list = CURRICULUM_DATA.get(grade, {}).get(subject, [])
    except Exception:
        return "Lỗi cấu trúc dữ liệu chương trình học."

    if not data_list:
        return "Không tìm thấy dữ liệu chương trình học cho khối lớp này (Hoặc chưa cập nhật DB)."

    matrix_rows = []
    tt_counter = 1
    
    for theme_data in data_list:
        theme = theme_data.get("Chủ đề", "")
        # Phân tách bài học bằng dấu chấm phẩy
        lessons_str = theme_data.get("Bài học", "")
        lessons = [l.strip() for l in lessons_str.split(';') if l.strip()]
        
        for lesson in lessons:
            so_tiet = 1
            ti_le = '2-5%' 
            nb = 'X' if tt_counter % 3 != 0 else ''
            th = 'X' if tt_counter % 3 == 0 and tt_counter % 5 != 0 else ''
            vd = 'X' if tt_counter % 5 == 0 else ''

            row = f"{tt_counter} | {theme} | {lesson} | {so_tiet} | {ti_le} | {nb} | {th} | {vd}"
            matrix_rows.append(row)
            tt_counter += 1
            
    return matrix_header + "\n".join(matrix_rows)

# --- HÀM CHUYỂN ĐỔI SANG DOCX ---
def to_docx_bytes(content):
    docx_simulation = f"\n{content}\n\n[Dữ liệu này được mô phỏng DOCX. Vui lòng dán vào MS Word để định dạng.]"
    buffer = BytesIO()
    buffer.write(docx_simulation.encode('utf-8'))
    buffer.seek(0)
    return buffer.getvalue()

# --- HÀM GIẢ LẬP GỌI AI ---
def generate_document_ai(api_key, grade, subject, matrix_content, output_type):
    if not api_key:
        return "⚠️ Vui lòng nhập API Key để bắt đầu."

    time.sleep(1.5) # Giả lập thời gian chờ
    
    if output_type == "Ma trận/Đặc tả (Theo mẫu PDF)":
        # Nếu người dùng upload file, ưu tiên dùng nội dung file
        if matrix_content and len(matrix_content) > 50:
             return f"Đã phân tích file tải lên:\n\n{matrix_content[:500]}...\n\n(AI đang chuyển đổi sang dạng bảng...)"
        return generate_matrix_content(grade, subject)

    # Logic tạo đề thi giả định (Sửa lại cách lấy data để không bị lỗi)
    try:
        # Lấy phần tử đầu tiên của list làm mẫu
        subject_data = CURRICULUM_DATA.get(grade, {}).get(subject, [{}])[0]
        demo_theme = subject_data.get("Chủ đề", "Chủ đề chung")
        demo_lesson = subject_data.get("Bài học", "Kiến thức tổng hợp")[:50] + "..."
    except:
        demo_theme = "Tổng hợp"
        demo_lesson = "Kiến thức SGK"
    
    return f"""
# ĐỀ KIỂM TRA ĐỊNH KỲ CUỐI KỲ I
**Môn: {subject} - {grade}**
**Chủ đề trọng tâm: {demo_theme}**
*Thời gian làm bài: 40 phút*
---
### A. PHẦN TRẮC NGHIỆM (4 điểm)
*Khoanh tròn vào chữ cái đặt trước câu trả lời đúng*

**Câu 1 (Mức 1 - Nhận biết):** Nội dung về {demo_theme}...
A. Đáp án 1
B. Đáp án 2
C. Đáp án 3

**Câu 2 (Mức 2 - Thông hiểu):** Dựa trên kiến thức bài {demo_lesson}...

### B. PHẦN TỰ LUẬN (6 điểm)
**Câu 3 (Mức 2):** Giải bài toán...
**Câu 4 (Mức 3 - Vận dụng):** (Nội dung vận dụng cao)
---
*Ghi chú: Đề thi này được tạo tự động bởi AI (Mô phỏng).*
"""

# --- GIAO DIỆN CHÍNH ---

# 1. SIDEBAR
with st.sidebar:
    st.header("🔑 Cấu hình AI")
    api_key = st.text_input("Nhập API Key (OpenAI/Gemini):", type="password")
    st.markdown("---")
    
    output_type = st.radio(
        "Chọn loại tài liệu cần tạo:",
        ("Đề thi (Theo Ma trận)", "Ma trận/Đặc tả (Theo mẫu PDF)")
    )
    st.markdown("---")
    
    with st.expander("📚 Hướng dẫn lấy API Key"):
        st.markdown("""
        1. **OpenAI:** [platform.openai.com](https://platform.openai.com)
        2. **Google Gemini:** [aistudio.google.com](https://aistudio.google.com)
        """)
    st.info("Hệ thống hỗ trợ tạo đề theo 3 mức độ nhận thức của TT27.")

# 2. HEADER & CHỌN LỚP/MÔN
st.title("🏫 Hệ Thống Ra Đề Thi Tiểu Học (TT27)")
st.markdown("---")

col_grade_select = st.container()
with col_grade_select:
    st.subheader("1. Chọn Khối Lớp & Môn Học")
    c1, c2 = st.columns(2) # Đã sửa lỗi [7]
    with c1:
        selected_grade = st.selectbox("Chọn Khối Lớp:", list(DATA_MON_HOC.keys()))
    with c2:
        subjects = DATA_MON_HOC[selected_grade]
        selected_subject = st.selectbox("Chọn Môn Học:", subjects)

st.markdown("---")

# 3. KHUNG LÀM VIỆC CHÍNH
col_left, col_right = st.columns([1, 1], gap="large") # Đã sửa lỗi chia cột

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
    btn_generate = st.button("✨ TẠO TÀI LIỆU BẰNG AI", type="primary", use_container_width=True)

# --- CỘT TRÁI: HIỂN THỊ KẾT QUẢ ---
with col_left:
    st.subheader(f"4. Nội dung {output_type} do AI tạo ra")

    if "exam_content" not in st.session_state:
        st.session_state.exam_content = ""

    if btn_generate:
        # Nếu chọn tạo Đề thi mà chưa có file thì cảnh báo (trừ khi dùng dữ liệu có sẵn)
        if output_type == "Đề thi (Theo Ma trận)" and not uploaded_file and not matrix_content:
             # Nếu không có file upload, hệ thống sẽ dùng dữ liệu CURRICULUM_DATA làm mặc định
             st.info("Đang sử dụng dữ liệu chương trình học mặc định để tạo đề...")
        
        with st.spinner(f"AI đang xử lý..."):
            result = generate_document_ai(api_key, selected_grade, selected_subject, matrix_content, output_type)
            st.session_state.exam_content = result

    text_area = st.text_area(
        f"Nội dung (Có thể chỉnh sửa):",
        value=st.session_state.exam_content,
        height=500
    )

    if st.session_state.exam_content:
        c_download_txt, c_download_docx = st.columns(2)
        
        with c_download_txt:
            st.download_button(
                label="📥 Xuất file (.txt)",
                data=st.session_state.exam_content,
                file_name=f"KetQua_{selected_subject}.txt",
                mime="text/plain",
                use_container_width=True
            )

        with c_download_docx:
            docx_data = to_docx_bytes(st.session_state.exam_content)
            st.download_button(
                label="📝 Xuất file (.docx)",
                data=docx_data,
                file_name=f"KetQua_{selected_subject}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
