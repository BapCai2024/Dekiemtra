import streamlit as st
import pandas as pd
import requests
import time
import io
import xlsxwriter

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

# --- 3. CƠ SỞ DỮ LIỆU (BẠN GIỮ NGUYÊN DB ĐẦY ĐỦ CỦA BẠN Ở ĐÂY) ---
# Để code gọn, mình để placeholder, bạn hãy paste lại nội dung CURRICULUM_DB đầy đủ vào nhé.
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

# (Lưu ý: Bạn PASTE lại cái CURRICULUM_DB khổng lồ của phiên bản trước vào đây để Tab 1 hoạt động nhé)
CURRICULUM_DB = {
    "Lớp 1": {"Toán": {"Học kỳ I": [{"Chủ đề": "Demo", "Bài học": "Bài Demo (Cần paste lại DB đầy đủ)", "YCCĐ": "Demo YCCĐ"}]}} 
}

# --- 4. CÁC HÀM XỬ LÝ ---

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

# Hàm tạo câu hỏi từ Ma trận Upload (Cập nhật Prompt nghiêm ngặt)
def generate_question_from_matrix_row(api_key, row_data_str, q_type, level, points):
    clean_key = api_key.strip()
    model_name = find_working_model(clean_key)
    if not model_name: return "❌ Lỗi kết nối hoặc API Key."

    prompt = f"""
    Bạn là một chuyên gia soạn đề thi Tiểu học theo chương trình GDPT 2018.
    
    NHIỆM VỤ:
    Hãy soạn **1 CÂU HỎI** kiểm tra đánh giá dựa trên thông tin trích xuất từ Ma trận đề thi dưới đây:
    "{row_data_str}"
    
    YÊU CẦU BẮT BUỘC VỀ NGUỒN LIỆU (TUYỆT ĐỐI TUÂN THỦ):
    1. **Nguồn dữ liệu:** Chỉ được sử dụng ngữ liệu, kiến thức từ các bộ sách giáo khoa hiện hành: **Kết nối tri thức với cuộc sống**, **Chân trời sáng tạo**, **Cánh diều** và **Chương trình GDPT 2018**.
    2. **Tuyệt đối không** tự bịa đặt kiến thức hoặc lấy dữ liệu từ các nguồn cũ (VNEN, sách năm 2000...).
    3. Nội dung câu hỏi phải phù hợp chính xác với Yêu cầu cần đạt (YCCĐ) trong đoạn văn bản trên.

    THÔNG TIN CẤU TRÚC:
    - Dạng: {q_type}
    - Mức độ: {level}
    - Điểm số: {points} điểm.
    - Nếu là trắc nghiệm: Phải có 4 đáp án A, B, C, D (chỉ 1 đúng).

    ĐỊNH DẠNG OUTPUT (Để hệ thống tự động xuất file):
    **Câu hỏi:** [Nội dung câu hỏi]
    **Đáp án:** [Đáp án đúng và Hướng dẫn chấm ngắn gọn]
    """
    return call_gemini_api(clean_key, model_name, prompt)

