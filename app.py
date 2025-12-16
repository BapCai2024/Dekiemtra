import streamlit as st
import pandas as pd
import requests
import time

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
    .success-box { background-color: #e8f5e9; padding: 10px; border-radius: 5px; border: 1px solid #c8e6c9; }
    div.stButton > button:first-child { border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 3. CƠ SỞ DỮ LIỆU ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tiếng Anh", "🇬🇧"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

# (Dữ liệu CURRICULUM_DB đầy đủ của bạn - Hãy dán lại phần dữ liệu đầy đủ nhất vào đây)
# Dưới đây là mẫu rút gọn để code chạy được, bạn nhớ thay bằng dữ liệu đầy đủ 5 khối lớp nhé.
CURRICULUM_DB = {
    "Lớp 1": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Các số đến 10", "Bài học": "Bài 1: Nhiều hơn, ít hơn (2 tiết)", "YCCĐ": "So sánh số lượng đồ vật."},
                {"Chủ đề": "Phép cộng, trừ", "Bài học": "Bài 12: Phép cộng trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép cộng không nhớ trong phạm vi 10."},
            ],
            "Học kỳ II": [{"Chủ đề": "Các số đến 100", "Bài học": "Bài 27: Số có hai chữ số (3 tiết)", "YCCĐ": "Đọc, viết, so sánh số có hai chữ số."}]
        },
        "Tiếng Việt": { "Học kỳ I": [], "Học kỳ II": [] } 
    },
    "Lớp 4": { 
         "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Số tự nhiên", "Bài học": "Chương 1: Các số đến lớp triệu", "YCCĐ": "Đọc, viết, so sánh, làm tròn các số đến lớp triệu."},
                {"Chủ đề": "Phép tính", "Bài học": "Chương 2: Bốn phép tính với số tự nhiên", "YCCĐ": "Thực hiện thành thạo phép cộng, trừ, nhân, chia."},
            ],
             "Học kỳ II": []
         }
    }
    # ... Hãy dán toàn bộ dữ liệu đầy đủ 5 lớp ở các bước trước vào đây ...
}

# --- 4. CÁC HÀM XỬ LÝ ---

def find_working_model(api_key):
    """Tìm model Gemini khả dụng"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            chat_models = [m['name'] for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])]
            preferred = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
            for p in preferred:
                for m in chat_models:
                    if p in m: return m
            return chat_models[0] if chat_models else None
        return None
    except:
        return None

def generate_single_question(api_key, grade, subject, lesson_info, q_type, level, points):
    """Hàm sinh 1 câu hỏi duy nhất"""
    clean_key = api_key.strip()
    if not clean_key: return "⚠️ Chưa nhập API Key."
    
    model_name = find_working_model(clean_key)
    if not model_name: return "❌ Lỗi Key hoặc Mạng."

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={clean_key}"
    headers = {'Content-Type': 'application/json'}

    prompt = f"""
    Đóng vai giáo viên {subject} Lớp {grade}.
    Hãy viết **1 CÂU HỎI KIỂM TRA** với yêu cầu sau:
    - Bài học: {lesson_info['Bài học']}
    - Yêu cầu cần đạt: {lesson_info['YCCĐ']}
    - Dạng câu hỏi: {q_type}
    - Mức độ nhận thức: {level}
    - Điểm số: {points} điểm.

    OUTPUT TRẢ VỀ (Bắt buộc theo định dạng sau, không thêm lời dẫn):
    **Câu hỏi:** [Nội dung câu hỏi]
    **Đáp án:** [Đáp án chi tiết]
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Lỗi API: {response.status_code}"
    except Exception as e:
        return f"Lỗi mạng: {e}"

# --- 5. QUẢN LÝ STATE ---
if "exam_list" not in st.session_state:
    st.session_state.exam_list = [] 
if "current_preview" not in st.session_state:
    st.session_state.current_preview = "" 
if "temp_question_data" not in st.session_state:
    st.session_state.temp_question_data = None 

# --- 6. GIAO DIỆN CHÍNH ---

