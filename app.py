import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🎓", layout="wide")

# --- CSS GIAO DIỆN ---
st.markdown("""
<style>
    .header {color: #d63031; font-size: 28px; font-weight: bold; text-align: center; margin-bottom: 20px; text-transform: uppercase;}
    .sub-header {color: #0984e3; font-weight: bold; margin-top: 10px; border-bottom: 2px solid #dfe6e9; padding-bottom: 5px;}
    .author-footer {text-align: center; font-style: italic; color: #636e72; margin-top: 50px; font-size: 14px;}
    .stSelectbox label, .stNumberInput label {font-weight: bold; color: #2d3436;}
</style>
""", unsafe_allow_html=True)

# --- 1. CÀI ĐẶT FONT CHỮ CHO FILE WORD (Times New Roman) ---
def set_font_style(doc):
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    rFonts = style.element.rPr.rFonts
    rFonts.set(qn('w:eastAsia'), 'Times New Roman')

# --- 2. HÀM TẠO FILE WORD CHUẨN FORM ---
def create_docx_file(school_name, exam_name, student_info, content_body, answer_key):
    doc = Document()
    set_font_style(doc)
    
    # Header: Phòng GD & Trường
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    p_left.add_run("PHÒNG GD&ĐT ............\n").bold = False
    p_left.add_run(f"{school_name.upper()}").bold = True
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n").bold = True
    p_right.add_run("Độc lập - Tự do - Hạnh phúc").bold = True
    p_right.add_run("\n-------------------").bold = False
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() 

    # Tên đề thi
    title = doc.add_paragraph()
    run_title = title.add_run(exam_name.upper())
    run_title.bold = True
    run_title.font.size = Pt(14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Thông tin HS
    info = doc.add_paragraph()
    info.add_run("Họ và tên học sinh: ..................................................................................... ").bold = False
    info.add_run(f"Lớp: {student_info['grade']}.....")
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() 

    # Khung điểm
    score_table = doc.add_table(rows=2, cols=2)
    score_table.style = 'Table Grid'
    score_table.cell(0, 0).text = "Điểm"
    score_table.cell(0, 1).text = "Lời nhận xét của giáo viên"
    score_table.cell(0,0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.cell(0,1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.rows[1].height = Cm(2.5)
    
    doc.add_paragraph() 

    # Nội dung đề
    doc.add_paragraph("------------------------------------------------------------------------------------------------------")
    body_para = doc.add_paragraph(content_body)
    body_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    doc.add_page_break()
    
    # Đáp án
    ans_title = doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN")
    ans_title.runs[0].bold = True
    ans_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(answer_key)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. HÀM TỰ DÒ MODEL ---
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in models: return 'gemini-1.5-flash'
        if 'models/gemini-pro' in models: return 'gemini-pro'
        return models[0].replace('models/', '') if models else 'gemini-pro'
    except:
        return 'gemini-pro'

# --- 4. HÀM GỌI AI ---
def generate_exam_content(api_key, subject_plan, matrix_content, config, info):
    if not api_key: return None, None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())

    prompt = f"""
    Bạn là chuyên gia giáo dục tiểu học. Hãy soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    Tuân thủ nghiêm ngặt Thông tư 27 (Đánh giá) và Thông tư 32.
    
    1. CẤU TRÚC ĐỀ (BẮT BUỘC):
    
    A. PHẦN I: TRẮC NGHIỆM (Tổng {config['total_mcq']} câu - {config['mcq_point']} điểm/câu).
       Phân bổ chi tiết các dạng sau:
       - Dạng nhiều lựa chọn (A,B,C,D): {config['q_abcd']} câu.
       - Dạng Đúng / Sai: {config['q_tf']} câu.
       - Dạng Điền khuyết (Điền từ vào chỗ trống): {config['q_fill']} câu.
       - Dạng Ghép nối (Nối cột A với cột B): {config['q_match']} câu.
       
       *Yêu cầu*: Phân bổ mức độ Biết/Hiểu (70%), Vận dụng (30%).
    
    B. PHẦN II: TỰ LUẬN ({config['essay_count']} câu - {config['essay_point']} điểm/câu).
       *Yêu cầu*: Câu hỏi mở, giải quyết vấn đề thực tiễn.
    
    2. NỘI DUNG KIẾN THỨC (Căn cứ vào đây):
    {subject_plan}
    
    3. MA TRẬN (Tham khảo):
    {matrix_content}
    
    YÊU CẦU OUTPUT:
    - Trình bày rõ ràng, không viết lại phần thông tin trường lớp.
    - Cuối cùng phải có phần ĐÁP ÁN tách biệt bởi chuỗi: ###TÁCH_Ở_ĐÂY###
    """
    
    try:
        response = model.generate_content(prompt)
        full_text = response.text
        if "###TÁCH_Ở_ĐÂY###" in full_text:
            parts = full_text.split("###TÁCH_Ở_ĐÂY###")
            return parts[0].strip(), parts[1].strip()
        else:
            return full_text, "Không tìm thấy đáp án tách biệt."
    except Exception as e:
        return f"Lỗi AI: {str(e)}", ""

# --- 5. HÀM ĐỌC FILE ---
def read_input_file(uploaded_file):
    if not uploaded_file: return ""
    try:
        if uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file).to_string()
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file).to_string()
        else:
            return uploaded_file.read().decode("utf-8")
    except: return "Lỗi đọc file."

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="header">HỆ THỐNG HỖ TRỢ RA ĐỀ TIỂU HỌC</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Cài đặt chung")
    api_key = st.text_input("Nhập API Key Google:", type="password")
    st.info("Hệ thống tự động sử dụng model AI tốt nhất hiện có.")
    
    st.markdown("---")
    st.subheader("🏫 Thông tin hiển thị")
    school_name = st.text_input("Tên trường:", value="Trường TH Nguyễn Du")
    exam_name = st.text_input("Tên kỳ thi:", value="KIỂM TRA CUỐI HỌC KÌ I")

