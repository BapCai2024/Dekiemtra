import streamlit as st
import pandas as pd
import requests
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
    .grade-box { padding: 5px; border-radius: 5px; font-weight: bold; text-align: center; color: white;}
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

# --- HÀM 1: ĐỌC FILE UPLOAD ---
def read_file_content(uploaded_file):
    if uploaded_file is None: return ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
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

# --- HÀM 2: TỰ ĐỘNG TÌM MODEL ---
def find_working_model(api_key):
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(list_url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            chat_models = [m['name'] for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])]
            preferred = ['models/gemini-1.5-pro', 'models/gemini-1.5-flash', 'models/gemini-pro', 'models/gemini-1.0-pro']
            for p in preferred:
                for real_model in chat_models:
                    if p in real_model: return real_model
            if chat_models: return chat_models[0]
        return None
    except:
        return None

# --- HÀM 3: GỌI AI VỚI CƠ CHẾ CHỐNG LỖI 429 ---
def generate_exam_final(api_key, grade, subject, content):
    clean_key = api_key.strip()
    if not clean_key: return "⚠️ Chưa nhập API Key."

    with st.spinner("Đang kết nối máy chủ Google..."):
        model_name = find_working_model(clean_key)
    
    if not model_name:
        return "❌ Lỗi Key hoặc Mạng. Vui lòng kiểm tra lại API Key."

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={clean_key}"
    headers = {'Content-Type': 'application/json'}
    
    # PROMPT ĐƯỢC CẬP NHẬT: Yêu cầu bám sát file và xuất cả ma trận
    prompt = f"""
    Bạn là Tổ trưởng chuyên môn trường TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN.
    
    NHIỆM VỤ:
    Dựa TUYỆT ĐỐI vào nội dung văn bản (Ma trận/Đặc tả) tôi cung cấp dưới đây để ra đề thi môn {subject} lớp {grade}.
    
    NỘI DUNG VĂN BẢN ĐẦU VÀO:
    --------------------------
    {content}
    --------------------------
    
    YÊU CẦU BẮT BUỘC:
    1. **NỘI DUNG:** Chỉ được sử dụng các đơn vị kiến thức có trong văn bản đầu vào ở trên. KHÔNG được tự ý bịa ra kiến thức nằm ngoài file này.
    2. **CẤU TRÚC:** Đề thi phải đúng theo các mức độ (M1, M2, M3) đã mô tả trong văn bản đầu vào.
    3. **ĐỐI TƯỢNG:** Ngôn ngữ trong sáng, ngắn gọn, phù hợp học sinh vùng cao.
    4. **ĐỊNH DẠNG ĐẦU RA:** Phải trình bày thành 2 phần rõ ràng:
       - PHẦN 1: ĐỀ KIỂM TRA (Có tiêu đề "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN" ở trên cùng).
       - PHẦN 2: HƯỚNG DẪN CHẤM VÀ MA TRẬN ĐỀ (Liệt kê đáp án đúng và ma trận câu hỏi tương ứng).
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    # CƠ CHẾ RETRY (THỬ LẠI KHI GẶP LỖI 429)
    max_retries = 3 # Số lần thử lại tối đa
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                st.toast(f"Hệ thống đang bận, đang thử lại lần {attempt+1}...")
                time.sleep(3 + (attempt * 2)) # Chờ 3s, 5s... tăng dần

            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                try:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                except:
                    return "⚠️ AI không trả về nội dung. Hãy thử file khác."
            
            elif response.status_code == 429:
                # Nếu gặp lỗi 429 (Too Many Requests), vòng lặp sẽ tiếp tục thử lại
                continue 
            
            else:
                return f"⚠️ Lỗi từ Google ({response.status_code}): {response.text}"
                
        except Exception as e:
            return f"Lỗi mạng: {e}"

    return "⚠️ Hệ thống Google đang quá tải (Lỗi 429). Vui lòng đợi 1-2 phút sau rồi ấn lại nút Tạo đề."

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
                st.success(f"✅ Ổn định! ({found_model})")
            else:
                st.error("❌ Key sai hoặc lỗi mạng.")
                
    st.markdown("---")
    st.info("Hệ thống đã tích hợp cơ chế chống nghẽn mạng (Anti-429 Error).")

# BƯỚC 1: CHỌN LỚP & MÔN
st.subheader("1. Chọn Lớp & Môn Học")
selected_grade = st.radio("Chọn khối:", list(SUBJECTS_DB.keys()), horizontal=True)

# Hiển thị màu lớp đẹp hơn
colors = {"Lớp 1": "#D32F2F", "Lớp 2": "#E65100", "Lớp 3": "#F57F17", "Lớp 4": "#2E7D32", "Lớp 5": "#1565C0"}
st.markdown(f"<div style='background-color:{colors[selected_grade]}; color:white; padding:5px; border-radius:5px; text-align:center;'>Đang làm việc với: {selected_grade}</div>", unsafe_allow_html=True)

# Lấy môn học
subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
selected_subject_full = st.selectbox("Chọn môn:", subjects_list)
selected_subject = selected_subject_full.split(" ", 1)[1]

st.markdown("---")

# BƯỚC 2: UPLOAD & XỬ LÝ
c1, c2 = st.columns([1, 1], gap="large")

with c1:
    st.subheader("2. Dữ liệu đầu vào")
    st.info("💡 Lưu ý: AI sẽ chỉ lấy kiến thức CÓ TRONG FILE này để ra đề.")
    uploaded_file = st.file_uploader("Upload Ma trận/Đặc tả (PDF, Word, Excel)", type=['pdf','docx','doc','xlsx'])
    
    file_txt = ""
    if uploaded_file:
        file_txt = read_file_content(uploaded_file)
        if len(file_txt) > 50:
            st.success(f"✅ Đã đọc nội dung file ({len(file_txt)} ký tự)")
        else:
            st.warning("⚠️ File trống hoặc không đọc được chữ. Hãy kiểm tra lại.")
    
    st.write("")
    btn_run = st.button("🚀 TẠO ĐỀ VÀ MA TRẬN", type="primary", use_container_width=True)

with c2:
    st.subheader("3. Kết quả")
    container = st.container(border=True)
    
    if "result_exam" not in st.session_state:
        st.session_state.result_exam = ""
        
    if btn_run:
        if not uploaded_file:
            st.warning("⚠️ Vui lòng upload file ma trận trước!")
        elif len(file_txt) < 50:
             st.error("⚠️ Nội dung file quá ngắn hoặc không đọc được.")
        else:
            st.session_state.result_exam = generate_exam_final(api_key_input, selected_grade, selected_subject, file_txt)

    # Hiển thị
    if st.session_state.result_exam:
        container.markdown(st.session_state.result_exam)
        # Nút tải xuống cập nhật tên
        st.download_button("📥 Tải xuống (Đề + Ma trận)", st.session_state.result_exam, f"De_va_Matran_{selected_subject}.txt")

# FOOTER
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""<div class='footer'><b>🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</b><br>Hệ thống hỗ trợ chuyên môn - Đổi mới kiểm tra đánh giá theo Thông tư 27</div>""", unsafe_allow_html=True)
