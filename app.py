import streamlit as st
import pandas as pd
import requests # Dùng requests để kiểm soát hoàn toàn kết nối
import json
import time
from io import BytesIO

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="HỖ TRỢ RA ĐỀ THI TIỂU HỌC",
    page_icon="✏️",
    layout="wide"
)

# --- CSS GIAO DIỆN ---
st.markdown("""
<style>
    .main-title { text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;}
    .grade-1 { background-color: #FFCDD2; padding: 5px; border-radius: 5px; color: #B71C1C; font-weight: bold; text-align: center;}
    .grade-2 { background-color: #FFE0B2; padding: 5px; border-radius: 5px; color: #E65100; font-weight: bold; text-align: center;}
    .grade-3 { background-color: #FFF9C4; padding: 5px; border-radius: 5px; color: #F57F17; font-weight: bold; text-align: center;}
    .grade-4 { background-color: #C8E6C9; padding: 5px; border-radius: 5px; color: #1B5E20; font-weight: bold; text-align: center;}
    .grade-5 { background-color: #B3E5FC; padding: 5px; border-radius: 5px; color: #01579B; font-weight: bold; text-align: center;}
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; text-align: center; padding: 10px; border-top: 1px solid #ddd; z-index: 99;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- DỮ LIỆU ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tiếng Anh", "🇬🇧"), ("Tin học & Công nghệ", "💻")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tiếng Anh", "🇬🇧"), ("Lịch sử & Địa lí", "🌏"), ("Khoa học", "🔬"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tiếng Anh", "🇬🇧"), ("Lịch sử & Địa lí", "🌏"), ("Khoa học", "🔬"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}
GRADE_COLORS = {"Lớp 1": "grade-1", "Lớp 2": "grade-2", "Lớp 3": "grade-3", "Lớp 4": "grade-4", "Lớp 5": "grade-5"}

# --- HÀM 1: ĐỌC FILE UPLOAD ---
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

# --- HÀM 2: TỰ ĐỘNG TÌM MODEL HỢP LỆ (KHẮC PHỤC LỖI 404) ---
def find_working_model(api_key):
    # API để lấy danh sách các model
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(list_url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            # Lọc ra các model có khả năng tạo nội dung (generateContent)
            chat_models = [m['name'] for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])]
            
            # Ưu tiên các model xịn theo thứ tự
            preferred = ['models/gemini-1.5-pro', 'models/gemini-1.5-flash', 'models/gemini-pro', 'models/gemini-1.0-pro']
            
            # Tìm xem có model ưu tiên nào trong danh sách không
            for p in preferred:
                # Tìm tương đối (vì google hay thêm version phía sau)
                for real_model in chat_models:
                    if p in real_model:
                        return real_model
            
            # Nếu không tìm thấy model ưu tiên, lấy cái đầu tiên tìm được
            if chat_models:
                return chat_models[0]
                
        return None # Không lấy được danh sách hoặc Key sai
    except:
        return None

# --- HÀM 3: GỌI AI ĐỂ TẠO ĐỀ ---
def generate_exam_final(api_key, grade, subject, content):
    clean_key = api_key.strip() # Xóa khoảng trắng thừa
    if not clean_key: return "⚠️ Chưa nhập API Key."

    # Bước 1: Tìm model phù hợp
    with st.spinner("Đang tìm Model phù hợp với Key của bạn..."):
        model_name = find_working_model(clean_key)
    
    if not model_name:
        return "❌ LỖI KẾT NỐI: API Key không đúng hoặc không lấy được danh sách Model. Vui lòng kiểm tra lại Key."

    # Bước 2: Gọi API tạo đề
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={clean_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    Đóng vai trò: Giáo viên trường TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN.
    Nhiệm vụ: Ra đề thi môn {subject} lớp {grade}.
    
    DỮ LIỆU ĐẦU VÀO:
    {content}
    
    YÊU CẦU CỤ THỂ:
    1. **Bám sát Yêu cầu cần đạt:** Của chương trình GDPT 2018 môn {subject} lớp {grade}.
    2. **Nguồn dữ liệu:** Chỉ dùng kiến thức trong SGK (Cánh Diều, Chân Trời ST, Kết Nối Tri Thức).
    3. **Ma trận:** Đảm bảo 3 mức độ (M1: Nhận biết, M2: Kết nối, M3: Vận dụng).
    4. **Văn phong:** Dễ hiểu, phù hợp học sinh vùng cao.
    5. **Tiêu đề:** Bắt buộc có dòng: "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN".
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        with st.spinner(f"Đang tạo đề bằng model {model_name}..."):
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                try:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                except:
                    return "⚠️ AI không trả về nội dung (Block an toàn). Hãy thử lại."
            else:
                return f"⚠️ Lỗi từ Google ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Lỗi mạng: {e}"

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.header("🔑 CẤU HÌNH API")
    api_key_input = st.text_input("Dán API Key vào đây:", type="password")
    
    if st.button("Kiểm tra kết nối"):
        clean_k = api_key_input.strip()
        if not clean_k:
            st.error("Chưa nhập Key!")
        else:
            found_model = find_working_model(clean_k)
            if found_model:
                st.success(f"✅ Kết nối tốt! (Sử dụng: {found_model})")
            else:
                st.error("❌ Không kết nối được. Kiểm tra lại Key (Key sai hoặc hết hạn).")
                
    st.markdown("---")
    st.info("Lưu ý: Hệ thống sẽ tự động chọn Model tốt nhất mà Key của bạn hỗ trợ.")

# BƯỚC 1: CHỌN LỚP & MÔN
st.subheader("1. Chọn Lớp & Môn Học")
selected_grade = st.radio("Chọn khối:", list(SUBJECTS_DB.keys()), horizontal=True)
st.markdown(f"<div class='{GRADE_COLORS[selected_grade]}'>Đang chọn: {selected_grade}</div>", unsafe_allow_html=True)

# Lấy môn học
subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
selected_subject_full = st.selectbox("Chọn môn:", subjects_list)
selected_subject = selected_subject_full.split(" ", 1)[1] # Lấy tên môn bỏ icon

st.markdown("---")

# BƯỚC 2: UPLOAD & XỬ LÝ
c1, c2 = st.columns([1, 1], gap="large")

with c1:
    st.subheader("2. Dữ liệu đầu vào")
    uploaded_file = st.file_uploader("Upload Ma trận/Đặc tả (PDF, Word, Excel)", type=['pdf','docx','doc','xlsx'])
    
    file_txt = ""
    if uploaded_file:
        file_txt = read_file_content(uploaded_file)
        st.success(f"Đã đọc file: {len(file_txt)} ký tự")
    
    st.write("")
    btn_run = st.button("🚀 TẠO ĐỀ THI NGAY", type="primary", use_container_width=True)

with c2:
    st.subheader("3. Kết quả")
    container = st.container(border=True)
    
    if "result_exam" not in st.session_state:
        st.session_state.result_exam = ""
        
    if btn_run:
        if not uploaded_file and len(file_txt) < 10:
            st.warning("⚠️ Vui lòng upload file ma trận trước!")
        else:
            st.session_state.result_exam = generate_exam_final(api_key_input, selected_grade, selected_subject, file_txt)

    # Hiển thị
    if st.session_state.result_exam:
        container.markdown(st.session_state.result_exam)
        st.download_button("📥 Tải về máy (.txt)", st.session_state.result_exam, f"De_thi_{selected_subject}.txt")

# FOOTER
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""<div class='footer'><b>🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</b><br>Hệ thống hỗ trợ chuyên môn - Đổi mới kiểm tra đánh giá theo Thông tư 27</div>""", unsafe_allow_html=True)
