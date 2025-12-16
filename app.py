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

# ==========================================
# 1. CẤU HÌNH & DỮ LIỆU CHUẨN (TỪ 5 FILE ĐÃ GỬI)
# ==========================================
st.set_page_config(page_title="HỆ THỐNG RA ĐỀ TIỂU HỌC CHUẨN TT27", page_icon="🏫", layout="wide")

# CSS Tùy chỉnh
st.markdown("""
<style>
    .block-container {max-width: 90% !important;}
    .footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: #333; text-align: center; padding: 10px; border-top: 1px solid #ccc; z-index: 100;}
    .main-footer {margin-bottom: 50px;}
</style>
""", unsafe_allow_html=True)

# Link Github chứa data.json (Thay link thật của bạn vào đây sau này)
GITHUB_DATA_URL = "https://raw.githubusercontent.com/username/repo/main/data.json"

# Môn học có điểm định kỳ theo Thông tư 27
VALID_SUBJECTS = {
    "Lớp 1": ["Toán", "Tiếng Việt"],
    "Lớp 2": ["Toán", "Tiếng Việt"],
    "Lớp 3": ["Toán", "Tiếng Việt", "Tiếng Anh", "Tin học", "Công nghệ"],
    "Lớp 4": ["Toán", "Tiếng Việt", "Tiếng Anh", "Tin học", "Công nghệ", "Khoa học", "Lịch sử & Địa lí"],
    "Lớp 5": ["Toán", "Tiếng Việt", "Tiếng Anh", "Tin học", "Công nghệ", "Khoa học", "Lịch sử & Địa lí"]
}