col1, col2 = st.columns([1, 1.2])

# --- CỘT 1: INPUT DỮ LIỆU ---
with col1:
    st.markdown('<div class="sub-header">1. Dữ liệu đầu vào</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    subject = c1.selectbox("Môn học", ["Tin học", "Công nghệ", "Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí"])
    grade = c2.selectbox("Khối lớp", ["Lớp 3", "Lớp 4", "Lớp 5"])
    
    st.caption("Tải dữ liệu để AI học (Word, Excel, Text)")
    file_plan = st.file_uploader("📂 Nội dung bài học / KH Dạy học", type=['docx', 'txt'])
    file_matrix = st.file_uploader("📊 Ma trận đề kiểm tra", type=['xlsx', 'docx', 'csv'])

# --- CỘT 2: CẤU HÌNH CHI TIẾT ---
with col2:
    st.markdown('<div class="sub-header">2. Cấu hình câu hỏi</div>', unsafe_allow_html=True)
    
    # --- CẤU HÌNH TRẮC NGHIỆM CHI TIẾT ---
    st.markdown("##### 🅰️ PHẦN TRẮC NGHIỆM")
    
    mcq_point = st.selectbox("Điểm mỗi câu TN:", [0.25, 0.5, 0.75, 1.0], index=1)
    
    t1, t2 = st.columns(2)
    with t1:
        q_abcd = st.number_input("Số câu Nhiều lựa chọn (ABCD):", min_value=0, value=4)
        q_tf = st.number_input("Số câu Đúng / Sai:", min_value=0, value=1)
    with t2:
        q_fill = st.number_input("Số câu Điền khuyết:", min_value=0, value=1)
        q_match = st.number_input("Số câu Ghép nối:", min_value=0, value=0)
    
    total_mcq = q_abcd + q_tf + q_fill + q_match
    st.info(f"👉 Tổng số câu Trắc nghiệm: **{total_mcq} câu**")

    # --- CẤU HÌNH TỰ LUẬN ---
    st.markdown("---")
    st.markdown("##### 🅱️ PHẦN TỰ LUẬN")
    
    l1, l2 = st.columns(2)
    with l1:
        essay_count = st.number_input("Số câu Tự luận:", min_value=0, value=2)
    with l2:
        essay_point = st.selectbox("Điểm mỗi câu TL:", [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0], index=2)

    # --- TÍNH TỔNG ĐIỂM ---
    total_score = (total_mcq * mcq_point) + (essay_count * essay_point)
    
    if total_score == 10:
        st.success(f"✅ TỔNG ĐIỂM TOÀN BÀI: {total_score} điểm")
    else:
        st.warning(f"⚠️ Tổng điểm hiện tại: {total_score}. Hãy điều chỉnh số câu hoặc điểm số để tròn 10.")

# --- NÚT TẠO ĐỀ ---
st.markdown("---")
if st.button("🚀 KHỞI TẠO ĐỀ & XUẤT FILE WORD", type="primary", use_container_width=True):
    if not api_key:
        st.error("Vui lòng nhập API Key trước.")
    elif not file_plan or not file_matrix:
        st.error("Vui lòng tải đủ file Nội dung và Ma trận.")
    else:
        plan_text = read_input_file(file_plan)
        matrix_text = read_input_file(file_matrix)
        
        with st.spinner("Đang phân tích dữ liệu và soạn đề theo cấu trúc yêu cầu..."):
            # Đóng gói cấu hình gửi cho AI
            config = {
                "total_mcq": total_mcq,
                "mcq_point": mcq_point,
                "q_abcd": q_abcd,
                "q_tf": q_tf,
                "q_fill": q_fill,
                "q_match": q_match,
                "essay_count": essay_count,
                "essay_point": essay_point
            }
            info = {"subject": subject, "grade": grade}
            
            exam_body, answer_key = generate_exam_content(api_key, plan_text, matrix_text, config, info)
            
            if exam_body:
                docx_file = create_docx_file(school_name, exam_name, info, exam_body, answer_key)
                
                st.markdown("### 🎉 Kết quả:")
                st.download_button(
                    label="📥 Tải Đề Kiểm Tra về máy (.docx)",
                    data=docx_file,
                    file_name=f"DeKiemTra_{subject}_{grade}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            else:
                st.error("Có lỗi xảy ra trong quá trình tạo đề.")

# --- FOOTER ---
st.markdown('<div class="author-footer">Lưu ý: Nội dung đề kiểm tra dựa trên Thông tư 27, Thông tư 32 và Chương trình môn học.<br>Tác giả: <b>BapCai</b></div>', unsafe_allow_html=True)
