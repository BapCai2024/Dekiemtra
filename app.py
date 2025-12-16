import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
from io import BytesIO

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="HỖ TRỢ RA ĐỀ THI TIỂU HỌC",
    page_icon="✏️",
    layout="wide"
)

# --- CSS TÙY CHỈNH MÀU SẮC ---
st.markdown("""
<style>
    /* Tiêu đề chính */
    .main-title {
        text-align: center;
        color: #2c3e50;
        font-family: 'Arial', sans-serif;
        padding-bottom: 20px;
        border-bottom: 2px solid #eee;
    }
    
    /* Màu sắc cho các khối lớp */
    .grade-1 { background-color: #FFCDD2; padding: 10px; border-radius: 10px; border-left: 5px solid #D32F2F; color: #B71C1C; font-weight: bold;}
    .grade-2 { background-color: #FFE0B2; padding: 10px; border-radius: 10px; border-left: 5px solid #F57C00; color: #E65100; font-weight: bold;}
    .grade-3 { background-color: #FFF9C4; padding: 10px; border-radius: 10px; border-left: 5px solid #FBC02D; color: #F57F17; font-weight: bold;}
    .grade-4 { background-color: #C8E6C9; padding: 10px; border-radius: 10px; border-left: 5px solid #388E3C; color: #1B5E20; font-weight: bold;}
    .grade-5 { background-color: #B3E5FC; padding: 10px; border-radius: 10px; border-left: 5px solid #0288D1; color: #01579B; font-weight: bold;}

    /* Style cho môn học */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 5px;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        color: #2c3e50;
        text-align: center;
        padding: 10px;
        border-top: 1px solid #ddd;
        font-weight: bold;
        z-index: 100;
    }
    .footer-text {
        font-size: 16px;
        text-transform: uppercase;
    }
    
    /* Ẩn footer mặc định của streamlit */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- DỮ LIỆU CẤU HÌNH ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖", "#e74c3c"), ("Toán", "✖️", "#3498db")],
    "Lớp 2": [("Tiếng Việt", "📖", "#e74c3c"), ("Toán", "✖️", "#3498db")],
    "Lớp 3": [("Tiếng Việt", "📖", "#e74c3c"), ("Toán", "✖️", "#3498db"), ("Tiếng Anh", "🇬🇧", "#9b59b6"), ("Tin học & Công nghệ", "💻", "#34495e")],
    "Lớp 4": [("Tiếng Việt", "📖", "#e74c3c"), ("Toán", "✖️", "#3498db"), ("Tiếng Anh", "🇬🇧", "#9b59b6"), ("Lịch sử & Địa lí", "🌏", "#d35400"), ("Khoa học", "🔬", "#27ae60"), ("Tin học", "💻", "#34495e"), ("Công nghệ", "🛠️", "#7f8c8d")],
    "Lớp 5": [("Tiếng Việt", "📖", "#e74c3c"), ("Toán", "✖️", "#3498db"), ("Tiếng Anh", "🇬🇧", "#9b59b6"), ("Lịch sử & Địa lí", "🌏", "#d35400"), ("Khoa học", "🔬", "#27ae60"), ("Tin học", "💻", "#34495e"), ("Công nghệ", "🛠️", "#7f8c8d")]
}

GRADE_COLORS = {
    "Lớp 1": "grade-1", "Lớp 2": "grade-2", "Lớp 3": "grade-3", "Lớp 4": "grade-4", "Lớp 5": "grade-5"
}

# --- HÀM XỬ LÝ FILE ---
def read_file_content(uploaded_file):
    if uploaded_file is None: return ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in reader.pages])
        elif uploaded_file.name.endswith(('.docx', '.doc')):
            import docx
            doc = docx.Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
            return df.to_string()
    except Exception as e:
        return f"Lỗi đọc file: {e}"
    return ""

# --- HÀM GỌI AI (GEMINI) ---
def generate_exam(api_key, grade, subject, content):
    if not api_key:
        return "⚠️ Vui lòng nhập Google Gemini API Key để tiếp tục."
    
    genai.configure(api_key=api_key)
    
    # --- SỬA LỖI TẠI ĐÂY ---
    # Sử dụng 'gemini-pro' thay vì 'gemini-1.5-flash' để tương thích tốt hơn
    try:
        model = genai.GenerativeModel("gemini-pro") 
    except:
        return "Lỗi: Không tìm thấy Model. Hãy chạy 'pip install -U google-generativeai' trong terminal."

    # PROMPT KỸ THUẬT
    prompt = f"""
    Bạn là một chuyên gia giáo dục tiểu học Việt Nam tại Trường PTDTBT Tiểu học Giàng Chu Phìn, cực kỳ am hiểu chương trình GDPT 2018 và Thông tư 27/2020/TT-BGDĐT.

    NHIỆM VỤ:
    Soạn đề kiểm tra định kỳ môn {subject} dành cho học sinh {grade}.
    
    DỮ LIỆU ĐẦU VÀO (MA TRẬN/ĐẶC TẢ):
    {content}

    YÊU CẦU BẮT BUỘC:
    1. **Nguồn kiến thức:** Chỉ sử dụng nội dung nằm trong chương trình GDPT 2018 và các bộ sách giáo khoa hiện hành (Cánh Diều, Chân Trời Sáng Tạo, Kết Nối Tri Thức). TUYỆT ĐỐI KHÔNG lấy kiến thức cũ hoặc kiến thức nước ngoài.
    2. **Cấu trúc đề:** - Phải thể hiện được 3 mức độ nhận thức theo Thông tư 27 (Mức 1: Nhận biết, Mức 2: Kết nối, Mức 3: Vận dụng).
       - Tỉ lệ trắc nghiệm/tự luận phù hợp với đặc thù môn {subject}.
    3. **Ngôn ngữ:** Trong sáng, dễ hiểu, phù hợp tâm lý lứa tuổi tiểu học, đặc biệt phù hợp với học sinh vùng cao.
    4. **Hình thức:** Trình bày rõ ràng, sử dụng Markdown để in đậm các câu hỏi.
    5. **Tiêu đề:** Đầu đề thi phải ghi rõ: "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN".

    HÃY XUẤT RA ĐỀ THI HOÀN CHỈNH KÈM ĐÁP ÁN GỢI Ý Ở CUỐI.
    """
    
    try:
        with st.spinner('AI đang phân tích chương trình GDPT 2018 và soạn đề...'):
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"Lỗi kết nối AI: {str(e)}. Hãy kiểm tra lại API Key hoặc mạng internet."

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# Sidebar: Nhập API
with st.sidebar:
    st.header("⚙️ Cấu hình")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    
    # --- TÍNH NĂNG CHECK API ---
    if st.button("Kiểm tra kết nối API"):
        if not api_key:
            st.error("Vui lòng nhập Key trước!")
        else:
            try:
                genai.configure(api_key=api_key)
                # Test thử model
                test_model = genai.GenerativeModel("gemini-pro")
                test_model.generate_content("Hello")
                st.success("Kết nối thành công! ✅")
            except Exception as e:
                st.error(f"Key không hợp lệ hoặc lỗi mạng: {e}")

    st.info("Để lấy API Key miễn phí, truy cập: [Google AI Studio](https://aistudio.google.com/)")
    st.markdown("---")
    st.markdown("**Hướng dẫn:**\n1. Chọn Lớp & Môn.\n2. Upload file Ma trận.\n3. Nhấn 'Tạo đề'.")

# BƯỚC 1: CHỌN LỚP (MÀU SẮC)
st.subheader("1️⃣ Chọn Khối Lớp")
selected_grade = st.radio("Chọn lớp:", list(SUBJECTS_DB.keys()), horizontal=True, label_visibility="collapsed")

# Hiển thị màu sắc tương ứng lớp đã chọn
st.markdown(f"<div class='{GRADE_COLORS[selected_grade]}'>Bạn đang chọn: {selected_grade}</div>", unsafe_allow_html=True)
st.write("")

# BƯỚC 2: CHỌN MÔN (HIỂN THỊ MÀU & ICON)
st.subheader(f"2️⃣ Chọn Môn Học - {selected_grade}")
if selected_grade:
    subjects_data = SUBJECTS_DB[selected_grade]
    subject_names = [f"{s[1]} {s[0]}" for s in subjects_data]
    selected_subject_raw = st.selectbox("Chọn môn để ra đề:", subject_names)
    
    selected_subject = selected_subject_raw.split(" ", 1)[1]
    
    st.info(f"Đang thiết lập thông số cho môn: **{selected_subject}**")

st.markdown("---")

# BƯỚC 3 & 4: UPLOAD & HIỂN THỊ (SPLIT VIEW)
col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("3️⃣ Upload Ma trận / Đặc tả")
    st.markdown(f"Tải lên file ma trận cho môn **{selected_subject}** (PDF, DOCX, Excel).")
    
    uploaded_file = st.file_uploader("Kéo thả file vào đây:", type=['pdf', 'docx', 'doc', 'xlsx', 'xls'])
    
    file_content = ""
    if uploaded_file:
        file_content = read_file_content(uploaded_file)
        st.success(f"✅ Đã đọc {len(file_content)} ký tự từ file.")
        with st.expander("Xem nội dung ma trận đã đọc"):
            st.text(file_content[:800] + "...")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    btn_generate = st.button("✨ TẠO ĐỀ KIỂM TRA NGAY", type="primary", use_container_width=True)

with col_output:
    st.subheader("4️⃣ Nội dung Đề thi (AI)")
    st.markdown("*Đề thi sẽ hiển thị tại đây, tuân thủ GDPT 2018.*")
    
    container = st.container(border=True)
    
    if "generated_exam" not in st.session_state:
        st.session_state.generated_exam = ""

    if btn_generate:
        if not uploaded_file:
            st.warning("⚠️ Vui lòng tải lên file Ma trận trước!")
        else:
            result = generate_exam(api_key, selected_grade, selected_subject, file_content)
            st.session_state.generated_exam = result

    if st.session_state.generated_exam:
        container.markdown(st.session_state.generated_exam)
        st.download_button(
            label="📥 Tải về (.txt)",
            data=st.session_state.generated_exam,
            file_name=f"De_Thi_{selected_subject}_{selected_grade}.txt",
            mime="text/plain"
        )

# --- CUỐI TRANG: TÊN TRƯỜNG ---
st.markdown("<br><br><br>", unsafe_allow_html=True) 
st.markdown(
    """
    <div class='footer'>
        <div class='footer-text'>🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</div>
        <small>Hệ thống hỗ trợ chuyên môn - Đổi mới kiểm tra đánh giá theo Thông tư 27</small>
    </div>
    """, 
    unsafe_allow_html=True
)
