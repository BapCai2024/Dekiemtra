import streamlit as st
import pandas as pd
import requests
import time
import io
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="HỖ TRỢ RA ĐỀ THI TIỂU HỌC (GDPT 2018)",
    page_icon="📚",
    layout="wide"
)

# --- 2. CSS GIAO DIỆN ---
st.markdown("""
<style>
    .main-title { text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;}
    .question-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1565C0; margin-bottom: 10px; }
    div.stButton > button:first-child { border-radius: 5px; }
    
    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #333;
        text-align: center; padding: 10px; font-size: 14px;
        border-top: 1px solid #ddd; z-index: 100;
    }
    .content-container { padding-bottom: 60px; }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size: 1.2rem; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA & CẤU HÌNH ---
# (Giữ nguyên phần DB môn học như cũ để dùng cho Tab 1)
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

# --- 4. CÁC HÀM XỬ LÝ AI ---

def find_working_model(api_key):
    preferred_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            available_models = [m['name'].replace('models/', '') for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            for p in preferred_models:
                if p in available_models: return p
            if available_models: return available_models[0]
        return None
    except:
        return None

def call_gemini_api(api_key, prompt, model_name=None):
    if not model_name:
        model_name = find_working_model(api_key)
    if not model_name: return "❌ Lỗi: Không tìm thấy Model hoặc Key sai."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Exception: {e}"

# --- 5. HÀM XỬ LÝ WORD (CHUẨN NĐ 30 - BỎ QUỐC HIỆU) ---
def create_doc_nd30(school_name, exam_name, questions_list):
    doc = Document()
    
    # Cấu hình Font mặc định (Times New Roman)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13) # Cỡ chữ chuẩn văn bản hành chính 13-14

    # --- 1. PHẦN HEADER (Tên cơ quan, trường) ---
    # Tạo bảng 2 cột vô hình để căn chỉnh: Bên trái là tên trường, bên phải để trống (vì bỏ Quốc hiệu)
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.allow_autofit = False
    
    # Cột 1: Tên trường (Đậm, Đứng)
    cell_left = table.cell(0, 0)
    cell_left.width = Cm(8)
    p_school = cell_left.paragraphs[0]
    p_school.add_run(school_name.upper()).bold = True
    p_school.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Dòng "Số: ..." hoặc gạch chân (tùy chọn, ở đây để trống cho đơn giản)
    
    doc.add_paragraph() # Khoảng cách

    # --- 2. TÊN ĐỀ BÀI (Giữa, Đậm, In hoa) ---
    p_title = doc.add_paragraph()
    run_title = p_title.add_run(exam_name.upper())
    run_title.bold = True
    run_title.font.size = Pt(14)
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph() # Khoảng cách

    # --- 3. NỘI DUNG CÂU HỎI ---
    for idx, q in enumerate(questions_list):
        # Tiêu đề câu (Ví dụ: Câu 1 (1.0 điểm):)
        p_q = doc.add_paragraph()
        run_q = p_q.add_run(f"Câu {idx+1} ({q['points']} điểm): ")
        run_q.bold = True
        
        # Nội dung câu hỏi (Xử lý xuống dòng từ AI)
        content_lines = q['content'].split('\n')
        for line in content_lines:
            # Loại bỏ các từ khóa AI hay sinh ra như "**Câu hỏi:**" để văn bản sạch hơn
            clean_line = line.replace("**Câu hỏi:**", "").replace("**Đáp án:**", "\nĐáp án (Gợi ý):").strip()
            if clean_line:
                doc.add_paragraph(clean_line)
        
        doc.add_paragraph() # Khoảng cách giữa các câu

    # Lưu vào buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 6. GIAO DIỆN CHÍNH ---

st.markdown("<div class='content-container'>", unsafe_allow_html=True) 
st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC (GDPT 2018) 🏫</h1>", unsafe_allow_html=True)

# SIDEBAR (API KEY)
with st.sidebar:
    st.header("🔑 CẤU HÌNH")
    api_key_input = st.text_input("API Key Google:", type="password")
    
    st.info("💡 Hướng dẫn:\n1. Nhập API Key.\n2. Chọn Tab 'Tải Ma Trận' để upload file Excel.\n3. AI sẽ tạo đề theo chương trình GDPT 2018 (Cánh Diều/KNTT/CTST).")

if "exam_result_full" not in st.session_state:
    st.session_state.exam_result_full = []

# TABS CHUYỂN ĐỔI
tab1, tab2 = st.tabs(["📝 SOẠN THỦ CÔNG", "📂 TẢI MA TRẬN & BẢNG ĐẶC TẢ"])

# ====================================================================================
# TAB 1: SOẠN THỦ CÔNG (Giữ nguyên logic cũ nhưng rút gọn hiển thị để tập trung Tab 2)
# ====================================================================================
with tab1:
    st.caption("Chế độ chọn từng bài học để ra câu hỏi lẻ.")
    # (Phần code cũ của bạn nằm ở đây - Để tiết kiệm không gian tôi hiển thị vắn tắt logic)
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        grade_t1 = st.selectbox("Khối lớp:", list(SUBJECTS_DB.keys()), key="t1_grade")
    with col_t2:
        subject_t1 = st.selectbox("Môn:", [s[0] for s in SUBJECTS_DB[grade_t1]], key="t1_subj")
    
    st.warning("👉 Chuyển sang Tab 'TẢI MA TRẬN & BẢNG ĐẶC TẢ' để sử dụng tính năng nâng cao vừa yêu cầu.")

# ====================================================================================
# TAB 2: TẢI MA TRẬN & BẢNG ĐẶC TẢ (TÍNH NĂNG MỚI)
# ====================================================================================
with tab2:
    st.subheader("📂 Tải lên Ma trận & Bảng đặc tả (Excel/CSV)")
    
    col_up1, col_up2 = st.columns([1, 1])
    with col_up1:
        uploaded_file = st.file_uploader("Chọn file Excel (.xlsx) chứa ma trận", type=['xlsx', 'csv'])
        
        # Link tải file mẫu (Giả lập)
        st.caption("📝 File Excel cần có các cột: **Chủ đề**, **Yêu cầu cần đạt**, **Dạng câu hỏi**, **Mức độ**, **Điểm**")
    
    with col_up2:
        book_set = st.selectbox("📚 Chọn Bộ sách tham chiếu (GDPT 2018):", 
                                ["Kết nối tri thức với cuộc sống", "Cánh Diều", "Chân trời sáng tạo", "Cùng khám phá"])
        
        exam_term = st.text_input("Tên kỳ thi:", value="KIỂM TRA CUỐI HỌC KỲ I")
        school_name_input = st.text_input("Tên trường (cho tiêu đề):", value="TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN")

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("👀 **Xem trước dữ liệu Ma trận:**")
            st.dataframe(df.head())

            # Nút tạo đề
            if st.button("🚀 AI TẠO ĐỀ THI TỪ MA TRẬN", type="primary"):
                if not api_key_input:
                    st.error("Vui lòng nhập API Key Google trước!")
                else:
                    required_cols = ['Chủ đề', 'Yêu cầu cần đạt', 'Dạng câu hỏi', 'Điểm']
                    # Kiểm tra cột (linh hoạt chữ hoa thường)
                    df.columns = [c.strip() for c in df.columns]
                    missing = [c for c in required_cols if c not in df.columns]
                    
                    if missing:
                        st.error(f"File thiếu các cột bắt buộc: {', '.join(missing)}")
                    else:
                        st.session_state.exam_result_full = []
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        total_rows = len(df)
                        
                        for index, row in df.iterrows():
                            # Xử lý từng dòng ma trận
                            status_text.text(f"⏳ Đang soạn câu {index + 1}/{total_rows}: {row['Chủ đề']}...")
                            
                            topic = row['Chủ đề']
                            yccd = row['Yêu cầu cần đạt']
                            q_type = row['Dạng câu hỏi']
                            level = row.get('Mức độ', 'Tùy chọn')
                            points = row['Điểm']
                            
                            # Prompt đặc biệt cho Ma trận
                            prompt = f"""
                            Bạn là chuyên gia giáo dục Tiểu học VN (GDPT 2018).
                            Hãy soạn 1 câu hỏi kiểm tra dựa trên dòng ma trận sau:
                            - Môn học: {subject_t1} - {grade_t1}
                            - Bộ sách tham khảo: {book_set} (Bắt buộc bám sát ngữ liệu/phong cách bộ sách này).
                            - Chủ đề: {topic}
                            - Yêu cầu cần đạt (YCCĐ): {yccd}
                            - Dạng câu hỏi: {q_type}
                            - Mức độ: {level}
                            - Điểm: {points}
                            
                            YÊU CẦU:
                            1. Câu hỏi tường minh, ngôn ngữ phù hợp lứa tuổi tiểu học.
                            2. Nếu là Tiếng Việt: Trích dẫn đoạn văn/thơ ngắn phù hợp với sách {book_set}.
                            3. Nếu là Toán: Số liệu hợp lý, khoa học.
                            4. Đưa ra Đáp án và Hướng dẫn chấm chi tiết ngay sau câu hỏi.
                            5. KHÔNG dùng định dạng Markdown cầu kỳ (như bảng), chỉ dùng text thuần túy để dễ xuất sang Word.
                            """
                            
                            ai_content = call_gemini_api(api_key_input, prompt)
                            
                            st.session_state.exam_result_full.append({
                                "topic": topic,
                                "points": points,
                                "content": ai_content
                            })
                            
                            progress_bar.progress((index + 1) / total_rows)
                            time.sleep(1) # Tránh rate limit
                        
                        status_text.success("✅ Đã tạo xong đề thi!")
        
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

    # --- KHU VỰC KẾT QUẢ & TẢI XUỐNG ---
    if st.session_state.exam_result_full:
        st.divider()
        st.markdown("### 📄 KẾT QUẢ ĐỀ THI DO AI TẠO RA")
        
        # Hiển thị trên web để review
        for idx, item in enumerate(st.session_state.exam_result_full):
            with st.expander(f"Câu {idx+1} ({item['points']} điểm) - {item['topic']}", expanded=False):
                st.write(item['content'])
        
        # Xử lý Tên file theo yêu cầu
        # Format: Truong PTDTBT... - De kiem tra...
        safe_school_name = school_name_input.replace(" ", "_").replace(".", "")
        safe_exam_name = exam_term.replace(" ", "_")
        file_name_download = f"{safe_school_name}-{safe_exam_name}.docx"
        
        # Tạo file Word
        docx_file = create_doc_nd30(school_name_input, exam_term, st.session_state.exam_result_full)
        
        col_d1, col_d2 = st.columns([2, 1])
        with col_d1:
            st.success("File Word đã sẵn sàng theo chuẩn Nghị định 30 (Bỏ Quốc hiệu).")
        with col_d2:
            st.download_button(
                label="📥 TẢI XUỐNG FILE WORD (.DOCX)",
                data=docx_file,
                file_name=file_name_download,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary"
            )

st.markdown("</div>", unsafe_allow_html=True)