st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# SIDEBAR API
with st.sidebar:
    st.header("🔑 CẤU HÌNH")
    api_key_input = st.text_input("API Key Google:", type="password")
    if st.button("Kiểm tra Key"):
        if find_working_model(api_key_input):
            st.success("Kết nối thành công!")
        else:
            st.error("Key lỗi.")
            
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
        st.rerun()

# BƯỚC 1: CHỌN LỚP - MÔN
col1, col2 = st.columns(2)
with col1:
    selected_grade = st.selectbox("Chọn Khối Lớp:", list(SUBJECTS_DB.keys()))
with col2:
    subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
    selected_subject_full = st.selectbox("Chọn Môn Học:", subjects_list)
    selected_subject = selected_subject_full.split(" ", 1)[1]

# Lấy dữ liệu môn học
raw_data = CURRICULUM_DB.get(selected_grade, {}).get(selected_subject, {})

if not raw_data:
    st.warning("⚠️ Chưa có dữ liệu cho môn này. Vui lòng cập nhật CURRICULUM_DB.")
    st.stop()

# BƯỚC 2: BỘ SOẠN CÂU HỎI
st.markdown("---")
st.subheader("🛠️ Soạn thảo câu hỏi theo Ma trận")

# 2.1. Bộ lọc Chủ đề & Bài học
col_a, col_b = st.columns(2)
with col_a:
    all_terms = list(raw_data.keys())
    selected_term = st.selectbox("Chọn Học kỳ:", all_terms)
    lessons_in_term = raw_data[selected_term]
    unique_topics = list(set([l['Chủ đề'] for l in lessons_in_term]))
    selected_topic = st.selectbox("Chọn Chủ đề:", unique_topics)

with col_b:
    filtered_lessons = [l for l in lessons_in_term if l['Chủ đề'] == selected_topic]
    lesson_options = {f"{l['Bài học']}": l for l in filtered_lessons}
    selected_lesson_name = st.selectbox("Chọn Bài học (có số tiết):", list(lesson_options.keys()))
    current_lesson_data = lesson_options[selected_lesson_name]
    st.info(f"🎯 **YCCĐ:** {current_lesson_data['YCCĐ']}")

# 2.2. Cấu hình câu hỏi
col_x, col_y, col_z = st.columns(3)
with col_x:
    q_type = st.selectbox("Dạng câu hỏi:", ["Trắc nghiệm (4 lựa chọn)", "Đúng/Sai", "Điền khuyết", "Nối đôi", "Tự luận", "Giải toán có lời văn"])
with col_y:
    level = st.selectbox("Mức độ nhận thức:", ["Mức 1: Biết (Nhận biết)", "Mức 2: Hiểu (Thông hiểu)", "Mức 3: Vận dụng (Giải quyết vấn đề)"])
with col_z:
    points = st.number_input("Điểm số:", min_value=0.25, max_value=10.0, step=0.25, value=1.0)

# 2.3. Nút Tạo & Xem trước
btn_preview = st.button("✨ Tạo thử & Xem trước nội dung", type="primary")

if btn_preview:
    if not api_key_input:
        st.error("Vui lòng nhập API Key trước.")
    else:
        with st.spinner("AI đang viết câu hỏi..."):
            preview_content = generate_single_question(
                api_key_input, selected_grade, selected_subject, 
                current_lesson_data, q_type, level, points
            )
            st.session_state.current_preview = preview_content
            # Lưu cả chủ đề (topic) để xuất ma trận
            st.session_state.temp_question_data = {
                "topic": selected_topic,
                "lesson": selected_lesson_name,
                "type": q_type,
                "level": level,
                "points": points,
                "content": preview_content
            }

