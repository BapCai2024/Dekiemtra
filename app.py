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
    st.error("⚠️ Chưa cài đặt thư viện 'xlsxwriter'. Vui lòng chạy lệnh: pip install xlsxwriter (hoặc thêm vào requirements.txt nếu dùng Cloud).")
    st.stop()

# --- 3. CSS GIAO DIỆN ---
st.markdown("""
<style>
    .main-title { text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;}
    .question-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; border-left: 5px solid #1565C0; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div.stButton > button:first-child { border-radius: 5px; }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #333;
        text-align: center; padding: 10px; font-size: 14px;
        border-top: 1px solid #ddd; z-index: 100;
    }
    .content-container { padding-bottom: 60px; }
</style>
""", unsafe_allow_html=True)

# --- 4. CƠ SỞ DỮ LIỆU CHƯƠNG TRÌNH HỌC ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

# (Phần dữ liệu chi tiết CURRICULUM_DB bạn giữ nguyên như cũ để Tab 1 hoạt động)
CURRICULUM_DB = {} # Placeholder, bạn hãy paste lại dữ liệu đầy đủ của bạn vào đây.

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

def generate_question_from_matrix_row(api_key, row_data_str, header_str, q_type, level, points):
    clean_key = api_key.strip()
    model_name = find_working_model(clean_key)
    if not model_name: return "❌ Lỗi kết nối hoặc API Key."

    prompt = f"""
    Bạn là chuyên gia giáo dục Tiểu học, am hiểu chương trình GDPT 2018.
    
    NHIỆM VỤ:
    Soạn **1 CÂU HỎI KIỂM TRA** dựa trên thông tin ma trận được cung cấp dưới đây.
    
    DỮ LIỆU ĐẦU VÀO (Từ ma trận):
    - Cấu trúc các cột: {header_str}
    - Dữ liệu hàng cần soạn: {row_data_str}
    
    YÊU CẦU QUAN TRỌNG VỀ NGUỒN LIỆU (TUYỆT ĐỐI TUÂN THỦ):
    1. **Nguồn tham khảo duy nhất:** Các bộ sách giáo khoa hiện hành (**Kết nối tri thức với cuộc sống**, **Chân trời sáng tạo**, **Cánh diều**) và Chương trình GDPT 2018.
    2. **Tuyệt đối KHÔNG** sử dụng ngữ liệu ngoài luồng, không tự bịa đặt kiến thức sai lệch với SGK.
    3. Nội dung câu hỏi phải bám sát "Nội dung/Đơn vị kiến thức" và "Yêu cầu cần đạt" trong dữ liệu hàng ở trên.

    THÔNG TIN CÂU HỎI:
    - Dạng: {q_type}
    - Mức độ nhận thức: {level}
    - Điểm số: {points}
    - Nếu là trắc nghiệm: Phải có 4 đáp án A, B, C, D (chỉ 1 đúng).
    
    OUTPUT FORMAT (Trả về đúng định dạng sau):
    **Câu hỏi:** [Nội dung câu hỏi]
    **Đáp án:** [Đáp án đúng & Hướng dẫn chấm chi tiết]
    """
    return call_gemini_api(clean_key, model_name, prompt)

