import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import pypdf # Thư viện đọc PDF

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🏫", layout="wide")

# --- CSS GIAO DIỆN ---
st.markdown("""
<style>
    .header {color: #d63031; font-size: 28px; font-weight: bold; text-align: center; margin-bottom: 20px; text-transform: uppercase; font-family: 'Times New Roman', serif;}
    .sub-header {color: #0984e3; font-weight: bold; margin-top: 15px; border-bottom: 2px solid #dfe6e9; padding-bottom: 5px;}
    .author-footer {text-align: center; font-style: italic; color: #636e72; margin-top: 50px; font-size: 14px; border-top: 1px solid #ddd; padding-top: 10px;}
    .guide-box {background-color: #f1f2f6; padding: 15px; border-radius: 8px; border: 1px solid #ced6e0; font-size: 14px;}
    .level-label {font-size: 13px; color: #2d3436; font-weight: bold;}
    .stSelectbox label, .stNumberInput label {font-weight: bold; color: #2d3436;}
</style>
""", unsafe_allow_html=True)

# --- 1. HÀM TẠO FILE WORD CHUẨN FORM ---
def set_font_style(doc):
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    rFonts = style.element.rPr.rFonts
    rFonts.set(qn('w:eastAsia'), 'Times New Roman')

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

# --- 2. HÀM TỰ DÒ MODEL ---
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in models: return 'gemini-1.5-flash'
        if 'models/gemini-pro' in models: return 'gemini-pro'
        return models[0].replace('models/', '') if models else 'gemini-pro'
    except:
        return 'gemini-pro'

