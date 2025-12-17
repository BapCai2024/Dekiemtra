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
    st.error("⚠️ Hệ thống thiếu thư viện 'xlsxwriter'. Nếu chạy trên máy cá nhân, hãy cài đặt bằng lệnh: `pip install xlsxwriter`.")
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
    /* Tabs custom */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f8f9fa; border-radius: 5px 5px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #e3f2fd; color: #0d47a1; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 4. CƠ SỞ DỮ LIỆU CHƯƠNG TRÌNH HỌC (GIỮ NGUYÊN DB CŨ CỦA BẠN) ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

# (Placeholder: Bạn hãy giữ nguyên CURRICULUM_DB đầy đủ trong code cũ của bạn)
CURRICULUM_DB = {
    "Lớp 1": {"Toán": {"Học kỳ I": [{"Chủ đề": "Số học", "Bài học": "Các số đến 10", "YCCĐ": "Đếm, đọc, viết số."}]}}
}

# --- 5. CÁC HÀM XỬ LÝ API VÀ LOGIC ---

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
    Bạn là chuyên gia giáo dục Tiểu học, am hiểu sâu sắc Chương trình GDPT 2018.
    
    NHIỆM VỤ:
    Soạn **1 CÂU HỎI KIỂM TRA** dựa trên dữ liệu từ dòng ma trận sau:
    "{row_data_str}"
    
    ⚠️ YÊU CẦU BẮT BUỘC VỀ NGUỒN DỮ LIỆU (TUÂN THỦ NGHIÊM NGẶT):
    1. **NGUỒN THAM KHẢO DUY NHẤT:** Chỉ được sử dụng ngữ liệu, kiến thức, và phong cách diễn đạt từ 03 bộ sách giáo khoa hiện hành:
       - **Kết nối tri thức với cuộc sống**
       - **Chân trời sáng tạo**
       - **Cánh diều**
       - Và **Chương trình Giáo dục phổ thông 2018**.
    2. **CẤM:** Tuyệt đối không tự bịa đặt kiến thức, không lấy dữ liệu từ các nguồn cũ (như VNEN, sách chương trình năm 2000).
    3. Nội dung câu hỏi phải bám sát "Nội dung kiến thức" và "Yêu cầu cần đạt" trong dữ liệu cung cấp.

    THÔNG TIN CẤU TRÚC:
    - Dạng câu hỏi: {q_type}
    - Mức độ nhận thức: {level}
    - Điểm số: {points} điểm.
    - Nếu là trắc nghiệm: Phải có 4 đáp án A, B, C, D (chỉ 1 đúng).
    - Ngôn ngữ: Trong sáng, phù hợp tâm lý lứa tuổi tiểu học.

    OUTPUT FORMAT (Trả về đúng định dạng này để hiển thị):
    **Câu hỏi:** [Nội dung câu hỏi chi tiết]
    **Đáp án:** [Đáp án đúng và Hướng dẫn chấm ngắn gọn]
    """
    return call_gemini_api(clean_key, model_name, prompt)

# Hàm xuất Excel mô phỏng đúng cấu trúc file mẫu Ma trận
def create_complex_excel(exam_list):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # --- SHEET 1: ĐỀ THI (Nội dung câu hỏi) ---
    ws_exam = workbook.add_worksheet("ĐỀ THI")
    fmt_wrap = workbook.add_format({'text_wrap': True, 'valign': 'top', 'font_name': 'Times New Roman', 'font_size': 13})
    fmt_bold = workbook.add_format({'bold': True, 'font_name': 'Times New Roman', 'font_size': 13})
    
    ws_exam.write(0, 0, "ĐỀ KIỂM TRA (Tạo bởi AI - Nguồn SGK 2018)", fmt_bold)
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

    # Tạo Header 3 dòng (Mô phỏng file mẫu)
    # Dòng 1
    ws_matrix.merge_range('A1:A3', 'TT', header_fmt)
    ws_matrix.merge_range('B1:B3', 'Chương/Chủ đề', header_fmt)
    ws_matrix.merge_range('C1:C3', 'Nội dung/Kiến thức', header_fmt)
    ws_matrix.merge_range('D1:D3', 'Yêu cầu cần đạt', header_fmt)
    ws_matrix.merge_range('E1:E3', 'Số tiết', header_fmt)
    ws_matrix.merge_range('F1:F3', 'Tỉ lệ', header_fmt)
    ws_matrix.merge_range('G1:G3', 'Số điểm', header_fmt)

    # Khu vực Trắc nghiệm (Cột H đến S - 4 nhóm x 3 cột = 12 cột)
    ws_matrix.merge_range('H1:S1', 'Trắc nghiệm', header_fmt)
    
    # Dòng 2: Loại Trắc nghiệm
    ws_matrix.merge_range('H2:J2', 'Nhiều lựa chọn', header_fmt)
    ws_matrix.merge_range('K2:M2', 'Đúng-Sai', header_fmt)
    ws_matrix.merge_range('N2:P2', 'Nối cột', header_fmt)
    ws_matrix.merge_range('Q2:S2', 'Điền khuyết', header_fmt)
    
    # Khu vực Tự luận (Cột T đến V - 3 cột)
    ws_matrix.merge_range('T1:V1', 'Tự luận', header_fmt)
    ws_matrix.merge_range('T2:V2', 'Các mức độ', header_fmt)

    ws_matrix.merge_range('W1:W3', 'Tổng số câu', header_fmt)
    ws_matrix.merge_range('X1:X3', 'Điểm bài', header_fmt)

    # Dòng 3: Mức độ (Biết, Hiểu, VD)
    levels = ['Biết', 'Hiểu', 'VD']
    # Loop cho TN (4 nhóm) và TL (1 nhóm) -> Tổng 5 nhóm = 15 cột
    start_col = 7 # Cột H (index 7)
    for i in range(15):
        ws_matrix.write(2, start_col + i, levels[i % 3], header_fmt)

    # Ghi dữ liệu
    r = 3
    for idx, q in enumerate(exam_list):
        ws_matrix.write(r, 0, idx+1, cell_fmt)
        ws_matrix.write(r, 1, q.get('topic', ''), cell_fmt)
        ws_matrix.write(r, 2, q.get('lesson', ''), cell_fmt)
        ws_matrix.write(r, 3, "Chi tiết xem đề thi", cell_fmt)
        
        # Đánh dấu X vào ô ma trận
        col_idx = -1
        is_tn = "Trắc nghiệm" in q['type'] or "Nối" in q['type'] or "Điền" in q['type'] or "Đúng" in q['type']
        
        # Xác định nhóm cột cơ sở
        if is_tn:
            if "Nhiều lựa chọn" in q['type'] or "4 lựa chọn" in q['type']: base = 7 # H
            elif "Đúng/Sai" in q['type']: base = 10 # K
            elif "Nối" in q['type']: base = 13 # N
            elif "Điền" in q['type']: base = 16 # Q
            else: base = 7
        else: # Tự luận
            base = 19 # T
            
        # Xác định mức độ (Offset 0, 1, 2)
        offset = 0
        if "Hiểu" in q['level']: offset = 1
        elif "Vận dụng" in q['level']: offset = 2
        
        col_idx = base + offset
        if 0 <= col_idx <= 21:
            ws_matrix.write(r, col_idx, "x", cell_fmt)
            
        ws_matrix.write(r, 23, q['points'], cell_fmt)
        r += 1

    ws_matrix.set_column('B:D', 25)
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
tab1, tab2 = st.tabs(["🛠️ Soạn thủ công (Theo DB)", "📂 Soạn từ File Ma trận (Upload)"])

# === TAB 1: SOẠN THỦ CÔNG (GIỮ NGUYÊN) ===
with tab1:
    st.info("Chế độ soạn câu hỏi dựa trên Cơ sở dữ liệu có sẵn trong hệ thống.")
    # (Phần logic cũ của bạn sẽ nằm ở đây - Giữ nguyên code cũ nếu cần)
    col1, col2 = st.columns(2)
    with col1:
        selected_grade = st.selectbox("Chọn Khối Lớp:", list(SUBJECTS_DB.keys()), key="grade_t1")
    with col2:
        subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
        selected_subject_full = st.selectbox("Chọn Môn Học:", subjects_list, key="subj_t1")
        selected_subject = selected_subject_full.split(" ", 1)[1]
    
    raw_data = CURRICULUM_DB.get(selected_grade, {}).get(selected_subject, {})
    if raw_data:
        # ... (Phần logic chọn bài học cũ của bạn)
        st.write("(Sử dụng các control như phiên bản trước để chọn bài học...)")
    else:
        st.warning("Đang cập nhật dữ liệu môn học này.")

# === TAB 2: UPLOAD MA TRẬN ===
with tab2:
    st.markdown("### 📥 Tải lên Ma trận đề thi")
    st.caption("Hỗ trợ file Excel (.xlsx) hoặc CSV để AI đọc chính xác nhất cấu trúc ma trận.")
    
    uploaded_file = st.file_uploader("Chọn file Ma trận:", type=['xlsx', 'xls', 'csv', 'docx', 'pdf'])
    
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        
        try:
            if file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file, header=None)
                st.session_state.uploaded_df = df
                st.success("Đã đọc file Excel thành công!")
            elif file_ext == 'csv':
                df = pd.read_csv(uploaded_file, header=None)
                st.session_state.uploaded_df = df
                st.success("Đã đọc file CSV thành công!")
            else:
                # Word/PDF handling
                st.warning("⚠️ Với file Word/PDF, hệ thống chưa hỗ trợ đọc bảng tự động do cấu trúc phức tạp. Vui lòng copy nội dung dòng ma trận vào ô bên dưới.")
                st.session_state.uploaded_df = None

            # HIỂN THỊ VÀ CHỌN DÒNG
            if st.session_state.uploaded_df is not None:
                st.markdown("#### 👁️ Xem trước Ma trận:")
                st.dataframe(st.session_state.uploaded_df.head(10), use_container_width=True)
                
                col_u1, col_u2 = st.columns([1, 2])
                with col_u1:
                    row_index = st.number_input("Chọn STT dòng trong bảng để ra đề:", 
                                               min_value=0, max_value=len(st.session_state.uploaded_df)-1, value=0)
                    st.caption("Hãy chọn dòng chứa 'Nội dung kiến thức' và 'YCCĐ'.")
                    
                    # Lấy dữ liệu dòng
                    selected_row_data = st.session_state.uploaded_df.iloc[row_index].fillna("").to_string(index=False)
            else:
                selected_row_data = st.text_area("Paste nội dung dòng ma trận vào đây:", height=100)

            # CẤU HÌNH CÂU HỎI
            st.markdown("---")
            st.markdown("### 📝 Cấu hình câu hỏi (AI)")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                u_q_type = st.selectbox("Dạng câu:", ["Trắc nghiệm (4 lựa chọn)", "Đúng/Sai", "Nối cột", "Điền khuyết", "Tự luận"], key="type_u")
            with col_c2:
                u_level = st.selectbox("Mức độ:", ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"], key="level_u")
            with col_c3:
                u_points = st.number_input("Điểm:", 0.25, 10.0, 1.0, 0.25, key="point_u")

            if st.button("✨ AI Soạn Đề (Nguồn SGK 2018)", type="primary"):
                if not api_key_input:
                    st.error("Chưa nhập API Key.")
                else:
                    with st.spinner("Đang tra cứu SGK (KNTT/CTST/CD) & Soạn thảo..."):
                        preview_u = generate_question_from_matrix_row(
                            api_key_input, selected_row_data, u_q_type, u_level, u_points
                        )
                        st.session_state.current_preview = preview_u
                        st.session_state.temp_question_data = {
                            "topic": "Từ File Upload", 
                            "lesson": f"Dòng {row_index}" if st.session_state.uploaded_df is not None else "Từ nội dung paste",
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
    st.markdown("### 📝 Nội dung Đề thi (AI vừa tạo):")
    st.info("Đây là nội dung câu hỏi được sinh ra từ dòng ma trận bạn chọn. Hãy kiểm tra kỹ trước khi thêm vào đề.")
    
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
st.subheader("📥 Tải xuống (File Ma trận & Đề)")

if len(st.session_state.exam_list) > 0:
    col_d1, col_d2 = st.columns(2)
    
    # Nút tải Excel (Đúng mẫu ma trận)
    excel_data = create_complex_excel(st.session_state.exam_list)
    with col_d1:
        st.download_button(
            label="📄 Tải Excel (.xlsx) - Đề + Ma trận chuẩn",
            data=excel_data,
            file_name="De_thi_SGK_Moi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    
    # Nút tải Word (Nội dung Text)
    word_text = "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN\nĐỀ KIỂM TRA (NGUỒN SGK 2018)\n\n"
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
