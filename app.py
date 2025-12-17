import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import pypdf

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Hệ Thống Ra Đề Thi Tiểu Học AI",
    page_icon="🏫",
    layout="wide"
)

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .subject-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        text-align: center;
        cursor: pointer;
        margin-bottom: 10px;
        transition: 0.3s;
    }
    .subject-card:hover {
        background-color: #dbe0e8;
        transform: scale(1.02);
    }
    .big-icon { font-size: 50px; }
    .stButton>button { width: 100%; border-radius: 5px; height: 50px; }
</style>
""", unsafe_allow_html=True)

# --- KHỞI TẠO DỮ LIỆU ---
GRADES = ["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]

# Loại bỏ môn Tiếng Anh theo yêu cầu
SUBJECTS_INFO = {
    "Tiếng Việt": "📚",
    "Toán": "🧮",
    "Tự nhiên & Xã hội": "🌱",
    "Khoa học": "🔬",
    "Lịch sử & Địa lí": "🌏",
    "Tin học": "💻",
    "Công nghệ": "🔧",
    "Đạo đức": "heart"
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

# --- HÀM TẠO FILE WORD (CHUẨN NĐ 30, BỎ QUỐC NGỮ) ---
def create_word_file(school_name, exam_name, content):
    doc = Document()
    
    # Cấu hình font chữ chung (Times New Roman)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)

    # Căn lề chuẩn (Trên 2, Dưới 2, Trái 3, Phải 2 cm)
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(2)

    # --- TẠO HEADER (BẢNG 2 CỘT) ---
    # Cột 1: Tên cơ quan/trường - Cột 2: Tên đề thi
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    # Set độ rộng cột (tương đối)
    table.columns[0].width = Cm(7) 
    table.columns[1].width = Cm(9)

    # Ô 1: Tên trường
    cell_1 = table.cell(0, 0)
    p1 = cell_1.paragraphs[0]
    # Dòng 1: Phòng GD (giả định hoặc user nhập thêm nếu cần)
    run1 = p1.add_run(f"PHÒNG GD&ĐT..............\n")
    run1.font.name = 'Times New Roman'
    run1.font.size = Pt(12)
    # Dòng 2: Tên trường (Đậm)
    run2 = p1.add_run(f"{school_name.upper()}")
    run2.bold = True
    run2.font.name = 'Times New Roman'
    run2.font.size = Pt(12)
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Ô 2: Tên kỳ thi
    cell_2 = table.cell(0, 1)
    p2 = cell_2.paragraphs[0]
    run3 = p2.add_run(f"{exam_name.upper()}\n")
    run3.bold = True
    run3.font.name = 'Times New Roman'
    run3.font.size = Pt(12)
    
    run4 = p2.add_run("Năm học: 2024 - 2025") # Có thể dynamic hóa
    run4.font.name = 'Times New Roman'
    run4.font.size = Pt(13)
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() # Khoảng trắng

    # --- NỘI DUNG ĐỀ THI ---
    # Tên bài thi giữa trang
    title = doc.add_paragraph("NỘI DUNG ĐỀ THI")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.runs[0].bold = True

    # Nội dung từ AI
    body_para = doc.add_paragraph(content)
    body_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Lưu vào buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- GIAO DIỆN CHÍNH ---
def main():
    st.title("🤖 HỆ THỐNG RA ĐỀ THI TIỂU HỌC (AI POWERED)")
    st.caption("Tuân thủ GDPT 2018 & Thông tư 27 | Nguồn dữ liệu nội bộ")

    # Sidebar: Cấu hình API và Trường
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        api_key = st.text_input("Nhập Google Gemini API Key:", type="password")
        school_name = st.text_input("Tên trường:", value="TRƯỜNG TH NGUYỄN DU")
        exam_term = st.selectbox("Kỳ thi:", ["ĐỀ THI GIỮA HỌC KÌ I", "ĐỀ THI CUỐI HỌC KÌ I", "ĐỀ THI GIỮA HỌC KÌ II", "ĐỀ THI CUỐI HỌC KÌ II"])
        
        st.info("💡 Lưu ý: Hệ thống chỉ sử dụng dữ liệu từ ma trận bạn tải lên và kiến thức chuẩn GDPT 2018.")

    if not api_key:
        st.warning("Vui lòng nhập API Key để bắt đầu.")
        return

    genai.configure(api_key=api_key)

    # Layout chọn Lớp và Môn
    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("1. Chọn Khối Lớp")
        selected_grade = st.radio("Lớp:", GRADES)

    with col2:
        st.subheader("2. Chọn Môn Học")
        # Hiển thị dạng lưới các môn học
        cols = st.columns(4)
        selected_subject = None
        
        # Tạo giao diện chọn môn bằng radio button nhưng ẩn đi, dùng card hiển thị
        # Ở đây dùng selectbox cho đơn giản và hiệu quả
        selected_subject = st.selectbox("Danh sách môn học:", list(SUBJECTS_INFO.keys()))
        
        # Hiển thị icon minh họa cho môn đã chọn
        st.markdown(f"""
            <div class="subject-card">
                <div class="big-icon">{SUBJECTS_INFO[selected_subject]}</div>
                <h3>{selected_subject} - {selected_grade}</h3>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Upload Ma trận
    st.subheader("3. Upload Ma trận & Bảng đặc tả")
    st.markdown("*Hỗ trợ file: Excel (.xlsx), Word (.docx), PDF (.pdf)*")
    uploaded_file = st.file_uploader("Kéo thả file vào đây", type=['xlsx', 'docx', 'pdf'])

    if uploaded_file and selected_subject:
        file_content = read_uploaded_file(uploaded_file)
        
        if file_content:
            st.success("✅ Đã đọc xong nội dung file ma trận!")
            
            with st.expander("Xem nội dung ma trận đã đọc"):
                st.text(file_content[:1000] + "...") # Hiển thị 1 phần

            if st.button("🚀 TẠO ĐỀ THI NGAY", type="primary"):
                with st.spinner("AI đang phân tích chương trình GDPT 2018 và tạo đề..."):
                    try:
                        # --- PROMPT ENGINEERING (QUAN TRỌNG) ---
                        model = genai.GenerativeModel('gemini-1.5-flash') # Hoặc pro
                        
                        prompt = f"""
                        Đóng vai trò là một chuyên gia giáo dục tiểu học Việt Nam, cực kỳ am hiểu chương trình GDPT 2018 và Thông tư 27/2020/TT-BGDĐT.
                        
                        NHIỆM VỤ:
                        Soạn một đề thi môn {selected_subject} cho {selected_grade}.
                        
                        NGUỒN DỮ LIỆU BẮT BUỘC:
                        1. Chỉ dựa vào nội dung trong văn bản Ma trận/Bảng đặc tả tôi cung cấp dưới đây.
                        2. Kiến thức phải chuẩn xác theo sách giáo khoa tiểu học hiện hành tại Việt Nam.
                        3. Tuyệt đối KHÔNG lấy kiến thức ngoài chương trình, KHÔNG sáng tạo vượt quá yêu cầu cần đạt.
                        
                        NỘI DUNG MA TRẬN/BẢNG ĐẶC TẢ:
                        ---
                        {file_content}
                        ---
                        
                        YÊU CẦU ĐẦU RA:
                        - Trình bày rõ ràng: Phần trắc nghiệm (nếu có) và Phần tự luận.
                        - Ngôn ngữ: Tiếng Việt chuẩn mực, phù hợp tâm lý lứa tuổi {selected_grade}.
                        - Câu hỏi phải bám sát mức độ nhận thức (Biết, Hiểu, Vận dụng) như trong ma trận.
                        - Không bao gồm lời giải chi tiết, chỉ cần đề thi.
                        """

                        response = model.generate_content(prompt)
                        exam_content = response.text

                        # Hiển thị kết quả
                        st.markdown("### 📄 Đề thi demo:")
                        st.write(exam_content)

                        # Tạo file Word để tải xuống
                        docx_file = create_word_file(school_name, exam_term, exam_content)

                        st.download_button(
                            label="📥 Tải xuống Đề thi (.docx)",
                            data=docx_file,
                            file_name=f"De_Thi_{selected_subject}_{selected_grade}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                    except Exception as e:
                        st.error(f"Lỗi khi gọi AI: {e}. Vui lòng kiểm tra API Key hoặc Quota.")

if __name__ == "__main__":
    main()
