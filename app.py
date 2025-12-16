import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import requests
import json
import PyPDF2
import time  # Thư viện time để xử lý chờ và hiệu ứng

# ==========================================
# 1. CẤU HÌNH & DỮ LIỆU CHUẨN
# ==========================================
st.set_page_config(page_title="HỆ THỐNG RA ĐỀ TIỂU HỌC CHUẨN TT27", page_icon="🏫", layout="wide")

st.markdown("""
<style>
    .block-container {max-width: 95% !important;}
    .footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: #333; text-align: center; padding: 10px; border-top: 1px solid #ccc; z-index: 100;}
    .upload-area {border: 2px dashed #4CAF50; padding: 20px; border-radius: 10px; background-color: #f9fbe7; text-align: center;}
    .process-box {border: 1px solid #ddd; padding: 20px; border-radius: 8px; background-color: #f8f9fa;}
    .status-ok {color: #2e7d32; font-weight: bold;}
    .status-def {color: #1565c0; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# Link dữ liệu
GITHUB_DATA_URL = "https://raw.githubusercontent.com/username/repo/main/data.json"

# Môn học định kỳ (TT27)
VALID_SUBJECTS = {
    "Lớp 1": ["Toán", "Tiếng Việt"],
    "Lớp 2": ["Toán", "Tiếng Việt"],
    "Lớp 3": ["Toán", "Tiếng Việt", "Tiếng Anh", "Tin học", "Công nghệ"],
    "Lớp 4": ["Toán", "Tiếng Việt", "Tiếng Anh", "Tin học", "Công nghệ", "Khoa học", "Lịch sử & Địa lí"],
    "Lớp 5": ["Toán", "Tiếng Việt", "Tiếng Anh", "Tin học", "Công nghệ", "Khoa học", "Lịch sử & Địa lí"]
}

# Dữ liệu dự phòng
DATA_FALLBACK = {
  "Toán": {
    "Lớp 1": {
      "Kết nối tri thức với cuộc sống": {
        "Chủ đề 1: Các số 0-10": [{"topic": "Bài 1: Các số 0-10", "periods": 12}],
        "Chủ đề 2: Phép cộng trừ phạm vi 10": [{"topic": "Cộng trừ phạm vi 10", "periods": 10}]
      }
    }
  }
}

# ==========================================
# 2. CÁC HÀM XỬ LÝ (DATA, FILE, WORD, AI)
# ==========================================
@st.cache_data
def load_data():
    try:
        response = requests.get(GITHUB_DATA_URL, timeout=3)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return DATA_FALLBACK

def read_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in reader.pages])
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            return df.to_string()
    except Exception as e:
        return f"Lỗi đọc file: {str(e)}"
    return ""

def create_docx_final(school, exam, info, body, key):
    doc = Document()
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass
    
    # Header
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False
    tbl.columns[0].width = Inches(3.0); tbl.columns[1].width = Inches(3.5)
    
    c1 = tbl.cell(0,0); p1 = c1.paragraphs[0]; p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.add_run(f"PHÒNG GD&ĐT ............\n").font.size = Pt(12)
    p1.add_run(f"{school.upper()}").bold = True
    
    c2 = tbl.cell(0,1); p2 = c2.paragraphs[0]; p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM").bold = True
    p2.add_run("\nĐộc lập - Tự do - Hạnh phúc").bold = True
    
    doc.add_paragraph()
    p_title = doc.add_paragraph(); p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.add_run(f"{exam.upper()}").bold = True; p_title.font.size = Pt(14)
    
    book_display = info.get('book', 'Tổng hợp')
    doc.add_paragraph(f"Môn: {info['subj']} - Lớp: {info['grade']} ({book_display})").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Thời gian làm bài: 40 phút").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

    # Body
    for line in str(body).split('\n'):
        if line.strip():
            p = doc.add_paragraph()
            if any(x in line.upper() for x in ["PHẦN", "CÂU", "BÀI"]):
                p.add_run(line.strip()).bold = True
            else: p.add_run(line.strip())

    # Key
    doc.add_page_break()
    p_key = doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN")
    p_key.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_key.runs[0].bold = True
    doc.add_paragraph(str(key))

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def get_best_available_model():
    """Hàm tự động tìm model tốt nhất hiện có trong API Key"""
    try:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in models:
            if 'flash' in m.name.lower() and '2.0' in m.name: return m.name
        for m in models:
            if 'flash' in m.name.lower() and '1.5' in m.name: return m.name
        for m in models:
            if 'flash' in m.name.lower(): return m.name
        if models: return models[0].name
        return 'gemini-1.5-flash'
    except:
        return 'gemini-1.5-flash'

def call_ai_generate(api_key, info, lessons, uploaded_ref):
    genai.configure(api_key=api_key)
    model_name = get_best_available_model()
    
    model = genai.GenerativeModel(model_name)
    lesson_text = str(lessons)
    
    ref_instruction = ""
    if uploaded_ref:
        ref_instruction = f"""
        3. CẤU TRÚC ĐỀ THI (BẮT BUỘC TUÂN THỦ FILE ĐÍNH KÈM SAU):
        Người dùng đã tải lên một file Ma trận/Đặc tả kỹ thuật. Hãy đọc kỹ nội dung dưới đây và ra đề thi bám sát cấu trúc:
        --- BẮT ĐẦU FILE ĐÍNH KÈM ---
        {uploaded_ref[:20000]}
        --- KẾT THÚC FILE ĐÍNH KÈM ---
        """
    else:
        ref_instruction = """
        3. CẤU TRÚC ĐỀ THI (TỰ ĐỘNG THEO TT27):
        - PHẦN I: Trắc nghiệm (Khoảng 40-50% điểm). Gồm: Nhiều lựa chọn, Đúng/Sai, Nối cột, Điền khuyết.
        - PHẦN II: Tự luận (Khoảng 50-60% điểm).
        - Đảm bảo 3 mức độ: Hoàn thành tốt, Hoàn thành, Chưa hoàn thành.
        """

    prompt = f"""
    Bạn là chuyên gia giáo dục tiểu học. Hãy soạn ĐỀ KIỂM TRA ĐỊNH KỲ môn {info['subj']} Lớp {info['grade']}.
    
    1. NGUỒN DỮ LIỆU THAM KHẢO:
    {lesson_text[:30000]} 
    
    2. YÊU CẦU CHUYÊN MÔN:
    - Sử dụng kiến thức chuẩn của Chương trình GDPT 2018.
    - Ngôn ngữ trong sáng, phù hợp lứa tuổi học sinh tiểu học.
    
    {ref_instruction}

    4. ĐỊNH DẠNG ĐẦU RA:
    - Trình bày rõ ràng thành 2 phần: ĐỀ BÀI và ĐÁP ÁN.
    - BẮT BUỘC ngăn cách giữa ĐỀ và ĐÁP ÁN bằng dòng chữ duy nhất: ###TACH_DAP_AN###
    """
    
    # --- LOGIC RETRY MẠNH MẼ HƠN CHO LỖI 429 ---
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            text = response.text
            if "###TACH_DAP_AN###" in text:
                return text.split("###TACH_DAP_AN###")
            return text, "Không tìm thấy dấu tách. AI trả về toàn bộ nội dung."
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                # Tăng thời gian chờ lên 60s để đảm bảo reset quota
                wait_time = 60
                if attempt < max_retries - 1:
                    st.toast(f"⚠️ Quá tải (429). Đang chờ {wait_time}s để thử lại... (Lần {attempt+1}/{max_retries})", icon="⏳")
                    time.sleep(wait_time)
                    continue
                else:
                    return None, "Hệ thống Google đang quá tải (Lỗi 429). Vui lòng thử lại sau 2-3 phút."
            else:
                return None, f"Lỗi gọi AI ({model_name}): {error_msg}"

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'preview_body' not in st.session_state: st.session_state.preview_body = ""
if 'preview_key' not in st.session_state: st.session_state.preview_key = ""

DATA_DB = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    api_key = st.text_input("Google API Key:", type="password")
    st.info("Nhập API Key để AI hoạt động.")
    
    if api_key:
        if st.button("Kiểm tra Model khả dụng"):
            try:
                genai.configure(api_key=api_key)
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                st.success("Kết nối thành công! Các model khả dụng:")
                st.code("\n".join(models), language="text")
            except Exception as e:
                st.error(f"Lỗi API Key: {e}")

    st.divider()
    school_name = st.text_input("Trường:", "TH PTDTBT GIÀNG CHU PHÌN")
    exam_name = st.text_input("Kỳ thi:", "KIỂM TRA CUỐI HỌC KÌ I")

# --- HOME ---
if st.session_state.step == 'home':
    st.markdown("<h2 style='text-align: center;'>HỆ THỐNG RA ĐỀ TIỂU HỌC (CHUẨN GDPT 2018)</h2>", unsafe_allow_html=True)
    st.write("---")
    st.markdown("#### 1️⃣ Chọn Khối Lớp")
    cols = st.columns(5)
    for i, g in enumerate(["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]):
        if cols[i].button(g, type="primary" if st.session_state.get('selected_grade') == g else "secondary", use_container_width=True):
            st.session_state.selected_grade = g
            st.session_state.selected_subject = None
            st.rerun()
            
    if st.session_state.get('selected_grade'):
        st.markdown("#### 2️⃣ Chọn Môn Học")
        valid_subs = VALID_SUBJECTS.get(st.session_state.selected_grade, [])
        c_sub = st.columns(4)
        for idx, s_name in enumerate(valid_subs):
            with c_sub[idx % 4]:
                if st.button(s_name, key=s_name, use_container_width=True):
                    st.session_state.selected_subject = s_name
                    st.session_state.step = 'config'
                    st.rerun()

# --- CONFIG ---
elif st.session_state.step == 'config':
    c1, c2 = st.columns([1, 6])
    if c1.button("⬅️ Quay lại"):
        st.session_state.step = 'home'
        st.rerun()
    
    grade = st.session_state.selected_grade
    subj = st.session_state.selected_subject
    c2.markdown(f"### 🚩 {grade} - {subj}")
    
    # Chia cột: Cột Trái (Status) - Cột Phải (Upload)
    col_left, col_right = st.columns([1, 1.2])
    
    current_data = DATA_DB.get(subj, {}).get(grade, {})
    ref_content = ""

    # --- 1. XỬ LÝ UPLOAD TRƯỚC (ĐỂ CÓ DỮ LIỆU HIỂN THỊ TRẠNG THÁI) ---
    with col_right:
        st.info("📂 B. Tải lên Ma trận / Đặc tả (Tùy chọn)")
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        st.write("Tải file PDF, Word, hoặc Excel chứa Ma trận đặc tả đề thi.")
        uploaded_file = st.file_uploader("Chọn file...", type=['pdf', 'docx', 'xlsx'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file:
            with st.spinner("Đang đọc nội dung file..."):
                ref_content = read_uploaded_file(uploaded_file)
                st.success(f"Đã đọc xong: {uploaded_file.name}")
                with st.expander("Xem nội dung file"):
                    st.text(ref_content[:500] + "...")

    # --- 2. HIỂN THỊ TRẠNG THÁI (THAY THẾ JSON PREVIEW) ---
    with col_left:
        st.info("📊 A. Trạng thái & Cấu trúc đề")
        st.markdown('<div class="process-box">', unsafe_allow_html=True)
        
        # Hiển thị chế độ dựa trên việc có file upload hay không
        if ref_content:
            st.markdown(f"**📑 Chế độ:** <span class='status-ok'>THEO MA TRẬN TẢI LÊN</span>", unsafe_allow_html=True)
            st.write(f"📄 **Nguồn:** `{uploaded_file.name}`")
            st.write("🤖 AI sẽ phân tích file này để xác định:")
            st.write("- Số lượng câu hỏi & Điểm số.")
            st.write("- Mức độ (Biết/Hiểu/Vận dụng).")
        else:
            st.markdown(f"**📑 Chế độ:** <span class='status-def'>MẶC ĐỊNH (TT27)</span>", unsafe_allow_html=True)
            st.write("🤖 AI tự động thiết lập cấu trúc:")
            st.write("- **Phần 1:** Trắc nghiệm (Nối, Điền khuyết, Đúng/Sai).")
            st.write("- **Phần 2:** Tự luận.")
            st.write("- **Đảm bảo:** Phù hợp chuẩn kiến thức GDPT 2018.")
            
        st.divider()
        st.markdown(f"**📚 Dữ liệu:** Chương trình {grade} - {subj}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # --- 3. NÚT BẤM & HIỆU ỨNG STEP-BY-STEP ---
    if st.button("🚀 SOẠN ĐỀ THI (XEM TRƯỚC)", type="primary", use_container_width=True):
        if not api_key:
            st.error("Vui lòng nhập Google API Key ở cột bên trái!")
        else:
            # Dùng st.status để hiển thị từng bước
            with st.status("🤖 AI đang làm việc...", expanded=True) as status:
                st.write("1️⃣ Đang đọc dữ liệu chương trình học và sách giáo khoa...")
                time.sleep(1) # Delay nhỏ để tạo hiệu ứng
                
                if ref_content:
                    st.write("2️⃣ Đang phân tích file Ma trận / Đặc tả kỹ thuật tải lên...")
                else:
                    st.write("2️⃣ Đang thiết lập cấu trúc đề chuẩn Thông tư 27...")
                time.sleep(1)
                
                st.write("3️⃣ Đang soạn thảo câu hỏi và đáp án (Quá trình này mất khoảng 30s - 60s)...")
                
                # Gọi AI
                info = {"subj": subj, "grade": grade, "book": "Tổng hợp"}
                data_context = json.dumps(current_data, ensure_ascii=False) if isinstance(current_data, dict) else str(current_data)
                
                body, key = call_ai_generate(api_key, info, data_context, ref_content)
                
                if body:
                    st.write("4️⃣ Hoàn tất! Đang hiển thị kết quả...")
                    status.update(label="✅ Đã soạn xong!", state="complete", expanded=False)
                    
                    st.session_state.preview_body = body
                    st.session_state.preview_key = key
                    st.session_state.info = info
                    st.session_state.step = 'preview'
                    st.rerun()
                else:
                    status.update(label="❌ Có lỗi xảy ra!", state="error")
                    st.error(key)

# --- PREVIEW ---
elif st.session_state.step == 'preview':
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅️ Chỉnh sửa yêu cầu", on_click=lambda: st.session_state.update(step='config')): pass
    
    c2.markdown("### 👁️ XEM TRƯỚC VÀ CHỈNH SỬA")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("**Nội dung Đề thi:**")
        new_body = st.text_area("Body", value=st.session_state.preview_body, height=600, label_visibility="collapsed")
    with col_p2:
        st.markdown("**Đáp án & Hướng dẫn chấm:**")
        new_key = st.text_area("Key", value=st.session_state.preview_key, height=600, label_visibility="collapsed")
        
    st.markdown("---")
    if st.button("💾 TẢI FILE WORD (.DOCX)", type="primary", use_container_width=True):
        f = create_docx_final(school_name, exam_name, st.session_state.info, new_body, new_key)
        st.download_button(
            label="📥 Click để tải về máy",
            data=f,
            file_name=f"De_{st.session_state.info['subj']}_{st.session_state.info['grade']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# Footer
st.markdown('<div style="margin-bottom: 60px;"></div>', unsafe_allow_html=True)
st.markdown('<div class="footer">© 2025 - Trần Ngọc Hải - Trường PTDTBT Tiểu học Giàng Chu Phìn - ĐT: 0944 134 973</div>', unsafe_allow_html=True)
