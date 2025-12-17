import streamlit as st
import pandas as pd
import requests
import time
import io

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="HỖ TRỢ RA ĐỀ THI TIỂU HỌC (GDPT 2018)",
    page_icon="📚",
    layout="wide"
)

# --- 2. XỬ LÝ THƯ VIỆN BỔ SUNG ---
try:
    import xlsxwriter
except ImportError:
    st.error("⚠️ Hệ thống thiếu thư viện 'xlsxwriter'. Nếu bạn chạy trên máy cá nhân, hãy mở Terminal và gõ: `pip install xlsxwriter`.")
    st.stop()

# --- 3. CSS GIAO DIỆN ---
st.markdown("""
<style>
    .main-title { text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;}
    .question-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; border-left: 5px solid #1565C0; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #333;
        text-align: center; padding: 10px; font-size: 14px;
        border-top: 1px solid #ddd; z-index: 100;
    }
    .content-container { padding-bottom: 60px; }
</style>
""", unsafe_allow_html=True)

# --- 4. CƠ SỞ DỮ LIỆU GIẢ LẬP (BẠN HÃY PASTE DB ĐẦY ĐỦ CỦA BẠN VÀO ĐÂY) ---
# Để code gọn, mình để placeholder.
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}
CURRICULUM_DB = {} # Vui lòng paste dữ liệu chi tiết của bạn vào đây

# --- 5. CÁC HÀM XỬ LÝ ---

