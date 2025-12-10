import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Ra Đề Chuẩn TT32 & TT27", page_icon="🎓", layout="wide")

# --- CSS GIAO DIỆN ---
st.markdown("""
<style>
    .header {color: #0033cc; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px;}
    .success-box {background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; border: 1px solid #c3e6cb;}
    .stSelectbox label {font-weight: bold; color: #333;}
</style>
""", unsafe_allow_html=True)

# --- 1. CÀI ĐẶT FONT CHỮ CHO FILE WORD (Times New Roman) ---
def set_font_style(doc):
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13) # Cỡ chữ 13 hoặc 14 chuẩn văn bản hành chính
    # Ép font cho toàn bộ document (xử lý sâu trong XML)
    rFonts = style.element.rPr.rFonts
    rFonts.set(qn('w:eastAsia'), 'Times New Roman')

# --- 2. HÀM TẠO FILE WORD CHUẨN FORM THÔNG TƯ ---
def create_docx_file(school_name, exam_name, student_info, content_body, answer_key):
    doc = Document()
    set_font_style(doc)
    
    # --- PHẦN 1: QUỐC HIỆU & TÊN TRƯỜNG (Table ẩn) ---
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    
    # Cột trái: Trường & Phòng
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    p_left.add_run("PHÒNG GD&ĐT ............\n").bold = False
    p_left.add_run(f"{school_name.upper()}").bold = True
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Cột phải: Quốc hiệu
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n").bold = True
    p_right.add_run("Độc lập - Tự do - Hạnh phúc").bold = True
    p_right.add_run("\n-------------------").bold = False
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() # Dòng trống

    # --- PHẦN 2: TÊN ĐỀ THI ---
    title = doc.add_paragraph()
    run_title = title.add_run(exam_name.upper())
    run_title.bold = True
    run_title.font.size = Pt(14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # --- PHẦN 3: THÔNG TIN HỌC SINH ---
    info = doc.add_paragraph()
    info.add_run("Họ và tên học sinh: ..................................................................................... ").bold = False
    info.add_run(f"Lớp: {student_info['grade']}.....")
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() 

    # --- PHẦN 4: KHUNG ĐIỂM & LỜI PHÊ (Chuẩn bài kiểm tra tiểu học) ---
    # Tạo bảng 2 dòng, 2 cột
    score_table = doc.add_table(rows=2, cols=2)
    score_table.style = 'Table Grid' # Kẻ bảng
    
    # Dòng 1
    score_table.cell(0, 0).text = "Điểm"
    score_table.cell(0, 1).text = "Lời nhận xét của giáo viên"
    # Căn giữa tiêu đề
    score_table.cell(0,0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.cell(0,1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Dòng 2 (Để trống cho HS làm bài)
    score_table.rows[1].height = Cm(2.5) # Chiều cao ô chấm điểm
    
    doc.add_paragraph() # Dòng trống ngăn cách

    # --- PHẦN 5: NỘI DUNG ĐỀ THI (Lấy từ AI) ---
    doc.add_paragraph("------------------------------------------------------------------------------------------------------")
    body_para = doc.add_paragraph(content_body)
    body_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Ngắt trang sang phần đáp án
    doc.add_page_break()
    
    # --- PHẦN 6: ĐÁP ÁN ---
    ans_title = doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN")
    ans_title.runs[0].bold = True
    ans_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(answer_key)

    # Lưu vào buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- HÀM TỰ DÒ MODEL (Tránh lỗi 404) ---
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in models: return 'gemini-1.5-flash'
        if 'models/gemini-pro' in models: return 'gemini-pro'
        return models[0].replace('models/', '') if models else 'gemini-pro'
    except:
        return 'gemini-pro'

# --- HÀM GỌI AI ---
def generate_exam_content(api_key, subject_plan, matrix_content, config, info):
    if not api_key: return None, None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())

    prompt = f"""
    Bạn là chuyên gia giáo dục tiểu học, nắm vững Thông tư 27/2020/TT-BGDĐT (Đánh giá học sinh) và Thông tư 32/2018/TT-BGDĐT (Chương trình GDPT).
    
    Nhiệm vụ: Soạn nội dung ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    
    1. CẤU TRÚC ĐỀ (Bắt buộc tuân thủ điểm số):
    - PHẦN I: TRẮC NGHIỆM ({config['mcq_count']} câu - {config['mcq_point']} điểm/câu).
      + Yêu cầu: Đa dạng (Chọn A,B,C,D; Đúng/Sai; Điền khuyết).
      + Phân bổ mức độ: Biết/Hiểu (chiếm 70%), Vận dụng (30%).
    
    - PHẦN II: TỰ LUẬN ({config['essay_count']} câu - {config['essay_point']} điểm/câu).
      + Yêu cầu: Câu hỏi mở, giải quyết vấn đề thực tiễn.
    
    2. NỘI DUNG KIẾN THỨC:
    {subject_plan}
    
    3. MA TRẬN THAM KHẢO:
    {matrix_content}
    
    YÊU CẦU OUTPUT 1 (ĐỀ BÀI):
    - Chỉ viết nội dung câu hỏi. Không viết lại phần Header (Trường, Lớp...).
    - Trình bày rõ: "PHẦN I. TRẮC NGHIỆM", "PHẦN II. TỰ LUẬN".
    - Câu hỏi rõ ràng, ngôn ngữ trong sáng phù hợp học sinh tiểu học.
    
    YÊU CẦU OUTPUT 2 (ĐÁP ÁN):
    - Tách riêng ra để tôi đưa vào trang sau.
    """
    
    # Gọi AI 2 lần (hoặc 1 lần rồi tách chuỗi) để lấy Đề và Đáp án riêng
    # Ở đây để đơn giản và nhanh, ta gọi 1 lần và nhờ AI tách bằng từ khóa
    prompt += "\n\nLƯU Ý CUỐI CÙNG: Hãy ngăn cách giữa ĐỀ BÀI và ĐÁP ÁN bằng chuỗi ký tự '###TÁCH_Ở_ĐÂY###'."

    try:
        response = model.generate_content(prompt)
        full_text = response.text
        if "###TÁCH_Ở_ĐÂY###" in full_text:
            parts = full_text.split("###TÁCH_Ở_ĐÂY###")
            return parts[0].strip(), parts[1].strip()
        else:
            return full_text, "Không tìm thấy đáp án tách biệt."
    except Exception as e:
        return f"Lỗi: {str(e)}", ""

# --- HÀM ĐỌC FILE ---
def read_input_file(uploaded_file):
    if not uploaded_file: return ""
    try:
        if uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith('.xlsx'):
            return pd.read_excel(uploaded_file).to_string()
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file).to_string()
        else:
            return uploaded_file.read().decode("utf-8")
    except: return "Lỗi đọc file."

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="header">📝 HỆ THỐNG RA ĐỀ TIỂU HỌC CHUẨN THÔNG TƯ 32/27</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Cài đặt")
    api_key = st.text_input("Nhập API Key:", type="password")
    
    st.subheader("🏫 Thông tin trường")
    school_name = st.text_input("Tên trường:", value="Trường TH Nguyễn Du")
    exam_name = st.text_input("Tên kỳ thi:", value="KIỂM TRA CUỐI HỌC KÌ I")

# --- CỘT 1: INPUT DỮ LIỆU ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. Dữ liệu nguồn")
    c1, c2 = st.columns(2)
    subject = c1.selectbox("Môn học", ["Tin học", "Công nghệ", "Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí"])
    grade = c2.selectbox("Khối lớp", ["Lớp 3", "Lớp 4", "Lớp 5"])
    
    file_plan = st.file_uploader("📂 Tải Nội dung bài học (Word/Text)", type=['docx', 'txt'])
    file_matrix = st.file_uploader("📊 Tải Ma trận đề (Excel/Word)", type=['xlsx', 'docx', 'csv'])

# --- CỘT 2: CẤU HÌNH ĐIỂM SỐ (Selectbox) ---
with col2:
    st.subheader("2. Cấu hình câu hỏi & Điểm số")
    
    st.markdown("**🅰️ PHẦN TRẮC NGHIỆM**")
    tn_col1, tn_col2 = st.columns(2)
    mcq_count = tn_col1.number_input("Số câu TN:", min_value=0, value=6)
    # Thay number_input bằng selectbox cho điểm số
    mcq_point = tn_col2.selectbox("Điểm mỗi câu TN:", [0.25, 0.5, 0.75, 1.0], index=1)
    
    st.markdown("**🅱️ PHẦN TỰ LUẬN**")
    tl_col1, tl_col2 = st.columns(2)
    essay_count = tl_col1.number_input("Số câu TL:", min_value=0, value=3)
    # Selectbox điểm tự luận
    essay_point = tl_col2.selectbox("Điểm mỗi câu TL:", [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0], index=2)
    
    # Tính tổng điểm
    total_score = (mcq_count * mcq_point) + (essay_count * essay_point)
    if total_score == 10:
        st.success(f"✅ Tổng điểm: {total_score}/10")
    else:
        st.warning(f"⚠️ Tổng điểm đang là: {total_score}. Hãy điều chỉnh lại cho đủ 10.")

# --- ACTION & DOWNLOAD ---
st.markdown("---")
if st.button("🚀 KHỞI TẠO & XUẤT FILE WORD", type="primary", use_container_width=True):
    if not api_key:
        st.error("Chưa nhập API Key.")
    elif not file_plan or not file_matrix:
        st.error("Chưa tải đủ file Nội dung và Ma trận.")
    else:
        # 1. Đọc file
        plan_text = read_input_file(file_plan)
        matrix_text = read_input_file(file_matrix)
        
        # 2. Gọi AI tạo nội dung
        with st.spinner("Đang phân tích Ma trận và soạn thảo theo chuẩn TT27..."):
            config = {
                "mcq_count": mcq_count, "mcq_point": mcq_point,
                "essay_count": essay_count, "essay_point": essay_point
            }
            info = {"subject": subject, "grade": grade}
            
            exam_body, answer_key = generate_exam_content(api_key, plan_text, matrix_text, config, info)
        
        if exam_body:
            # 3. Tạo file Word
            docx_file = create_docx_file(school_name, exam_name, info, exam_body, answer_key)
            
            # 4. Hiện nút tải về
            st.markdown("### 🎉 Đã xong! Mời tải về:")
            st.download_button(
                label="📥 Tải Đề Kiểm Tra (.docx)",
                data=docx_file,
                file_name=f"DeKiemTra_{subject}_{grade}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            # 5. Xem trước (Optional)
            with st.expander("Xem trước nội dung thô"):
                st.text(exam_body)
        else:
            st.error("Có lỗi khi tạo đề. Vui lòng thử lại.")

st.caption("Lưu ý: File Word tải về đã được căn chỉnh lề và font chữ Times New Roman theo chuẩn văn bản.")