# 2.4. Khu vực Hiển thị Xem trước & Xác nhận
if st.session_state.current_preview:
    st.markdown("### 👁️ Xem trước câu hỏi:")
    with st.container():
        st.markdown(f"<div class='question-box'>{st.session_state.current_preview}</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("✅ Thêm vào đề thi"):
            if st.session_state.temp_question_data:
                st.session_state.exam_list.append(st.session_state.temp_question_data)
                st.session_state.current_preview = "" 
                st.session_state.temp_question_data = None
                st.success("Đã thêm câu hỏi thành công!")
                st.rerun()
    with c2:
        st.caption("Nếu chưa ưng ý, hãy bấm nút 'Tạo thử' lại để sinh câu mới.")

# BƯỚC 3: XUẤT ĐỀ VÀ MA TRẬN
st.markdown("---")
st.subheader("📋 Danh sách câu hỏi & Xuất file")

if len(st.session_state.exam_list) > 0:
    # 3.1. Hiển thị bảng tóm tắt trên web
    df_preview = pd.DataFrame(st.session_state.exam_list)
    st.dataframe(
        df_preview[['topic', 'lesson', 'type', 'level', 'points']],
        column_config={
            "topic": "Chủ đề",
            "lesson": "Bài học",
            "type": "Dạng",
            "level": "Mức độ",
            "points": "Điểm"
        },
        use_container_width=True
    )

    if st.button("❌ Xóa câu hỏi gần nhất"):
        st.session_state.exam_list.pop()
        st.rerun()

    # 3.2. Xây dựng nội dung file tải về (Ma trận + Đề thi)
    
    # --- PHẦN 1: TẠO BẢNG ĐẶC TẢ MA TRẬN (TEXT) ---
    matrix_text = f"BẢNG ĐẶC TẢ MA TRẬN ĐỀ THI {selected_subject.upper()} - {selected_grade.upper()}\n"
    matrix_text += "="*80 + "\n"
    matrix_text += f"{'STT':<5} | {'Chủ đề':<20} | {'Bài học':<30} | {'Dạng':<15} | {'Mức độ':<15} | {'Điểm':<5}\n"
    matrix_text += "-"*80 + "\n"
    
    for idx, item in enumerate(st.session_state.exam_list):
        # Cắt ngắn text để hiển thị đẹp trong bảng text
        topic_short = (item['topic'][:18] + '..') if len(item['topic']) > 18 else item['topic']
        lesson_short = (item['lesson'][:28] + '..') if len(item['lesson']) > 28 else item['lesson']
        
        row_str = f"{idx+1:<5} | {topic_short:<20} | {lesson_short:<30} | {item['type']:<15} | {item['level']:<15} | {item['points']:<5}\n"
        matrix_text += row_str
    
    matrix_text += "-"*80 + "\n"
    matrix_text += f"TỔNG SỐ CÂU: {len(st.session_state.exam_list)} câu\n"
    matrix_text += f"TỔNG ĐIỂM:   {sum(q['points'] for q in st.session_state.exam_list)} điểm\n"
    matrix_text += "="*80 + "\n\n\n"

    # --- PHẦN 2: TẠO NỘI DUNG ĐỀ THI ---
    exam_text = f"TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN\n"
    exam_text += f"ĐỀ KIỂM TRA {selected_subject.upper()} - {selected_grade.upper()}\n"
    exam_text += f"Thời gian làm bài: 40 phút\n"
    exam_text += "-"*50 + "\n\n"
    
    for idx, q in enumerate(st.session_state.exam_list):
        exam_text += f"Câu {idx+1} ({q['points']} điểm): \n"
        # Chỉ lấy phần nội dung câu hỏi (bỏ phần đáp án để in cho HS nếu cần xử lý kỹ hơn, 
        # nhưng ở đây AI trả về cả đáp án nên ta in hết để GV cắt dán)
        exam_text += f"{q['content']}\n"
        exam_text += "\n" + "."*50 + "\n\n"

    # Gộp 2 phần
    final_output_file = matrix_text + exam_text

    # Nút tải xuống
    st.download_button(
        label="📥 Tải xuống (Đề thi + Bảng đặc tả)",
        data=final_output_file,
        file_name=f"De_thi_va_Ma_tran_{selected_subject}_{selected_grade}.txt",
        mime="text/plain",
        type="primary"
    )

else:
    st.info("Chưa có câu hỏi nào. Hãy soạn và thêm câu hỏi ở trên.")
