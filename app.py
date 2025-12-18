import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
import time
import re
import random

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="HỆ THỐNG RA ĐỀ THI TIỂU HỌC TOÀN DIỆN",
    page_icon="🏫",
    layout="wide"
)

# --- 2. CSS GIAO DIỆN ---
st.markdown("""
<style>
    /* Tab 1 Style */
    .subject-card { padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9; text-align: center; margin-bottom: 10px; }
    .stTextArea textarea { font-family: 'Times New Roman'; font-size: 16px; }
    .success-box { padding: 10px; background-color: #d4edda; color: #155724; border-radius: 5px; margin-bottom: 10px; }
    
    /* Tab 2 Style */
    .question-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1565C0; margin-bottom: 10px; }
    
    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #333;
        text-align: center; padding: 10px; font-size: 14px;
        border-top: 1px solid #ddd; z-index: 100;
    }
    .content-container { padding-bottom: 60px; }
    
    /* Tiêu đề chính */
    .main-header {
        text-align: center; 
        color: #1565C0; 
        font-weight: bold; 
        font-size: 28px; 
        text-transform: uppercase;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. IMPORT AN TOÀN ---
try:
    import pypdf
except ImportError:
    st.error("⚠️ Thiếu thư viện 'pypdf'. Vui lòng cài đặt: pip install pypdf")

# -------------------------------------------------------------------
# 4. CSDL CHƯƠNG TRÌNH – GIỮ NGUYÊN TOÀN BỘ ĐOẠN NÀY TỪ FILE CỦA BẠN
# -------------------------------------------------------------------
# SUBJECTS_DB = {...}
# CURRICULUM_DB = {...}
# Toàn bộ phần SUBJECTS_DB và CURRICULUM_DB của bạn dán nguyên vẹn vào đây.
# -------------------------------------------------------------------

# --- CẤU TRÚC DỮ LIỆU ĐÃ ĐƯỢC CHUẨN HÓA LẠI ĐỂ TẠO LIST BÀI HỌC ---
CURRICULUM_DB_PROCESSED = {}

for grade, subjects in CURRICULUM_DB.items():
    CURRICULUM_DB_PROCESSED[grade] = {}
    for subject, semesters in subjects.items():
        CURRICULUM_DB_PROCESSED[grade][subject] = {}
        for semester, content in semesters.items():
            processed_topics = []
            for item in content:
                topic_name = item['Chủ đề']
                raw_lessons_str = item['Bài học']
                lessons_list = [l.strip() for l in raw_lessons_str.split(';') if l.strip()]
                processed_topics.append({
                    'Chủ đề': topic_name,
                    'Bài học': lessons_list
                })
            CURRICULUM_DB_PROCESSED[grade][subject][semester] = processed_topics

# --- 5. HỆ THỐNG API MỚI (CHỐNG LỖI 404 VÀ 429) ---
def generate_content_with_rotation(api_key, prompt):
    genai.configure(api_key=api_key)
    try:
        all_models = list(genai.list_models())
    except Exception as e:
        return f"Lỗi kết nối lấy danh sách model: {e}", None

    valid_models = [
        m.name for m in all_models 
        if 'generateContent' in m.supported_generation_methods
    ]
    if not valid_models:
        return "Lỗi: API Key đúng nhưng không tìm thấy model nào hỗ trợ tạo văn bản (generateContent).", None

    priority_order = []
    for m in valid_models:
        if 'flash' in m.lower() and '1.5' in m:
            priority_order.append(m)
    for m in valid_models:
        if 'pro' in m.lower() and '1.5' in m and m not in priority_order:
            priority_order.append(m)
    for m in valid_models:
        if m not in priority_order:
            priority_order.append(m)

    last_error = ""
    for model_name in priority_order:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text, model_name
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            continue

    return f"Hết model khả dụng. Lỗi cuối cùng: {last_error}", None

# --- HÀM SINH YÊU CẦU CẦN ĐẠT (YCCĐ) TỰ ĐỘNG CHO MỌI MÔN ---
def generate_yccd_from_lesson(api_key, grade, subject, topic, lesson_name):
    """
    Sinh Yêu cầu cần đạt cho 1 bài học.
    """
    genai.configure(api_key=api_key)
    mon_lower = subject.lower()

    if "toán" in mon_lower:
        subject_hint = """
- Nêu: (1) Kiến thức số học/hình học/đo lường; (2) Kĩ năng thực hiện phép tính; (3) Vận dụng giải toán thực tế.
"""
    elif "tiếng việt" in mon_lower:
        subject_hint = """
- Nêu: (1) Năng lực đọc hiểu; (2) Kĩ năng viết / nói và nghe; (3) Vốn từ, ngữ pháp, chính tả.
"""
    elif "khoa học" in mon_lower:
        subject_hint = """
- Nêu: (1) Hiểu hiện tượng tự nhiên, cơ thể người; (2) Kĩ năng quan sát, thí nghiệm, giải thích; (3) Thái độ bảo vệ môi trường, sức khoẻ.
"""
    elif "lịch sử" in mon_lower or "địa lí" in mon_lower or "địa lý" in mon_lower:
        subject_hint = """
- Nêu: (1) Kiến thức về sự kiện lịch sử / đặc điểm tự nhiên – kinh tế – xã hội; (2) Kĩ năng đọc bản đồ; (3) Tình yêu quê hương, đất nước.
"""
    elif "tin học" in mon_lower:
        subject_hint = """
- Nêu: (1) Hiểu biết về máy tính, Internet, ứng dụng; (2) Kĩ năng thao tác phần mềm; (3) An toàn, văn hoá trong môi trường số.
"""
    elif "công nghệ" in mon_lower:
        subject_hint = """
- Nêu: (1) Vai trò công nghệ; (2) Thao tác, quy trình đơn giản; (3) An toàn khi dùng dụng cụ, thiết bị.
"""
    else:
        subject_hint = """
- Nêu rõ kiến thức, kĩ năng, thái độ cốt lõi mà HS cần đạt theo CTGDPT 2018.
"""

    prompt = f"""
Bạn là chuyên gia xây dựng chương trình Giáo dục phổ thông 2018 bậc Tiểu học ở Việt Nam.

Nhiệm vụ:
- Soạn **Yêu cầu cần đạt** cho bài học dưới đây, bám sát CTGDPT 2018, nhưng viết lại bằng lời của bạn.

Thông tin bài học:
- Lớp: {grade}
- Môn: {subject}
- Chủ đề: {topic}
- Tên bài học: {lesson_name}

Gợi ý theo đặc thù môn học:
{subject_hint}

Yêu cầu:
1. Viết dưới dạng các gạch đầu dòng.
2. Mỗi gạch đầu dòng thể hiện 1 năng lực/kiến thức/kĩ năng cụ thể.
3. Không sao chép nguyên văn SGK.
4. Không thêm lời dẫn, chỉ liệt kê YCCĐ.

Ví dụ hình thức:
- Nhận biết được ...
- Thực hiện được ...
- Vận dụng được ...
"""
    text, _ = generate_content_with_rotation(api_key, prompt)
    return text.strip()

# --- 6. HÀM HỖ TRỢ FILE ---
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
                for page in reader.pages:
                    text += page.extract_text()
                return text
        return None
    except Exception:
        return None

def set_font_style(doc):
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)

# ... (giữ nguyên create_word_from_question_list, create_matrix_document, create_word_file_simple, extract_periods)
# Dán nguyên các hàm tạo Word, matrix, extract_periods của bạn vào đây, không đổi.

# --- 7. MAIN APP ---
def main():
    if 'exam_result' not in st.session_state:
        st.session_state.exam_result = ""
    if "exam_list" not in st.session_state:
        st.session_state.exam_list = []
    if "current_preview" not in st.session_state:
        st.session_state.current_preview = ""
    if "temp_question_data" not in st.session_state:
        st.session_state.temp_question_data = None
    if "last_lesson_selected" not in st.session_state:
        st.session_state.last_lesson_selected = ""
    if "auto_yccd_content" not in st.session_state:
        st.session_state.auto_yccd_content = "Nắm vững kiến thức cơ bản và vận dụng giải bài tập."

    # SIDEBAR
    with st.sidebar:
        st.header("🔑 CẤU HÌNH HỆ THỐNG")
        st.subheader("HỖ TRỢ RA ĐỀ CẤP TIỂU HỌC")
        api_key = st.text_input("Nhập API Key Google:", type="password")

        if st.button("🔌 Kiểm tra kết nối API"):
            if not api_key:
                st.warning("Vui lòng nhập API Key trước.")
            else:
                try:
                    genai.configure(api_key=api_key)
                    models = list(genai.list_models())
                    st.success(f"✅ Kết nối thành công! (Tìm thấy {len(models)} models)")
                except Exception as e:
                    st.error(f"❌ Kết nối thất bại: {e}")

        st.divider()
        st.markdown("**TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN**")
        st.caption("Hệ thống hỗ trợ chuyên môn")

    if not api_key:
        st.warning("Vui lòng nhập API Key để bắt đầu.")
        return

    st.markdown('<div class="main-header">HỖ TRỢ RA ĐỀ THI CẤP TIỂU HỌC</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📁 TẠO ĐỀ TỪ FILE (UPLOAD)", "✍️ SOẠN TỪNG CÂU (CSDL)", "📊 MA TRẬN ĐỀ THI"])

    # ========================== TAB 1 ==========================
    with tab1:
        st.header("Tạo đề thi từ file Ma trận có sẵn")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("1. Chọn Lớp")
            grade_t1 = st.radio("Khối lớp:", list(SUBJECTS_DB.keys()), key="t1_grade")
        with col2:
            st.subheader("2. Chọn Môn")
            subjects_t1 = SUBJECTS_DB[grade_t1]
            sub_name_t1 = st.selectbox("Môn học:", [s[0] for s in subjects_t1], key="t1_sub")
            icon_t1 = next(i for n, i in subjects_t1 if n == sub_name_t1)
            st.markdown(f"<div class='subject-card'><h3>{icon_t1} {sub_name_t1}</h3></div>", unsafe_allow_html=True)

        exam_term_t1 = st.selectbox(
            "Kỳ thi:",
            [
                "ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ I",
                "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ I",
                "ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ II",
                "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ II"
            ],
            key="t1_term"
        )
        school_name_t1 = st.text_input(
            "Tên trường:",
            value="TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN",
            key="t1_school"
        )

        st.subheader("3. Upload Ma trận")
        uploaded = st.file_uploader("Chọn file (.xlsx, .docx, .pdf)", type=['xlsx', 'docx', 'pdf'], key="t1_up")

        if uploaded and st.button("🚀 TẠO ĐỀ THI NGAY", type="primary", key="t1_btn"):
            content = read_uploaded_file(uploaded)
            if content:
                with st.spinner("Đang phân tích ma trận và tạo đề từ nguồn GDPT 2018..."):
                    prompt = f"""
Bạn là chuyên gia giáo dục Tiểu học Việt Nam, am hiểu chương trình GDPT 2018 và kĩ thuật ra đề theo ma trận.

Môn: {sub_name_t1}
Lớp: {grade_t1}

NHIỆM VỤ:
- Soạn **1 đề kiểm tra** dựa CHÍNH XÁC vào **ma trận đề** được trích ở dưới.
- Mọi quyết định về: số câu, dạng câu hỏi, mức độ nhận thức, điểm từng câu đều phải bám vào ma trận.

MA TRẬN ĐỀ (VĂN BẢN TRÍCH TỪ FILE UPLOAD):
--------------------
{content}
--------------------

HƯỚNG DẪN PHÂN TÍCH MA TRẬN:
1. Đọc kĩ bảng ma trận, với mỗi dòng xác định:
   - Chương/Chủ đề
   - Nội dung/Đơn vị kiến thức
   - Số tiết, tỉ lệ, số điểm cần đạt
   - Các ô số câu thuộc:
     + Trắc nghiệm nhiều lựa chọn (Biết / Hiểu / Vận dụng)
     + Trắc nghiệm Đúng – Sai (Biết / Hiểu / Vận dụng)
     + Nối cột (Biết / Hiểu / Vận dụng)
     + Điền khuyết (Biết / Hiểu / Vận dụng)
     + (Nếu có) Tự luận (Biết / Hiểu / Vận dụng), số câu/ý và điểm.

2. Nếu ma trận có bảng riêng “điểm 1 câu…”:
   → Phải dùng chính xác các điểm đó cho từng loại câu (nhiều lựa chọn, đúng sai, nối cột, điền khuyết, tự luận).

3. Nếu ma trận chỉ ghi “Tổng điểm” của 1 dòng và số câu:
   → Điểm mỗi câu = Tổng điểm / Số câu trong dòng đó.
   → KHÔNG được gán toàn bộ tổng điểm cho 1 câu duy nhất.

4. Với mỗi ô ma trận có SỐ CÂU > 0, phải soạn đúng:
   - Số câu tương ứng
   - Dạng câu hỏi đúng (Nhiều lựa chọn / Đúng – Sai / Nối cột / Điền khuyết / Tự luận)
   - Mức độ nhận thức đúng (Biết / Hiểu / Vận dụng)
   - Nội dung bám sát “Nội dung/Đơn vị kiến thức”
   - Điểm mỗi câu đúng theo quy tắc.

GỢI Ý THEO MÔN HỌC:
- Nếu môn Toán: câu hỏi có số liệu rõ ràng, tính toán, so sánh, giải toán có lời văn…
- Nếu môn Tiếng Việt: đọc hiểu, từ – câu – đoạn, chính tả, luyện từ và câu, tập làm văn.
- Nếu Khoa học: hiện tượng tự nhiên, cơ thể người, sức khỏe, môi trường.
- Nếu Lịch sử & Địa lí: sự kiện, nhân vật, địa lí tự nhiên, dân cư, kinh tế, bản đồ.
- Nếu Tin học, Công nghệ: khái niệm, thao tác phần mềm, thiết bị, an toàn số, quy trình đơn giản.

ĐỊNH DẠNG ĐẦU RA:
- Liệt kê câu theo thứ tự Câu 1, Câu 2, ...
- Mỗi câu:

Câu [số] – [Dạng câu hỏi] – [Mức độ: Biết/Hiểu/Vận dụng] – [Số điểm]:
[Nội dung câu hỏi]

Nếu “Trắc nghiệm nhiều lựa chọn”:
A. ...
B. ...
C. ...
D. ...
Đáp án: ...

Nếu “Đúng – Sai”:
[Mệnh đề ...]
Yêu cầu: Chọn Đúng (Đ) hoặc Sai (S).
Đáp án: ...

Nếu “Nối cột”:
Cột A:
1. ...
2. ...
Cột B:
a. ...
b. ...
Đáp án: 1-b, 2-a, ...

Nếu “Điền khuyết”:
[Câu hỏi có chỗ trống ............]
Đáp án: ...

Nếu “Tự luận”:
[Yêu cầu chi tiết...]
Gợi ý chấm: ...

YÊU CẦU:
- Không viết hướng dẫn meta, chỉ viết nội dung đề thi.
- Tổng số câu và tổng điểm khớp với ma trận.
"""
                    result_text, used_model = generate_content_with_rotation(api_key, prompt)
                    if used_model:
                        st.session_state.exam_result = result_text
                        st.success(f"Đã tạo xong bằng model: {used_model}")
                    else:
                        st.error(result_text)

        if st.session_state.exam_result:
            st.markdown("---")
            edited_text = st.text_area(
                "Sửa nội dung:",
                value=st.session_state.exam_result,
                height=500,
                key="t1_edit"
            )
            st.session_state.exam_result = edited_text
            docx = create_word_file_simple(school_name_t1, exam_term_t1, edited_text)
            st.download_button(
                "📥 TẢI VỀ FILE WORD (.docx)",
                docx,
                file_name=f"De_{sub_name_t1}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary"
            )

    # ========================== TAB 2 ==========================
    with tab2:
        st.header("Soạn thảo từng câu hỏi theo CSDL")
        col1, col2 = st.columns(2)
        with col1:
            selected_grade = st.selectbox("Chọn Khối Lớp:", list(SUBJECTS_DB.keys()), key="t2_grade")
        with col2:
            subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
            selected_subject_full = st.selectbox("Chọn Môn Học:", subjects_list, key="t2_sub")
            selected_subject = selected_subject_full.split(" ", 1)[1]

        raw_data = CURRICULUM_DB_PROCESSED.get(selected_grade, {}).get(selected_subject, {})
        if not raw_data:
            st.warning("⚠️ Dữ liệu môn này đang cập nhật.")
        else:
            st.markdown("---")
            st.subheader("🛠️ Soạn thảo câu hỏi")
            col_a, col_b = st.columns(2)
            with col_a:
                all_terms = list(raw_data.keys())
                selected_term = st.selectbox("Chọn Học kỳ:", all_terms, key="t2_term")
                lessons_in_term = raw_data[selected_term]
                unique_topics = sorted(list(set([l['Chủ đề'] for l in lessons_in_term])))
                selected_topic = st.selectbox("Chọn Chủ đề:", unique_topics, key="t2_topic")
            with col_b:
                filtered_lessons = [l for l in lessons_in_term if l['Chủ đề'] == selected_topic]
                all_lessons_in_topic = []
                for item in filtered_lessons:
                    all_lessons_in_topic.extend(item['Bài học'])
                selected_lesson_name = st.selectbox("Chọn Bài học:", all_lessons_in_topic, key="t2_lesson")

            # Tự động sinh YCCĐ từ tên bài
            if st.session_state.last_lesson_selected != selected_lesson_name:
                with st.spinner("Đang sinh YCCĐ theo CTGDPT 2018 từ tên bài..."):
                    ai_yccd = generate_yccd_from_lesson(
                        api_key=api_key,
                        grade=selected_grade,
                        subject=selected_subject,
                        topic=selected_topic,
                        lesson_name=selected_lesson_name
                    )
                    if ai_yccd:
                        st.session_state.auto_yccd_content = ai_yccd
                        st.session_state.last_lesson_selected = selected_lesson_name

            yccd_input = st.text_area(
                "Yêu cầu cần đạt (AI tự động lấy):",
                value=st.session_state.auto_yccd_content,
                height=68,
                key="t2_yccd_input"
            )

            current_lesson_data = {
                "Chủ đề": selected_topic,
                "Bài học": selected_lesson_name,
                "YCCĐ": yccd_input
            }

            col_x, col_y, col_z = st.columns(3)
            with col_x:
                question_types = [
                    "Trắc nghiệm (4 lựa chọn)",
                    "Đúng/Sai",
                    "Ghép nối (Nối cột)",
                    "Điền khuyết (Hoàn thành câu)",
                    "Tự luận"
                ]
                if selected_subject == "Tin học":
                    question_types.append("Thực hành trên máy tính")
                q_type = st.selectbox("Dạng câu hỏi:", question_types, key="t2_type")
            with col_y:
                level = st.selectbox(
                    "Mức độ:",
                    ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"],
                    key="t2_lv"
                )
            with col_z:
                points = st.number_input(
                    "Điểm số:",
                    min_value=0.25,
                    max_value=10.0,
                    step=0.25,
                    value=1.0,
                    key="t2_pt"
                )

            def extract_periods(lesson_name):
                match = re.search(r'\((\d+)\s*tiết\)', lesson_name, re.IGNORECASE)
                if match:
                    return match.group(1)
                return "-"

            # HÀM TẠO CÂU HỎI
            def generate_question():
                with st.spinner("AI đang viết..."):
                    random_seed = random.randint(1, 100000)
                    prompt_q = f"""
Đóng vai chuyên gia giáo dục Tiểu học, am hiểu chương trình GDPT 2018 và đặc thù môn {selected_subject} lớp {selected_grade}.

Nhiệm vụ: Soạn **1 CÂU HỎI KIỂM TRA** dựa trên thông tin sau:

- Môn: {selected_subject}
- Lớp: {selected_grade}
- Chủ đề: {current_lesson_data['Chủ đề']}
- Bài học cụ thể: {current_lesson_data['Bài học']}
- Yêu cầu cần đạt của bài: 
{current_lesson_data['YCCĐ']}

- Dạng câu hỏi: {q_type}
- Mức độ nhận thức: {level}  (Mức 1 = Biết, Mức 2 = Hiểu, Mức 3 = Vận dụng)
- Số điểm: {points}
- Seed ngẫu nhiên: {random_seed}

GỢI Ý THEO MÔN:
- Nếu môn Toán:
  + Câu hỏi phải có số liệu rõ ràng, yêu cầu thực hiện phép tính, so sánh, giải toán có lời văn, đo lường, hình học...
- Nếu môn Tiếng Việt:
  + Có thể hỏi về đọc hiểu (đoạn/bài), từ loại, câu, dấu câu, chính tả, tập làm văn (viết đoạn/câu).
- Nếu Khoa học:
  + Hỏi hiện tượng, khái niệm, vai trò, giải thích đơn giản, lựa chọn cách làm đúng, bảo vệ môi trường/sức khoẻ.
- Nếu Lịch sử & Địa lí:
  + Hỏi về sự kiện, nhân vật, đặc điểm tự nhiên, dân cư, kinh tế, bản đồ, vị trí địa lí, ý nghĩa lịch sử.
- Nếu Tin học:
  + Hỏi về thao tác với chuột/bàn phím, thư mục, tệp, Internet, an toàn thông tin, phần mềm trong chương trình.
- Nếu Công nghệ:
  + Hỏi về vật liệu, dụng cụ, quy trình, thao tác an toàn, ứng dụng của công nghệ trong đời sống.

YÊU CẦU ĐỊNH DẠNG NGHIÊM NGẶT:

1. VỚI DẠNG "Trắc nghiệm (4 lựa chọn)":
- Câu hỏi phải có số liệu/nội dung rõ ràng, chỉ 1 đáp án đúng duy nhất.
- Hiển thị 4 đáp án mỗi dòng một đáp án, dạng:
  A. ...
  B. ...
  C. ...
  D. ...
- Ghi dòng cuối: "Đáp án: [chữ cái]"

2. VỚI DẠNG "Đúng/Sai":
- Nêu 1 hoặc vài mệnh đề.
- Yêu cầu HS chọn Đúng (Đ) hoặc Sai (S).
- Cuối ghi: "Đáp án: ..." (nêu rõ từng mệnh đề Đ/S).

3. VỚI DẠNG "Ghép nối (Nối cột)":
- Liệt kê Cột A (1,2,3,...) và Cột B (a,b,c,...) rõ ràng.
- Cuối ghi: "Đáp án: 1-b, 2-a, ..." (hoặc tương tự).

4. VỚI DẠNG "Điền khuyết (Hoàn thành câu)":
- Trong câu hỏi phải có chỗ trống với dấu "........".
- Cuối ghi: "Đáp án: ..."

5. VỚI DẠNG "Tự luận":
- Nêu yêu cầu rõ ràng, gắn với YCCĐ và bài học.
- Cuối ghi: "Gợi ý: ..." (nêu hướng trả lời ngắn gọn).

6. VỚI DẠNG "Thực hành trên máy tính" (Tin học):
- Nêu nhiệm vụ thực hành cụ thể.
- Cuối ghi: "Gợi ý đánh giá: ..." (tiêu chí chấm điểm).

OUTPUT:
- Chỉ ghi nội dung câu hỏi và đáp án, không thêm lời dẫn.
"""
                    preview_content, _ = generate_content_with_rotation(api_key, prompt_q)
                    st.session_state.current_preview = preview_content
                    st.session_state.temp_question_data = {
                        "topic": selected_topic,
                        "lesson": selected_lesson_name,
                        "type": q_type,
                        "level": level,
                        "points": points,
                        "content": preview_content,
                        "yccd": yccd_input,
                        "periods": extract_periods(selected_lesson_name)
                    }

            if st.button("✨ Tạo câu hỏi (Xem trước)", type="primary", key="t2_preview"):
                generate_question()

            if st.session_state.current_preview:
                st.markdown(f"<div class='question-box'>{st.session_state.current_preview}</div>", unsafe_allow_html=True)
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    if st.button("✅ Thêm vào đề thi", key="t2_add"):
                        st.session_state.exam_list.append(st.session_state.temp_question_data)
                        st.session_state.current_preview = ""
                        st.success("Đã thêm vào danh sách!")
                        st.rerun()
                with col_btn2:
                    if st.button("🔄 Tạo câu hỏi khác", key="t2_regen"):
                        generate_question()
                        st.rerun()

            if len(st.session_state.exam_list) > 0:
                st.markdown("---")
                st.subheader(f"📊 Bảng thống kê chi tiết ({len(st.session_state.exam_list)} câu)")
                stats_data = []
                for i, q in enumerate(st.session_state.exam_list):
                    stats_data.append({
                        "Thứ tự câu": f"Câu {i+1}",
                        "Tên bài": q['lesson'],
                        "Số tiết": q.get('periods', '-'),
                        "Các mức": q['level'],
                        "Dạng câu hỏi": q['type'],
                        "Điểm": q['points']
                    })
                df_stats = pd.DataFrame(stats_data)
                st.dataframe(df_stats, use_container_width=True)

                st.markdown("#### 📝 Chỉnh sửa chi tiết đề thi")
                for i, item in enumerate(st.session_state.exam_list):
                    with st.expander(f"Câu {i+1} ({item['points']} điểm) - {item['type']}"):
                        new_content = st.text_area(
                            f"Nội dung câu {i+1}:",
                            value=item['content'],
                            height=150,
                            key=f"edit_q_{i}"
                        )
                        st.session_state.exam_list[i]['content'] = new_content
                        if st.button("🗑️ Xóa câu này", key=f"del_q_{i}"):
                            st.session_state.exam_list.pop(i)
                            st.rerun()

                col_act1, col_act2 = st.columns(2)
                with col_act2:
                    if st.button("❌ Xóa toàn bộ đề", key="t2_clear"):
                        st.session_state.exam_list = []
                        st.rerun()

                docx_file = create_word_from_question_list(
                    "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN",
                    selected_subject,
                    st.session_state.exam_list
                )
                st.download_button(
                    label="📥 TẢI ĐỀ THI (WORD)",
                    data=docx_file,
                    file_name=f"De_thi_{selected_subject}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )

    # ========================== TAB 3 ==========================
    with tab3:
        st.header("📊 BẢNG MA TRẬN ĐỀ THI (BẢN ĐẶC TẢ)")
        st.info("Chỉnh sửa trực tiếp trên bảng và tải về file Word theo mẫu.")
        if len(st.session_state.exam_list) == 0:
            st.info("⚠️ Vui lòng soạn câu hỏi ở Tab 2 trước.")
        else:
            matrix_data = []
            for i, q in enumerate(st.session_state.exam_list):
                matrix_data.append({
                    "STT": i + 1,
                    "Chủ đề": q['topic'],
                    "Bài học": q['lesson'],
                    "Yêu cầu cần đạt": q.get('yccd', ''),
                    "Dạng câu hỏi": q['type'],
                    "Mức độ": q['level'],
                    "Số điểm": q['points'],
                    "Ghi chú": ""
                })
            df_matrix = pd.DataFrame(matrix_data)
            edited_df = st.data_editor(
                df_matrix,
                num_rows="dynamic",
                use_container_width=True,
                key="matrix_editor"
            )
            if st.button("💾 Cập nhật thay đổi từ Ma trận vào Hệ thống"):
                for index, row in edited_df.iterrows():
                    if index < len(st.session_state.exam_list):
                        st.session_state.exam_list[index]['topic'] = row['Chủ đề']
                        st.session_state.exam_list[index]['lesson'] = row['Bài học']
                        st.session_state.exam_list[index]['type'] = row['Dạng câu hỏi']
                        st.session_state.exam_list[index]['level'] = row['Mức độ']
                        st.session_state.exam_list[index]['points'] = row['Số điểm']
                        st.session_state.exam_list[index]['yccd'] = row['Yêu cầu cần đạt']
                st.success("Đã cập nhật dữ liệu thành công!")
                st.rerun()

            matrix_docx = create_matrix_document(st.session_state.exam_list, selected_subject, selected_grade)
            st.download_button(
                label="📥 TẢI BẢN ĐẶC TẢ ĐỀ THI (WORD)",
                data=matrix_docx,
                file_name=f"Ban_dac_ta_{selected_subject}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary"
            )

    st.markdown("""
    <div class="footer">
        <p style="margin: 0; font-weight: bold; color: #2c3e50;">🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
