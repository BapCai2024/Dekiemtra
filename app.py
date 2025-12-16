import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import time

# ==========================================
# 1. DỮ LIỆU CỨNG CHI TIẾT (CHUẨN GDPT 2018)
# ==========================================

PREDEFINED_TOPICS = {
    # --- MÔN TOÁN ---
    "Toán": {
        "Lớp 1": [
            "Các số từ 0 đến 10", "Hình vuông, hình tròn, hình tam giác, hình chữ nhật",
            "Phép cộng trong phạm vi 10", "Phép trừ trong phạm vi 10",
            "Các số trong phạm vi 20", "Phép cộng, phép trừ (không nhớ) trong phạm vi 20",
            "Các số trong phạm vi 100", "Đo độ dài (cm)", "Thời gian (Ngày, giờ)"
        ],
        "Lớp 2": [
            "Phép cộng có nhớ trong phạm vi 100", "Phép trừ có nhớ trong phạm vi 100",
            "Làm quen với hình khối (Khối trụ, khối cầu)", "Ngày, giờ, phút, tháng, năm",
            "Phép nhân (Bảng nhân 2, 5)", "Phép chia (Bảng chia 2, 5)",
            "Độ dài (dm, m, km)", "Các số trong phạm vi 1000"
        ],
        "Lớp 3": [
            "Bảng nhân 3, 4, 6, 7, 8, 9", "Bảng chia 3, 4, 6, 7, 8, 9",
            "Nhân số có 2, 3 chữ số với số có 1 chữ số", "Chia số có 2, 3 chữ số cho số có 1 chữ số",
            "Góc vuông, góc không vuông", "Chu vi hình tam giác, tứ giác, chữ nhật, hình vuông",
            "Các số trong phạm vi 10.000", "Diện tích hình chữ nhật, hình vuông",
            "Các số trong phạm vi 100.000"
        ],
        "Lớp 4": [
            "Số tự nhiên. Bảng đơn vị đo khối lượng", "Các phép tính với số tự nhiên",
            "Biểu đồ cột. Số trung bình cộng", "Hai đường thẳng vuông góc, song song",
            "Phân số. Các phép tính với phân số", "Hình bình hành. Hình thoi",
            "Tỉ lệ bản đồ"
        ],
        "Lớp 5": [
            "Ôn tập và bổ sung về phân số", "Số thập phân. Các phép tính với số thập phân",
            "Hình tam giác. Diện tích hình tam giác", "Hình thang. Diện tích hình thang",
            "Hình tròn. Chu vi và diện tích hình tròn", "Hình hộp chữ nhật. Hình lập phương",
            "Số đo thời gian. Toán chuyển động đều"
        ]
    },
    
    # --- MÔN TIẾNG VIỆT ---
    "Tiếng Việt": {
        "Lớp 1": [
            "Làm quen với chữ cái và dấu thanh", "Vần đơn, vần kép", 
            "Tập đọc: Chủ điểm Nhà trường", "Tập đọc: Chủ điểm Gia đình",
            "Tập đọc: Chủ điểm Thiên nhiên", "Chính tả: Nghe - viết", "Kể chuyện theo tranh"
        ],
        "Lớp 2": [
            "Đọc: Em là búp măng non", "Đọc: Bạn bè, thầy cô", "Từ chỉ sự vật, hoạt động, đặc điểm",
            "Câu kiểu Ai là gì? Ai làm gì? Ai thế nào?", "Viết đoạn văn kể về người thân",
            "Viết đoạn văn kể về một việc làm tốt", "Nghe - viết chính tả"
        ],
        "Lớp 3": [
            "Đọc: Măng non", "Đọc: Mái ấm", "Đọc: Tới trường", "Đọc: Cộng đồng",
            "Mở rộng vốn từ: Thiếu nhi, Gia đình, Trường học", "Biện pháp so sánh",
            "Viết đơn, viết thư", "Viết đoạn văn kể chuyện", "Nghe - viết chính tả"
        ],
        "Lớp 4": [
            "Đọc: Thương người như thể thương thân", "Đọc: Măng mọc thẳng", "Đọc: Trên đôi cánh ước mơ",
            "Luyện từ và câu: Danh từ, Động từ, Tính từ", "Luyện từ và câu: Câu hỏi, Câu kể, Câu cảm",
            "Tập làm văn: Kể chuyện", "Tập làm văn: Miêu tả đồ vật", "Tập làm văn: Miêu tả cây cối"
        ],
        "Lớp 5": [
            "Đọc: Việt Nam - Tổ quốc em", "Đọc: Cánh chim hòa bình", "Đọc: Con người với thiên nhiên",
            "Luyện từ và câu: Từ đồng nghĩa, trái nghĩa, đồng âm", "Luyện từ và câu: Đại từ, Quan hệ từ",
            "Tập làm văn: Tả cảnh", "Tập làm văn: Tả người"
        ]
    },

    # --- MÔN TIN HỌC (LỚP 3, 4, 5) ---
    "Tin học": {
        "Lớp 3": [
            "Làm quen với máy tính", "Chuột máy tính", "Bàn phím máy tính", 
            "Làm quen với Internet", "Sắp xếp thư mục và tệp tin", 
            "Luyện tập gõ bàn phím", "Bảo vệ sức khỏe khi dùng máy tính"
        ],
        "Lớp 4": [
            "Phần cứng và Phần mềm", "Thông tin và xử lý thông tin",
            "Tìm kiếm thông tin trên Internet", "Đạo đức, pháp luật và văn hóa số",
            "Soạn thảo văn bản: Chèn ảnh, bảng", "Làm quen với phần mềm trình chiếu",
            "Lập trình trực quan (Scratch cơ bản)"
        ],
        "Lớp 5": [
            "Khám phá Computer (Quản lý tệp tin)", "Mạng máy tính và Internet",
            "Tổ chức và lưu trữ thông tin", "Soạn thảo văn bản nâng cao",
            "Thiết kế bài trình chiếu đa phương tiện", "Sử dụng thư điện tử (Email)",
            "Thế giới Logo của em (hoặc Lập trình Scratch nâng cao)"
        ]
    },

    # --- CÔNG NGHỆ (LỚP 3, 4, 5) ---
    "Công nghệ": {
        "Lớp 3": [
            "Tự nhiên và Công nghệ", "Sử dụng đèn học", "Sử dụng quạt điện",
            "Sử dụng máy thu thanh", "Làm đồ dùng học tập", "An toàn với điện"
        ],
        "Lớp 4": [
            "Hoa và cây cảnh trong đời sống", "Trồng hoa, cây cảnh trong chậu",
            "Lắp ghép mô hình kĩ thuật", "Đồ chơi dân gian"
        ],
        "Lớp 5": [
            "Công nghệ và đời sống", "Sáng tạo với các vật liệu",
            "Lắp ráp mô hình xe", "Sử dụng điện thoại/Tivi thông minh an toàn"
        ]
    },

    # --- KHOA HỌC / TNXH ---
    "Tự nhiên & Xã hội": {
        "Lớp 1": ["Gia đình", "Trường học", "Cộng đồng địa phương", "Thực vật và động vật", "Con người và sức khỏe"],
        "Lớp 2": ["Gia đình", "Trường học", "Cộng đồng địa phương", "Thực vật và động vật", "Con người và sức khỏe", "Trái Đất và bầu trời"],
        "Lớp 3": ["Gia đình", "Trường học", "Cộng đồng địa phương", "Thực vật và động vật", "Con người và sức khỏe", "Trái Đất và bầu trời"]
    },
    "Khoa học": {
        "Lớp 4": [
            "Chất. Nước và không khí", "Ánh sáng và nhiệt",
            "Trao đổi chất ở thực vật", "Trao đổi chất ở động vật",
            "Nấm", "Dinh dưỡng ở người"
        ],
        "Lớp 5": [
            "Sự biến đổi chất", "Sử dụng năng lượng (Mặt trời, Gió, Nước chảy)",
            "Sự sinh sản của thực vật", "Sự sinh sản của động vật",
            "Cơ thể người và sức khỏe (Tuổi dậy thì, Phòng bệnh)", "Môi trường và tài nguyên"
        ]
    },

    # --- LỊCH SỬ & ĐỊA LÍ (LỚP 4, 5) ---
    "Lịch sử & Địa lí": {
        "Lớp 4": [
            "Làm quen với phương tiện học tập", "Địa phương em (Tỉnh/Thành phố)",
            "Trung du và miền núi Bắc Bộ", "Đồng bằng Bắc Bộ",
            "Duyên hải miền Trung", "Tây Nguyên", "Nam Bộ"
        ],
        "Lớp 5": [
            "Đất nước và con người Việt Nam", "Những quốc gia đầu tiên trên lãnh thổ VN",
            "Xây dựng và bảo vệ đất nước (X - XIX)", "Việt Nam từ năm 1858 đến nay",
            "Các nước láng giềng", "Châu Á, Châu Âu, Châu Phi, Châu Mĩ..."
        ]
    }
}