def create_excel_with_matrix_structure(exam_list):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # SHEET 1: ĐỀ THI
    ws_exam = workbook.add_worksheet("ĐỀ THI")
    format_wrap = workbook.add_format({'text_wrap': True, 'valign': 'top', 'font_name': 'Times New Roman', 'font_size': 13})
    format_bold = workbook.add_format({'bold': True, 'font_name': 'Times New Roman', 'font_size': 13})
    
    ws_exam.write(0, 0, "ĐỀ KIỂM TRA (Tạo bởi AI)", format_bold)
    row = 2
    for idx, q in enumerate(exam_list):
        ws_exam.write(row, 0, f"Câu {idx+1} ({q['points']} điểm):", format_bold)
        ws_exam.write(row+1, 0, q['content'], format_wrap)
        row += 3
    ws_exam.set_column(0, 0, 90)

    # SHEET 2: MA TRẬN (Mô phỏng cấu trúc file mẫu)
    ws_matrix = workbook.add_worksheet("MA TRẬN")
    
    # Định dạng Header
    header_fmt = workbook.add_format({
        'bold': True, 'align': 'center', 'valign': 'vcenter', 
        'border': 1, 'bg_color': '#D9E1F2', 'text_wrap': True, 'font_name': 'Times New Roman'
    })
    cell_fmt = workbook.add_format({
        'border': 1, 'text_wrap': True, 'valign': 'top', 'font_name': 'Times New Roman'
    })
    
    # Tạo Header phức tạp (Mô phỏng file mẫu CSV bạn gửi)
    # Dòng 1: Header chính
    ws_matrix.merge_range('A1:A3', 'TT', header_fmt)
    ws_matrix.merge_range('B1:B3', 'Chương/Chủ đề', header_fmt)
    ws_matrix.merge_range('C1:C3', 'Nội dung/Kiến thức', header_fmt)
    ws_matrix.merge_range('D1:D3', 'Yêu cầu cần đạt', header_fmt)
    
    # Khu vực Trắc nghiệm (Nhiều lựa chọn / Đúng sai / Nối cột) - Giả lập
    ws_matrix.merge_range('E1:M1', 'Trắc nghiệm (TN)', header_fmt)
    ws_matrix.merge_range('E2:G2', 'Nhiều lựa chọn', header_fmt)
    ws_matrix.merge_range('H2:J2', 'Đúng-Sai', header_fmt)
    ws_matrix.merge_range('K2:M2', 'Nối cột', header_fmt)
    
    # Mức độ con
    sub_headers = ['Biết', 'Hiểu', 'VD']
    for i, title in enumerate(sub_headers * 3): # Lặp lại cho 3 nhóm
        ws_matrix.write(2, 4 + i, title, header_fmt)

    # Khu vực Tự luận
    ws_matrix.merge_range('N1:P1', 'Tự luận (TL)', header_fmt)
    ws_matrix.merge_range('N2:P2', 'Các mức độ', header_fmt)
    ws_matrix.write(2, 13, 'Biết', header_fmt)
    ws_matrix.write(2, 14, 'Hiểu', header_fmt)
    ws_matrix.write(2, 15, 'VD', header_fmt)
    
    ws_matrix.merge_range('Q1:Q3', 'Tổng điểm', header_fmt)
    ws_matrix.merge_range('R1:R3', 'Câu số', header_fmt)

    # Ghi dữ liệu câu hỏi vào Ma trận
    r = 3
    for idx, q in enumerate(exam_list):
        ws_matrix.write(r, 0, idx+1, cell_fmt)
        
        # Nếu là câu hỏi từ file upload, ta có thông tin gốc
        # Nếu là thủ công, ta dùng thông tin đã chọn
        ws_matrix.write(r, 1, q.get('topic', ''), cell_fmt) 
        ws_matrix.write(r, 2, q.get('lesson', ''), cell_fmt)
        ws_matrix.write(r, 3, "Theo chuẩn KTKN", cell_fmt) 

        # Đánh dấu X vào ô mức độ tương ứng
        # Logic đơn giản để đánh dấu: 
        # Cột E-G: TN Nhiều lựa chọn
        # Cột N-P: Tự luận
        col_mark = -1
        is_tn = "Trắc nghiệm" in q['type']
        
        if is_tn:
            if "Biết" in q['level']: col_mark = 4
            elif "Hiểu" in q['level']: col_mark = 5
            elif "Vận dụng" in q['level']: col_mark = 6
        else: # Tự luận
            if "Biết" in q['level']: col_mark = 13
            elif "Hiểu" in q['level']: col_mark = 14
            elif "Vận dụng" in q['level']: col_mark = 15
            
        if col_mark != -1:
            ws_matrix.write(r, col_mark, "x", cell_fmt)
            
        ws_matrix.write(r, 16, q['points'], cell_fmt)
        ws_matrix.write(r, 17, f"Câu {idx+1}", cell_fmt)
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
        st.rerun()

# TABS
tab1, tab2 = st.tabs(["🛠️ Soạn thủ công", "📂 Soạn từ File Ma trận (Upload)"])

# === TAB 1: THỦ CÔNG ===
with tab1:
    st.info("Chức năng soạn theo Database có sẵn (Vui lòng điền CURRICULUM_DB đầy đủ để sử dụng).")
    # (Code phần này giữ nguyên như các phiên bản trước)