# Dữ liệu tích hợp sẵn (Được tổng hợp từ các file bạn đã gửi)
# Hệ thống sẽ dùng dữ liệu này nếu không tải được từ GitHub
DATA_FALLBACK = {
  "Toán": {
    "Lớp 1": {
      "Kết nối tri thức với cuộc sống": {
        "Chủ đề 1: Các số từ 0 đến 10": [{"topic": "Các số 0-10", "periods": 13}, {"topic": "So sánh số", "periods": 2}],
        "Chủ đề 2: Hình phẳng": [{"topic": "Hình vuông, tròn, tam giác", "periods": 3}],
        "Chủ đề 3: Phép cộng, trừ phạm vi 10": [{"topic": "Phép cộng, trừ phạm vi 10", "periods": 8}]
      }
    },
    "Lớp 2": {
      "Kết nối tri thức với cuộc sống": {
        "Chủ đề 1: Ôn tập và bổ sung": [{"topic": "Ôn tập các số đến 100", "periods": 3}],
        "Chủ đề 2: Phép cộng, trừ qua 10": [{"topic": "Phép cộng, trừ qua 10", "periods": 12}],
        "Chủ đề 3: Khối lượng, dung tích": [{"topic": "Ki-lô-gam, Lít", "periods": 5}]
      }
    },
    "Lớp 3": {
      "Kết nối tri thức với cuộc sống": {
        "Chủ đề 1: Ôn tập và bổ sung": [{"topic": "Ôn tập số đến 1000", "periods": 8}],
        "Chủ đề 2: Bảng nhân, bảng chia": [{"topic": "Bảng nhân/chia 6,7,8,9", "periods": 8}]
      }
    },
    "Lớp 4": {
      "Kết nối tri thức với cuộc sống": {
        "Chủ đề 1: Ôn tập và bổ sung": [{"topic": "Số tự nhiên & Phép tính", "periods": 12}],
        "Chủ đề 2: Góc và đơn vị đo": [{"topic": "Góc, Đơn vị đo góc", "periods": 5}],
        "Chủ đề 3: Số có nhiều chữ số": [{"topic": "Số lớp triệu, Yến, Tạ, Tấn", "periods": 12}]
      }
    },
    "Lớp 5": {
      "Kết nối tri thức với cuộc sống": {
        "Chủ đề 1: Ôn tập và bổ sung": [{"topic": "Phân số, Hỗn số", "periods": 11}],
        "Chủ đề 2: Số thập phân": [{"topic": "Khái niệm số thập phân", "periods": 8}],
        "Chủ đề 3: Đơn vị đo diện tích": [{"topic": "Km2, Ha", "periods": 4}]
      }
    }
  },
  "Tiếng Việt": {
    "Lớp 1": { "Cùng học để phát triển năng lực": { "Học vần": [{"topic": "Các âm vần cơ bản", "periods": 20}] } },
    "Lớp 2": { "Kết nối tri thức với cuộc sống": { "Chủ đề: Em lớn lên từng ngày": [{"topic": "Bài 1-4", "periods": 16}] } },
    "Lớp 3": { "Kết nối tri thức với cuộc sống": { "Chủ đề: Trải nghiệm thú vị": [{"topic": "Bài 1-5", "periods": 20}] } },
    "Lớp 4": { "Kết nối tri thức với cuộc sống": { "Chủ điểm: Mỗi người một vẻ": [{"topic": "Bài 1-4", "periods": 14}] } },
    "Lớp 5": { "Kết nối tri thức với cuộc sống": { "Chủ điểm: Thế giới tuổi thơ": [{"topic": "Bài 1-4", "periods": 14}] } }
  },
  "Khoa học": {
    "Lớp 4": { "Kết nối tri thức với cuộc sống": { "Chủ đề 1: Chất": [{"topic": "Nước, Không khí", "periods": 8}], "Chủ đề 2: Năng lượng": [{"topic": "Ánh sáng, Âm thanh", "periods": 6}] } },
    "Lớp 5": { "Kết nối tri thức với cuộc sống": { "Chủ đề 1: Chất": [{"topic": "Đất, Hỗn hợp", "periods": 9}], "Chủ đề 2: Năng lượng": [{"topic": "Năng lượng điện", "periods": 4}] } }
  },
  "Lịch sử & Địa lí": {
    "Lớp 4": { "Kết nối tri thức với cuộc sống": { "Chủ đề 1: Địa phương em": [{"topic": "Thiên nhiên, Văn hóa", "periods": 6}], "Chủ đề 2: Trung du Bắc Bộ": [{"topic": "Dân cư, Đền Hùng", "periods": 10}] } },
    "Lớp 5": { "Kết nối tri thức với cuộc sống": { "Chủ đề 1: Đất nước con người": [{"topic": "Vị trí, Thiên nhiên, Biển đảo", "periods": 12}] } }
  },
  "Tin học": {
    "Lớp 3": { "Kết nối tri thức với cuộc sống": { "Chủ đề 1: Máy tính và em": [{"topic": "Thông tin, Máy tính", "periods": 9}] } },
    "Lớp 4": { "Kết nối tri thức với cuộc sống": { "Chủ đề 1: Máy tính và em": [{"topic": "Phần cứng, Phần mềm", "periods": 4}] } },
    "Lớp 5": { "Kết nối tri thức với cuộc sống": { "Chủ đề 5: Ứng dụng tin học": [{"topic": "Soạn thảo văn bản", "periods": 4}] } }
  },
  "Công nghệ": {
    "Lớp 3": { "Kết nối tri thức với cuộc sống": { "Công nghệ đời sống": [{"topic": "Tự nhiên, Đèn học, Quạt", "periods": 9}] } },
    "Lớp 4": { "Kết nối tri thức với cuộc sống": { "Hoa và cây cảnh": [{"topic": "Lợi ích, Gieo hạt", "periods": 12}] } },
    "Lớp 5": { "Kết nối tri thức với cuộc sống": { "Nhà sáng chế": [{"topic": "Thiết kế sản phẩm", "periods": 10}] } }
  },
  "Tiếng Anh": {
    "Lớp 3": { "i-Learn Smart Start": { "Unit 1": [{"topic": "My Friends", "periods": 6}], "Unit 2": [{"topic": "Family", "periods": 4}] } },
    "Lớp 4": { "i-Learn Smart Start": { "Unit 1": [{"topic": "Animals", "periods": 9}], "Unit 2": [{"topic": "What I can do", "periods": 6}] } },
    "Lớp 5": { "i-Learn Smart Start": { "Unit 1": [{"topic": "School", "periods": 9}], "Unit 2": [{"topic": "Holidays", "periods": 6}] } }
  }
}