# --- 3. HÀM GỌI AI (NÂNG CẤP MỨC ĐỘ) ---
def generate_exam_content(api_key, subject_plan, matrix_content, config, info):
    if not api_key: return None, None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())

    prompt = f"""
    Bạn là chuyên gia giáo dục tiểu học (Việt Nam). Hãy soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    Yêu cầu tuyệt đối tuân thủ Thông tư 27 (Đánh giá năng lực) và Thông tư 32.
    
    PHẦN 1: CẤU TRÚC ĐỀ BẮT BUỘC:
    
    A. PHẦN TRẮC NGHIỆM ({config['mcq_total']} câu - {config['mcq_point']} điểm/câu):
       1. Phân bổ theo mức độ nhận thức:
          - Mức 1 (Biết/Nhận biết): {config['mcq_lv1']} câu.
          - Mức 2 (Hiểu/Thông hiểu): {config['mcq_lv2']} câu.
          - Mức 3 (Vận dụng): {config['mcq_lv3']} câu.
       
       2. Phân bổ theo dạng câu hỏi (Hãy cố gắng lồng ghép các dạng này vào các mức độ trên):
          - Nhiều lựa chọn (ABCD): {config['q_abcd']} câu.
          - Đúng / Sai: {config['q_tf']} câu.
          - Điền khuyết: {config['q_fill']} câu.
          - Ghép nối: {config['q_match']} câu.
    
    B. PHẦN TỰ LUẬN ({config['essay_total']} câu - {config['essay_point']} điểm/câu):
       - Mức 1 (Biết): {config['essay_lv1']} câu.
       - Mức 2 (Hiểu): {config['essay_lv2']} câu.
       - Mức 3 (Vận dụng): {config['essay_lv3']} câu.
    
    PHẦN 2: DỮ LIỆU ĐẦU VÀO:
    - Kế hoạch dạy học / Nội dung cần kiểm tra: 
    {subject_plan}
    
    - Ma trận tham khảo:
    {matrix_content}
    
    OUTPUT YÊU CẦU:
    - Trình bày đề rõ ràng, ngôn ngữ phù hợp lứa tuổi {info['grade']}.
    - KHÔNG viết lại header (Trường, lớp...). Bắt đầu ngay bằng "PHẦN I..."
    - Cuối cùng phải có ĐÁP ÁN tách biệt bằng chuỗi: ###TÁCH_Ở_ĐÂY###
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

# --- 4. HÀM ĐỌC FILE (Word/PDF/Text) ---
def read_input_file(uploaded_file):
    if not uploaded_file: return ""
    try:
        # Đọc file Word
        if uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        # Đọc file PDF (MỚI)
        elif uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        # Đọc file Excel
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file).to_string()
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file).to_string()
        # Đọc file Text
        else:
            return uploaded_file.read().decode("utf-8")
    except Exception as e: return f"Lỗi đọc file: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="header">HỆ THỐNG HỖ TRỢ RA ĐỀ TIỂU HỌC</div>', unsafe_allow_html=True)

# --- SIDEBAR: CÀI ĐẶT & HƯỚNG DẪN API ---
with st.sidebar:
    st.header("🔑 Cài đặt API")
    
    # Hướng dẫn chi tiết
    with st.expander("ℹ️ Hướng dẫn lấy Mã API (Bấm xem)"):
        st.markdown("""
        **Bước 1:** Truy cập trang: [aistudio.google.com](https://aistudio.google.com/)
        
        **Bước 2:** Đăng nhập bằng tài khoản Gmail của bạn.
        
        **Bước 3:** Bấm nút màu xanh **"Get API key"** (ở góc trái trên).
        
        **Bước 4:** Bấm **"Create API key"** -> Chọn dự án mới -> Bấm **Create**.
        
        **Bước 5:** Copy đoạn mã hiện ra và dán vào ô bên dưới.
        """)
    
    api_key = st.text_input("Dán Mã API vào đây:", type="password", help="Mã bắt đầu bằng AIza...")
    
    st.markdown("---")
    st.subheader("🏫 Thông tin trường")
    school_name = st.text_input("Tên trường:", value="Trường TH Nguyễn Du")
    exam_name = st.text_input("Tên kỳ thi:", value="KIỂM TRA CUỐI HỌC KÌ I")

col1, col2 = st.columns([1, 1.2])

# --- CỘT 1: INPUT DỮ LIỆU ---
with col1:
    st.markdown('<div class="sub-header">1. Dữ liệu đầu vào</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    subject = c1.selectbox("Môn học", ["Tin học", "Công nghệ", "Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí"])
    grade = c2.selectbox("Khối lớp", ["Lớp 3", "Lớp 4", "Lớp 5"])
    
    st.markdown("---")
    st.write("📂 **Kế hoạch dạy học / Nội dung bài học:**")
    st.caption("Chấp nhận file: Word (.docx), PDF (.pdf), Text (.txt)")
    file_plan = st.file_uploader("Tải lên tại đây:", type=['docx', 'pdf', 'txt'], key='plan')
    
    st.write("📊 **Ma trận đề kiểm tra:**")
    st.caption("Chấp nhận file: Excel (.xlsx), Word (.docx), CSV")
    file_matrix = st.file_uploader("Tải lên tại đây:", type=['xlsx', 'docx', 'csv'], key='matrix')

# --- CỘT 2: CẤU HÌNH CHI TIẾT ---
with col2:
    st.markdown('<div class="sub-header">2. Cấu hình & Mức độ nhận thức</div>', unsafe_allow_html=True)
    
    # --- TAB CẤU HÌNH ---
    tab_tn, tab_tl = st.tabs(["🅰️ Phần Trắc Nghiệm", "🅱️ Phần Tự Luận"])
    
    with tab_tn:
        mcq_point = st.selectbox("Điểm mỗi câu:", [0.25, 0.5, 0.75, 1.0], index=1)
        
        st.markdown("**1. Phân bổ Mức độ (Biết - Hiểu - Vận dụng):**")
        c_lv1, c_lv2, c_lv3 = st.columns(3)
        mcq_lv1 = c_lv1.number_input("Mức 1 (Biết):", min_value=0, value=3)
        mcq_lv2 = c_lv2.number_input("Mức 2 (Hiểu):", min_value=0, value=2)
        mcq_lv3 = c_lv3.number_input("Mức 3 (Vận dụng):", min_value=0, value=1)
        
        mcq_total = mcq_lv1 + mcq_lv2 + mcq_lv3
        st.info(f"Tổng số câu Trắc nghiệm: **{mcq_total} câu**")

        st.markdown("**2. Phân bổ Dạng câu hỏi (Tùy chọn):**")
        st.caption("Tổng số lượng ở đây nên khớp với tổng số câu ở trên")
        q1, q2 = st.columns(2)
        q_abcd = q1.number_input("Chọn A,B,C,D:", min_value=0, value=mcq_total-2)
        q_tf = q1.number_input("Đúng / Sai:", min_value=0, value=1)
        q_fill = q2.number_input("Điền khuyết:", min_value=0, value=1)
        q_match = q2.number_input("Ghép nối:", min_value=0, value=0)

    with tab_tl:
        essay_point = st.selectbox("Điểm mỗi câu TL:", [1.0, 1.5, 2.0, 2.5, 3.0], index=2)
        
        st.markdown("**Phân bổ Mức độ:**")
        tl_lv1, tl_lv2, tl_lv3 = st.columns(3)
        essay_lv1 = tl_lv1.number_input("TL - Biết:", min_value=0, value=0)
        essay_lv2 = tl_lv2.number_input("TL - Hiểu:", min_value=0, value=1)
        essay_lv3 = tl_lv3.number_input("TL - Vận dụng:", min_value=0, value=1)
        
        essay_total = essay_lv1 + essay_lv2 + essay_lv3
        st.info(f"Tổng số câu Tự luận: **{essay_total} câu**")

    # --- TÍNH TỔNG ĐIỂM ---
    total_score = (mcq_total * mcq_point) + (essay_total * essay_point)
    st.markdown("---")
    if total_score == 10:
        st.success(f"✅ TỔNG ĐIỂM TOÀN BÀI: {total_score} ĐIỂM")
    else:
        st.warning(f"⚠️ Tổng điểm hiện tại: {total_score}. Vui lòng điều chỉnh số lượng câu.")

# --- NÚT TẠO ĐỀ ---
if st.button("🚀 KHỞI TẠO ĐỀ & XUẤT FILE WORD", type="primary", use_container_width=True):
    if not api_key:
        st.error("Vui lòng nhập Mã API.")
    elif not file_plan or not file_matrix:
        st.error("Vui lòng tải đủ file Nội dung (PDF/Word) và Ma trận.")
    else:
        plan_text = read_input_file(file_plan)
        matrix_text = read_input_file(file_matrix)
        
        with st.spinner("Đang phân tích mức độ kiến thức và soạn đề..."):
            # Cấu hình gửi AI
            config = {
                "mcq_total": mcq_total, "mcq_point": mcq_point,
                "mcq_lv1": mcq_lv1, "mcq_lv2": mcq_lv2, "mcq_lv3": mcq_lv3,
                "q_abcd": q_abcd, "q_tf": q_tf, "q_fill": q_fill, "q_match": q_match,
                "essay_total": essay_total, "essay_point": essay_point,
                "essay_lv1": essay_lv1, "essay_lv2": essay_lv2, "essay_lv3": essay_lv3
            }
            info = {"subject": subject, "grade": grade}
            
            exam_body, answer_key = generate_exam_content(api_key, plan_text, matrix_text, config, info)
            
            if exam_body:
                docx_file = create_docx_file(school_name, exam_name, info, exam_body, answer_key)
                
                st.markdown("### 🎉 Đã xong! Mời tải về:")
                st.download_button(
                    label=f"📥 Tải Đề {subject} {grade} (.docx)",
                    data=docx_file,
                    file_name=f"DeKiemTra_{subject}_{grade}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            else:
                st.error("Có lỗi xảy ra. Vui lòng kiểm tra lại API Key hoặc file đầu vào.")

# --- FOOTER ---
st.markdown('<div class="author-footer">Hệ thống hỗ trợ chuyên môn Tiểu học.<br>Lưu ý: Nội dung tuân thủ Thông tư 27, Thông tư 32 và Chương trình GDPT 2018.<br>Tác giả: <b>BapCai</b></div>', unsafe_allow_html=True)
