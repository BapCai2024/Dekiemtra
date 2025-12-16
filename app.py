import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
from io import BytesIO
import sys
import subprocess

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="HỖ TRỢ RA ĐỀ THI TIỂU HỌC",
    page_icon="✏️",
    layout="wide"
)

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .main-title { text-align: center; color: #2c3e50; padding-bottom: 20px; border-bottom: 2px solid #eee; }
    .grade-1 { background-color: #FFCDD2; padding: 10px; border-radius: 10px; border-left: 5px solid #D32F2F; color: #B71C1C; font-weight: bold;}
    .grade-2 { background-color: #FFE0B2; padding: 10px; border-radius: 10px; border-left: 5px solid #F57C00; color: #E65100; font-weight: bold;}
    .grade-3 { background-color: #FFF9C4; padding: 10px; border-radius: 10px; border-left: 5px solid #FBC02D; color: #F57F17; font-weight: bold;}
    .grade-4 { background-color: #C8E6C9; padding: 10px; border-radius: 10px; border-left: 5px solid #388E3C; color: #1B5E20; font-weight: bold;}
    .grade-5 { background-color: #B3E5FC; padding: 10px; border-radius: 10px; border-left: 5px solid #0288D1; color: #01579B; font-weight: bold;}
    div[data-testid="stMetric"] { background-color: #f8f9fa; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: #2c3e50; text-align: center; padding: 10px; border-top: 1px solid #ddd; font-weight: bold; z-index: 100; }
    .footer-text { font-size: 16px; text-transform: uppercase; }
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
GRADE_COLORS = {"Lớp 1": "grade-1", "Lớp 2": "grade-2", "Lớp 3": "grade-3", "Lớp 4": "grade-4", "Lớp 5": "grade-5"}

# --- HÀM ĐỌC FILE ---
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

# --- HÀM GỌI AI (ĐÃ SỬA LỖI & THÊM YÊU CẦU CẦN ĐẠT) ---
def generate_exam(api_key, grade, subject, content):
    if not api_key: return "⚠️ Vui lòng nhập API Key."
    
    genai.configure(api_key=api_key)
    
    # DANH SÁCH MODEL SẼ THỬ LẦN LƯỢT (Nếu cái đầu lỗi thì thử cái sau)
    models_to_try = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]
    
    active_model = None
    response_text = ""
    error_log = []

    # PROMPT MỚI THEO YÊU CẦU CỦA BẠN
    prompt = f"""
    Đóng vai trò là chuyên gia giáo dục tại TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN.
    Nhiệm vụ: Soạn đề thi môn {subject} lớp {grade} theo TT27.
    
    DỮ LIỆU MA TRẬN:
    {content}
    
    YÊU CẦU TUYỆT ĐỐI:
    1. **YÊU CẦU CẦN ĐẠT:** Nội dung đề thi phải bám sát "Yêu cầu cần đạt" của chương trình GDPT 2018 đối với môn {subject} lớp {grade}.
    2. **NGUỒN KIẾN THỨC:** Chỉ lấy dữ liệu từ các bộ sách (Cánh Diều, Chân Trời ST, Kết Nối Tri Thức). Không lấy nguồn ngoài.
    3. **CẤU TRÚC:** Đảm bảo 3 mức độ nhận thức (1, 2, 3).
    4. **ĐỐI TƯỢNG:** Ngôn ngữ trong sáng, phù hợp học sinh vùng cao.
    5. **TIÊU ĐỀ:** Phải có dòng chữ "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN" ở đầu đề.
    """

    # VÒNG LẶP THỬ MODEL (FIX LỖI 404)
    with st.spinner('Đang kết nối AI (Đang tự động thử các dòng Model)...'):
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                # Thử gọi lệnh đơn giản trước để xem model có sống không
                response = model.generate_content(prompt)
                response_text = response.text
                active_model = model_name
                break # Nếu thành công thì thoát vòng lặp ngay
            except Exception as e:
                error_log.append(f"{model_name}: {str(e)}")
                continue # Nếu lỗi thì thử model tiếp theo trong danh sách

    if response_text:
        return f"*(Đã tạo bằng model: {active_model})*\n\n" + response_text
    else:
        # Nếu thử hết cả 3 model mà vẫn lỗi
        return f"⚠️ KHÔNG THỂ TẠO ĐỀ. Chi tiết lỗi:\n" + "\n".join(error_log) + "\n\n👉 LỜI KHUYÊN: Hãy tắt hẳn cửa sổ đen (CMD) và chạy lại lệnh 'streamlit run app.py'."

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# SIDEBAR & CÔNG CỤ SỬA LỖI
with st.sidebar:
    st.header("⚙️ Cấu hình")
    api_key = st.text_input("Nhập API Key:", type="password")
    
    st.markdown("---")
    st.warning("👇 NẾU VẪN BỊ LỖI, BẤM NÚT DƯỚI 👇")
    
    # NÚT SỬA LỖI (UPDATE MẠNH)
    if st.button("🔧 CẬP NHẬT HỆ THỐNG", type="primary"):
        with st.status("Đang xử lý..."):
            python_path = sys.executable 
            st.write(f"Python: {python_path}")
            try:
                st.write("Đang gỡ bản cũ...")
                subprocess.run([python_path, "-m", "pip", "uninstall", "google-generativeai", "-y"])
                st.write("Đang cài bản mới nhất...")
                subprocess.check_call([python_path, "-m", "pip", "install", "google-generativeai==0.5.2"]) # Cài bản ổn định
                st.success("✅ ĐÃ XONG! QUAN TRỌNG: Bạn hãy tắt cửa sổ CMD đi và chạy lại.")
            except Exception as e:
                st.error(f"Lỗi: {e}")

    st.markdown("---")
    st.info("Lấy API Key: [Google AI Studio](https://aistudio.google.com/)")

# BƯỚC 1: CHỌN LỚP
st.subheader("1️⃣ Chọn Khối Lớp")
selected_grade = st.radio("Chọn lớp:", list(SUBJECTS_DB.keys()), horizontal=True, label_visibility="collapsed")
st.markdown(f"<div class='{GRADE_COLORS[selected_grade]}'>Bạn đang chọn: {selected_grade}</div>", unsafe_allow_html=True)
st.write("")

# BƯỚC 2: CHỌN MÔN
st.subheader(f"2️⃣ Chọn Môn Học - {selected_grade}")
if selected_grade:
    subjects_data = SUBJECTS_DB[selected_grade]
    subject_names = [f"{s[1]} {s[0]}" for s in subjects_data]
    selected_subject_raw = st.selectbox("Chọn môn để ra đề:", subject_names)
    selected_subject = selected_subject_raw.split(" ", 1)[1]
    st.info(f"Môn: **{selected_subject}**")

st.markdown("---")

# BƯỚC 3 & 4: UPLOAD & KẾT QUẢ
col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("3️⃣ Upload Ma trận")
    uploaded_file = st.file_uploader("Tải file (PDF, DOCX, Excel)", type=['pdf', 'docx', 'doc', 'xlsx', 'xls'])
    
    file_content = ""
    if uploaded_file:
        file_content = read_file_content(uploaded_file)
        st.success(f"Đã đọc file. ({len(file_content)} ký tự)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_generate = st.button("✨ TẠO ĐỀ KIỂM TRA NGAY", type="primary", use_container_width=True)

with col_output:
    st.subheader("4️⃣ Đề thi AI")
    container = st.container(border=True)
    
    if "generated_exam" not in st.session_state:
        st.session_state.generated_exam = ""

    if btn_generate:
        if not uploaded_file:
            st.warning("⚠️ Chưa có file ma trận!")
        else:
            result = generate_exam(api_key, selected_grade, selected_subject, file_content)
            st.session_state.generated_exam = result

    if st.session_state.generated_exam:
        container.markdown(st.session_state.generated_exam)
        st.download_button("📥 Tải về (.txt)", st.session_state.generated_exam, f"De_Thi_{selected_subject}.txt")

# FOOTER
st.markdown("<br><br><br>", unsafe_allow_html=True) 
st.markdown("""<div class='footer'><div class='footer-text'>🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</div><small>Hệ thống hỗ trợ chuyên môn - TT27</small></div>""", unsafe_allow_html=True)
