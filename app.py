import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Ra Đề Thi (Universal Fix)", page_icon="🛡️", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .subject-card { padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9; text-align: center; margin-bottom: 10px; }
    .stTextArea textarea { font-family: 'Times New Roman'; font-size: 16px; }
    .success-box { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- IMPORT AN TOÀN ---
try:
    import pypdf
except ImportError:
    st.error("⚠️ Thiếu thư viện 'pypdf'. Vui lòng thêm pypdf vào requirements.txt")

# --- DỮ LIỆU MÔN HỌC ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 2": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 3": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 4": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 5": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")]
}

# --- HÀM TÌM MODEL THỰC TẾ (CHỮA LỖI 404 TRIỆT ĐỂ) ---
def get_best_available_model(api_key):
    """
    Hàm này hỏi Google xem Key này dùng được những model nào,
    sau đó chọn model tốt nhất (ưu tiên Flash để nhanh và rẻ).
    """
    genai.configure(api_key=api_key)
    try:
        # Lấy danh sách model thực tế từ Google
        all_models = genai.list_models()
        
        # Lọc ra model có thể tạo văn bản (generateContent)
        valid_models = []
        for m in all_models:
            if 'generateContent' in m.supported_generation_methods:
                valid_models.append(m.name)
        
        if not valid_models:
            return None, "API Key đúng, nhưng không tìm thấy model nào hỗ trợ tạo văn bản."

        # Ưu tiên chọn model theo thứ tự này
        priorities = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        selected_model = None
        
        # Tìm trong danh sách ưu tiên
        for p in priorities:
            for v in valid_models:
                if p in v: # Nếu tìm thấy tên model ưu tiên
                    selected_model = v
                    break
            if selected_model: break
        
        # Nếu không có model ưu tiên, lấy cái đầu tiên tìm được
        if not selected_model:
            selected_model = valid_models[0]
            
        return selected_model, None

    except Exception as e:
        return None, f"Lỗi kết nối API: {str(e)}"

# --- HÀM GỌI AI ---
def generate_content_safe(api_key, prompt):
    # Bước 1: Tìm model sống
    model_name, error = get_best_available_model(api_key)
    
    if error:
        raise Exception(error)
    
    if not model_name:
        raise Exception("Không tìm thấy model nào khả dụng.")

    # Bước 2: Gọi model đó
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text, model_name
    except Exception as e:
        # Nếu lỗi 429 (Quá tải), chờ 2s rồi thử lại 1 lần nữa
        if "429" in str(e):
            time.sleep(2)
            response = model.generate_content(prompt)
            return response.text, model_name
        else:
            raise e

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
            if 'pypdf' in globals():
                reader = pypdf.PdfReader(uploaded_file)
                text = ""
                for page in reader.pages: text += page.extract_text()
                return text
        return None
    except Exception:
        return None

# --- HÀM TẠO FILE WORD ---
def create_word_file(school_name, exam_name, content):
    doc = Document()
    style = doc.styles['Normal']; font = style.font; font.name = 'Times New Roman'; font.size = Pt(13)
    for section in doc.sections:
        section.top_margin = Cm(2); section.bottom_margin = Cm(2)
        section.left_margin = Cm(3); section.right_margin = Cm(2)

    table = doc.add_table(rows=1, cols=2); table.autofit = False
    table.columns[0].width = Cm(7); table.columns[1].width = Cm(9)

    cell_1 = table.cell(0, 0); p1 = cell_1.paragraphs[0]
    run_s = p1.add_run(f"{school_name.upper()}"); run_s.bold = True; run_s.font.size = Pt(12)
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    cell_2 = table.cell(0, 1); p2 = cell_2.paragraphs[0]
    run_e = p2.add_run(f"{exam_name.upper()}\n"); run_e.bold = True; run_e.font.size = Pt(12)
    run_y = p2.add_run("Năm học: .........."); run_y.font.size = Pt(13)
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    for line in content.split('\n'):
        if line.strip():
            p = doc.add_paragraph(line); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    buffer = io.BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

# --- MAIN ---
def main():
    st.title("🛡️ HỆ THỐNG RA ĐỀ THI (UNIVERSAL FIX)")
    
    if 'exam_result' not in st.session_state: st.session_state.exam_result = ""

    with st.sidebar:
        st.header("1. Cấu hình")
        api_key = st.text_input("Nhập API Key:", type="password")
        
        # Nút kiểm tra API để người dùng yên tâm
        if api_key:
            if st.button("Kiểm tra kết nối"):
                m_name, err = get_best_available_model(api_key)
                if m_name:
                    st.success(f"✅ Kết nối tốt! Sẽ dùng model: {m_name}")
                else:
                    st.error(f"❌ Lỗi: {err}")

        st.divider()
        school_name = st.text_input("Tên trường:", value="TRƯỜNG TH NGUYỄN DU")
        exam_term = st.selectbox("Kỳ thi:", 
             ["ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ I", "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ I",
              "ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ II", "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ II"])

    if not api_key: st.warning("Vui lòng nhập API Key."); return

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

    if uploaded and st.button("🚀 TẠO ĐỀ THI", type="primary"):
        content = read_uploaded_file(uploaded)
        if content:
            with st.spinner("Đang tìm model phù hợp và tạo đề..."):
                try:
                    prompt = f"""
                    Vai trò: Giáo viên tiểu học. Soạn đề thi môn {sub_name} lớp {grade}.
                    Yêu cầu:
                    1. Chỉ dùng dữ liệu từ văn bản dưới đây.
                    2. Không bịa kiến thức ngoài.
                    3. Cấu trúc: Phần I. Trắc nghiệm (nếu có), Phần II. Tự luận.
                    Dữ liệu ma trận:
                    {content}
                    """
                    
                    # Gọi hàm tạo đề
                    result_text, used_model = generate_content_safe(api_key, prompt)
                    
                    st.session_state.exam_result = result_text
                    st.markdown(f"<div class='success-box'>✅ Đã tạo xong bằng model: <b>{used_model}</b></div>", unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    # KHUNG SỬA VÀ TẢI
    if st.session_state.exam_result:
        st.markdown("---")
        st.subheader("📝 Xem và Sửa nội dung")
        edited_text = st.text_area("Sửa trực tiếp tại đây:", value=st.session_state.exam_result, height=500)
        st.session_state.exam_result = edited_text 

        docx = create_word_file(school_name, exam_term, edited_text)
        st.download_button("📥 TẢI VỀ FILE WORD (.DOCX)", docx, file_name=f"De_{sub_name}_{grade}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")

if __name__ == "__main__":
    main()
