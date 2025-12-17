import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import pypdf # Đã thêm vào requirements.txt

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Hỗ Trợ Ra Đề Thi Tiểu Học (TT27)",
    page_icon="✍️",
    layout="wide"
)

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .subject-card {
        padding: 15px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: #ffffff;
        text-align: center;
        margin-bottom: 10px;
    }
    .main-header { font-size: 24px; font-weight: bold; color: #2c3e50; }
    .stButton>button { width: 100%; border-radius: 5px; height: 50px; background-color: #007bff; color: white;}
</style>
""", unsafe_allow_html=True)

# --- DỮ LIỆU MÔN HỌC THEO THÔNG TƯ 27 (CHỈ CÁC MÔN CÓ ĐIỂM SỐ) ---
# Loại bỏ Tiếng Anh theo yêu cầu.
# Lớp 1, 2, 3: Chỉ Toán, Tiếng Việt (Tin học & Công nghệ bắt đầu từ lớp 3)
# Lớp 4, 5: Thêm Khoa học, Lịch sử & Địa lí.
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 2": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 3": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 4": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 5": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")]
}

# --- HÀM XỬ LÝ FILE ---
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
        else:
            return None
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return None

# --- HÀM TẠO FILE WORD (CHUẨN HÓA THEO YÊU CẦU MỚI) ---
def create_word_file(school_name, exam_name, content):
    doc = Document()
    
    # Cấu hình font chữ chung Times New Roman
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)

    # Căn lề chuẩn NĐ 30 (Trên 2, Dưới 2, Trái 3, Phải 2 cm)
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)

    # --- HEADER (Bảng 2 cột ẩn viền) ---
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(7) 
    table.columns[1].width = Cm(9)

    # Ô 1: Chỉ tên trường (Theo yêu cầu: Bỏ Phòng GD)
    cell_1 = table.cell(0, 0)
    p1 = cell_1.paragraphs[0]
    run_school = p1.add_run(f"{school_name.upper()}")
    run_school.bold = True
    run_school.font.size = Pt(12)
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Ô 2: Tên kỳ thi + Năm học để trống
    cell_2 = table.cell(0, 1)
    p2 = cell_2.paragraphs[0]
    run_exam = p2.add_run(f"{exam_name.upper()}\n")
    run_exam.bold = True
    run_exam.font.size = Pt(12)
    
    # Năm học để trống
    run_year = p2.add_run("Năm học: ..........") 
    run_year.font.size = Pt(13)
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() # Dòng trống ngăn cách

    # --- TIÊU ĐỀ NỘI DUNG ---
    title = doc.add_paragraph("ĐỀ BÀI")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.runs[0].bold = True

    # --- NỘI DUNG TỪ AI ---
    # Xử lý xuống dòng chuẩn
    for line in content.split('\n'):
        p = doc.add_paragraph(line)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Lưu vào buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- MAIN APP ---
def main():
    st.title("HỆ THỐNG RA ĐỀ THI TIỂU HỌC (TT27)")
    
    with st.sidebar:
        st.header("Cấu hình hệ thống")
        api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
        
        st.divider()
        st.header("Thông tin đầu trang")
        school_name = st.text_input("Tên trường:", value="TRƯỜNG TH NGUYỄN DU")
        exam_term = st.selectbox("Kỳ thi:", 
                               ["ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ I", 
                                "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ I", 
                                "ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ II", 
                                "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ II"])

    if not api_key:
        st.warning("⚠️ Vui lòng nhập API Key để sử dụng.")
        return

    genai.configure(api_key=api_key)

    # 1. Chọn Lớp
    st.subheader("1. Chọn Khối Lớp")
    selected_grade_key = st.radio("Chọn khối lớp:", list(SUBJECTS_DB.keys()), horizontal=True)

    # 2. Chọn Môn (Dynamic theo lớp)
    st.subheader("2. Chọn Môn Học")
    
    # Lấy danh sách môn của lớp đã chọn
    available_subjects = SUBJECTS_DB[selected_grade_key]
    
    # Tạo danh sách tên môn để hiển thị trong selectbox
    subject_names = [sub[0] for sub in available_subjects]
    selected_subject_name = st.selectbox("Môn học:", subject_names)
    
    # Tìm icon tương ứng
    selected_icon = next(icon for name, icon in available_subjects if name == selected_subject_name)

    # Hiển thị Card môn học
    st.markdown(f"""
        <div class="subject-card">
            <h1 style='margin:0'>{selected_icon}</h1>
            <h3 style='margin:0'>{selected_subject_name} - {selected_grade_key}</h3>
        </div>
    """, unsafe_allow_html=True)

    # 3. Upload Ma trận
    st.subheader("3. Dữ liệu đầu vào (Ma trận & Đặc tả)")
    st.info("Chỉ chấp nhận file ma trận. Hệ thống sẽ tạo đề bám sát file này.")
    uploaded_file = st.file_uploader("Tải lên file Ma trận/Đặc tả (.xlsx, .docx, .pdf)", type=['xlsx', 'docx', 'pdf'])

    if uploaded_file:
        file_content = read_uploaded_file(uploaded_file)
        if file_content:
            st.success("Đã đọc dữ liệu thành công!")
            
            if st.button("BẮT ĐẦU TẠO ĐỀ THI"):
                with st.spinner("Đang phân tích chương trình GDPT 2018 và tạo đề..."):
                    try:
                        # Cấu hình Model
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        # Prompt tối ưu hóa
                        prompt = f"""
                        Bạn là chuyên gia giáo dục tiểu học, am hiểu Thông tư 27/2020/TT-BGDĐT.
                        
                        NHIỆM VỤ: Soạn đề kiểm tra định kì môn {selected_subject_name} lớp {selected_grade_key}.
                        
                        YÊU CẦU BẮT BUỘC:
                        1. NGUỒN DỮ LIỆU: Chỉ sử dụng nội dung kiến thức trong văn bản người dùng cung cấp dưới đây. Tuyệt đối không lấy kiến thức bên ngoài.
                        2. CẤU TRÚC: Tuân thủ đúng cấu trúc ma trận/bảng đặc tả đã cung cấp.
                        3. HÌNH THỨC: Trình bày rõ ràng, ngôn ngữ phù hợp học sinh tiểu học.
                        
                        DỮ LIỆU MA TRẬN/ĐẶC TẢ ĐẦU VÀO:
                        ---
                        {file_content}
                        ---
                        
                        Hãy viết nội dung đề thi (không cần đáp án chi tiết, chỉ cần đề bài):
                        """
                        
                        response = model.generate_content(prompt)
                        exam_text = response.text
                        
                        st.markdown("---")
                        st.subheader("Kết quả từ AI:")
                        st.write(exam_text)
                        
                        # Tạo file Word để tải về
                        docx_buffer = create_word_file(school_name, exam_term, exam_text)
                        
                        st.download_button(
                            label="📥 TẢI VỀ FILE WORD (.DOCX)",
                            data=docx_buffer,
                            file_name=f"De_Kiem_Tra_{selected_subject_name}_{selected_grade_key}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary"
                        )
                        
                    except Exception as e:
                        st.error(f"Lỗi xử lý: {e}")

if __name__ == "__main__":
    main()
