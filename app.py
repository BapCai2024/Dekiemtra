import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document # Thư viện xử lý Word
import io

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
    st.success("✅ Thông tư 27/2020/TT-BGDĐT")
    st.success("✅ Chương trình GDPT 2018")

# --- HÀM XỬ LÝ ĐỌC FILE MA TRẬN (EXCEL/WORD) ---
def get_matrix_content(uploaded_file):
    """Hàm đọc nội dung từ file Excel hoặc Word và chuyển thành dạng Text cho AI hiểu"""
    content_text = ""
    preview_data = None # Dùng để hiện bảng xem trước cho đẹp

    try:
        # 1. Xử lý file Excel
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
            # Chuyển toàn bộ bảng Excel thành chuỗi văn bản
            content_text = df.to_string() 
            preview_data = df.head(10) # Lấy 10 dòng đầu để xem trước

        # 2. Xử lý file Word
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            full_text = []
            # Duyệt qua tất cả các bảng trong file Word
            for table in doc.tables:
                for row in table.rows:
                    # Nối các ô trong hàng bằng dấu gạch đứng |
                    row_text = [cell.text.strip() for cell in row.cells]
                    full_text.append(" | ".join(row_text))
            
            content_text = "\n".join(full_text)
            preview_data = "Đã trích xuất dữ liệu từ bảng trong file Word."

        # 3. Xử lý file CSV (giữ lại code cũ phòng hờ)
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            content_text = df.to_string()
            preview_data = df.head(10)

    except Exception as e:
        return None, f"Lỗi đọc file: {str(e)}"

    return content_text, preview_data

# --- HÀM GỌI AI ---
def generate_exam(api_key, subject_plan, matrix_content, question_types, grade, subject):
    if not api_key:
        return "⚠️ Vui lòng nhập API Key để tiếp tục."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Bạn là chuyên gia giáo dục tiểu học. Hãy soạn đề kiểm tra môn {subject} Lớp {grade} theo chuẩn Thông tư 27.

    -------------------
    1. NỘI DUNG DẠY HỌC / KIẾN THỨC CẦN RA ĐỀ:
    {subject_plan}

    -------------------
    2. MA TRẬN ĐỀ (BẢNG PHÂN BỔ CÂU HỎI):
    Dưới đây là dữ liệu ma trận (được trích xuất từ file Excel/Word của giáo viên). 
    Hãy đọc kỹ các cột: Tên chủ đề, Số câu, Mức độ (Biết/Hiểu/Vận dụng), Điểm số.
    
    [DỮ LIỆU MA TRẬN BẮT ĐẦU]
    {matrix_content}
    [DỮ LIỆU MA TRẬN KẾT THÚC]

    -------------------
    3. YÊU CẦU:
    - Soạn đề thi gồm các dạng: {', '.join(question_types)}.
    - Tuân thủ nghiêm ngặt số lượng câu hỏi và mức độ kiến thức trong Ma trận.
    - Văn phong phù hợp học sinh tiểu học.
    
    CẤU TRÚC ĐỀ TRẢ VỀ:
    PHẦN I: TRẮC NGHIỆM (Số điểm theo ma trận)
    PHẦN II: TỰ LUẬN (Số điểm theo ma trận)
    PHẦN III: HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN (Chi tiết)
    """

    with st.spinner('Đang đọc file Ma trận và soạn đề...'):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Lỗi khi gọi AI: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-header">📝 RA ĐỀ KIỂM TRA TIỂU HỌC <br>(Hỗ trợ Excel, Word, CSV)</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<p class="step-header">1. Thông tin chung</p>', unsafe_allow_html=True)
    subject = st.selectbox("Môn học", ["Tin học", "Công nghệ", "Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí"])
    grade = st.selectbox("Khối lớp", ["Lớp 3", "Lớp 4", "Lớp 5"])
    
    st.markdown('<p class="step-header">2. Tải Ma trận (Hard Data)</p>', unsafe_allow_html=True)
    # Cập nhật cho phép tải nhiều loại file
    uploaded_matrix = st.file_uploader("Tải file Ma trận (Excel .xlsx, Word .docx)", type=['xlsx', 'xls', 'docx', 'csv'])
    
    matrix_text = ""
    if uploaded_matrix is not None:
        matrix_text, preview = get_matrix_content(uploaded_matrix)
        if matrix_text is None:
            st.error(preview) # Hiện lỗi
        else:
            st.success("✅ Đã đọc được file Ma trận!")
            if isinstance(preview, pd.DataFrame):
                st.dataframe(preview, height=150)
            else:
                st.info(preview)

    st.markdown('<p class="step-header">3. Nội dung kiến thức</p>', unsafe_allow_html=True)
    plan_content = st.text_area("Dán nội dung bài học/Yêu cầu cần đạt vào đây:", height=200, placeholder="Ví dụ: Bài 1 - Thông tin và quyết định...")

with col2:
    st.markdown('<p class="step-header">4. Cấu hình & Xuất đề</p>', unsafe_allow_html=True)
    q_types = st.multiselect(
        "Chọn dạng câu hỏi:",
        ["Trắc nghiệm ABCD", "Đúng / Sai", "Ghép nối", "Điền khuyết", "Tự luận"],
        default=["Trắc nghiệm ABCD", "Tự luận"]
    )
    
    if st.button("🚀 TẠO ĐỀ KIỂM TRA", type="primary"):
        if not plan_content:
            st.warning("⚠️ Chưa nhập nội dung kiến thức.")
        elif not uploaded_matrix:
            st.warning("⚠️ Chưa tải file Ma trận.")
        else:
            result = generate_exam(api_key, plan_content, matrix_text, q_types, grade, subject)
            st.markdown(result)
            st.download_button(label="📥 Tải Đề về máy (.txt)", data=result, file_name=f"DeKiemTra_{subject}_{grade}.txt")

st.markdown("---")
st.caption("Hệ thống hỗ trợ đọc Ma trận từ Excel và bảng trong Word.")