# Hàm xuất Excel theo mẫu Ma trận
def create_excel_download(exam_list):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # 1. Sheet Đề thi
    ws_exam = workbook.add_worksheet("ĐỀ THI")
    format_wrap = workbook.add_format({'text_wrap': True, 'valign': 'top'})
    format_bold = workbook.add_format({'bold': True, 'font_size': 12})
    
    ws_exam.write(0, 0, "ĐỀ KIỂM TRA (Được tạo bởi AI)", format_bold)
    row = 2
    for idx, q in enumerate(exam_list):
        ws_exam.write(row, 0, f"Câu {idx+1} ({q['points']} điểm):", format_bold)
        ws_exam.write(row+1, 0, q['content'], format_wrap)
        row += 3
    ws_exam.set_column(0, 0, 80)

    # 2. Sheet Ma trận (Cố gắng tái tạo cấu trúc file mẫu)
    ws_matrix = workbook.add_worksheet("MA TRẬN ĐỀ")
    header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D3D3D3'})
    cell_format = workbook.add_format({'border': 1, 'text_wrap': True, 'valign': 'top'})

    # Tạo Header phức tạp (Mô phỏng file mẫu)
    # Dòng 1
    ws_matrix.merge_range('A1:A3', 'TT', header_format)
    ws_matrix.merge_range('B1:B3', 'Chương/Chủ đề', header_format)
    ws_matrix.merge_range('C1:C3', 'Nội dung/Kiến thức', header_format)
    ws_matrix.merge_range('D1:D3', 'Yêu cầu cần đạt', header_format)
    
    # Khu vực Mức độ nhận thức (Giả lập các cột trắc nghiệm/tự luận)
    ws_matrix.merge_range('E1:G1', 'Mức độ Nhận thức', header_format)
    ws_matrix.write('E2', 'Biết', header_format)
    ws_matrix.write('F2', 'Hiểu', header_format)
    ws_matrix.write('G2', 'Vận dụng', header_format)
    ws_matrix.write('E3', 'TN/TL', header_format) # Rút gọn
    ws_matrix.write('F3', 'TN/TL', header_format)
    ws_matrix.write('G3', 'TN/TL', header_format)
    
    ws_matrix.merge_range('H1:H3', 'Tổng điểm', header_format)
    ws_matrix.merge_range('I1:I3', 'Ghi chú (Câu số)', header_format)

    # Ghi dữ liệu
    data_row = 3
    for idx, q in enumerate(exam_list):
        ws_matrix.write(data_row, 0, idx+1, cell_format)
        # Vì dữ liệu từ file upload có thể hỗn hợp, ta cố gắng map
        ws_matrix.write(data_row, 1, q.get('topic', ''), cell_format) # Chủ đề
        ws_matrix.write(data_row, 2, q.get('lesson', ''), cell_format) # Nội dung (hoặc lấy từ bài học)
        ws_matrix.write(data_row, 3, "Xem chi tiết trong đề", cell_format) # YCCĐ thường dài
        
        # Đánh dấu X vào cột mức độ
        level_map = {'Mức 1': 4, 'Mức 2': 5, 'Mức 3': 6} # Cột E, F, G
        col_idx = 4 # Mặc định
        for key, val in level_map.items():
            if key in q['level']:
                col_idx = val
                break
        
        ws_matrix.write(data_row, col_idx, "x", cell_format)
        ws_matrix.write(data_row, 7, q['points'], cell_format)
        ws_matrix.write(data_row, 8, f"Câu {idx+1}", cell_format)
        
        data_row += 1

    # Set width
    ws_matrix.set_column('B:D', 25)
    ws_matrix.set_column('E:I', 10)

    workbook.close()
    output.seek(0)
    return output

# --- 5. QUẢN LÝ STATE ---
if "exam_list" not in st.session_state: st.session_state.exam_list = [] 
if "current_preview" not in st.session_state: st.session_state.current_preview = "" 
if "temp_question_data" not in st.session_state: st.session_state.temp_question_data = None 
if "uploaded_df" not in st.session_state: st.session_state.uploaded_df = None

# --- 6. GIAO DIỆN CHÍNH ---

st.markdown("<div class='content-container'>", unsafe_allow_html=True) 
st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.header("🔑 CẤU HÌNH")
    api_key_input = st.text_input("API Key Google:", type="password")
    
    st.markdown("---")
    st.write("📊 **Thống kê đề hiện tại:**")
    total_q = len(st.session_state.exam_list)
    total_p = sum([q['points'] for q in st.session_state.exam_list])
    
    if total_p == 10:
        st.success(f"Số câu: {total_q} | Tổng điểm: {total_p}/10 ✅")
    else:
        st.warning(f"Số câu: {total_q} | Tổng điểm: {total_p}/10")
    
    if st.button("🗑️ Xóa làm lại từ đầu"):
        st.session_state.exam_list = []
        st.session_state.current_preview = ""
        st.session_state.uploaded_df = None
        st.session_state.temp_question_data = None
        st.rerun()

# TABS
tab1, tab2 = st.tabs(["🛠️ Soạn thủ công (Theo DB)", "📂 Soạn từ File Ma trận (Upload)"])

# === TAB 1: SOẠN THỦ CÔNG (GIỮ NGUYÊN LOGIC CŨ) ===
with tab1:
    # (Để tiết kiệm không gian, phần logic này giữ nguyên như code cũ, chỉ gọi hàm call_gemini_api)
    # Bạn copy lại phần logic chọn môn/lớp ở Tab 1 của phiên bản trước vào đây nhé.
    st.info("Chức năng soạn theo Database có sẵn (Vui lòng paste lại code logic Tab 1 từ phiên bản trước nếu cần dùng).")
    # Placeholder đơn giản để không lỗi
    grade_t1 = st.selectbox("Lớp", ["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"], key="g1")