def find_working_model(api_key):
    preferred_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            available = [m['name'].replace('models/', '') for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
            for p in preferred_models:
                if p in available: return p
            return available[0] if available else None
        return None
    except: return None

def call_gemini_api(api_key, model_name, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Lỗi API: {response.text}"
    except Exception as e:
        return f"Lỗi mạng: {e}"

def generate_question_from_matrix_row(api_key, row_data_str, q_type, level, points):
    clean_key = api_key.strip()
    model_name = find_working_model(clean_key)
    if not model_name: return "❌ Lỗi kết nối hoặc API Key."

    prompt = f"""
    Bạn là chuyên gia giáo dục Tiểu học (GDPT 2018).
    
    NHIỆM VỤ:
    Soạn **1 CÂU HỎI KIỂM TRA** dựa trên thông tin ma trận sau:
    "{row_data_str}"
    
    ⚠️ YÊU CẦU TUYỆT ĐỐI VỀ NGUỒN DỮ LIỆU:
    1. **Chỉ được sử dụng** ngữ liệu và kiến thức từ các bộ sách giáo khoa đang hành: 
       - **Kết nối tri thức với cuộc sống**
       - **Chân trời sáng tạo**
       - **Cánh diều**
       - Và **Chương trình GDPT 2018**.
    2. **TUYỆT ĐỐI KHÔNG** lấy dữ liệu từ nguồn ngoài, không tự bịa đặt kiến thức không có trong chương trình.
    3. Nội dung câu hỏi phải bám sát "Nội dung kiến thức" và "Yêu cầu cần đạt" trong đoạn text trên.

    THÔNG TIN CẤU TRÚC:
    - Dạng: {q_type}
    - Mức độ: {level}
    - Điểm: {points}
    - Nếu là trắc nghiệm: Phải có 4 đáp án A, B, C, D (chỉ 1 đúng).

    OUTPUT FORMAT:
    **Câu hỏi:** [Nội dung câu hỏi]
    **Đáp án:** [Đáp án đúng và hướng dẫn chấm]
    """
    return call_gemini_api(clean_key, model_name, prompt)

# Hàm xuất Excel mô phỏng đúng file mẫu bạn gửi
def create_complex_excel(exam_list):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # --- SHEET 1: ĐỀ THI (Nội dung) ---
    ws_exam = workbook.add_worksheet("ĐỀ THI")
    fmt_wrap = workbook.add_format({'text_wrap': True, 'valign': 'top', 'font_name': 'Times New Roman', 'font_size': 13})
    fmt_bold = workbook.add_format({'bold': True, 'font_name': 'Times New Roman', 'font_size': 13})
    
    ws_exam.write(0, 0, "ĐỀ KIỂM TRA (Tạo bởi AI - Nguồn SGK)", fmt_bold)
    row = 2
    for idx, q in enumerate(exam_list):
        ws_exam.write(row, 0, f"Câu {idx+1} ({q['points']} điểm) - {q['level']}:", fmt_bold)
        ws_exam.write(row+1, 0, q['content'], fmt_wrap)
        row += 3
    ws_exam.set_column(0, 0, 90)

    # --- SHEET 2: MA TRẬN (Đúng mẫu file gốc) ---
    ws_matrix = workbook.add_worksheet("MA TRẬN")
    
    # Format Header
    header_fmt = workbook.add_format({
        'bold': True, 'align': 'center', 'valign': 'vcenter', 
        'border': 1, 'bg_color': '#D9E1F2', 'text_wrap': True, 'font_name': 'Times New Roman', 'font_size': 11
    })
    cell_fmt = workbook.add_format({
        'border': 1, 'text_wrap': True, 'valign': 'top', 'font_name': 'Times New Roman', 'font_size': 11
    })

    # Tạo Header 3 dòng như file mẫu
    # Dòng 1: Header cấp 1
    ws_matrix.merge_range('A1:A3', 'TT', header_fmt)
    ws_matrix.merge_range('B1:B3', 'Chương/Chủ đề', header_fmt)
    ws_matrix.merge_range('C1:C3', 'Nội dung/Kiến thức', header_fmt)
    ws_matrix.merge_range('D1:D3', 'Yêu cầu cần đạt', header_fmt)
    ws_matrix.merge_range('E1:E3', 'Số tiết', header_fmt)
    ws_matrix.merge_range('F1:F3', 'Tỉ lệ', header_fmt)
    ws_matrix.merge_range('G1:G3', 'Số điểm', header_fmt)

    # Khu vực Trắc nghiệm (Cột H đến S - 12 cột)
    ws_matrix.merge_range('H1:S1', 'Trắc nghiệm', header_fmt)
    # Dòng 2: Loại Trắc nghiệm
    ws_matrix.merge_range('H2:J2', 'Nhiều lựa chọn', header_fmt)
    ws_matrix.merge_range('K2:M2', 'Đúng-Sai', header_fmt)
    ws_matrix.merge_range('N2:P2', 'Nối cột', header_fmt)
    ws_matrix.merge_range('Q2:S2', 'Điền khuyết', header_fmt)
    
    # Khu vực Tự luận (Cột T đến V - 3 cột)
    ws_matrix.merge_range('T1:V1', 'Tự luận', header_fmt)
    ws_matrix.merge_range('T2:V2', 'Các mức độ', header_fmt) # Hoặc để trống

    ws_matrix.merge_range('W1:W3', 'Tổng số câu', header_fmt)
    ws_matrix.merge_range('X1:X3', 'Điểm bài', header_fmt)

    # Dòng 3: Mức độ (Biết, Hiểu, VD lặp lại)
    levels = ['Biết', 'Hiểu', 'VD']
    # TN: 4 nhóm * 3 mức = 12 cột (H -> S)
    for i in range(12):
        ws_matrix.write(2, 7 + i, levels[i % 3], header_fmt)
    # TL: 1 nhóm * 3 mức = 3 cột (T -> V)
    for i in range(3):
        ws_matrix.write(2, 19 + i, levels[i], header_fmt)

    # Ghi dữ liệu (Mapping đơn giản)
    r = 3
    for idx, q in enumerate(exam_list):
        ws_matrix.write(r, 0, idx+1, cell_fmt)
        ws_matrix.write(r, 1, q.get('topic', ''), cell_fmt)
        ws_matrix.write(r, 2, q.get('lesson', ''), cell_fmt)
        ws_matrix.write(r, 3, "Chi tiết trong đề", cell_fmt)
        
        # Đánh dấu X
        col_idx = -1
        is_tn = "Trắc nghiệm" in q['type']
        
        # Xác định nhóm cột
        if is_tn:
            if "Nhiều lựa chọn" in q['type'] or "4 lựa chọn" in q['type']: base = 7
            elif "Đúng/Sai" in q['type']: base = 10
            elif "Nối" in q['type']: base = 13
            elif "Điền" in q['type']: base = 16
            else: base = 7 # Mặc định
        else: # Tự luận
            base = 19
            
        # Xác định mức độ (Offset 0, 1, 2)
        offset = 0
        if "Hiểu" in q['level']: offset = 1
        elif "Vận dụng" in q['level']: offset = 2
        
        col_idx = base + offset
        if 0 <= col_idx <= 21: # Kiểm tra trong vùng ma trận
            ws_matrix.write(r, col_idx, "x", cell_fmt)
            
        ws_matrix.write(r, 23, q['points'], cell_fmt)
        r += 1

    ws_matrix.set_column('B:D', 20)
    workbook.close()
    output.seek(0)
    return output

# --- 6. QUẢN LÝ STATE ---
if "exam_list" not in st.session_state: st.session_state.exam_list = [] 
if "current_preview" not in st.session_state: st.session_state.current_preview = "" 
if "temp_question_data" not in st.session_state: st.session_state.temp_question_data = None 
if "uploaded_df" not in st.session_state: st.session_state.uploaded_df = None

# --- 7. GIAO DIỆN CHÍNH ---

st.markdown("<div class='content-container'>", unsafe_allow_html=True) 
st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.header("🔑 CẤU HÌNH")
    api_key_input = st.text_input("API Key Google:", type="password")
    
    st.markdown("---")
    st.write("📊 **Thống kê:**")
    st.write(f"Số câu: {len(st.session_state.exam_list)}")
    st.write(f"Tổng điểm: {sum([q['points'] for q in st.session_state.exam_list])}/10")
    
    if st.button("🗑️ Xóa làm lại"):
        st.session_state.exam_list = []
        st.session_state.current_preview = ""
        st.session_state.uploaded_df = None
        st.rerun()

# TABS
tab1, tab2 = st.tabs(["🛠️ Soạn thủ công (DB)", "📂 Soạn từ File Ma trận (Upload)"])

# === TAB 1: THỦ CÔNG ===
with tab1:
    st.info("Chế độ soạn dựa trên Database có sẵn.")
    # (Phần này giữ nguyên logic cũ, bạn paste lại nếu cần dùng)

# === TAB 2: UPLOAD MA TRẬN ===
with tab2:
    st.markdown("### 📥 Tải lên Ma trận đề thi")
    st.caption("Hỗ trợ: Excel (.xlsx), CSV, Word, PDF. (Khuyên dùng Excel/CSV để AI đọc chính xác nhất).")
    
    uploaded_file = st.file_uploader("Chọn file Ma trận:", type=['xlsx', 'xls', 'csv', 'docx', 'pdf'])
    
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        # Xử lý đọc file
        try:
            if file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file, header=None)
                st.session_state.uploaded_df = df
                st.success("Đã đọc file Excel.")
            elif file_ext == 'csv':
                df = pd.read_csv(uploaded_file, header=None)
                st.session_state.uploaded_df = df
                st.success("Đã đọc file CSV.")
            else:
                # Với Word/PDF, chỉ thông báo (vì khó parse bảng tự động chính xác trên web đơn giản)
                st.warning("Với file Word/PDF, vui lòng mở file trên máy tính và copy nội dung dòng cần ra đề vào ô bên dưới.")
                st.session_state.uploaded_df = None

            # HIỂN THỊ MA TRẬN (Nếu là Excel/CSV)
            if st.session_state.uploaded_df is not None:
                st.markdown("#### 👁️ Xem trước Ma trận:")
                st.dataframe(st.session_state.uploaded_df.head(10), use_container_width=True)
                
                col_u1, col_u2 = st.columns([1, 2])
                with col_u1:
                    row_index = st.number_input("Chọn dòng (STT) trong bảng trên:", min_value=0, max_value=len(st.session_state.uploaded_df)-1, value=0)
                    selected_row_data = st.session_state.uploaded_df.iloc[row_index].fillna("").to_string(index=False)
            else:
                selected_row_data = st.text_area("Paste nội dung dòng ma trận vào đây (Nếu là file Word/PDF):")

            # CẤU HÌNH SINH CÂU HỎI
            st.markdown("---")
            st.markdown("### 📝 Cấu hình câu hỏi")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                u_q_type = st.selectbox("Dạng câu:", ["Trắc nghiệm (4 lựa chọn)", "Đúng/Sai", "Nối cột", "Điền khuyết", "Tự luận"])
            with col_c2:
                u_level = st.selectbox("Mức độ:", ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"])
            with col_c3:
                u_points = st.number_input("Điểm:", 0.25, 10.0, 1.0, 0.25)

            if st.button("✨ AI Soạn đề (Nguồn SGK)", type="primary"):
                if not api_key_input:
                    st.error("Chưa nhập API Key.")
                else:
                    with st.spinner("Đang tra cứu SGK (KNTT/CTST/CD) & GDPT 2018..."):
                        preview_u = generate_question_from_matrix_row(
                            api_key_input, selected_row_data, u_q_type, u_level, u_points
                        )
                        st.session_state.current_preview = preview_u
                        st.session_state.temp_question_data = {
                            "topic": "Từ Ma trận Upload", 
                            "lesson": "Theo file",
                            "type": u_q_type, 
                            "level": u_level, 
                            "points": u_points, 
                            "content": preview_u
                        }

        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

# === HIỂN THỊ KẾT QUẢ (NỘI DUNG ĐỀ THI) ===
if st.session_state.current_preview:
    st.markdown("---")
    st.markdown("### 📝 Nội dung Đề thi (AI tạo):")
    st.info("Dưới đây là nội dung đề thi được tạo ra. Bảng ma trận sẽ được cập nhật khi bạn tải file về.")
    
    with st.container():
        st.markdown(f"<div class='question-box'>{st.session_state.current_preview}</div>", unsafe_allow_html=True)
    
    if st.button("✅ Chốt câu hỏi này (Thêm vào danh sách)"):
        if st.session_state.temp_question_data:
            st.session_state.exam_list.append(st.session_state.temp_question_data)
            st.session_state.current_preview = ""
            st.session_state.temp_question_data = None
            st.success("Đã thêm vào danh sách!")
            st.rerun()

# === TẢI XUỐNG ===
st.markdown("---")
st.subheader("📥 Tải xuống (Đúng mẫu Ma trận đính kèm)")

if len(st.session_state.exam_list) > 0:
    col_d1, col_d2 = st.columns(2)
    
    # Excel
    excel_data = create_complex_excel(st.session_state.exam_list)
    with col_d1:
        st.download_button(
            label="📄 Tải Excel (.xlsx) - Đề + Ma trận chuẩn",
            data=excel_data,
            file_name="De_thi_SGK_Moi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    
    # Word (Text content)
    word_text = "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN\nĐỀ KIỂM TRA\n\n"
    for idx, q in enumerate(st.session_state.exam_list):
        word_text += f"Câu {idx+1} ({q['points']}đ):\n{q['content']}\n\n"
        
    with col_d2:
        st.download_button(
            label="📄 Tải Word (.doc) - Nội dung đề",
            data=word_text,
            file_name="De_thi_SGK_Moi.doc",
            mime="application/msword"
        )
else:
    st.write("Danh sách trống.")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("""<div class="footer"><p style="margin: 0; font-weight: bold;">🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</p></div>""", unsafe_allow_html=True)
