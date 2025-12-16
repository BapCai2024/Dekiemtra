import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io
import time

# ==========================================
# 1. DỮ LIỆU BÀI HỌC KÈM SỐ TIẾT (CHUẨN CT GDPT 2018)
# ==========================================
# Cấu trúc: { "Môn": { "Lớp": [ {"topic": "Tên bài", "periods": Số_tiết} ] } }

PREDEFINED_DATA = {
    "Toán": {
        "Lớp 1": [
            {"topic": "Các số 0, 1, 2, 3, 4, 5", "periods": 2},
            {"topic": "Các số 6, 7, 8, 9, 10", "periods": 3},
            {"topic": "Hình vuông, hình tròn, hình tam giác", "periods": 2},
            {"topic": "Phép cộng trong phạm vi 10", "periods": 4},
            {"topic": "Phép trừ trong phạm vi 10", "periods": 4},
            {"topic": "Đo độ dài", "periods": 1}
        ],
        "Lớp 2": [
            {"topic": "Phép cộng có nhớ trong phạm vi 20", "periods": 3},
            {"topic": "Phép cộng có nhớ trong phạm vi 100", "periods": 4},
            {"topic": "Làm quen với hình khối (Trụ, Cầu)", "periods": 2},
            {"topic": "Ngày, giờ, ngày tháng", "periods": 2},
            {"topic": "Bảng nhân 2, 5", "periods": 3},
            {"topic": "Bảng chia 2, 5", "periods": 3}
        ],
        "Lớp 3": [
            {"topic": "Ôn tập phép cộng, phép trừ", "periods": 2},
            {"topic": "Bảng nhân 3, 4, 6", "periods": 3},
            {"topic": "Bảng chia 3, 4, 6", "periods": 3},
            {"topic": "Hình tam giác, hình tứ giác", "periods": 2},
            {"topic": "Gam. Đơn vị đo khối lượng", "periods": 1},
            {"topic": "Phép nhân số có 2 chữ số với số có 1 chữ số", "periods": 3}
        ],
        "Lớp 4": [
            {"topic": "Số tự nhiên. Hàng và lớp", "periods": 3},
            {"topic": "Các số có sáu chữ số", "periods": 2},
            {"topic": "Biểu thức có chứa chữ", "periods": 2},
            {"topic": "Góc nhọn, góc tù, góc bẹt", "periods": 2},
            {"topic": "Hai đường thẳng vuông góc", "periods": 1},
            {"topic": "Phép cộng, phép trừ số tự nhiên", "periods": 3},
            {"topic": "Biểu đồ cột", "periods": 1}
        ],
        "Lớp 5": [
            {"topic": "Ôn tập về phân số", "periods": 2},
            {"topic": "Hỗn số", "periods": 2},
            {"topic": "Số thập phân", "periods": 3},
            {"topic": "Hàng của số thập phân", "periods": 2},
            {"topic": "Viết các số đo độ dài dưới dạng số thập phân", "periods": 2},
            {"topic": "Cộng, trừ số thập phân", "periods": 4}
        ]
    },
    "Tiếng Việt": {
        "Lớp 1": [
            {"topic": "Làm quen với chữ cái (A, B, C...)", "periods": 12},
            {"topic": "Làm quen với dấu thanh", "periods": 4},
            {"topic": "Âm và Vần", "periods": 20},
            {"topic": "Tập đọc: Chủ điểm Nhà trường", "periods": 2}
        ],
        "Lớp 4": [
            {"topic": "Đọc: Những ngày hè tươi đẹp", "periods": 2},
            {"topic": "LTVC: Danh từ", "periods": 1},
            {"topic": "Viết: Tìm hiểu cách viết bài văn kể chuyện", "periods": 2},
            {"topic": "Đọc: Đóa hoa đồng thoại", "periods": 2},
            {"topic": "LTVC: Động từ", "periods": 1}
        ],
        "Lớp 5": [
            {"topic": "Đọc: Chuyện một khu vườn nhỏ", "periods": 2},
            {"topic": "LTVC: Đại từ", "periods": 1},
            {"topic": "Viết: Luyện tập tả cảnh", "periods": 2},
            {"topic": "Đọc: Tiếng vĩ cầm ở Mỹ Lai", "periods": 2}
        ]
    },
    "Tin học": {
        "Lớp 3": [
            {"topic": "Bài 1: Thông tin và quyết định", "periods": 1},
            {"topic": "Bài 2: Xử lý thông tin", "periods": 1},
            {"topic": "Bài 3: Máy tính và em", "periods": 2},
            {"topic": "Bài 4: Làm quen với chuột máy tính", "periods": 2},
            {"topic": "Bài 5: Sử dụng bàn phím", "periods": 2}
        ],
        "Lớp 4": [
            {"topic": "Bài 1: Phần cứng và phần mềm máy tính", "periods": 2},
            {"topic": "Bài 2: Gõ bàn phím đúng cách", "periods": 2},
            {"topic": "Bài 3: Thông tin trên trang web", "periods": 1},
            {"topic": "Bài 4: Tìm kiếm thông tin trên Internet", "periods": 2},
            {"topic": "Bài 5: Sử dụng phần mềm soạn thảo văn bản", "periods": 3}
        ],
        "Lớp 5": [
            {"topic": "Bài 1: Các bộ phận của máy tính", "periods": 1},
            {"topic": "Bài 2: Khám phá Computer", "periods": 2},
            {"topic": "Bài 3: Tổ chức thông tin trong máy tính", "periods": 2},
            {"topic": "Bài 4: Thư điện tử (Email)", "periods": 2}
        ]
    }
}

