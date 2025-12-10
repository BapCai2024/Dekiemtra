import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
import io

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Ra Đề Tiểu Học (Theo Mức Độ)", page_icon="📝", layout="wide")

# --- CSS TÙY CHỈNH GIAO DIỆN ---
st.markdown("""
<style>
    .main-header {font-size: 22px; font-weight: bold; color: #004085; text-align: center; margin-bottom: 20px;}
    .sub-header {font-size: 16px; font-weight: bold; color: #c82333; margin-top: 10px; border-bottom: 2px solid #ddd; padding-bottom: 5px;}
    .level-label {font-weight: bold; color: #333;}
    .score-display {font-size: 18px; font-weight: bold; color: #28a745; text-align: center; background: #e8f5e9; padding: 10px; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("🔑 Cài đặt")
    api_key = st.text_input("Dán Google API Key vào đây:", type="password")
    st.info("Hướng dẫn: Vào aistudio.google.com -> Get API Key -> Create -> Copy và dán vào đây.")
    st.markdown("---")
    st.warning("Lưu ý: Tổng điểm toàn bài nên là 10.")

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

# --- HÀM GỌI AI ---
def generate_exam_levels(api_key, subject_plan, matrix_content, levels_config, grade, subject):
    if not api_key:
        return "⚠️ Vui lòng nhập API Key trước."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # Trích xuất cấu hình để đưa vào prompt
    mcq = levels_config['mcq']
    essay = levels_config['essay']
    
    prompt = f"""
    Đóng vai Giáo viên cốt cán môn {subject} Tiểu học. Hãy soạn ĐỀ KIỂM TRA LỚP {grade}.
    
    =========================================
    1. CẤU TRÚC ĐỀ BẮT BUỘC (PHÂN HÓA THEO MỨC ĐỘ NHẬN THỨC):
    
    A. PHẦN TRẮC NGHIỆM (Điểm mỗi câu: {mcq['point']}):
    - Mức 1 (Nhận biết): {mcq['L1']} câu.
    - Mức 2 (Thông hiểu): {mcq['L2']} câu.
    - Mức 3 (Vận dụng): {mcq['L3']} câu.
    => Tổng số câu TN: {mcq['L1'] + mcq['L2'] + mcq['L3']} câu.
    
    B. PHẦN TỰ LUẬN (Điểm mỗi câu: {essay['point']}):
    - Mức 1 (Nhận biết): {essay['L1']} câu.
    - Mức 2 (Thông hiểu): {essay['L2']} câu.
    - Mức 3 (Vận dụng): {essay['L3']} câu.
    => Tổng số câu TL: {essay['L1'] + essay['L2'] + essay['L3']} câu.
    
    *Lưu ý: Nếu mức độ nào là 0 câu thì không soạn.*
    
    =========================================
    2. NỘI DUNG KIẾN THỨC CẦN KIỂM TRA (Dựa vào file giáo viên cung cấp):
    {subject_plan}

    =========================================
    3. THAM KHẢO MA TRẬN CHI TIẾT (Để lấy chủ đề tương ứng):
    {matrix_content}

    =========================================
    4. YÊU CẦU ĐẦU RA:
    - Trình bày đề thi rõ ràng.
    - Có phần II: ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM (Ghi rõ mỗi câu thuộc mức độ nào bên cạnh đáp án).
    - Ngôn ngữ phù hợp học sinh Lớp {grade}.
    """

    with st.spinner('Đang phân tích mức độ kiến thức và soạn đề...'):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Lỗi AI: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">📝 HỆ THỐNG RA ĐỀ THEO MA TRẬN & MỨC ĐỘ NHẬN THỨC</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.2])

# === CỘT TRÁI: ĐẦU VÀO ===
with col_left:
    st.markdown('<div class="sub-header">1. Dữ liệu nguồn</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: subject = st.selectbox("Môn học", ["Tin học", "Công nghệ", "Toán", "Tiếng Việt", "Khoa học", "LS&ĐL"])
    with c2: grade = st.selectbox("Khối lớp", ["Lớp 3", "Lớp 4", "Lớp 5"])
    
    st.write("📂 **Kế hoạch bài dạy (Nội dung):**")
    file_plan = st.file_uploader("Tải file Word/Text bài học", type=['docx', 'txt'], key="plan")
    plan_text = read_file_content(file_plan) if file_plan else ""
    if plan_text: st.success("✅ Đã nhận nội dung.")

    st.write("📊 **Ma trận đề (Tham khảo chủ đề):**")
    file_matrix = st.file_uploader("Tải file Ma trận (Excel/Word/CSV)", type=['xlsx', 'docx', 'csv'], key="matrix")
    matrix_text = read_file_content(file_matrix) if file_matrix else ""
    if matrix_text: st.success("✅ Đã nhận ma trận.")

# === CỘT PHẢI: CẤU HÌNH MỨC ĐỘ ===
with col_right:
    st.markdown('<div class="sub-header">2. Cấu hình số lượng câu hỏi</div>', unsafe_allow_html=True)
    
    # --- Cấu hình Trắc Nghiệm ---
    st.markdown("##### 🅰️ Phần Trắc Nghiệm")
    col_tn_pt, col_tn1, col_tn2, col_tn3 = st.columns([1.5, 1, 1, 1])
    with col_tn_pt:
        mcq_point = st.number_input("Điểm/câu TN:", 0.1, 2.0, 0.5, step=0.1)
    with col_tn1:
        mcq_l1 = st.number_input("Mức 1 (Biết)", 0, 10, 4, key="m1")
    with col_tn2:
        mcq_l2 = st.number_input("Mức 2 (Hiểu)", 0, 10, 3, key="m2")
    with col_tn3:
        mcq_l3 = st.number_input("Mức 3 (Vận dụng)", 0, 10, 1, key="m3")
    
    # --- Cấu hình Tự Luận ---
    st.markdown("##### 🅱️ Phần Tự Luận")
    col_tl_pt, col_tl1, col_tl2, col_tl3 = st.columns([1.5, 1, 1, 1])
    with col_tl_pt:
        essay_point = st.number_input("Điểm/câu TL:", 0.5, 5.0, 1.0, step=0.5)
    with col_tl1:
        essay_l1 = st.number_input("Mức 1 (Biết)", 0, 5, 0, key="e1")
    with col_tl2:
        essay_l2 = st.number_input("Mức 2 (Hiểu)", 0, 5, 1, key="e2")
    with col_tl3:
        essay_l3 = st.number_input("Mức 3 (Vận dụng)", 0, 5, 1, key="e3")

    # --- Tính toán tổng điểm ---
    total_mcq_count = mcq_l1 + mcq_l2 + mcq_l3
    total_essay_count = essay_l1 + essay_l2 + essay_l3
    total_score = (total_mcq_count * mcq_point) + (total_essay_count * essay_point)
    
    st.markdown(f"""
    <div class="score-display">
        Tổng số câu: {total_mcq_count} TN + {total_essay_count} TL<br>
        TỔNG ĐIỂM DỰ KIẾN: {total_score} ĐIỂM
    </div>
    """, unsafe_allow_html=True)
    
    if total_score != 10:
        st.warning("⚠️ Tổng điểm đang khác 10. Hãy điều chỉnh số lượng câu hoặc điểm số.")

    # --- Nút tạo đề ---
    st.markdown("---")
    if st.button("🚀 TẠO ĐỀ NGAY", type="primary", use_container_width=True):
        if not plan_text or not matrix_text:
            st.error("Vui lòng tải đủ 2 file: Nội dung và Ma trận.")
        else:
            # Gom cấu hình
            levels_config = {
                "mcq": {"point": mcq_point, "L1": mcq_l1, "L2": mcq_l2, "L3": mcq_l3},
                "essay": {"point": essay_point, "L1": essay_l1, "L2": essay_l2, "L3": essay_l3}
            }
            
            result = generate_exam_levels(api_key, plan_text, matrix_text, levels_config, grade, subject)
            
            st.markdown("### 📄 KẾT QUẢ:")
            st.markdown(result)
            st.download_button("📥 Tải Đề về máy (.txt)", result, file_name=f"DeThi_{subject}_{grade}.txt")