# Danh sách môn học và icon (Dùng để hiển thị Card)
SUBJECTS_DATA = [
    {"name": "Toán", "icon": "📐", "color": "#3498db", "class": "bg-blue"},
    {"name": "Tiếng Việt", "icon": "📚", "color": "#e74c3c", "class": "bg-red"},
    {"name": "Tin học", "icon": "💻", "color": "#9b59b6", "class": "bg-purple"},
    {"name": "Tự nhiên & Xã hội", "icon": "🌱", "color": "#2ecc71", "class": "bg-green"}, # Lớp 1,2,3
    {"name": "Khoa học", "icon": "🔬", "color": "#27ae60", "class": "bg-green"}, # Lớp 4,5
    {"name": "Lịch sử & Địa lí", "icon": "🌏", "color": "#e67e22", "class": "bg-orange"},
    {"name": "Công nghệ", "icon": "🛠️", "color": "#1abc9c", "class": "bg-teal"},
]

# ==========================================
# 2. CẤU HÌNH & GIAO DIỆN
# ==========================================
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🏫", layout="wide")

# Khởi tạo Session State
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_grade' not in st.session_state: st.session_state.selected_grade = 'Lớp 1'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = 'Toán'
if 'selected_color' not in st.session_state: st.session_state.selected_color = '#3498db'
if 'matrix_df' not in st.session_state: st.session_state.matrix_df = pd.DataFrame()