# === TAB 2: SOẠN TỪ FILE MA TRẬN ===
with tab2:
    st.markdown("### 📥 Tải lên Ma trận đề thi (Excel/Word/PDF)")
    st.info("💡 Hệ thống hỗ trợ tốt nhất cho file **Excel (.xlsx, .xls)** hoặc **CSV** đúng mẫu.")
    
    uploaded_file = st.file_uploader("Chọn file Ma trận:", type=['xlsx', 'xls', 'csv'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, header=None)
            else:
                df = pd.read_excel(uploaded_file, header=None)
            
            st.session_state.uploaded_df = df
            st.success("Đã phân tích file thành công!")
            
            # Hiển thị Ma trận gốc
            st.markdown("#### 👁️ Ma trận dữ liệu:")
            st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 🤖 Cấu hình AI sinh đề")
            
            col_u1, col_u2 = st.columns([1, 2])
            with col_u1:
                # Chọn dòng dữ liệu
                row_index = st.number_input("Chọn STT dòng trong bảng trên để ra đề:", 
                                           min_value=0, max_value=len(df)-1, value=5, step=1)
                st.caption("Hãy chọn dòng chứa 'Nội dung kiến thức' và 'YCCĐ'.")
                
                # Cấu hình câu hỏi
                u_q_type = st.selectbox("Dạng câu hỏi:", ["Trắc nghiệm (4 lựa chọn)", "Đúng/Sai", "Điền khuyết", "Tự luận", "Nối đôi"], key="type_t2")
                u_level = st.selectbox("Mức độ:", ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"], key="level_t2")
                u_points = st.number_input("Điểm:", 0.25, 10.0, 1.0, 0.25, key="point_t2")

            with col_u2:
                # Lấy dữ liệu dòng đã chọn để hiển thị
                selected_row_data = df.iloc[row_index].fillna("").to_string(index=False)
                st.text_area("Dữ liệu dòng được gửi cho AI (Prompt Context):", value=selected_row_data, height=200)

            if st.button("✨ AI Tạo câu hỏi từ Ma trận này", type="primary", key="btn_gen_upload"):
                if not api_key_input:
                    st.error("Vui lòng nhập API Key.")
                else:
                    with st.spinner("Đang tra cứu SGK (KNTT/CTST/CD) và tạo câu hỏi..."):
                        preview_u = generate_question_from_matrix_row(
                            api_key_input, selected_row_data, u_q_type, u_level, u_points
                        )
                        st.session_state.current_preview = preview_u
                        st.session_state.temp_question_data = {
                            "topic": "Từ file Ma trận", 
                            "lesson": f"Dữ liệu dòng {row_index}",
                            "type": u_q_type, 
                            "level": u_level, 
                            "points": u_points, 
                            "content": preview_u
                        }
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}. Hãy đảm bảo file Excel không bị lỗi format quá phức tạp.")

# === HIỂN THỊ KẾT QUẢ & THÊM VÀO ĐỀ ===
if st.session_state.current_preview:
    st.markdown("---")
    st.markdown("### 👁️ Kết quả:")
    with st.container():
        st.markdown(f"<div class='question-box'>{st.session_state.current_preview}</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("✅ Thêm vào đề thi"):
            if st.session_state.temp_question_data:
                st.session_state.exam_list.append(st.session_state.temp_question_data)
                st.session_state.current_preview = ""
                st.session_state.temp_question_data = None
                st.success("Đã thêm!")
                st.rerun()
    with c2:
        st.caption("Nếu chưa chuẩn sách GK, hãy bấm tạo lại.")

# === XUẤT FILE ===
st.markdown("---")
st.subheader("📋 Danh sách & Tải xuống")

if len(st.session_state.exam_list) > 0:
    df_show = pd.DataFrame(st.session_state.exam_list)
    st.dataframe(df_show[['lesson', 'type', 'level', 'points']], use_container_width=True)

    if st.button("❌ Xóa câu hỏi gần nhất"):
        st.session_state.exam_list.pop()
        st.rerun()

    col_d1, col_d2 = st.columns(2)
    
    # Xuất Excel (Bao gồm Sheet Đề và Sheet Ma trận giả lập)
    excel_data = create_excel_download(st.session_state.exam_list)
    with col_d1:
        st.download_button(
            label="📥 Tải xuống Excel (.xlsx) - Có Ma trận",
            data=excel_data,
            file_name="De_thi_va_Ma_tran_AI.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
    # Xuất Word (Dạng Text đơn giản)
    word_content = "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN\nĐỀ KIỂM TRA\n\n"
    for idx, q in enumerate(st.session_state.exam_list):
        word_content += f"Câu {idx+1} ({q['points']}đ):\n{q['content']}\n\n"
    
    with col_d2:
        st.download_button(
            label="📥 Tải xuống Word (.doc/txt)",
            data=word_content,
            file_name="De_thi_AI.doc",
            mime="application/msword"
        )

else:
    st.info("Chưa có câu hỏi nào trong danh sách.")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("""<div class="footer"><p style="margin: 0; font-weight: bold;">🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</p></div>""", unsafe_allow_html=True)