# === TAB 2: UPLOAD MA TRẬN ===
with tab2:
    st.markdown("### 📥 Tải lên Ma trận (Excel/CSV)")
    st.caption("Khuyên dùng file Excel (.xlsx) hoặc CSV để AI đọc chính xác nhất. File Word/PDF có thể gây lỗi định dạng.")
    
    uploaded_file = st.file_uploader("Chọn file:", type=['xlsx', 'xls', 'csv'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                # Bỏ qua các dòng trống ở đầu nếu có
                df = pd.read_csv(uploaded_file, header=None) 
            else:
                df = pd.read_excel(uploaded_file, header=None)
            
            st.session_state.uploaded_df = df
            st.success("Đọc file thành công!")
            
            # Hiển thị
            st.markdown("#### 👁️ Xem dữ liệu file:")
            st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 🤖 Cấu hình sinh câu hỏi")
            
            col_u1, col_u2 = st.columns([1, 2])
            with col_u1:
                row_index = st.number_input("Chọn STT dòng trong bảng để ra đề:", 
                                           min_value=0, max_value=len(df)-1, value=3, step=1)
                st.caption("Chọn dòng chứa 'Nội dung kiến thức' và 'YCCĐ'.")
                
                u_q_type = st.selectbox("Dạng câu:", ["Trắc nghiệm (4 lựa chọn)", "Đúng/Sai", "Điền khuyết", "Tự luận", "Nối đôi"], key="type_t2")
                u_level = st.selectbox("Mức độ:", ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"], key="level_t2")
                u_points = st.number_input("Điểm:", 0.25, 10.0, 1.0, 0.25, key="point_t2")

            with col_u2:
                # Lấy header giả định (dòng 2 trong file mẫu thường là header)
                header_row = df.iloc[2].fillna("").astype(str).tolist() if len(df) > 2 else []
                header_str = " | ".join(header_row)
                
                # Lấy data dòng chọn
                selected_row_data = df.iloc[row_index].fillna("").to_string(index=False)
                st.text_area("Dữ liệu gửi cho AI:", value=selected_row_data, height=150)
                
            if st.button("✨ AI Soạn câu hỏi", type="primary"):
                if not api_key_input:
                    st.error("Chưa nhập API Key.")
                else:
                    with st.spinner("Đang tra cứu SGK (KNTT/CTST/CD) & Soạn thảo..."):
                        preview_u = generate_question_from_matrix_row(
                            api_key_input, selected_row_data, header_str, u_q_type, u_level, u_points
                        )
                        st.session_state.current_preview = preview_u
                        st.session_state.temp_question_data = {
                            "topic": "Từ Ma trận Upload", 
                            "lesson": f"Dữ liệu dòng {row_index}",
                            "type": u_q_type, 
                            "level": u_level, 
                            "points": u_points, 
                            "content": preview_u
                        }
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")

# === KẾT QUẢ & XUẤT FILE ===
if st.session_state.current_preview:
    st.markdown("---")
    st.markdown("### 👁️ Kết quả:")
    with st.container():
        st.markdown(f"<div class='question-box'>{st.session_state.current_preview}</div>", unsafe_allow_html=True)
    
    if st.button("✅ Thêm vào đề"):
        if st.session_state.temp_question_data:
            st.session_state.exam_list.append(st.session_state.temp_question_data)
            st.session_state.current_preview = ""
            st.session_state.temp_question_data = None
            st.rerun()

st.markdown("---")
st.subheader("📥 Tải xuống Đề thi & Ma trận")

if len(st.session_state.exam_list) > 0:
    col_d1, col_d2 = st.columns(2)
    
    # Nút tải Excel
    excel_data = create_excel_with_matrix_structure(st.session_state.exam_list)
    with col_d1:
        st.download_button(
            label="📄 Tải Excel (.xlsx) - Kèm Ma trận mẫu",
            data=excel_data,
            file_name="De_thi_Ma_tran.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

    # Nút tải Word (Text)
    word_text = "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN\nĐỀ KIỂM TRA\n\n"
    for idx, q in enumerate(st.session_state.exam_list):
        word_text += f"Câu {idx+1} ({q['points']}đ):\n{q['content']}\n\n"
        
    with col_d2:
        st.download_button(
            label="📄 Tải Word/Text (.doc)",
            data=word_text,
            file_name="De_thi.doc",
            mime="application/msword"
        )
else:
    st.info("Danh sách trống.")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("""<div class="footer"><p style="margin: 0; font-weight: bold;">🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</p></div>""", unsafe_allow_html=True)
