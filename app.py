import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import pypdf

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🏫", layout="wide")

# --- CSS GIAO DIỆN ---
st.markdown("""
<style>
    .header {color: #d63031; font-size: 28px; font-weight: bold; text-align: center; margin-bottom: 20px; text-transform: uppercase; font-family: 'Times New Roman', serif;}
    .sub-header {color: #0984e3; font-weight: bold; margin-top: 15px; border-bottom: 2px solid #dfe6e9; padding-bottom: 5px;}
    .author-footer {text-align: center; font-style: italic; color: #636e72; margin-top: 50px; font-size: 14px; border-top: 1px solid #ddd; padding-top: 10px;}
    .stSelectbox label, .stNumberInput label {font-weight: bold; color: #2d3436;}
    .error-box {background-color: #ffcccc; color: #cc0000; padding: 10px; border-radius: 5px; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# --- 1. HÀM TẠO FILE WORD CHUẨN FORM (ĐÃ VÁ LỖI) ---
def set_font_style(doc):
    try:
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(13)
        rFonts = style.element.rPr.rFonts
        rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except:
        pass # Nếu lỗi chỉnh font thì bỏ qua, ưu tiên xuất được file

def create_docx_file(school_name, exam_name, student_info, content_body, answer_key):
    doc = Document()
    set_font_style(doc)
    
    # Header
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    p_left.add_run("PHÒNG GD&ĐT ............\n").bold = False
    p_left.add_run(f"{str(school_name).upper()}").bold = True
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n").bold = True
    p_right.add_run("Độc lập - Tự do - Hạnh phúc").bold = True
    p_right.add_run("\n-------------------").bold = False
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph() 

    # Tên đề
    title = doc.add_paragraph()
    run_title = title.add_run(str(exam_name).upper())
    run_title.bold = True
    run_title.font.size = Pt(14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Thông tin HS
    info = doc.add_paragraph()
    info.add_run("Họ và tên học sinh: ..................................................................................... ").bold = False
    info.add_run(f"Lớp: {student_info.get('grade', '...')}.....")
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

    # Nội dung đề (Xử lý lỗi None)
    doc.add_paragraph("------------------------------------------------------------------------------------------------------")
    
    clean_body = str(content_body) if content_body else "Nội dung đề đang cập nhật..."
    # Loại bỏ các ký tự Markdown gây lỗi nếu có
    clean_body = clean_body.replace("**", "").replace("##", "") 
    
    body_para = doc.add_paragraph(clean_body)
    body_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    doc.add_page_break()
    
    # Đáp án
    ans_title = doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN")
    ans_title.runs[0].bold = True
    ans_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    clean_ans = str(answer_key) if answer_key else "Đang cập nhật..."
    clean_ans = clean_ans.replace("**", "").replace("##", "")
    doc.add_paragraph(clean_ans)

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

# --- 3. HÀM GỌI AI ---
def generate_exam_content(api_key, subject_plan, matrix_content, config, info):
    if not api_key: return None, None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(get_best_model())

    prompt = f"""
    Bạn là chuyên gia giáo dục tiểu học. Hãy soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    Yêu cầu tuân thủ Thông tư 27 (Đánh giá năng lực) và Thông tư 32.
    
    PHẦN 1: CẤU TRÚC:
    A. TRẮC NGHIỆM ({config['mcq_total']} câu - {config['mcq_point']} đ/câu):
       - Mức 1 (Biết): {config['mcq_lv1']} câu.
       - Mức 2 (Hiểu): {config['mcq_lv2']} câu.
       - Mức 3 (Vận dụng): {config['mcq_lv3']} câu.
       (Bao gồm các dạng: ABCD, Đúng/Sai, Điền khuyết, Ghép nối tùy vào nội dung).
    
    B. TỰ LUẬN ({config['essay_total']} câu - {config['essay_point']} đ/câu):
       - Mức 1: {config['essay_lv1']}, Mức 2: {config['essay_lv2']}, Mức 3: {config['essay_lv3']} câu.
    
    PHẦN 2: DỮ LIỆU NGUỒN:
    - Nội dung: {subject_plan}
    - Ma trận: {matrix_content}
    
    OUTPUT:
    - Trình bày đề rõ ràng.
    - BẮT BUỘC: Ngăn cách giữa ĐỀ và ĐÁP ÁN bằng chuỗi ký tự duy nhất này: ###TÁCH_Ở_ĐÂY###
    """
    
    try:
        response = model.generate_content(prompt)
        full_text = response.text
        
        # Xử lý an toàn khi tách chuỗi
        if "###TÁCH_Ở_ĐÂY###" in full_text:
            parts = full_text.split("###TÁCH_Ở_ĐÂY###")
            return parts[0].strip(), parts[1].strip()
        else:
            # Nếu AI quên tách, trả về toàn bộ vào phần Đề, phần đáp án để trống
            return full_text, "AI không tách riêng đáp án. Vui lòng xem ở phần cuối đề bài."
            
    except Exception as e:
        return f"Lỗi kết nối AI: {str(e)}", ""

# --- 4. HÀM ĐỌC FILE ---
def read_input_file(uploaded_file):
    if not uploaded_file: return ""
    try:
        if uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file).to_string()
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file).to_string()
        else:
            return uploaded_file.read().decode("utf-8")
    except Exception as e: return f"Lỗi đọc file: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="header">HỆ THỐNG HỖ TRỢ RA ĐỀ TIỂU HỌC</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Cài đặt API")
    with st.expander("ℹ️ Hướng dẫn lấy Mã API"):
        st.markdown("""
        1. Vào: [aistudio.google.com](https://aistudio.google.com/)
        2. Đăng nhập Gmail -> Bấm **Get API key**.
        3. Bấm **Create API key** -> Copy mã.
        """)
    api_key = st.text_input("Dán Mã API vào đây:", type="password")
    
    st.markdown("---")
    st.subheader("🏫 Thông tin trường")
    school_name = st.text_input("Tên trường:", value="Trường TH Nguyễn Du")
    exam_name = st.text_input("Tên kỳ thi:", value="KIỂM TRA CUỐI HỌC KÌ I")

col1, col2 = st.columns([1, 1.2])

# --- INPUT ---
with col1:
    st.markdown('<div class="sub-header">1. Dữ liệu đầu vào</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    subject = c1.selectbox("Môn học", ["Tin học", "Công nghệ", "Toán", "Tiếng Việt", "Khoa học", "Lịch sử & Địa lí"])
    grade = c2.selectbox("Khối lớp", ["Lớp 3", "Lớp 4", "Lớp 5"])
    
    st.write("📂 **Kế hoạch dạy học:** (PDF/Word/Txt)")
    file_plan = st.file_uploader("Tải lên:", type=['docx', 'pdf', 'txt'], key='plan', label_visibility="collapsed")
    
    st.write("📊 **Ma trận đề:** (Excel/Word/CSV)")
    file_matrix = st.file_uploader("Tải lên:", type=['xlsx', 'docx', 'csv'], key='matrix', label_visibility="collapsed")

# --- CONFIG ---
with col2:
    st.markdown('<div class="sub-header">2. Cấu hình & Mức độ</div>', unsafe_allow_html=True)
    
    tab_tn, tab_tl = st.tabs(["🅰️ Trắc Nghiệm", "🅱️ Tự Luận"])
    
    with tab_tn:
        mcq_point = st.selectbox("Điểm/câu TN:", [0.25, 0.5, 0.75, 1.0], index=1)
        c_lv1, c_lv2, c_lv3 = st.columns(3)
        mcq_lv1 = c_lv1.number_input("Mức 1 (Biết):", 0, 10, 3)
        mcq_lv2 = c_lv2.number_input("Mức 2 (Hiểu):", 0, 10, 2)
        mcq_lv3 = c_lv3.number_input("Mức 3 (Vận dụng):", 0, 10, 1)
        mcq_total = mcq_lv1 + mcq_lv2 + mcq_lv3
        
        st.markdown("**Các dạng câu hỏi (Tùy chọn):**")
        q1, q2 = st.columns(2)
        q_abcd = q1.number_input("ABCD:", 0, 20, max(0, mcq_total-2))
        q_tf = q1.number_input("Đúng/Sai:", 0, 5, 1)
        q_fill = q2.number_input("Điền khuyết:", 0, 5, 1)
        q_match = q2.number_input("Ghép nối:", 0, 5, 0)

    with tab_tl:
        essay_point = st.selectbox("Điểm/câu TL:", [1.0, 1.5, 2.0, 2.5, 3.0], index=2)
        tl_lv1, tl_lv2, tl_lv3 = st.columns(3)
        essay_lv1 = tl_lv1.number_input("TL Biết:", 0, 5, 0)
        essay_lv2 = tl_lv2.number_input("TL Hiểu:", 0, 5, 1)
        essay_lv3 = tl_lv3.number_input("TL Vận dụng:", 0, 5, 1)
        essay_total = essay_lv1 + essay_lv2 + essay_lv3

    total_score = (mcq_total * mcq_point) + (essay_total * essay_point)
    if total_score == 10:
        st.success(f"✅ TỔNG ĐIỂM: {total_score}")
    else:
        st.warning(f"⚠️ Tổng điểm: {total_score}. Hãy chỉnh lại cho đủ 10.")

# --- ACTION ---
if st.button("🚀 KHỞI TẠO ĐỀ & XUẤT FILE WORD", type="primary", use_container_width=True):
    if not api_key:
        st.error("Thiếu Mã API.")
    elif not file_plan or not file_matrix:
        st.error("Thiếu file dữ liệu.")
    else:
        # Đọc file an toàn
        plan_text = read_input_file(file_plan)
        matrix_text = read_input_file(file_matrix)
        
        # Kiểm tra nội dung file có rỗng không
        if len(plan_text) < 10 or len(matrix_text) < 10:
            st.error("File tải lên không có nội dung hoặc lỗi định dạng. Hãy kiểm tra lại.")
        else:
            with st.spinner("Đang soạn đề... (Vui lòng chờ khoảng 30s)"):
                config = {
                    "mcq_total": mcq_total, "mcq_point": mcq_point,
                    "mcq_lv1": mcq_lv1, "mcq_lv2": mcq_lv2, "mcq_lv3": mcq_lv3,
                    "essay_total": essay_total, "essay_point": essay_point,
                    "essay_lv1": essay_lv1, "essay_lv2": essay_lv2, "essay_lv3": essay_lv3
                }
                info = {"subject": subject, "grade": grade}
                
                # Gọi AI
                exam_body, answer_key = generate_exam_content(api_key, plan_text, matrix_text, config, info)
                
                if exam_body and "Lỗi" not in exam_body:
                    try:
                        # Tạo file Word an toàn
                        docx_file = create_docx_file(school_name, exam_name, info, exam_body, answer_key)
                        
                        st.markdown("### 🎉 Kết quả:")
                        st.download_button(
                            label=f"📥 Tải Đề {subject} {grade} (.docx)",
                            data=docx_file,
                            file_name=f"DeKiemTra_{subject}_{grade}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    except Exception as e:
                        st.error(f"Lỗi khi tạo file Word: {str(e)}")
                else:
                    st.error(f"Lỗi từ AI: {exam_body}")

# --- FOOTER ---
st.markdown('<div class="author-footer">Hệ thống hỗ trợ chuyên môn Tiểu học.<br>Tác giả: <b>BapCai</b></div>', unsafe_allow_html=True)