# ==========================================
# 2. HÀM HỖ TRỢ
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
    
    # Header chuẩn
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False
    tbl.columns[0].width = Inches(3.0)
    tbl.columns[1].width = Inches(3.5)
    
    c1 = tbl.cell(0,0); p1 = c1.paragraphs[0]; p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.add_run(f"PHÒNG GD&ĐT ............\n").font.size = Pt(12)
    p1.add_run(f"{school.upper()}").bold = True
    
    c2 = tbl.cell(0,1); p2 = c2.paragraphs[0]; p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM").bold = True
    p2.add_run("\nĐộc lập - Tự do - Hạnh phúc").bold = True
    
    doc.add_paragraph()
    p_title = doc.add_paragraph(); p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.add_run(f"{exam.upper()}").bold = True; p_title.font.size = Pt(14)
    doc.add_paragraph(f"Môn: {info['subj']} - Lớp: {info['grade']} ({info['book']})").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Thời gian làm bài: 40 phút").alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

    # Nội dung Đề
    for line in str(body).split('\n'):
        if line.strip():
            p = doc.add_paragraph()
            # In đậm các tiêu đề lớn
            if any(x in line.upper() for x in ["PHẦN I", "PHẦN II", "CÂU", "BÀI"]):
                p.add_run(line.strip()).bold = True
            else:
                p.add_run(line.strip())

    # Đáp án (Trang mới)
    doc.add_page_break()
    p_key = doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN")
    p_key.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_key.runs[0].bold = True
    doc.add_paragraph(str(key))

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def call_ai_generate(api_key, info, lessons, uploaded_ref):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Xây dựng nội dung yêu cầu
    lesson_text = "\n".join([f"- {l}" for l in lessons])
    
    ref_text = ""
    if uploaded_ref:
        ref_text = f"\n3. TÀI LIỆU MA TRẬN / ĐẶC TẢ MẪU (Hãy tuân thủ cấu trúc này):\n{uploaded_ref[:15000]}"

    prompt = f"""
    Đóng vai chuyên gia giáo dục tiểu học. Hãy soạn ĐỀ KIỂM TRA ĐỊNH KỲ môn {info['subj']} Lớp {info['grade']} - Bộ sách {info['book']}.
    
    1. NỘI DUNG KIẾN THỨC CẦN KIỂM TRA:
    {lesson_text}
    (Hãy tự truy xuất kiến thức chuẩn GDPT 2018 liên quan đến các bài học này để ra đề chính xác).

    2. CẤU TRÚC ĐỀ THI:
    - Tuân thủ Thông tư 27/2020/TT-BGDĐT.
    - Gồm: PHẦN I. TRẮC NGHIỆM và PHẦN II. TỰ LUẬN.
    - Đảm bảo tỷ lệ các mức độ: Hoàn thành tốt, Hoàn thành, Chưa hoàn thành (Mức 1, 2, 3).
    {ref_text}

    4. YÊU CẦU TRÌNH BÀY:
    - Ngôn ngữ trong sáng, phù hợp học sinh tiểu học.
    - Cuối cùng là PHẦN ĐÁP ÁN CHI TIẾT và Biểu điểm.
    - BẮT BUỘC: Ngăn cách giữa ĐỀ và ĐÁP ÁN bằng dòng chữ duy nhất: ###TACH_DAP_AN###
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "###TACH_DAP_AN###" in text:
            return text.split("###TACH_DAP_AN###")
        return text, "Không tìm thấy dấu tách. AI trả về toàn bộ nội dung."
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'preview_body' not in st.session_state: st.session_state.preview_body = ""
if 'preview_key' not in st.session_state: st.session_state.preview_key = ""

# Load Data
DATA_DB = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Cài đặt chung")
    st.markdown("""<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Lấy API Key miễn phí</a>""", unsafe_allow_html=True)
    api_key = st.text_input("Google API Key:", type="password")
    st.divider()
    school_name = st.text_input("Trường:", "TH PTDTBT GIÀNG CHU PHÌN")
    exam_name = st.text_input("Kỳ thi:", "KIỂM TRA CUỐI HỌC KÌ I")

# --- BƯỚC 1: CHỌN LỚP & MÔN ---
if st.session_state.step == 'home':
    st.markdown("<h2 style='text-align: center;'>HỆ THỐNG RA ĐỀ TIỂU HỌC (CHUẨN TT27)</h2>", unsafe_allow_html=True)
    st.markdown("#### 1️⃣ Chọn Khối Lớp")
    
    cols = st.columns(5)
    for i, g in enumerate(["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]):
        if cols[i].button(g, type="primary" if st.session_state.get('selected_grade') == g else "secondary", use_container_width=True):
            st.session_state.selected_grade = g
            st.session_state.selected_subject = None
            st.rerun()
            
    if st.session_state.get('selected_grade'):
        st.markdown("#### 2️⃣ Chọn Môn Học (Có đánh giá định kỳ)")
        valid_subs = VALID_SUBJECTS.get(st.session_state.selected_grade, [])
        c_sub = st.columns(4)
        for idx, s_name in enumerate(valid_subs):
            with c_sub[idx % 4]:
                if st.button(s_name, key=s_name, use_container_width=True):
                    st.session_state.selected_subject = s_name
                    st.session_state.step = 'config'
                    st.rerun()

# --- BƯỚC 2: CẤU HÌNH & TẠO ĐỀ ---
elif st.session_state.step == 'config':
    c1, c2 = st.columns([1, 6])
    if c1.button("⬅️ Quay lại"):
        st.session_state.step = 'home'
        st.rerun()
    
    grade = st.session_state.selected_grade
    subj = st.session_state.selected_subject
    c2.markdown(f"### 🚩 {grade} - {subj}")
    
    col_left, col_right = st.columns([1, 1.5])
    
    # TRÁI: CHỌN NỘI DUNG (TỪ JSON)
    with col_left:
        st.info("📚 Nội dung kiểm tra")
        
        # Lấy dữ liệu môn học
        db_grade = DATA_DB.get(subj, {}).get(grade, {})
        if not db_grade:
            st.warning("Đang cập nhật dữ liệu chi tiết. Vui lòng chọn Bộ sách mặc định.")
            books = ["Kết nối tri thức với cuộc sống", "Chân trời sáng tạo", "Cánh Diều"]
        else:
            books = list(db_grade.keys())
            
        sel_book = st.selectbox("Bộ sách:", books)
        
        topics = []
        if db_grade and sel_book in db_grade:
            topics = list(db_grade[sel_book].keys())
            
        sel_topic = st.selectbox("Chủ đề:", topics) if topics else None
        
        lesson_opts = []
        if sel_topic:
            raw_lessons = db_grade[sel_book][sel_topic]
            lesson_opts = [f"{l['topic']} ({l['periods']} tiết)" for l in raw_lessons]
            
        sel_lessons = st.multiselect("Chọn Bài học / Đơn vị kiến thức:", lesson_opts, default=lesson_opts)
        
    # PHẢI: UPLOAD FILE MA TRẬN
    with col_right:
        st.info("📂 Cấu trúc đề thi (Tùy chọn)")
        st.write("Tải lên file Ma trận / Đặc tả (PDF/Word/Excel) để AI ra đề đúng cấu trúc mong muốn.")
        uploaded_file = st.file_uploader("Upload file mẫu:", type=['pdf', 'docx', 'xlsx'])
        
        ref_content = ""
        if uploaded_file:
            with st.spinner("Đang đọc file..."):
                ref_content = read_uploaded_file(uploaded_file)
                st.success(f"Đã đọc xong: {uploaded_file.name}")
        
        st.divider()
        if st.button("🚀 SOẠN ĐỀ NGAY (XEM TRƯỚC)", type="primary", use_container_width=True):
            if not api_key:
                st.error("Vui lòng nhập Google API Key ở cột bên trái!")
            else:
                if not sel_lessons:
                    st.warning("Vui lòng chọn ít nhất 1 bài học!")
                else:
                    with st.spinner("AI đang phân tích chương trình và soạn đề..."):
                        info = {"subj": subj, "grade": grade, "book": sel_book}
                        body, key = call_ai_generate(api_key, info, sel_lessons, ref_content)
                        
                        if body:
                            st.session_state.preview_body = body
                            st.session_state.preview_key = key
                            st.session_state.info = info
                            st.session_state.step = 'preview'
                            st.rerun()
                        else:
                            st.error(key)

# --- BƯỚC 3: XEM TRƯỚC & TẢI ---
elif st.session_state.step == 'preview':
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅️ Quay lại chỉnh sửa", on_click=lambda: st.session_state.update(step='config')): pass
    
    c2.markdown("### 👁️ XEM TRƯỚC VÀ CHỈNH SỬA")
    st.info("Bạn có thể chỉnh sửa trực tiếp nội dung Đề và Đáp án trước khi xuất file Word.")
    
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
st.markdown('<div class="main-footer"></div>', unsafe_allow_html=True)
st.markdown('<div class="footer">© 2025 - Trần Ngọc Hải - Trường PTDTBT Tiểu học Giàng Chu Phìn - ĐT: 0944 134 973</div>', unsafe_allow_html=True)
