import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import time
import requests

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
    .main-title { text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;}
    .question-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1565C0; margin-bottom: 10px; }
    
    /* Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #333;
        text-align: center; padding: 10px; font-size: 14px;
        border-top: 1px solid #ddd; z-index: 100;
    }
    .content-container { padding-bottom: 60px; }
</style>
""", unsafe_allow_html=True)

# --- 3. IMPORT AN TOÀN ---
try:
    import pypdf
except ImportError:
    st.error("⚠️ Thiếu thư viện 'pypdf'. Vui lòng cài đặt: pip install pypdf")

# --- 4. DỮ LIỆU CSDL (GIỮ NGUYÊN) ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 2": [("Tiếng Việt", "📚"), ("Toán", "🧮")],
    "Lớp 3": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 4": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")],
    "Lớp 5": [("Tiếng Việt", "📚"), ("Toán", "🧮"), ("Khoa học", "🔬"), ("Lịch sử & Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🔧")]
}

CURRICULUM_DB = {
    "Lớp 1": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 1: Các số 0, 1, 2, 3, 4, 5 (3 tiết)", "YCCĐ": "Đếm, đọc, viết các số trong phạm vi 5."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 2: Các số 6, 7, 8, 9, 10 (4 tiết)", "YCCĐ": "Đếm, đọc, viết các số từ 6 đến 10."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 3: Nhiều hơn, ít hơn, bằng nhau (2 tiết)", "YCCĐ": "So sánh số lượng giữa hai nhóm đối tượng."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 4: So sánh số (2 tiết)", "YCCĐ": "Sử dụng dấu >, <, = để so sánh các số PV 10."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 5: Mấy và mấy (2 tiết)", "YCCĐ": "Làm quen với tách số và gộp số."},
                {"Chủ đề": "2. Làm quen với hình phẳng", "Bài học": "Bài 7: Hình vuông, hình tròn, hình tam giác, hình chữ nhật (3 tiết)", "YCCĐ": "Nhận dạng và gọi tên đúng các hình phẳng."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 8: Phép cộng trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép cộng; hiểu ý nghĩa thêm vào/gộp lại."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 9: Phép trừ trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép trừ; hiểu ý nghĩa bớt đi/tách ra."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 10: Luyện tập chung (3 tiết)", "YCCĐ": "Vận dụng cộng trừ giải quyết tình huống thực tế."},
                {"Chủ đề": "4. Làm quen khối hình", "Bài học": "Bài 14: Khối lập phương, khối hộp chữ nhật (2 tiết)", "YCCĐ": "Nhận dạng khối lập phương, khối hộp chữ nhật."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Các số đến 100", "Bài học": "Bài 21: Số có hai chữ số (3 tiết)", "YCCĐ": "Đọc, viết, nhận biết cấu tạo số có hai chữ số."},
                {"Chủ đề": "5. Các số đến 100", "Bài học": "Bài 22: So sánh số có hai chữ số (2 tiết)", "YCCĐ": "Biết cách so sánh hai số có hai chữ số."},
                {"Chủ đề": "5. Các số đến 100", "Bài học": "Bài 23: Bảng các số từ 1 đến 100 (2 tiết)", "YCCĐ": "Nhận biết thứ tự số; số liền trước, liền sau."},
                {"Chủ đề": "6. Cộng, trừ PV 100", "Bài học": "Bài 29: Phép cộng số có hai chữ số với số có một chữ số (2 tiết)", "YCCĐ": "Cộng không nhớ; đặt tính rồi tính."},
                {"Chủ đề": "6. Cộng, trừ PV 100", "Bài học": "Bài 30: Phép cộng số có hai chữ số với số có hai chữ số (2 tiết)", "YCCĐ": "Cộng không nhớ số có 2 chữ số."},
                {"Chủ đề": "6. Cộng, trừ PV 100", "Bài học": "Bài 32: Phép trừ số có hai chữ số cho số có một chữ số (2 tiết)", "YCCĐ": "Trừ không nhớ; đặt tính rồi tính."},
                {"Chủ đề": "7. Thời gian, Đo lường", "Bài học": "Bài 35: Các ngày trong tuần (1 tiết)", "YCCĐ": "Biết thứ tự các ngày trong tuần; đọc thời khóa biểu."},
                {"Chủ đề": "7. Thời gian, Đo lường", "Bài học": "Bài 36: Thực hành xem lịch và giờ (2 tiết)", "YCCĐ": "Xem giờ đúng trên đồng hồ; xem lịch tờ."},
                {"Chủ đề": "8. Ôn tập cuối năm", "Bài học": "Bài 38: Ôn tập các số và phép tính (3 tiết)", "YCCĐ": "Tổng hợp kiến thức số học và phép tính."},
                {"Chủ đề": "8. Ôn tập cuối năm", "Bài học": "Bài 39: Ôn tập hình học và đo lường (2 tiết)", "YCCĐ": "Tổng hợp kiến thức hình học, đo lường, giải toán."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 1: A a (2 tiết)", "YCCĐ": "Nhận biết, đọc, viết đúng âm a, chữ a."},
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 2: B b, dấu huyền (2 tiết)", "YCCĐ": "Đọc đúng âm b, thanh huyền; tiếng bà."},
                {"Chủ đề": "Học vần", "Bài học": "Bài 16: M m, N n (2 tiết)", "YCCĐ": "Đọc viết âm m, n."},
                {"Chủ đề": "Học vần", "Bài học": "Bài: an, at (2 tiết)", "YCCĐ": "Vần an, at."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Gia đình", "Bài học": "Bài: Ngôi nhà (2 tiết)", "YCCĐ": "Đọc hiểu bài thơ Ngôi nhà."},
                {"Chủ đề": "Thiên nhiên", "Bài học": "Bài: Hoa kết trái (2 tiết)", "YCCĐ": "Nhận biết các loại hoa quả."},
                {"Chủ đề": "Nhà trường", "Bài học": "Bài: Trường em (2 tiết)", "YCCĐ": "Tình cảm với trường lớp."}
            ]
        }
    },
    "Lớp 2": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập", "Bài học": "Bài 1: Ôn tập các số đến 100 (2 tiết)", "YCCĐ": "Củng cố số học lớp 1."},
                {"Chủ đề": "2. Phép cộng trừ qua 10", "Bài học": "Bài 6: Bảng cộng qua 10 (3 tiết)", "YCCĐ": "Thực hiện cộng có nhớ."},
                {"Chủ đề": "2. Phép cộng trừ qua 10", "Bài học": "Bài 11: Bảng trừ qua 10 (3 tiết)", "YCCĐ": "Thực hiện trừ có nhớ."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 18: Đường thẳng, đường cong (1 tiết)", "YCCĐ": "Phân biệt đường thẳng/cong."},
                {"Chủ đề": "4. Đo lường", "Bài học": "Bài 22: Ngày, tháng (2 tiết)", "YCCĐ": "Xem lịch."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Phép nhân chia", "Bài học": "Bài 40: Bảng nhân 2 (2 tiết)", "YCCĐ": "Thuộc bảng nhân 2."},
                {"Chủ đề": "5. Phép nhân chia", "Bài học": "Bài 41: Bảng nhân 5 (2 tiết)", "YCCĐ": "Thuộc bảng nhân 5."},
                {"Chủ đề": "6. Số đến 1000", "Bài học": "Bài 48: Đơn vị, chục, trăm, nghìn (2 tiết)", "YCCĐ": "Cấu tạo số 3 chữ số."},
                {"Chủ đề": "6. Số đến 1000", "Bài học": "Bài 59: Phép cộng có nhớ PV 1000 (3 tiết)", "YCCĐ": "Cộng số có 3 chữ số."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Tôi là học sinh lớp 2 (2 tiết)", "YCCĐ": "Tâm trạng ngày khai trường."},
                {"Chủ đề": "Bạn bè", "Bài học": "Đọc: Út Tin (2 tiết)", "YCCĐ": "Đặc điểm nhân vật."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Mùa nước nổi (2 tiết)", "YCCĐ": "Vẻ đẹp miền Tây."},
                {"Chủ đề": "Bác Hồ", "Bài học": "Đọc: Ai ngoan sẽ được thưởng (2 tiết)", "YCCĐ": "Đức tính trung thực."}
            ]
        }
    },
    "Lớp 3": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Bảng nhân chia", "Bài học": "Bài 5: Bảng nhân 6 (2 tiết)", "YCCĐ": "Thuộc bảng 6."},
                {"Chủ đề": "Bảng nhân chia", "Bài học": "Bài 9: Bảng nhân 8 (2 tiết)", "YCCĐ": "Thuộc bảng 8."},
                {"Chủ đề": "Góc", "Bài học": "Bài 15: Góc vuông, không vuông (1 tiết)", "YCCĐ": "Dùng ê-ke."},
                {"Chủ đề": "Chia số lớn", "Bài học": "Bài 38: Chia số có 3 chữ số (3 tiết)", "YCCĐ": "Chia hết và có dư."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Số đến 100.000", "Bài học": "Bài 45: Các số 100000 (3 tiết)", "YCCĐ": "Đọc viết số 5 chữ số."},
                {"Chủ đề": "Diện tích", "Bài học": "Bài 52: Diện tích hình chữ nhật (2 tiết)", "YCCĐ": "Công thức S = a x b."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Chiếc áo mùa thu (2 tiết)", "YCCĐ": "Nhân hóa."},
                {"Chủ đề": "Cộng đồng", "Bài học": "Đọc: Lớp học trên đường (2 tiết)", "YCCĐ": "Nghị lực học tập."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lễ hội", "Bài học": "Đọc: Hội đua voi Tây Nguyên (2 tiết)", "YCCĐ": "Văn hóa lễ hội."}
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 1: Các thành phần của máy tính (1 tiết)", "YCCĐ": "Nhận diện bộ phận máy tính."},
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 2: Chức năng các bộ phận (1 tiết)", "YCCĐ": "Chức năng chuột, phím, màn hình."},
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 3: Làm quen chuột máy tính (2 tiết)", "YCCĐ": "Thao tác chuột."},
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 4: Làm quen bàn phím (2 tiết)", "YCCĐ": "Khu vực bàn phím."},
                {"Chủ đề": "Mạng máy tính", "Bài học": "Bài 5: Xem tin tức giải trí (2 tiết)", "YCCĐ": "Truy cập web."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Tổ chức lưu trữ", "Bài học": "Bài 6: Sắp xếp để tìm kiếm (1 tiết)", "YCCĐ": "Lợi ích sắp xếp dữ liệu."},
                {"Chủ đề": "Tổ chức lưu trữ", "Bài học": "Bài 7: Sơ đồ hình cây (1 tiết)", "YCCĐ": "Cấu trúc thư mục."},
                {"Chủ đề": "Soạn thảo", "Bài học": "Bài 8: Làm quen soạn thảo (2 tiết)", "YCCĐ": "Gõ tiếng Việt."},
                {"Chủ đề": "Vẽ", "Bài học": "Bài 11: Vẽ tranh đơn giản (2 tiết)", "YCCĐ": "Sử dụng Paint."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 1: Tự nhiên và Công nghệ (2 tiết)", "YCCĐ": "Phân biệt đối tượng tự nhiên và sản phẩm công nghệ."},
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 2: Sử dụng đèn học (2 tiết)", "YCCĐ": "Nhận biết và sử dụng đèn học an toàn."},
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 3: Sử dụng quạt điện (2 tiết)", "YCCĐ": "Chọn tốc độ gió, sử dụng quạt an toàn."},
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 4: Sử dụng máy thu thanh (2 tiết)", "YCCĐ": "Biết chức năng và cách chỉnh đài phát thanh."},
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 5: Sử dụng máy thu hình (2 tiết)", "YCCĐ": "Chọn kênh, chỉnh âm lượng tivi."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "An toàn công nghệ", "Bài học": "Bài 6: An toàn với môi trường công nghệ (2 tiết)", "YCCĐ": "Phòng tránh tai nạn điện trong gia đình."},
                {"Chủ đề": "Thủ công", "Bài học": "Bài 7: Làm đồ dùng học tập (3 tiết)", "YCCĐ": "Làm thước kẻ, ống bút từ vật liệu tái chế."},
                {"Chủ đề": "Thủ công", "Bài học": "Bài 8: Làm biển báo giao thông (3 tiết)", "YCCĐ": "Làm mô hình biển báo cấm, biển chỉ dẫn."},
                {"Chủ đề": "Thủ công", "Bài học": "Bài 9: Làm đồ chơi đơn giản (3 tiết)", "YCCĐ": "Làm máy bay giấy hoặc chong chóng."}
            ]
        }
    },
    "Lớp 4": {
        "Tin học": { 
            "Học kỳ I": [
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 1: Các thiết bị phần cứng (1 tiết)", "YCCĐ": "Phân loại thiết bị gắn liền (thân, màn) và ngoại vi (chuột, bàn phím, máy in)."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 2: Phần cứng và phần mềm (1 tiết)", "YCCĐ": "Nêu được sơ lược về vai trò của phần cứng và phần mềm; mối quan hệ phụ thuộc giữa chúng."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 3: Thông tin trên trang web (2 tiết)", "YCCĐ": "Nhận biết được siêu văn bản, liên kết trên trang web; biết cách truy cập liên kết."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 4: Tìm kiếm thông tin trên Internet (2 tiết)", "YCCĐ": "Sử dụng máy tìm kiếm (Google) để tìm thông tin theo từ khóa đơn giản; lọc kết quả phù hợp."},
                {"Chủ đề": "Chủ đề D: Đạo đức, pháp luật", "Bài học": "Bài 6: Bản quyền nội dung số (1 tiết)", "YCCĐ": "Giải thích được sơ lược vì sao cần tôn trọng bản quyền; không sao chép trái phép sản phẩm số."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 8: Làm quen với Scratch (2 tiết)", "YCCĐ": "Nhận biết giao diện Scratch; sân khấu, nhân vật, khối lệnh."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 9: Tạo chương trình đầu tiên (2 tiết)", "YCCĐ": "Lắp ghép khối lệnh sự kiện, hiển thị để nhân vật hoạt động."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 10: Điều khiển nhân vật (2 tiết)", "YCCĐ": "Sử dụng nhóm lệnh Motion (Di chuyển) và Looks (Hiển thị) kết hợp sự kiện bàn phím/chuột."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 13: Tạo bài trình chiếu (2 tiết)", "YCCĐ": "Tạo được bài trình chiếu đơn giản có tiêu đề và nội dung; chèn hình ảnh minh họa."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 14: Hiệu ứng chuyển trang (2 tiết)", "YCCĐ": "Chọn và áp dụng hiệu ứng chuyển slide (Transitions) phù hợp cho bài trình chiếu."}
            ]
        },
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Số tự nhiên", "Bài học": "Bài 5: Dãy số tự nhiên (1 tiết)", "YCCĐ": "Nhận biết đặc điểm của dãy số tự nhiên; số liền trước, số liền sau; không có số tự nhiên lớn nhất."},
                {"Chủ đề": "1. Số tự nhiên", "Bài học": "Bài 6: Viết số tự nhiên trong hệ thập phân (1 tiết)", "YCCĐ": "Viết và đọc đúng số tự nhiên; nhận biết giá trị của chữ số theo vị trí."},
                {"Chủ đề": "2. Góc và Đơn vị", "Bài học": "Bài 10: Góc nhọn, góc tù, góc bẹt (2 tiết)", "YCCĐ": "Nhận biết và phân biệt các loại góc bằng quan sát và kiểm tra bằng thước đo góc."},
                {"Chủ đề": "2. Góc và Đơn vị", "Bài học": "Bài 11: Đơn vị đo góc. Độ (1 tiết)", "YCCĐ": "Biết đơn vị đo góc là độ; sử dụng thước đo góc để đo số đo góc."},
                {"Chủ đề": "3. Phép tính số tự nhiên", "Bài học": "Bài 25: Phép chia cho số có hai chữ số (3 tiết)", "YCCĐ": "Thực hiện phép chia số có nhiều chữ số cho số có hai chữ số; biết cách ước lượng thương."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Phân số", "Bài học": "Bài 40: Rút gọn phân số (2 tiết)", "YCCĐ": "Biết cách rút gọn phân số bằng cách chia cả tử và mẫu cho cùng một số tự nhiên lớn hơn 1."},
                {"Chủ đề": "4. Phân số", "Bài học": "Bài 41: Quy đồng mẫu số các phân số (2 tiết)", "YCCĐ": "Thực hiện quy đồng mẫu số hai phân số trong trường hợp đơn giản."},
                {"Chủ đề": "5. Phép tính phân số", "Bài học": "Bài 55: Phép cộng phân số (2 tiết)", "YCCĐ": "Thực hiện cộng hai phân số cùng mẫu và khác mẫu số (thông qua quy đồng)."},
                {"Chủ đề": "5. Phép tính phân số", "Bài học": "Bài 57: Phép nhân phân số (2 tiết)", "YCCĐ": "Thực hiện nhân tử với tử, mẫu với mẫu; rút gọn kết quả nếu có thể."},
                {"Chủ đề": "6. Hình học", "Bài học": "Bài 60: Hình bình hành (1 tiết)", "YCCĐ": "Nhận biết hình bình hành qua các đặc điểm: các cạnh đối diện song song và bằng nhau."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Điều ước của vua Mi-đát (2 tiết) [KNTT]", "YCCĐ": "Hiểu thông điệp: Hạnh phúc không nằm ở vàng bạc mà ở những điều giản dị quanh ta."},
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Tiếng nói của cỏ cây (2 tiết) [KNTT]", "YCCĐ": "Cảm nhận vẻ đẹp và sự sống động, có hồn của thế giới tự nhiên qua cái nhìn của nhân vật."},
                {"Chủ đề": "Tuổi nhỏ chí lớn", "Bài học": "Đọc: Tuổi ngựa (2 tiết) [CTST]", "YCCĐ": "Cảm nhận khát vọng đi xa và tình yêu mẹ tha thiết của bạn nhỏ."},
                {"Chủ đề": "Tuổi nhỏ chí lớn", "Bài học": "Đọc: Văn hay chữ tốt (2 tiết) [Cánh Diều]", "YCCĐ": "Ca ngợi tinh thần kiên trì, khổ luyện để thành tài của danh nhân Cao Bá Quát."},
                {"Chủ đề": "Trải nghiệm", "Bài học": "Đọc: Ở Vương quốc Tương Lai (2 tiết) [KNTT]", "YCCĐ": "Đọc văn bản kịch; hiểu ước mơ sáng tạo của trẻ em."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Sầu riêng (2 tiết) [KNTT]", "YCCĐ": "Nhận biết nghệ thuật miêu tả hương vị, dáng vẻ đặc sắc của cây trái miền Nam."},
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Chợ Tết (2 tiết) [CTST]", "YCCĐ": "Cảm nhận bức tranh giàu màu sắc, âm thanh và không khí vui tươi của phiên chợ Tết vùng cao."},
                {"Chủ đề": "Khám phá thế giới", "Bài học": "Đọc: Đường đi Sa Pa (2 tiết) [KNTT]", "YCCĐ": "Cảm nhận vẻ đẹp biến đổi kì ảo, hùng vĩ của thiên nhiên Sa Pa."},
                {"Chủ đề": "Khám phá thế giới", "Bài học": "Đọc: Hơn một ngàn ngày vòng quanh trái đất (2 tiết) [Cánh Diều]", "YCCĐ": "Hiểu về hành trình dũng cảm thám hiểm thế giới và khẳng định trái đất hình cầu của Ma-zen-lan."}
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "1. Chất", "Bài học": "Bài 1: Tính chất của nước (2 tiết)", "YCCĐ": "Nêu tính chất không màu, không mùi, hòa tan."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 2: Sự chuyển thể của nước (2 tiết)", "YCCĐ": "Phân biệt lỏng, rắn, hơi; sự bay hơi/ngưng tụ."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 3: Vòng tuần hoàn của nước trong tự nhiên (2 tiết)", "YCCĐ": "Vẽ và chú thích được sơ đồ vòng tuần hoàn của nước; nêu ý nghĩa."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 5: Không khí (2 tiết)", "YCCĐ": "Nêu được các thành phần chính của không khí (Oxy, Nitơ...); vai trò của Oxy."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 8: Ánh sáng và bóng tối (2 tiết)", "YCCĐ": "Giải thích được nguyên nhân tạo ra bóng tối; sự thay đổi của bóng khi nguồn sáng thay đổi."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 10: Âm thanh (2 tiết)", "YCCĐ": "Nêu sự lan truyền âm thanh; vật phát ra âm thanh rung động."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 11: Nhiệt độ và nhiệt kế (2 tiết)", "YCCĐ": "Biết cách sử dụng nhiệt kế đo nhiệt độ cơ thể/không khí."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 16: Nhu cầu sống của thực vật (2 tiết)", "YCCĐ": "Cây cần nước, ánh sáng, không khí, chất khoáng để sống."},
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 20: Chuỗi thức ăn (2 tiết)", "YCCĐ": "Vẽ sơ đồ chuỗi thức ăn đơn giản trong tự nhiên."},
                {"Chủ đề": "4. Nấm", "Bài học": "Bài 23: Các loại nấm (2 tiết)", "YCCĐ": "Phân biệt nấm ăn và nấm độc; nêu ích lợi của nấm trong đời sống."},
                {"Chủ đề": "5. Con người và sức khỏe", "Bài học": "Bài 26: Các nhóm chất dinh dưỡng (2 tiết)", "YCCĐ": "Kể tên 4 nhóm chất dinh dưỡng; vai trò của từng nhóm đối với cơ thể."}
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "1. Địa phương em", "Bài học": "Bài 1: Làm quen với bản đồ (2 tiết)", "YCCĐ": "Nhận biết các kí hiệu bản đồ, xác định phương hướng."},
                {"Chủ đề": "2. Trung du Bắc Bộ", "Bài học": "Bài 3: Thiên nhiên vùng Trung du và miền núi Bắc Bộ (2 tiết)", "YCCĐ": "Mô tả đặc điểm địa hình đồi núi, khí hậu lạnh vào mùa đông."},
                {"Chủ đề": "2. Trung du Bắc Bộ", "Bài học": "Bài 5: Đền Hùng và lễ giỗ tổ (2 tiết)", "YCCĐ": "Kể lại truyền thuyết Hùng Vương; ý nghĩa lễ hội Đền Hùng."},
                {"Chủ đề": "3. Đồng bằng Bắc Bộ", "Bài học": "Bài 8: Sông Hồng và văn minh lúa nước (2 tiết)", "YCCĐ": "Nêu vai trò sông Hồng; hệ thống đê điều."},
                {"Chủ đề": "3. Đồng bằng Bắc Bộ", "Bài học": "Bài 10: Thăng Long - Hà Nội (2 tiết)", "YCCĐ": "Nêu các tên gọi của Hà Nội qua các thời kì; Văn Miếu."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Duyên hải Miền Trung", "Bài học": "Bài 15: Biển đảo Việt Nam (2 tiết)", "YCCĐ": "Xác định vị trí quần đảo Hoàng Sa, Trường Sa trên bản đồ; ý thức chủ quyền biển đảo."},
                {"Chủ đề": "4. Duyên hải Miền Trung", "Bài học": "Bài 16: Phố cổ Hội An (2 tiết)", "YCCĐ": "Mô tả kiến trúc, di sản văn hóa Phố cổ Hội An."},
                {"Chủ đề": "5. Tây Nguyên", "Bài học": "Bài 18: Thiên nhiên vùng Tây Nguyên (2 tiết)", "YCCĐ": "Mô tả đặc điểm đất đỏ bazan và các cao nguyên xếp tầng."},
                {"Chủ đề": "5. Tây Nguyên", "Bài học": "Bài 20: Văn hóa Cồng chiêng (2 tiết)", "YCCĐ": "Nêu giá trị di sản văn hóa phi vật thể Cồng chiêng."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 1: Lợi ích của hoa và cây cảnh (2 tiết)", "YCCĐ": "Nêu lợi ích trang trí, làm đẹp."},
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 2: Các loại hoa phổ biến (2 tiết)", "YCCĐ": "Nhận biết tên gọi và đặc điểm đặc trưng của hoa hồng, hoa cúc, hoa đào, hoa mai."},
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 3: Các loại cây cảnh phổ biến (2 tiết)", "YCCĐ": "Nhận biết một số loại cây cảnh thông dụng; ý nghĩa trang trí của chúng."},
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 4: Trồng cây con trong chậu (3 tiết)", "YCCĐ": "Thực hiện đúng quy trình trồng cây con trong chậu."},
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 5: Trồng và chăm sóc hoa trong chậu (3 tiết)", "YCCĐ": "Tưới nước, bón phân cho hoa."},
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 6: Chậu và giá thể trồng hoa (2 tiết)", "YCCĐ": "Chọn chậu và đất trồng phù hợp."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "2. Lắp ghép kĩ thuật", "Bài học": "Bài 7: Bộ lắp ghép mô hình kĩ thuật (2 tiết)", "YCCĐ": "Nhận biết các chi tiết trong bộ lắp ghép."},
                {"Chủ đề": "2. Lắp ghép kĩ thuật", "Bài học": "Bài 8: Lắp ghép mô hình cái đu (2 tiết)", "YCCĐ": "Lắp được cái đu đúng quy trình."},
                {"Chủ đề": "2. Lắp ghép kĩ thuật", "Bài học": "Bài 9: Lắp ghép mô hình rô-bốt (2 tiết)", "YCCĐ": "Lắp được rô-bốt đơn giản."},
                {"Chủ đề": "2. Lắp ghép kĩ thuật", "Bài học": "Bài 10: Lắp ghép mô hình tự chọn (3 tiết)", "YCCĐ": "Sáng tạo mô hình mới."}
            ]
        }
    },
    "Lớp 5": {
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 1: Cây thư mục (1 tiết)", "YCCĐ": "Nhận biết cấu trúc cây thư mục; tạo, đổi tên, xóa thư mục hợp lí để quản lý tệp."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 2: Tìm kiếm tệp và thư mục (1 tiết)", "YCCĐ": "Sử dụng công cụ tìm kiếm trong máy tính để tìm tệp."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 3: Thư điện tử (Email) (2 tiết)", "YCCĐ": "Biết cấu trúc địa chỉ email; thực hiện đăng nhập, soạn, gửi và nhận thư điện tử đơn giản."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 4: An toàn khi sử dụng Email (1 tiết)", "YCCĐ": "Nhận biết thư rác; không mở thư lạ; bảo mật mật khẩu."},
                {"Chủ đề": "Chủ đề D: Đạo đức, pháp luật", "Bài học": "Bài 5: Bản quyền nội dung số (1 tiết)", "YCCĐ": "Hiểu khái niệm bản quyền; ý thức tôn trọng sản phẩm số và không vi phạm bản quyền."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 6: Định dạng văn bản nâng cao (2 tiết)", "YCCĐ": "Biết cách định dạng đoạn văn, căn lề, giãn dòng; chèn bảng biểu vào văn bản."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học (Scratch)", "Bài học": "Bài 9: Biến nhớ trong Scratch (3 tiết)", "YCCĐ": "Tạo được biến nhớ (Variable); sử dụng biến để lưu trữ điểm số hoặc thời gian trong trò chơi."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học (Scratch)", "Bài học": "Bài 10: Sử dụng biến trong tính toán (2 tiết)", "YCCĐ": "Sử dụng các phép toán cộng, trừ, nhân, chia với biến."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học (Scratch)", "Bài học": "Bài 12: Cấu trúc rẽ nhánh (3 tiết)", "YCCĐ": "Sử dụng thành thạo khối lệnh 'Nếu... thì...' và 'Nếu... thì... không thì...' để điều khiển nhân vật."},
                {"Chủ đề": "Chủ đề F: Giải quyết vấn đề", "Bài học": "Bài 15: Dự án kể chuyện tương tác (4 tiết)", "YCCĐ": "Vận dụng tổng hợp kiến thức lập trình (sự kiện, hội thoại, biến, rẽ nhánh) để tạo một câu chuyện hoàn chỉnh."}
            ]
        },
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Số thập phân", "Bài học": "Bài 8: Số thập phân (3 tiết)", "YCCĐ": "Nhận biết, đọc, viết số thập phân; hiểu giá trị của chữ số ở phần nguyên và phần thập phân."},
                {"Chủ đề": "1. Số thập phân", "Bài học": "Bài 10: So sánh các số thập phân (2 tiết)", "YCCĐ": "Biết cách so sánh hai số thập phân; sắp xếp các số theo thứ tự."},
                {"Chủ đề": "2. Các phép tính số thập phân", "Bài học": "Bài 15: Cộng, trừ số thập phân (3 tiết)", "YCCĐ": "Đặt tính và thực hiện thành thạo phép cộng, trừ số thập phân; giải toán có lời văn."},
                {"Chủ đề": "2. Các phép tính số thập phân", "Bài học": "Bài 18: Nhân số thập phân (3 tiết)", "YCCĐ": "Thực hiện nhân một số thập phân với một số tự nhiên và với một số thập phân."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 22: Hình tam giác (2 tiết)", "YCCĐ": "Nhận biết đặc điểm hình tam giác; phân biệt các loại tam giác; xác định đáy và đường cao tương ứng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Tỉ số phần trăm", "Bài học": "Bài 45: Tỉ số phần trăm (2 tiết)", "YCCĐ": "Hiểu ý nghĩa tỉ số phần trăm; biết viết phân số dưới dạng tỉ số phần trăm và ngược lại."},
                {"Chủ đề": "4. Tỉ số phần trăm", "Bài học": "Bài 46: Giải toán về tỉ số phần trăm (3 tiết)", "YCCĐ": "Giải được 3 dạng toán cơ bản về tỉ số phần trăm (Tìm tỉ số, Tìm giá trị %, Tìm số khi biết giá trị %)."},
                {"Chủ đề": "5. Thể tích", "Bài học": "Bài 50: Thể tích hình lập phương (2 tiết)", "YCCĐ": "Nhớ công thức V = a x a x a và tính được thể tích hình lập phương."},
                {"Chủ đề": "5. Thể tích", "Bài học": "Bài 51: Thể tích hình hộp chữ nhật (2 tiết)", "YCCĐ": "Nhớ công thức V = a x b x c và tính được thể tích hình hộp chữ nhật."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Việt Nam gấm vóc", "Bài học": "Đọc: Thư gửi các học sinh (2 tiết) [KNTT]", "YCCĐ": "Hiểu tình cảm yêu thương và sự kỳ vọng to lớn của Bác Hồ đối với thế hệ trẻ."},
                {"Chủ đề": "Việt Nam gấm vóc", "Bài học": "Đọc: Quang cảnh làng mạc ngày mùa (2 tiết) [KNTT]", "YCCĐ": "Cảm nhận vẻ đẹp trù phú, màu sắc vàng rực rỡ và không khí đầm ấm của làng quê Việt Nam."},
                {"Chủ đề": "Cánh chim hòa bình", "Bài học": "Đọc: Bài ca về trái đất (2 tiết) [KNTT]", "YCCĐ": "Hiểu thông điệp: Trái đất là ngôi nhà chung, trẻ em cần đoàn kết bảo vệ hòa bình."},
                {"Chủ đề": "Môi trường xanh", "Bài học": "Đọc: Chuyện một khu vườn nhỏ (2 tiết) [Cánh Diều]", "YCCĐ": "Giáo dục ý thức yêu quý thiên nhiên và làm đẹp môi trường sống ngay tại gia đình."},
                {"Chủ đề": "Môi trường xanh", "Bài học": "Đọc: Kỳ diệu rừng xanh (2 tiết) [CTST]", "YCCĐ": "Cảm nhận vẻ đẹp kì thú, bí ẩn của rừng xanh; ý thức bảo vệ rừng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Người công dân", "Bài học": "Đọc: Người công dân số Một (2 tiết) [KNTT]", "YCCĐ": "Hiểu tâm trạng day dứt, trăn trở và khát vọng cứu nước của người thanh niên Nguyễn Tất Thành."},
                {"Chủ đề": "Người công dân", "Bài học": "Đọc: Thái sư Trần Thủ Độ (2 tiết) [Cánh Diều]", "YCCĐ": "Ca ngợi tấm gương chí công vô tư, đặt lợi ích đất nước lên trên tình riêng của Trần Thủ Độ."},
                {"Chủ đề": "Đất nước đổi mới", "Bài học": "Đọc: Trí dũng song toàn (2 tiết) [CTST]", "YCCĐ": "Ca ngợi sứ thần Giang Văn Minh vừa mưu trí vừa bất khuất để bảo vệ danh dự và quyền lợi đất nước."}
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "1. Chất", "Bài học": "Bài 1: Đất và bảo vệ đất (2 tiết)", "YCCĐ": "Nêu thành phần của đất; biện pháp bảo vệ đất."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 3: Hỗn hợp và dung dịch (2 tiết)", "YCCĐ": "Phân biệt hỗn hợp, dung dịch; tách chất."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 5: Sự biến đổi hóa học (2 tiết)", "YCCĐ": "Phân biệt sự biến đổi lí học (giữ nguyên chất) và sự biến đổi hóa học (sinh ra chất mới)."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 8: Năng lượng mặt trời (2 tiết)", "YCCĐ": "Nêu vai trò của năng lượng mặt trời (chiếu sáng, sưởi ấm...); ứng dụng trong đời sống."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 12: Sử dụng năng lượng điện (2 tiết)", "YCCĐ": "Nêu các ứng dụng của điện; biện pháp an toàn điện và sử dụng tiết kiệm điện."},
                {"Chủ đề": "3. Sự sinh sản", "Bài học": "Bài 18: Sự sinh sản của thực vật có hoa (2 tiết)", "YCCĐ": "Chỉ được cơ quan sinh sản của cây (nhị, nhụy); phân biệt hoa lưỡng tính và hoa đơn tính."},
                {"Chủ đề": "3. Sự sinh sản", "Bài học": "Bài 19: Sự sinh sản của động vật (2 tiết)", "YCCĐ": "Phân biệt động vật đẻ trứng và đẻ con; sơ lược vòng đời của côn trùng."}
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "Xây dựng đất nước", "Bài học": "Bài 4: Nhà Nguyễn (2 tiết)", "YCCĐ": "Nêu được thời gian thành lập; một số đóng góp (về văn hóa, lãnh thổ) và hạn chế của nhà Nguyễn."},
                {"Chủ đề": "Bảo vệ đất nước", "Bài học": "Bài 8: Phong trào chống Pháp cuối thế kỉ XIX (2 tiết)", "YCCĐ": "Kể lại được diễn biến cơ bản của phong trào Cần Vương; vai trò của Phan Đình Phùng, Hàm Nghi."},
                {"Chủ đề": "Cách mạng VN", "Bài học": "Bài 12: Chiến dịch Điện Biên Phủ (3 tiết)", "YCCĐ": "Trình bày diễn biến, ý nghĩa lịch sử to lớn của chiến thắng Điện Biên Phủ 'lừng lẫy năm châu'."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thế giới", "Bài học": "Bài 18: Các châu lục và đại dương (3 tiết)", "YCCĐ": "Nhận biết và chỉ đúng vị trí 6 châu lục và 4 đại dương trên lược đồ/quả địa cầu."},
                {"Chủ đề": "Châu Á", "Bài học": "Bài 19: Châu Á (2 tiết)", "YCCĐ": "Nêu được đặc điểm vị trí, địa hình, khí hậu và dân cư tiêu biểu của Châu Á."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Sáng chế", "Bài học": "Bài 3: Tìm hiểu về thiết kế (2 tiết)", "YCCĐ": "Hiểu khái niệm thiết kế; hình thành ý tưởng và phác thảo bản vẽ thiết kế đơn giản."},
                {"Chủ đề": "Sáng chế", "Bài học": "Bài 4: Thiết kế sản phẩm đơn giản (3 tiết)", "YCCĐ": "Vận dụng kiến thức để thiết kế một sản phẩm phục vụ học tập hoặc vui chơi."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lắp ráp kĩ thuật", "Bài học": "Bài 8: Lắp ráp mô hình rô-bốt (4 tiết)", "YCCĐ": "Đọc bản vẽ, lựa chọn chi tiết và lắp ráp hoàn thiện mô hình rô-bốt từ bộ kĩ thuật."}
            ]
        }
    }
}

# --- 5. HỆ THỐNG API (UNIVERSAL FIX + ANTI-429) ---
def generate_content_with_rotation(api_key, prompt):
    """
    Cơ chế Fallback thông minh:
    1. Ưu tiên Flash (Rẻ, nhanh)
    2. Nếu lỗi, thử Flash bản khác
    3. Nếu lỗi, thử Pro
    """
    genai.configure(api_key=api_key)
    
    # DANH SÁCH MẠNH MẼ: Flash -> Pro -> Experimental
    # Đưa gemini-1.5-flash lên đầu vì quota cao nhất
    model_priority = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    last_error = ""

    for model_name in model_priority:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text, model_name
        except Exception as e:
            error_msg = str(e)
            last_error = error_msg
            
            # Nếu lỗi 429 (Quá tải) -> In ra và thử model tiếp theo ngay lập tức
            if "429" in error_msg:
                # Không sleep lâu, chuyển ngay sang model khác
                continue 
            elif "404" in error_msg:
                continue
            else:
                continue

    return f"Lỗi: Tất cả model đều bận. {last_error}", None

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
                for page in reader.pages: text += page.extract_text()
                return text
        return None
    except Exception:
        return None

def create_word_file_simple(school_name, exam_name, content):
    doc = Document()
    style = doc.styles['Normal']; font = style.font; font.name = 'Times New Roman'; font.size = Pt(13)
    for section in doc.sections:
        section.top_margin = Cm(2); section.bottom_margin = Cm(2)
        section.left_margin = Cm(3); section.right_margin = Cm(2)

    table = doc.add_table(rows=1, cols=2); table.autofit = False
    table.columns[0].width = Cm(7); table.columns[1].width = Cm(9)

    cell_1 = table.cell(0, 0); p1 = cell_1.paragraphs[0]
    run_s = p1.add_run(f"{school_name.upper()}"); run_s.bold = True; run_s.font.size = Pt(12)
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    cell_2 = table.cell(0, 1); p2 = cell_2.paragraphs[0]
    run_e = p2.add_run(f"{exam_name.upper()}\n"); run_e.bold = True; run_e.font.size = Pt(12)
    run_y = p2.add_run("Năm học: .........."); run_y.font.size = Pt(13)
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    for line in content.split('\n'):
        if line.strip():
            p = doc.add_paragraph(line); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    buffer = io.BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

# --- 7. MAIN APP ---
def main():
    if 'exam_result' not in st.session_state: st.session_state.exam_result = ""
    if "exam_list" not in st.session_state: st.session_state.exam_list = [] 
    if "current_preview" not in st.session_state: st.session_state.current_preview = "" 
    if "temp_question_data" not in st.session_state: st.session_state.temp_question_data = None 

    # --- SIDEBAR CHUNG ---
    with st.sidebar:
        st.header("🔑 CẤU HÌNH HỆ THỐNG")
        api_key = st.text_input("Nhập API Key Google:", type="password")
        
        st.divider()
        st.markdown("**TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN**")
        st.caption("Hệ thống hỗ trợ chuyên môn")

    if not api_key:
        st.warning("Vui lòng nhập API Key để bắt đầu.")
        return

    # --- TABS GIAO DIỆN ---
    tab1, tab2 = st.tabs(["📁 TẠO ĐỀ TỪ FILE (UPLOAD)", "✍️ SOẠN TỪNG CÂU (CSDL)"])

    # ========================== TAB 1: CODE CŨ (App 1) ==========================
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
            
            exam_term_t1 = st.selectbox("Kỳ thi:", 
                ["ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ I", "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ I",
                "ĐỀ KIỂM TRA ĐỊNH KÌ GIỮA HỌC KÌ II", "ĐỀ KIỂM TRA ĐỊNH KÌ CUỐI HỌC KÌ II"], key="t1_term")
            
            school_name_t1 = st.text_input("Tên trường:", value="TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN", key="t1_school")

        st.subheader("3. Upload Ma trận")
        uploaded = st.file_uploader("Chọn file (.xlsx, .docx, .pdf)", type=['xlsx', 'docx', 'pdf'], key="t1_up")

        if uploaded and st.button("🚀 TẠO ĐỀ THI NGAY", type="primary", key="t1_btn"):
            content = read_uploaded_file(uploaded)
            if content:
                with st.spinner("Đang tìm model phù hợp và tạo đề..."):
                    prompt = f"""
                    Vai trò: Giáo viên tiểu học. Soạn đề thi môn {sub_name_t1} lớp {grade_t1}.
                    Yêu cầu:
                    1. Chỉ dùng dữ liệu từ văn bản dưới đây.
                    2. Không bịa kiến thức ngoài.
                    3. Cấu trúc: Phần I. Trắc nghiệm (nếu có), Phần II. Tự luận.
                    Dữ liệu ma trận:
                    {content}
                    """
                    result_text, used_model = generate_content_with_rotation(api_key, prompt)
                    if used_model:
                        st.session_state.exam_result = result_text
                        st.success(f"Đã tạo xong bằng model: {used_model}")
                    else:
                        st.error(result_text)

        if st.session_state.exam_result:
            st.markdown("---")
            edited_text = st.text_area("Sửa nội dung:", value=st.session_state.exam_result, height=500, key="t1_edit")
            st.session_state.exam_result = edited_text 
            docx = create_word_file_simple(school_name_t1, exam_term_t1, edited_text)
            st.download_button("📥 TẢI VỀ FILE WORD", docx, file_name=f"De_{sub_name_t1}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")

    # ========================== TAB 2: CODE CŨ (Import st) ==========================
    with tab2:
        st.header("Soạn thảo từng câu hỏi theo CSDL")
        
        # BƯỚC 1: CHỌN LỚP - MÔN
        col1, col2 = st.columns(2)
        with col1:
            selected_grade = st.selectbox("Chọn Khối Lớp:", list(SUBJECTS_DB.keys()), key="t2_grade")
        with col2:
            subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
            selected_subject_full = st.selectbox("Chọn Môn Học:", subjects_list, key="t2_sub")
            selected_subject = selected_subject_full.split(" ", 1)[1]

        # Lấy dữ liệu môn học
        raw_data = CURRICULUM_DB.get(selected_grade, {}).get(selected_subject, {})

        if not raw_data:
            st.warning("⚠️ Dữ liệu đang cập nhật. Vui lòng chọn môn khác.")
        else:
            # BƯỚC 2: BỘ SOẠN CÂU HỎI
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
                lesson_options = {f"{l['Bài học']}": l for l in filtered_lessons}
                selected_lesson_name = st.selectbox("Chọn Bài học:", list(lesson_options.keys()), key="t2_lesson")
                current_lesson_data = lesson_options[selected_lesson_name]
                st.info(f"🎯 **YCCĐ:** {current_lesson_data['YCCĐ']}")

            col_x, col_y, col_z = st.columns(3)
            with col_x:
                q_type = st.selectbox("Dạng câu hỏi:", ["Trắc nghiệm", "Đúng/Sai", "Điền khuyết", "Tự luận"], key="t2_type")
            with col_y:
                level = st.selectbox("Mức độ:", ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"], key="t2_lv")
            with col_z:
                points = st.number_input("Điểm số:", min_value=0.25, max_value=10.0, step=0.25, value=1.0, key="t2_pt")

            if st.button("✨ Tạo câu hỏi (Preview)", type="primary", key="t2_preview"):
                with st.spinner("AI đang viết..."):
                    prompt_q = f"""
                    Đóng vai chuyên gia giáo dục Tiểu học. Soạn **1 CÂU HỎI KIỂM TRA** môn {selected_subject} Lớp {selected_grade}.
                    - Bài học: {current_lesson_data['Bài học']}
                    - YCCĐ: {current_lesson_data['YCCĐ']}
                    - Dạng: {q_type} - Mức độ: {level} - Điểm: {points}
                    OUTPUT:
                    **Câu hỏi:** ...
                    **Đáp án:** ...
                    """
                    preview_content, _ = generate_content_with_rotation(api_key, prompt_q)
                    st.session_state.current_preview = preview_content
                    st.session_state.temp_question_data = {
                        "topic": selected_topic, "lesson": selected_lesson_name,
                        "type": q_type, "level": level, "points": points, "content": preview_content
                    }

            if st.session_state.current_preview:
                st.markdown(f"<div class='question-box'>{st.session_state.current_preview}</div>", unsafe_allow_html=True)
                if st.button("✅ Thêm vào đề thi", key="t2_add"):
                    st.session_state.exam_list.append(st.session_state.temp_question_data)
                    st.session_state.current_preview = ""
                    st.success("Đã thêm!")
                    st.rerun()

            # BƯỚC 3: DANH SÁCH & XUẤT
            if len(st.session_state.exam_list) > 0:
                st.markdown("---")
                st.subheader(f"📋 Danh sách đã chọn ({len(st.session_state.exam_list)} câu)")
                df_preview = pd.DataFrame(st.session_state.exam_list)
                st.dataframe(df_preview[['lesson', 'type', 'points']], use_container_width=True)
                
                if st.button("❌ Xóa câu cuối", key="t2_del"):
                    st.session_state.exam_list.pop()
                    st.rerun()

                # Xuất file (Logic cũ)
                exam_text = f"TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN\nĐỀ KIỂM TRA {selected_subject.upper()}\n" + "-"*50 + "\n\n"
                for idx, q in enumerate(st.session_state.exam_list):
                    exam_text += f"Câu {idx+1} ({q['points']}đ): {q['content']}\n\n"
                
                st.download_button("📥 Tải xuống (.txt)", exam_text, file_name="De_thi.txt", key="t2_down")

    # --- FOOTER ---
    st.markdown("""
    <div class="footer">
        <p style="margin: 0; font-weight: bold; color: #2c3e50;">🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
