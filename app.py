import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
import io
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Ra Đề Tiểu Học (Auto-Fix)", page_icon="🛡️", layout="wide")

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .main-header {font-size: 22px; font-weight: bold; color: #004085; text-align: center; margin-bottom: 20px;}
    .sub-header {font-size: 16px; font-weight: bold; color: #c82333; margin-top: 10px; border-bottom: 2px solid #ddd; padding-bottom: 5px;}
    .score-display {font-size: 18px; font-weight: bold; color: #28a745; text-align: center; background: #e8f5e9; padding: 10px; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("🔑 Cài đặt")
    api_key = st.text_input("Dán Google API Key vào đây:", type="password")
    st.info("Hệ thống sẽ tự động chọn Model tốt nhất cho Key của bạn.")

# --- HÀM ĐỌC FILE ---
def read_file_content(uploaded_file):
    try:
        if uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text for cell in row.cells]
                    text += "\n| " + " | ".join(row_text) + " |"
            return text
        elif uploaded_file.name.endswith('.txt'):
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(('.xlsx', '.xls', '.csv')):
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            return df.to_string()
    except Exception as e:
        return f"Lỗi: {str(e)}"
    return ""

# --- HÀM CHỌN MODEL TỰ ĐỘNG (ĐỂ SỬA LỖI 404) ---
def get_best_available_model():
    """Hàm này tự dò xem tài khoản được dùng model nào để tránh lỗi 404"""
    try:
        # Lấy danh sách model mà key này được phép dùng
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ưu tiên số 1: Flash 1.5 (Nhanh, rẻ, tốt)
        if 'models/gemini-1.5-flash' in available_models:
            return 'gemini-1.5-flash'
        
        # Ưu tiên số 2: Pro 1.5
        if 'models/gemini-1.5-pro' in available_models:
            return 'gemini-1.5-pro'
            
        # Ưu tiên số 3: Gemini Pro (Bản cũ ổn định)
        if 'models/gemini-pro' in available_models:
            return 'gemini-pro'
            
        # Nếu không tìm thấy cái nào quen thuộc, lấy cái đầu tiên trong danh sách
        if available_models:
            return available_models[0].replace('models/', '')
            
    except Exception as e:
        # Nếu lỗi quá nặng (do thư viện quá cũ), trả về model an toàn nhất
        return 'gemini-pro'
    
    return 'gemini-pro'

# --- HÀM GỌI AI ---
def generate_exam_levels(api_key, subject_plan, matrix_content, levels_config, grade, subject):
    if not api_key:
        return "⚠️ Vui lòng nhập API Key trước."
    
    genai.configure(api_key=api_key)
    
    # --- BƯỚC QUAN TRỌNG: Tự động chọn model ---
    model_name = get_best_available_model()
    # Hiển thị model đang dùng để người dùng yên tâm
    st.toast(f"Đang sử dụng model: {model_name}", icon="🤖")
    
    model = genai.GenerativeModel(model_name)

    mcq = levels_config['mcq']
    essay = levels_config['essay']
    
    prompt = f"""
    Đóng vai Giáo viên cốt cán môn {subject} Tiểu học. Hãy soạn ĐỀ KIỂM TRA LỚP {grade}.
    
    1. CẤU TRÚC ĐỀ BẮT BUỘC:
    A. TRẮC NGHIỆM ({mcq['point']} đ/câu): Biết {mcq['L1']}, Hiểu {mcq['L2']}, Vận dụng {mcq['L3']} câu.
    B. TỰ LUẬN ({essay['point']} đ/câu): Biết {essay['L1']}, Hiểu {essay['L2']}, Vận dụng {essay['L3']} câu.
    
    2. NỘI DUNG: {subject_plan}
    3. MA TRẬN: {matrix_content}
    
    YÊU CẦU: Có ĐÁP ÁN và HƯỚNG DẪN CHẤM. Ngôn ngữ phù hợp Lớp {grade}.
    """

    # Cơ chế thử lại nếu mạng lag (Retry)
    for attempt in range(3):
        try:
            with st.spinner(f'Đang soạn đề... (Dùng {model_name})'):
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg: # Lỗi quá tải
                time.sleep(5)
                continue
            elif "404" in error_msg: # Lỗi không tìm thấy model
                return f"❌ Lỗi model '{model_name}'. Hãy thử cập nhật thư viện: pip install -U google-generativeai"
            else:
                return f"❌ Lỗi: {error_msg}"
    
    return "❌ Hệ thống đang bận, vui lòng thử lại sau."

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">📝 HỆ THỐNG RA ĐỀ (PHIÊN BẢN SỬA LỖI 404)</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.2])

# === CỘT TRÁI ===
with col_left:
    st.markdown('<div class="sub-header">1. Dữ liệu nguồn</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: subject = st.selectbox("Môn học", ["Tin học", "Công nghệ", "Toán", "Tiếng Việt", "Khoa học", "LS&ĐL"])
    with c2: grade = st.selectbox("Khối lớp", ["Lớp 3", "Lớp 4", "Lớp 5"])
    
    file_plan = st.file_uploader("Tải nội dung bài học", type=['docx', 'txt'])
    plan_text = read_file_content(file_plan) if file_plan else ""

    file_matrix = st.file_uploader("Tải Ma trận (Excel/Word)", type=['xlsx', 'docx', 'csv'])
    matrix_text = read_file_content(file_matrix) if file_matrix else ""

# === CỘT PHẢI ===
with col_right:
    st.markdown('<div class="sub-header">2. Cấu hình</div>', unsafe_allow_html=True)
    
    st.markdown("##### 🅰️ Trắc Nghiệm")
    c_tn1, c_tn2, c_tn3, c_tn4 = st.columns([1, 1, 1, 1])
    with c_tn1: mcq_point = st.number_input("Điểm/câu", 0.1, 2.0, 0.5)
    with c_tn2: mcq_l1 = st.number_input("Biết (TN)", 0, 10, 4)
    with c_tn3: mcq_l2 = st.number_input("Hiểu (TN)", 0, 10, 3)
    with c_tn4: mcq_l3 = st.number_input("Vận dụng", 0, 10, 1)
    
    st.markdown("##### 🅱️ Tự Luận")
    c_tl1, c_tl2, c_tl3, c_tl4 = st.columns([1, 1, 1, 1])
    with c_tl1: essay_point = st.number_input("Điểm/câu", 0.5, 5.0, 1.0)
    with c_tl2: essay_l1 = st.number_input("Biết (TL)", 0, 5, 0)
    with c_tl3: essay_l2 = st.number_input("Hiểu (TL)", 0, 5, 1)
    with c_tl4: essay_l3 = st.number_input("Vận dụng", 0, 5, 1)

    total_score = ((mcq_l1+mcq_l2+mcq_l3)*mcq_point) + ((essay_l1+essay_l2+essay_l3)*essay_point)
    st.markdown(f'<div class="score-display">TỔNG ĐIỂM: {total_score}</div>', unsafe_allow_html=True)
    
    if st.button("🚀 TẠO ĐỀ NGAY", type="primary", use_container_width=True):
        if not plan_text or not matrix_text:
            st.error("Thiếu file nội dung hoặc ma trận.")
        else:
            levels_config = {
                "mcq": {"point": mcq_point, "L1": mcq_l1, "L2": mcq_l2, "L3": mcq_l3},
                "essay": {"point": essay_point, "L1": essay_l1, "L2": essay_l2, "L3": essay_l3}
            }
            result = generate_exam_levels(api_key, plan_text, matrix_text, levels_config, grade, subject)
            st.markdown(result)
            st.download_button("📥 Tải Đề về máy (.txt)", result, file_name=f"DeThi_{subject}_{grade}.txt")