# Fallback cho các môn chưa nhập liệu chi tiết
DEFAULT_TOPICS = [
    {"topic": "Chủ đề 1: Khái niệm cơ bản", "periods": 2},
    {"topic": "Chủ đề 2: Nội dung nâng cao", "periods": 3},
    {"topic": "Chủ đề 3: Thực hành/Vận dụng", "periods": 2},
    {"topic": "Chủ đề 4: Ôn tập chương", "periods": 1}
]

SUBJECTS_INFO = [
    {"name": "Toán", "icon": "📐", "color": "#3498db", "class": "bg-blue"},
    {"name": "Tiếng Việt", "icon": "📚", "color": "#e74c3c", "class": "bg-red"},
    {"name": "Tin học", "icon": "💻", "color": "#9b59b6", "class": "bg-purple"},
    {"name": "Khoa học/TNXH", "icon": "🌱", "color": "#2ecc71", "class": "bg-green"},
    {"name": "Lịch sử & Địa lí", "icon": "🌏", "color": "#e67e22", "class": "bg-orange"},
    {"name": "Công nghệ", "icon": "🛠️", "color": "#1abc9c", "class": "bg-teal"},
]

# ==========================================
# 2. CẤU HÌNH & GIAO DIỆN
# ==========================================
st.set_page_config(page_title="Hệ Thống Ra Đề Chuẩn NĐ30", page_icon="🏫", layout="wide")

if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_grade' not in st.session_state: st.session_state.selected_grade = 'Lớp 1'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = 'Toán'
if 'selected_color' not in st.session_state: st.session_state.selected_color = '#3498db'
if 'matrix_df' not in st.session_state: st.session_state.matrix_df = pd.DataFrame()

st.markdown("""
<style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .main-title {font-family: 'Times New Roman', serif; font-size: 28px; font-weight: bold; text-align: center; color: #2c3e50; text-transform: uppercase; margin-bottom: 10px;}
    .sub-title {text-align: center; font-size: 16px; color: #7f8c8d; margin-bottom: 30px;}
    
    /* Card Môn học */
    .subject-card {padding: 15px; border-radius: 8px; color: white; text-align: center; font-weight: bold; font-size: 16px; cursor: pointer; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
    .subject-card:hover {transform: scale(1.02); transition: 0.2s;}
    .bg-blue {background-color: #3498db;} .bg-red {background-color: #e74c3c;} .bg-purple {background-color: #9b59b6;}
    .bg-green {background-color: #27ae60;} .bg-orange {background-color: #e67e22;} .bg-teal {background-color: #16a085;}
    
    /* Matrix Display */
    .matrix-container {background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #ddd;}
    .total-display {font-size: 18px; font-weight: bold; text-align: right; padding: 10px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HÀM XỬ LÝ WORD (CHUẨN NGHỊ ĐỊNH 30)
# ==========================================
def create_element(name):
    return OxmlElement(name)

def create_attribute(element, name, value):
    element.set(qn(name), value)

def add_page_number(run):
    fldChar1 = create_element('w:fldChar')
    create_attribute(fldChar1, 'w:fldCharType', 'begin')
    instrText = create_element('w:instrText')
    create_attribute(instrText, 'xml:space', 'preserve')
    instrText.text = "PAGE"
    fldChar2 = create_element('w:fldChar')
    create_attribute(fldChar2, 'w:fldCharType', 'end')
    run._element.append(fldChar1)
    run._element.append(instrText)
    run._element.append(fldChar2)

def clean_text(text):
    text = str(text)
    # Loại bỏ các câu thoại thừa của AI
    text = re.sub(r"^Here is.*?:", "", text, flags=re.MULTILINE)
    text = re.sub(r"^Tuyệt vời.*?\n|^Chào bạn.*?\n", "", text, flags=re.IGNORECASE | re.MULTILINE)
    # Loại bỏ markdown
    text = text.replace("**", "").replace("##", "").replace("###", "")
    return text.strip()

def create_docx(school_name, exam_name, info, body, key):
    doc = Document()
    
    # Cài đặt Font Times New Roman toàn văn bản
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13) # Cỡ chữ 13 hoặc 14 chuẩn NĐ30
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass

    # --- HEADER CHUẨN NGHỊ ĐỊNH 30 ---
    # Tạo bảng header 2 cột: Trái (Cơ quan), Phải (Quốc hiệu)
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.8) # Cột trái rộng vừa phải
    table.columns[1].width = Inches(3.2) # Cột phải rộng hơn
    
    # Cột Trái: Đơn vị chủ quản & Tên trường
    cell_left
