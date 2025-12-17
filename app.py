import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import time

# --- XỬ LÝ LỖI THIẾU THƯ VIỆN ---
try:
    import pypdf
except ImportError:
    st.error("⚠️ Thiếu thư viện 'pypdf'. Nếu chạy Local hãy gõ: pip install pypdf. Nếu chạy Cloud hãy thêm pypdf vào requirements.txt")
    st.stop()

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Ra Đề Thi (TT27) - Auto Fix", page_icon="🏫", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .subject-card { padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9; text-align: center; margin-bottom: 10px; }
    .stTextArea textarea { font-family: 'Times New Roman'; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# --- DỮ LIỆU MÔN HỌC (TT27 - KHÔNG TIẾNG ANH) ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 2": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 3": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 4": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 5": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")]
}

# --- HÀM THỬ MODEL (AUTO FIX LỖI 404) ---
def generate_content_safe(api_key, prompt):
    genai.configure(api_key=api_key)
    
    # Danh sách model sẽ thử lần lượt. Nếu cái đầu lỗi sẽ thử cái sau.
    # gemini-1.5-flash: Nhanh, mới.
    # gemini-pro: Cũ hơn nhưng cực kỳ ổn định, ít lỗi vặt.
    models_to_try = ["gemini-1.5-flash", "gemini-pro", "gemini-1.5-pro"]
    
    last_error = None
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text, model_name # Trả về nội dung và tên model đã dùng thành công
        except Exception as e:
            last_error = e
            continue # Thử model tiếp theo
            
    # Nếu thử hết mà vẫn lỗi
    raise last_error

# --- HÀM XỬ LÝ FILE ĐẦU VÀO ---
def read_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            return df.to_string()
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        return None
    except Exception:
        return None

# --- HÀM TẠO FILE WORD ---
def create_word_file(school_name, exam_name, content):
    doc = Document()
    
    # Font Times New Roman
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)

    # Margin chuẩn NĐ 30
    for section in doc.sections:
        section.top_margin = Cm(2); section.bottom_margin = Cm(2)
        section.left_margin = Cm(3); section.right_margin = Cm(2)

    # Header 2 cột
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(7); table.columns[1].width = Cm(9)

    # Cột 1: Tên Trường (Bỏ PGD)
    cell_1 = table.cell(0, 0)
    p1 = cell_1.paragraphs[0]
    run_s = p1.add_run(f"{school_name.upper()}")
    run_s.bold = True
    run_s.font.size = Pt(12)
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Cột 2: Tên Kỳ Thi + Năm học trống
    cell_2 = table.cell(0, 1)
    p2 = cell_2.paragraphs[0]
    run_e = p2.add_run(f"{exam_name.upper()}\n")
    run_e.bold = True
    run_e.font.size = Pt(12)
    run_y = p2.add_run("Năm học: ..........")
    run_y.font.size = Pt(13)
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() # Dòng trống

    # Nội dung
    for line in content.split('\n'):
        if line.strip():
            p = doc.add_paragraph(line)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- MAIN ---
def main():
    st.title("🛠️ HỆ THỐNG RA ĐỀ THI (AUTO-FIX)")
    
    if 'exam_result' not in st.session_state:
        st.session_state.exam_result = ""

    with st.sidebar:
        st.header("1. Cấu hình")
        api_key = st.text_input("Nhập API Key:", type="password")
        st.divider()
        school_name = st.text_input("Tên trường:", value="TRƯỜNG TH NGUYỄN DU")
        exam_term = st.selectbox("Kỳ thi:", 
             ["ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ I", "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ I",
              "ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ II", "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ II"])

    if not api_key:
        st.warning("Vui lòng nhập API Key."); return

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("2. Chọn Lớp")
        grade = st.radio("Khối:", list(SUBJECTS_DB.keys()))
    with col2:
        st.subheader("3. Chọn Môn")
        subjects = SUBJECTS_DB[grade]
        sub_name = st.selectbox("Môn học:", [s[0] for s in subjects])
        icon = next(i for n, i in subjects if n == sub_name)
        st.markdown(f"<div class='subject-card'><h3>{icon} {sub_name}</h3></div>", unsafe_allow_html=True)

    st.subheader("4. Upload Ma trận (Bắt buộc)")
    uploaded = st.file_uploader("Chọn file (.xlsx, .docx, .pdf)", type=['xlsx', 'docx', 'pdf'])

    if uploaded:
        if st.button("🚀 TẠO ĐỀ THI (AUTO FIX)", type="primary"):
            content = read_uploaded_file(uploaded)
            if content:
                with st.spinner("Đang kết nối AI và tự động xử lý lỗi nếu có..."):
                    try:
                        prompt = f"""
                        Vai trò: Giáo viên tiểu học Việt Nam.
                        Nhiệm vụ: Soạn đề thi môn {sub_name} lớp {grade}.
                        Yêu cầu:
                        1. Chỉ dùng dữ liệu từ văn bản cung cấp dưới đây.
                        2. Không bịa đặt kiến thức ngoài.
                        3. Cấu trúc: Phần I. Trắc nghiệm (nếu ma trận có), Phần II. Tự luận.
                        Dữ liệu:
                        {content}
                        """
                        # GỌI HÀM AN TOÀN
                        result_text, used_model = generate_content_safe(api_key, prompt)
                        st.session_state.exam_result = result_text
                        st.success(f"✅ Đã tạo xong! (Sử dụng model: {used_model})")
                        
                    except Exception as e:
                        st.error(f"Vẫn gặp lỗi nghiêm trọng: {e}. Vui lòng kiểm tra lại API Key.")

    # KHUNG SỬA VÀ TẢI
    if st.session_state.exam_result:
        st.markdown("---")
        st.subheader("📝 Xem và Sửa nội dung")
        edited_text = st.text_area("Sửa trực tiếp tại đây:", value=st.session_state.exam_result, height=500)
        st.session_state.exam_result = edited_text # Cập nhật

        docx = create_word_file(school_name, exam_term, edited_text)
        st.download_button(
            "📥 TẢI VỀ FILE WORD (.DOCX)", 
            docx, 
            file_name=f"De_{sub_name}_{grade}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )

if __name__ == "__main__":
    main()
