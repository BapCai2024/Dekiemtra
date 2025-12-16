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
</style>
""", unsafe_allow_html=True)

# --- DỮ LIỆU CẤU HÌNH ---
# Danh sách môn học đánh giá định kỳ theo TT27
# Cấu trúc: [Tên môn, Icon, Màu sắc đại diện (Hex)]
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
   model = genai.GenerativeModel("gemini-2.5-flash") # hoặc ("gemini-2.5-pro")

    # PROMPT KỸ THUẬT (SYSTEM INSTRUCTION)
    prompt = f"""
    Bạn là một chuyên gia giáo dục tiểu học Việt Nam, cực kỳ am hiểu chương trình GDPT 2018 và Thông tư 27/2020/TT-BGDĐT.

    NHIỆM VỤ:
    Soạn đề kiểm tra định kỳ môn {subject} dành cho học sinh {grade}.
    
    DỮ LIỆU ĐẦU VÀO (MA TRẬN/ĐẶC TẢ):
    {content}

    YÊU CẦU BẮT BUỘC:
    1. **Nguồn kiến thức:** Chỉ sử dụng nội dung nằm trong chương trình GDPT 2018 và các bộ sách giáo khoa hiện hành (Cánh Diều, Chân Trời Sáng Tạo, Kết Nối Tri Thức). TUYỆT ĐỐI KHÔNG lấy kiến thức cũ hoặc kiến thức nước ngoài.
    2. **Cấu trúc đề:** - Phải thể hiện được 3 mức độ nhận thức theo Thông tư 27 (Mức 1: Nhận biết, Mức 2: Kết nối, Mức 3: Vận dụng).
       - Tỉ lệ trắc nghiệm/tự luận phù hợp với đặc thù môn {subject}.
    3. **Ngôn ngữ:** Trong sáng, dễ hiểu, phù hợp tâm lý lứa tuổi tiểu học.
    4. **Hình thức:** Trình bày rõ ràng, sử dụng Markdown để in đậm các câu hỏi.

    HÃY XUẤT RA ĐỀ THI HOÀN CHỈNH KÈM ĐÁP ÁN GỢI Ý Ở CUỐI.
    """
    
    try:
        with st.spinner('AI đang phân tích chương trình GDPT 2018 và soạn đề...'):
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"Lỗi kết nối AI: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# Sidebar: Nhập API
with st.sidebar:
    st.header("⚙️ Cấu hình")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    st.info("Để lấy API Key miễn phí, truy cập: [Google AI Studio](https://aistudio.google.com/)")
    st.markdown("---")
    st.markdown("**Hướng dẫn:**\n1. Chọn Lớp & Môn.\n2. Upload file Ma trận.\n3. Nhấn 'Tạo đề'.")

# BƯỚC 1: CHỌN LỚP (MÀU SẮC)
st.subheader("1️⃣ Chọn Khối Lớp")
cols = st.columns(5)
selected_grade = None

# Tạo nút chọn lớp giả lập bằng radio button nằm ngang cho đẹp
grade_options = list(SUBJECTS_DB.keys())
selected_grade = st.radio("Chọn lớp:", grade_options, horizontal=True, label_visibility="collapsed")

# Hiển thị màu sắc tương ứng lớp đã chọn
st.markdown(f"<div class='{GRADE_COLORS[selected_grade]}'>Bạn đang chọn: {selected_grade}</div>", unsafe_allow_html=True)
st.write("")

# BƯỚC 2: CHỌN MÔN (HIỂN THỊ MÀU & ICON)
st.subheader(f"2️⃣ Chọn Môn Học - {selected_grade}")
if selected_grade:
    subjects_data = SUBJECTS_DB[selected_grade]
    # Lấy danh sách tên môn để hiển thị selectbox
    subject_names = [f"{s[1]} {s[0]}" for s in subjects_data]
    selected_subject_raw = st.selectbox("Chọn môn để ra đề:", subject_names)
    
    # Tách tên môn ra khỏi icon để xử lý
    selected_subject = selected_subject_raw.split(" ", 1)[1]
    selected_icon = selected_subject_raw.split(" ", 1)[0]
    
    # Hiển thị thẻ môn học đẹp mắt
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
    
    # NÚT TẠO ĐỀ (MÀU SẮC PHÙ HỢP)
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

    # Hiển thị kết quả
    if st.session_state.generated_exam:
        container.markdown(st.session_state.generated_exam)
        
        # Nút tải về
        st.download_button(
            label="📥 Tải về (.txt)",
            data=st.session_state.generated_exam,
            file_name=f"De_Thi_{selected_subject}_{selected_grade}.txt",
            mime="text/plain"
        )
