import streamlit as st
import google.generativeai as genai
import pandas as pd
from io import StringIO

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Tạo Đề Kiểm Tra Tiểu Học (Chuẩn TT27)", page_icon="🏫", layout="wide")

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .main-header {font-size: 26px; font-weight: bold; color: #2E86C1; text-align: center; margin-bottom: 20px;}
    .step-header {font-size: 18px; font-weight: bold; color: #E74C3C; margin-top: 10px;}
    .stDataFrame {border: 1px solid #ddd; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CẤU HÌNH ---
with st.sidebar:
    st.header("⚙️ Cài đặt hệ thống")
    api_key = st.text_input("Nhập Google API Key:", type="password")
    st.info("Lấy API Key miễn phí tại: aistudio.google.com")
    st.markdown("---")
    st.markdown("**Quy định áp dụng:**")
    st.success("✅ Thông tư 27/2020/TT-BGDĐT (Đánh giá Tiểu học)")
    st.success("✅ Chương trình GDPT 2018")

# --- HÀM XỬ LÝ AI ---
def generate_exam(api_key, subject_plan, matrix_content, question_types, grade, subject):
    if not api_key:
        return "⚠️ Vui lòng nhập API Key để tiếp tục."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Prompt chuyên sâu (System Prompt)
    prompt = f"""
    Bạn là một chuyên gia khảo thí và giáo viên tiểu học cốt cán tại Việt Nam.
    Nhiệm vụ: Soạn đề kiểm tra định kỳ môn {subject} Lớp {grade}.

    -------------------
    1. CĂN CỨ PHÁP LÝ (BẮT BUỘC TUÂN THỦ):
    - Áp dụng Thông tư 27/2020/TT-BGDĐT về đánh giá học sinh tiểu học.
    - Đảm bảo 3 mức độ nhận thức: Mức 1 (Nhận biết/Nhắc lại), Mức 2 (Kết nối/Hiểu), Mức 3 (Vận dụng/Giải quyết vấn đề).
    - Ngôn ngữ: Tiếng Việt trong sáng, phù hợp tâm lý lứa tuổi tiểu học.

    -------------------
    2. DỮ LIỆU ĐẦU VÀO:
    
    A. KẾ HOẠCH DẠY HỌC / NỘI DUNG CẦN KIỂM TRA:
    {subject_plan}

    B. MA TRẬN ĐỀ (KHUNG PHÂN BỔ CÂU HỎI VÀ ĐIỂM SỐ):
    Dưới đây là cấu trúc ma trận (dạng CSV) quy định số lượng câu hỏi cho từng chủ đề:
    {matrix_content}

    -------------------
    3. YÊU CẦU ĐẦU RA:
    Hãy tạo một đề kiểm tra chi tiết bao gồm các dạng câu hỏi sau (nếu phù hợp với Ma trận): {', '.join(question_types)}.
    
    Cấu trúc đề bài trả về:
    
    PHẦN I: TRẮC NGHIỆM KHÁCH QUAN
    (Soạn các câu hỏi trắc nghiệm, đúng/sai, nối cột... dựa theo phân bổ trong Ma trận và Nội dung dạy học. Đảm bảo số lượng câu khớp với ma trận).
    
    PHẦN II: TỰ LUẬN / THỰC HÀNH
    (Soạn câu hỏi tự luận hoặc yêu cầu thực hành nếu ma trận có yêu cầu).

    PHẦN III: ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM CHI TIẾT
    (Cung cấp đáp án chính xác và biểu điểm).

    LƯU Ý QUAN TRỌNG:
    - Chỉ lấy kiến thức nằm trong phần "Kế hoạch dạy học" đã cung cấp.
    - Bám sát số lượng câu hỏi quy định trong "Ma trận đề". Ví dụ: Ma trận ghi Chủ đề A có 1 câu Biết, 1 câu Hiểu thì phải ra đúng số lượng đó.
    """

    with st.spinner('Đang phân tích Ma trận và Kế hoạch dạy học...'):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Lỗi khi gọi AI: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">📝 HỆ THỐNG RA ĐỀ KIỂM TRA TIỂU HỌC <br>(Theo Thông tư 27 & Ma trận nhà trường)</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<p class="step-header">1. Thông tin môn học</p>', unsafe_allow_html=True)
    subject = st.selectbox("Môn học", ["Tin học", "Công nghệ", "Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí"])
    grade = st.selectbox("Khối lớp", ["Lớp 3", "Lớp 4", "Lớp 5"])
    
    st.markdown('<p class="step-header">2. Tải dữ liệu nguồn</p>', unsafe_allow_html=True)
    
    # Upload Kế hoạch dạy học
    uploaded_plan = st.file_uploader("Tải Kế hoạch/Nội dung dạy học (Text/Word)", type=['txt', 'docx'])
    plan_content = ""
    if uploaded_plan is not None:
        if uploaded_plan.name.endswith('.txt'):
            plan_content = uploaded_plan.read().decode("utf-8")
        else:
            plan_content = "Đã nhận file Word. (Tính năng đọc Word cần xử lý thêm, tạm thời coi như text rỗng hoặc bạn hãy copy nội dung dán vào file txt)." 
            # Để đơn giản demo, ta dùng text_area dự phòng bên dưới
    
    # Text area dự phòng nếu không upload file
    if not plan_content:
        plan_content = st.text_area("Hoặc dán nội dung bài học cần kiểm tra vào đây:", height=150)

    # Upload Ma trận (Hard Data của bạn)
    st.markdown("---")
    uploaded_matrix = st.file_uploader("Tải Ma trận đề (File CSV chuẩn)", type=['csv'])
    matrix_text = ""
    if uploaded_matrix is not None:
        try:
            df = pd.read_csv(uploaded_matrix)
            st.dataframe(df.head(5), height=150) # Hiển thị sơ bộ ma trận
            matrix_text = df.to_string() # Chuyển CSV thành text để AI đọc
        except Exception as e:
            st.error(f"Lỗi đọc file CSV: {e}")

    st.markdown('<p class="step-header">3. Chọn dạng câu hỏi</p>', unsafe_allow_html=True)
    q_types = st.multiselect(
        "Chọn các dạng bài muốn xuất hiện trong đề:",
        ["Trắc nghiệm 4 lựa chọn (A,B,C,D)", "Đúng / Sai", "Ghép nối (Nối cột)", "Điền khuyết", "Tự luận / Thực hành"],
        default=["Trắc nghiệm 4 lựa chọn (A,B,C,D)", "Tự luận / Thực hành"]
    )

with col2:
    st.markdown('<p class="step-header">4. Kết quả Đề kiểm tra</p>', unsafe_allow_html=True)
    
    if st.button("🚀 TẠO ĐỀ KIỂM TRA NGAY", type="primary"):
        if not plan_content:
            st.warning("⚠️ Chưa có nội dung dạy học.")
        elif not uploaded_matrix:
            st.warning("⚠️ Chưa tải file Ma trận lên (File CSV bạn cung cấp).")
        else:
            result = generate_exam(api_key, plan_content, matrix_text, q_types, grade, subject)
            st.markdown(result)
            
            # Nút tải về
            st.download_button(
                label="📥 Tải Đề về máy (.txt)",
                data=result,
                file_name=f"DeKiemTra_{subject}_{grade}.txt"
            )

# --- HƯỚNG DẪN CHÂN TRANG ---
st.markdown("---")
st.caption("© 2024 - Công cụ hỗ trợ giáo viên tiểu học. Phát triển dựa trên Streamlit & Google Gemini.")