# CSS Tùy chỉnh
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
    .floating-author-badge {position: fixed; bottom: 20px; right: 20px; background-color: white; padding: 10px 15px; border-radius: 50px; box-shadow: 0 4px 15px rgba(0,0,0,0.15); border: 2px solid #0984e3; z-index: 9999; display: flex; align-items: center; gap: 12px; transition: transform 0.3s ease;}
    .floating-author-badge:hover {transform: scale(1.05);}
    .author-avatar {width: 40px; height: 40px; border-radius: 50%; border: 2px solid #dfe6e9;}
    .author-info {display: flex; flex-direction: column; line-height: 1.2;}
    .author-name {font-weight: bold; color: #2d3436; font-size: 14px;}
    .author-link {font-size: 11px; color: #0984e3; text-decoration: none; font-weight: 600;}
    .main-title {font-family: 'Times New Roman', serif; font-size: 28px; font-weight: bold; text-align: center; text-transform: uppercase; color: #2c3e50; margin-bottom: 20px;}
    .subject-card {padding: 15px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 16px; cursor: pointer; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;}
    .subject-card:hover {transform: scale(1.05);}
    .bg-blue {background-color: #3498db;} .bg-green {background-color: #2ecc71;} .bg-red {background-color: #e74c3c;}
    .bg-purple {background-color: #9b59b6;} .bg-orange {background-color: #e67e22;} .bg-teal {background-color: #1abc9c;}
    .footer {text-align: center; color: #666; font-size: 14px; margin-top: 50px; border-top: 1px solid #ddd; padding-top: 10px;}
</style>
""", unsafe_allow_html=True)

def show_floating_badge():
    st.markdown("""
    <div class="floating-author-badge">
        <img src="https://api.dicebear.com/9.x/avataaars/svg?seed=BapCai&backgroundColor=b6e3f4" class="author-avatar">
        <div class="author-info">
            <span class="author-name">BapCai</span>
            <a href="#" class="author-link">🌐 Trang chủ tác giả</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CÁC HÀM XỬ LÝ
# ==========================================

def clean_text_for_word(text):
    if not text: return ""
    text = str(text)
    patterns = [r"^Tuyệt vời.*?\n", r"^Dưới đây là.*?\n", r"^Chắc chắn rồi.*?\n", r"^Chào bạn.*?\n"]
    for p in patterns: text = re.sub(p, "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"(PHÒNG GD|TRƯỜNG|SỞ GIÁO DỤC|CỘNG HÒA XÃ HỘI).*?(Họ và tên|Lớp).*?\n", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.replace("**", "").replace("##", "").replace("###", "").strip()

def create_docx_file(school_name, exam_name, student_info, content_body, answer_key):
    doc = Document()
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass
    
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    run_school = p_left.add_run(f"{str(school_name).upper()}")
    run_school.bold = True
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n").bold = True
    p_right.add_run("Độc lập - Tự do - Hạnh phúc").bold = True
    p_right.add_run("\n-------------------").bold = False
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph() 
    
    title = doc.add_paragraph()
    run_title = title.add_run(str(exam_name).upper())
    run_title.bold = True
    run_title.font.size = Pt(14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info = doc.add_paragraph()
    info.add_run("Họ và tên học sinh: ..................................................................................... ").bold = False
    info.add_run(f"Lớp: {student_info.get('grade', '...')}.....")
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph() 
    
    score_table = doc.add_table(rows=2, cols=2)
    score_table.style = 'Table Grid'
    score_table.cell(0, 0).text = "Điểm"
    score_table.cell(0, 1).text = "Lời nhận xét của giáo viên"
    score_table.cell(0,0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.cell(0,1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    score_table.rows[1].height = Cm(2.5)
    doc.add_paragraph() 
    doc.add_paragraph("------------------------------------------------------------------------------------------------------")
    
    clean_body = clean_text_for_word(content_body)
    for line in clean_body.split('\n'):
        line = line.strip()
        if not line: continue
        para = doc.add_paragraph()
        if re.match(r"^(Câu|PHẦN|Bài|Phần|B\.) \d+|^(Câu|PHẦN|Bài|Phần) [IVX]+", line, re.IGNORECASE):
            para.add_run(line).bold = True
        else: para.add_run(line)
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    doc.add_page_break()
    ans_title = doc.add_paragraph("HƯỚNG DẪN CHẤM VÀ ĐÁP ÁN")
    ans_title.runs[0].bold = True
    ans_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(clean_text_for_word(answer_key))
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def generate_exam_from_matrix(api_key, matrix_dataframe, info):
    if not api_key: return None, None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    matrix_str = matrix_dataframe.to_string(index=False)
    
    prompt = f"""
    Bạn là chuyên gia giáo dục tiểu học. Hãy soạn ĐỀ KIỂM TRA MÔN {info['subject']} - {info['grade']}.
    Dựa tuyệt đối vào BẢNG MA TRẬN ĐẶC TẢ sau đây:
    
    {matrix_str}
    
    YÊU CẦU QUAN TRỌNG:
    1. Soạn đúng số lượng câu hỏi, dạng bài (Trắc nghiệm/Tự luận) và mức độ (Biết/Hiểu/Vận dụng) cho từng chủ đề như trong bảng.
    2. Điểm số phải khớp với bảng.
    3. Nội dung phù hợp lứa tuổi học sinh tiểu học {info['grade']}.
    4. KHÔNG viết lời dẫn. Bắt đầu ngay bằng "PHẦN I. TRẮC NGHIỆM..."
    5. Tách đáp án ở cuối bằng chuỗi: ###TÁCH_Ở_ĐÂY###
    """
    try:
        response = model.generate_content(prompt)
        full_text = response.text
        if "###TÁCH_Ở_ĐÂY###" in full_text:
            parts = full_text.split("###TÁCH_Ở_ĐÂY###")
            return parts[0].strip(), parts[1].strip()
        else: return full_text, "Không tìm thấy đáp án tách biệt."
    except Exception as e: return f"Lỗi AI: {str(e)}", ""

# ==========================================
# 4. GIAO DIỆN CHÍNH
# ==========================================

st.markdown('<div class="main-title">HỆ THỐNG HỖ TRỢ RA ĐỀ TIỂU HỌC</div>', unsafe_allow_html=True)
show_floating_badge()

# --- MÀN HÌNH 1: CHỌN MÔN & LỚP ---
if st.session_state.step == 'home':
    st.write("### 1️⃣ Chọn Khối Lớp & Môn Học:")
    
    # Chọn Lớp
    st.markdown('**Chọn Khối Lớp:**')
    grades = ["Lớp 1", "Lớp 2", "Lớp 3", "Lớp 4", "Lớp 5"]
    cols_grade = st.columns(5)
    for i, g in enumerate(grades):
        if cols_grade[i].button(g, key=f"grade_{g}", use_container_width=True, 
                                type="primary" if st.session_state.selected_grade == g else "secondary"):
            st.session_state.selected_grade = g
    
    st.markdown("---")
    
    # Chọn Môn (Lọc môn theo lớp)
    st.markdown('**Chọn Môn Học:**')
    
    # Lọc môn học phù hợp với khối lớp (Ví dụ: Lớp 1,2,3 ko có Tin học nếu muốn)
    # Ở đây tôi để hiện hết, nhưng có thể ẩn bớt nếu cần thiết.
    
    cols = st.columns(3)
    for index, sub in enumerate(SUBJECTS_DATA):
        col_idx = index % 3
        with cols[col_idx]:
            # Nút bấm chọn môn
            if st.button(f"{sub['icon']} {sub['name']}", key=sub['name'], use_container_width=True):
                st.session_state.selected_subject = sub['name']
                st.session_state.selected_color = sub['color']
                st.session_state.step = 'config'
                # Reset ma trận
                st.session_state.matrix_df = pd.DataFrame(columns=["Chủ đề", "Mức độ", "Dạng bài", "Số câu", "Điểm"])
                st.rerun()

# --- MÀN HÌNH 2: CẤU HÌNH MA TRẬN ---
elif st.session_state.step == 'config':
    if st.button("⬅️ Quay lại chọn môn"):
        st.session_state.step = 'home'
        st.rerun()

    subject = st.session_state.selected_subject
    grade = st.session_state.selected_grade
    color = st.session_state.selected_color
    
    st.markdown(f"""<div style="background-color:{color}; padding:10px; border-radius:8px; color:white; margin-bottom:20px; text-align:center;"><h3 style="margin:0;">{grade.upper()} - MÔN: {subject.upper()}</h3></div>""", unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Cài đặt")
        api_key = st.text_input("Mã API Google:", type="password")
        st.subheader("🏫 Thông tin")
        school_name = st.text_input("Tên trường:", value="PTDTBT Tiểu học Giàng Chu Phìn")
        exam_name = st.text_input("Kỳ thi:", value="CUỐI HỌC KÌ I")

    col_left, col_right = st.columns([1, 1.5])

    # === CỘT TRÁI: CHỌN CHỦ ĐỀ CÓ SẴN TRONG CODE ===
    with col_left:
        st.info("2️⃣ Chọn Chủ đề bài học")
        
        # Lấy danh sách chủ đề từ biến PREDEFINED_TOPICS
        topic_list = []
        if subject in PREDEFINED_TOPICS:
            if grade in PREDEFINED_TOPICS[subject]:
                topic_list = PREDEFINED_TOPICS[subject][grade]
            else:
                # Nếu không tìm thấy lớp cụ thể, lấy list mặc định đầu tiên
                first_key = list(PREDEFINED_TOPICS[subject].keys())[0]
                topic_list = PREDEFINED_TOPICS[subject][first_key]
        else:
            topic_list = ["Chủ đề 1", "Chủ đề 2", "Chủ đề 3"] # Fallback

        # Multiselect
        selected_topics = st.multiselect("Tích chọn các bài học cần kiểm tra:", topic_list)
        
        st.markdown("---")
        st.markdown("**Cấu hình nhanh cho các chủ đề đã chọn:**")
        
        c1, c2 = st.columns(2)
        default_level = c1.selectbox("Mức độ:", ["Biết", "Hiểu", "Vận dụng"], index=0)
        default_type = c2.selectbox("Dạng bài:", ["Trắc nghiệm (ABCD)", "Đúng/Sai", "Điền khuyết", "Nối cột", "Tự luận"], index=0)
        default_point = st.number_input("Điểm mặc định:", 0.25, 5.0)
