import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
import io

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Ra Đề Tiểu Học (Pro)", page_icon="🏫", layout="wide")

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .main-header {font-size: 24px; font-weight: bold; color: #0066cc; text-align: center; margin-bottom: 20px;}
    .section-header {font-size: 16px; font-weight: bold; color: #d9534f; margin-top: 15px; border-bottom: 1px solid #ddd; padding-bottom: 5px;}
    .info-box {background-color: #f0f8ff; padding: 10px; border-radius: 5px; font-size: 14px;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("🔑 Cấu hình kết nối")
    api_key = st.text_input("Google API Key:", type="password")
    st.info("Hệ thống tuân thủ Thông tư 27 & Chương trình GDPT 2018.")

# --- HÀM ĐỌC FILE (Word/Text/Excel) ---
def read_file_content(uploaded_file):
    """Hàm đa năng đọc nội dung từ file Word, Text hoặc Excel"""
    try:
        if uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            # Đọc thêm bảng trong Word nếu có
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
        return f"Lỗi đọc file: {str(e)}"
    return ""

# --- HÀM GỌI AI ---
def generate_exam_advanced(api_key, subject_plan, matrix_content, config_mcq, config_essay, grade, subject):
    if not api_key:
        return "⚠️ Vui lòng nhập API Key."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Tính toán tổng điểm để nhắc AI
    total_score = (config_mcq['count'] * config_mcq['point']) + (config_essay['count'] * config_essay['point'])

    prompt = f"""
    Đóng vai Trưởng bộ môn {subject} Tiểu học. Hãy soạn ĐỀ KIỂM TRA LỚP {grade}.
    
    =========================================
    1. CẤU TRÚC ĐỀ BẮT BUỘC (TUÂN THỦ TUYỆT ĐỐI):
    - Tổng điểm toàn bài: {total_score} điểm.
    
    A. PHẦN TRẮC NGHIỆM:
    - Số lượng câu: {config_mcq['count']} câu.
    - Điểm số: {config_mcq['point']} điểm/câu.
    - Các dạng cho phép: {', '.join(config_mcq['types'])}.
    
    B. PHẦN TỰ LUẬN:
    - Số lượng câu: {config_essay['count']} câu.
    - Điểm số: {config_essay['point']} điểm/câu (hoặc phân bổ linh hoạt sao cho tổng phần tự luận là {config_essay['count'] * config_essay['point']} điểm).
    
    =========================================
    2. NỘI DUNG KIẾN THỨC (CĂN CỨ ĐỂ RA ĐỀ):
    {subject_plan}

    =========================================
    3. MA TRẬN MỨC ĐỘ NHẬN THỨC (THAM KHẢO PHÂN BỔ KHÓ/DỄ):
    (Hãy cố gắng phân bổ các câu hỏi trên vào các mức Biết/Hiểu/Vận dụng tương ứng với ma trận này)
    {matrix_content}

    =========================================
    4. YÊU CẦU ĐẦU RA:
    - Trình bày đề rõ ràng, phân chia Phần I (Trắc nghiệm) và Phần II (Tự luận).
    - Cuối đề phải có: HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN CHI TIẾT.
    - Ngôn ngữ phù hợp học sinh Lớp {grade}.
    """

    with st.spinner('Đang thiết lập cấu trúc và biên soạn câu hỏi...'):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Lỗi AI: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">📝 HỆ THỐNG RA ĐỀ TIỂU HỌC (TÙY BIẾN CAO)</div>', unsafe_allow_html=True)

col_input, col_config = st.columns([1, 1])

# --- CỘT 1: DỮ LIỆU ĐẦU VÀO ---
with col_input:
    st.markdown('<div class="section-header">1. DỮ LIỆU NGUỒN (INPUT)</div>', unsafe_allow_html=True)
    
    # Chọn môn và lớp
    c1, c2 = st.columns(2)
    with c1:
        subject = st.selectbox("Môn học", ["Tin học", "Công nghệ", "Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí"])
    with c2:
        grade = st.selectbox("Khối lớp", ["Lớp 3", "Lớp 4", "Lớp 5"])

    # Upload Nội dung kiến thức (Thay cho text area cũ)
    st.markdown("---")
    st.write("📂 **Nội dung/Kế hoạch dạy học:**")
    file_plan = st.file_uploader("Tải file bài học (.docx, .txt)", type=['docx', 'txt'], key="plan")
    
    plan_content = ""
    if file_plan:
        plan_content = read_file_content(file_plan)
        st.success(f"✅ Đã đọc nội dung bài học: {len(plan_content)} ký tự.")
    else:
        st.warning("⚠️ Hãy tải file nội dung bài học lên.")

    # Upload Ma trận
    st.markdown("---")
    st.write("📊 **Ma trận đề (Khung chuẩn):**")
    file_matrix = st.file_uploader("Tải file Ma trận (.xlsx, .csv)", type=['xlsx', 'xls', 'csv'], key="matrix")
    
    matrix_content = ""
    if file_matrix:
        matrix_content = read_file_content(file_matrix)
        st.success("✅ Đã nhận diện Ma trận.")

# --- CỘT 2: CẤU HÌNH ĐỀ THI ---
with col_config:
    st.markdown('<div class="section-header">2. CẤU HÌNH ĐỀ THI (OUTPUT)</div>', unsafe_allow_html=True)
    
    st.markdown("#### 🅰️ Phần Trắc Nghiệm")
    col_tn1, col_tn2 = st.columns(2)
    with col_tn1:
        num_mcq = st.number_input("Số câu Trắc nghiệm:", min_value=0, value=8, step=1)
    with col_tn2:
        point_mcq = st.number_input("Điểm mỗi câu TN:", min_value=0.1, value=0.5, step=0.1, format="%.1f")
    
    type_mcq = st.multiselect(
        "Dạng câu hỏi TN cho phép:",
        ["Chọn đáp án A,B,C,D", "Đúng/Sai", "Nối cột", "Điền từ"],
        default=["Chọn đáp án A,B,C,D", "Đúng/Sai"]
    )
    
    st.markdown("---")
    st.markdown("#### 🅱️ Phần Tự Luận")
    col_tl1, col_tl2 = st.columns(2)
    with col_tl1:
        num_essay = st.number_input("Số câu Tự luận:", min_value=0, value=2, step=1)
    with col_tl2:
        point_essay = st.number_input("Điểm trung bình/câu:", min_value=0.5, value=3.0, step=0.5, format="%.1f")
    
    st.info(f"🧮 **Tổng điểm dự kiến:** {num_mcq * point_mcq + num_essay * point_essay} điểm")

    st.markdown("---")
    if st.button("🚀 KHỞI TẠO ĐỀ THI", type="primary", use_container_width=True):
        if not plan_content or not matrix_content:
            st.error("Vui lòng tải đủ 2 file: Nội dung bài học và Ma trận.")
        else:
            # Gom cấu hình lại để gửi cho hàm xử lý
            config_mcq = {"count": num_mcq, "point": point_mcq, "types": type_mcq}
            config_essay = {"count": num_essay, "point": point_essay}
            
            result = generate_exam_advanced(api_key, plan_content, matrix_content, config_mcq, config_essay, grade, subject)
            
            st.markdown("### 📄 KẾT QUẢ ĐỀ THI:")
            st.markdown(result)
            st.download_button("📥 Tải Đề về máy (.txt)", result, file_name=f"DeThi_{subject}_{grade}.txt")
