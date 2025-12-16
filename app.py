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
    div.stButton > button:first-child { border-radius: 5px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: #333; text-align: center; padding: 10px; font-size: 14px; border-top: 1px solid #ddd; z-index: 100; }
    .content-container { padding-bottom: 60px; }
</style>
""", unsafe_allow_html=True)

# --- 3. CƠ SỞ DỮ LIỆU (CHI TIẾT MỤC LỤC SGK) ---
# Quy ước: KNTT = Kết nối tri thức | CKP = Cùng Khám Phá (Tin học)

SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

CURRICULUM_DB = {
    # =================================================================================
    # KHỐI LỚP 1 (Sách: Kết nối tri thức)
    # =================================================================================
    "Lớp 1": {
        "Toán": { 
            "Học kỳ I": [
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 1: Các số 0, 1, 2, 3, 4, 5 (3 tiết)", "YCCĐ": "Đếm, đọc, viết các số đến 5."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 2: Các số 6, 7, 8, 9, 10 (4 tiết)", "YCCĐ": "Đếm, đọc, viết các số đến 10."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 3: Nhiều hơn, ít hơn, bằng nhau (2 tiết)", "YCCĐ": "So sánh số lượng hai nhóm vật."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 4: So sánh số (2 tiết)", "YCCĐ": "Sử dụng dấu >, <, =."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 5: Mấy và mấy (2 tiết)", "YCCĐ": "Gộp và tách số trong phạm vi 10."},
                {"Chủ đề": "2. Làm quen với hình phẳng", "Bài học": "Bài 7: Hình vuông, hình tròn, hình tam giác (2 tiết)", "YCCĐ": "Nhận dạng hình phẳng."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 8: Phép cộng trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép cộng, viết phép tính."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 9: Phép trừ trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép trừ, viết phép tính."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 10: Luyện tập chung (3 tiết)", "YCCĐ": "Vận dụng cộng trừ giải quyết vấn đề."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Các số trong PV 100", "Bài học": "Bài 21: Số có hai chữ số (3 tiết)", "YCCĐ": "Đọc, viết, nhận biết cấu tạo số."},
                {"Chủ đề": "4. Các số trong PV 100", "Bài học": "Bài 23: Bảng các số từ 1 đến 100 (2 tiết)", "YCCĐ": "Thứ tự số, số liền trước/sau."},
                {"Chủ đề": "5. Cộng, trừ PV 100", "Bài học": "Bài 29: Phép cộng số có hai chữ số với số có một chữ số (2 tiết)", "YCCĐ": "Cộng không nhớ, đặt tính đúng."},
                {"Chủ đề": "5. Cộng, trừ PV 100", "Bài học": "Bài 30: Phép cộng số có hai chữ số với số có hai chữ số (2 tiết)", "YCCĐ": "Cộng không nhớ PV 100."},
                {"Chủ đề": "5. Cộng, trừ PV 100", "Bài học": "Bài 32: Phép trừ số có hai chữ số cho số có một chữ số (2 tiết)", "YCCĐ": "Trừ không nhớ PV 100."},
                {"Chủ đề": "6. Thời gian, Đo lường", "Bài học": "Bài 35: Các ngày trong tuần (1 tiết)", "YCCĐ": "Đọc thứ ngày, thời khóa biểu."},
                {"Chủ đề": "6. Thời gian, Đo lường", "Bài học": "Bài 36: Thực hành xem lịch và giờ (2 tiết)", "YCCĐ": "Xem giờ đúng, xem lịch tờ."},
                {"Chủ đề": "7. Ôn tập cuối năm", "Bài học": "Bài 38: Ôn tập các số và phép tính (3 tiết)", "YCCĐ": "Tổng hợp kiến thức cả năm."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 1: A a (KNTT)", "YCCĐ": "Nhận biết âm a, chữ a."},
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 2: B b, dấu huyền (KNTT)", "YCCĐ": "Đọc âm b, thanh huyền, tiếng bà."},
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 3: C c, dấu sắc (KNTT)", "YCCĐ": "Đọc âm c, thanh sắc, tiếng cá."},
                {"Chủ đề": "Học vần (Kết hợp)", "Bài học": "Bài: an, at (KNTT/CTST)", "YCCĐ": "Đọc trơn, viết đúng vần an, at."},
                {"Chủ đề": "Học vần (Kết hợp)", "Bài học": "Bài: on, ot (KNTT/Cánh Diều)", "YCCĐ": "Đọc trơn, viết đúng vần on, ot."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Gia đình", "Bài học": "Bài đọc: Ngôi nhà (KNTT)", "YCCĐ": "Đọc hiểu bài thơ, tình cảm gia đình."},
                {"Chủ đề": "Gia đình", "Bài học": "Bài đọc: Làm anh (Cánh Diều)", "YCCĐ": "Hiểu trách nhiệm của anh chị em."},
                {"Chủ đề": "Thiên nhiên", "Bài học": "Bài đọc: Hoa kết trái (CTST)", "YCCĐ": "Nhận biết các loại hoa quả."},
                {"Chủ đề": "Nhà trường", "Bài học": "Bài đọc: Trường em (KNTT)", "YCCĐ": "Tình cảm yêu mến trường lớp."},
                {"Chủ đề": "Bác Hồ", "Bài học": "Bài đọc: Bác Hồ và thiếu nhi (Cánh Diều)", "YCCĐ": "Cảm nhận tình thương của Bác."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 2 (Sách: Kết nối tri thức)
    # =================================================================================
    "Lớp 2": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập và bổ sung", "Bài học": "Bài 1: Ôn tập các số đến 100", "YCCĐ": "Đọc, viết, so sánh số đến 100."},
                {"Chủ đề": "2. Phép cộng, trừ qua 10", "Bài học": "Bài 6: Bảng cộng (qua 10)", "YCCĐ": "Thuộc bảng cộng, tính nhẩm."},
                {"Chủ đề": "2. Phép cộng, trừ qua 10", "Bài học": "Bài 11: Bảng trừ (qua 10)", "YCCĐ": "Thuộc bảng trừ, tính nhẩm."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 18: Đường thẳng, đường cong", "YCCĐ": "Phân biệt đường thẳng, cong."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 19: Điểm, đoạn thẳng", "YCCĐ": "Nhận biết điểm, đoạn thẳng, 3 điểm thẳng hàng."},
                {"Chủ đề": "4. Đo lường", "Bài học": "Bài 22: Ngày, tháng", "YCCĐ": "Xem lịch, biết số ngày trong tháng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Phép nhân, chia", "Bài học": "Bài 40: Bảng nhân 2", "YCCĐ": "Lập và thuộc bảng nhân 2."},
                {"Chủ đề": "5. Phép nhân, chia", "Bài học": "Bài 41: Bảng nhân 5", "YCCĐ": "Lập và thuộc bảng nhân 5."},
                {"Chủ đề": "5. Phép nhân, chia", "Bài học": "Bài 45: Bảng chia 2", "YCCĐ": "Lập và thuộc bảng chia 2."},
                {"Chủ đề": "6. Các số đến 1000", "Bài học": "Bài 48: Đơn vị, chục, trăm, nghìn", "YCCĐ": "Nhận biết hàng, quan hệ giữa các hàng."},
                {"Chủ đề": "6. Các số đến 1000", "Bài học": "Bài 59: Phép cộng (có nhớ) trong PV 1000", "YCCĐ": "Cộng có nhớ số có 3 chữ số."},
                {"Chủ đề": "7. Ôn tập", "Bài học": "Bài 70: Ôn tập chung", "YCCĐ": "Hệ thống kiến thức cả năm."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Tôi là học sinh lớp 2 (KNTT)", "YCCĐ": "Hiểu tâm trạng ngày khai trường."},
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Ngày hôm qua đâu rồi? (KNTT)", "YCCĐ": "Hiểu giá trị thời gian."},
                {"Chủ đề": "Bạn bè", "Bài học": "Đọc: Út Tin (CTST)", "YCCĐ": "Nhận diện đặc điểm nhân vật."},
                {"Chủ đề": "Thầy cô", "Bài học": "Đọc: Cô giáo lớp em (Cánh Diều)", "YCCĐ": "Cảm nhận tình cảm thầy trò."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Mùa nước nổi (CTST)", "YCCĐ": "Vẻ đẹp thiên nhiên miền Tây."},
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Đường đến trường (KNTT)", "YCCĐ": "Vẻ đẹp cảnh vật đường đi học."},
                {"Chủ đề": "Bốn mùa", "Bài học": "Đọc: Chuyện bốn mùa (KNTT)", "YCCĐ": "Đặc điểm các mùa trong năm."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 3
    # =================================================================================
    "Lớp 3": {
        "Tin học": { # Sách: Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 1: Các thành phần của máy tính (1 tiết)", "YCCĐ": "Nhận diện: thân máy, màn hình, phím, chuột."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 2: Chức năng các bộ phận máy tính (1 tiết)", "YCCĐ": "Biết chức năng thiết bị vào/ra."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 3: Làm quen với chuột máy tính (2 tiết)", "YCCĐ": "Thao tác: di chuyển, nháy, kéo thả."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 4: Làm quen với bàn phím máy tính (2 tiết)", "YCCĐ": "Nhận biết khu vực phím, đặt tay đúng."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 5: Xem tin tức và giải trí trên Internet (2 tiết)", "YCCĐ": "Truy cập trang web, xem thông tin."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chủ đề C: Tổ chức lưu trữ", "Bài học": "Bài 6: Sắp xếp để tìm kiếm (1 tiết)", "YCCĐ": "Hiểu sự cần thiết của sắp xếp dữ liệu."},
                {"Chủ đề": "Chủ đề C: Tổ chức lưu trữ", "Bài học": "Bài 7: Sơ đồ hình cây (1 tiết)", "YCCĐ": "Nhận biết cấu trúc cây thư mục."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 8: Làm quen với soạn thảo văn bản (2 tiết)", "YCCĐ": "Gõ kí tự, dấu tiếng Việt (Telex/Vni)."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 9: Soạn thảo văn bản đơn giản (2 tiết)", "YCCĐ": "Gõ đoạn văn ngắn, xóa sửa lỗi."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 11: Vẽ tranh đơn giản (2 tiết)", "YCCĐ": "Sử dụng công cụ vẽ hình cơ bản."},
                {"Chủ đề": "Chủ đề F: Giải quyết vấn đề", "Bài học": "Bài 13: Luyện tập sử dụng chuột (2 tiết)", "YCCĐ": "Thành thạo thao tác chuột qua trò chơi."}
            ]
        },
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập và bổ sung", "Bài học": "Bài 1: Ôn tập các số đến 1000", "YCCĐ": "Đọc, viết, so sánh số đến 1000."},
                {"Chủ đề": "2. Bảng nhân, bảng chia", "Bài học": "Bài 5: Bảng nhân 6", "YCCĐ": "Lập và thuộc bảng nhân 6."},
                {"Chủ đề": "2. Bảng nhân, bảng chia", "Bài học": "Bài 9: Bảng nhân 8", "YCCĐ": "Lập và thuộc bảng nhân 8."},
                {"Chủ đề": "3. Góc và Hình", "Bài học": "Bài 15: Góc vuông, góc không vuông", "YCCĐ": "Nhận biết góc vuông bằng ê-ke."},
                {"Chủ đề": "4. Phép chia số lớn", "Bài học": "Bài 38: Chia số có ba chữ số cho số có một chữ số", "YCCĐ": "Chia hết và chia có dư."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Số đến 100.000", "Bài học": "Bài 45: Các số trong phạm vi 100000", "YCCĐ": "Đọc, viết số có 5 chữ số."},
                {"Chủ đề": "6. Diện tích", "Bài học": "Bài 51: Diện tích của một hình", "YCCĐ": "Làm quen biểu tượng diện tích."},
                {"Chủ đề": "6. Diện tích", "Bài học": "Bài 52: Diện tích hình chữ nhật", "YCCĐ": "Vận dụng công thức tính diện tích HCN."},
                {"Chủ đề": "7. Cộng trừ PV 100.000", "Bài học": "Bài 58: Phép cộng trong phạm vi 100000", "YCCĐ": "Cộng có nhớ trong phạm vi 100.000."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Chiếc áo mùa thu (CTST)", "YCCĐ": "Nhận biết nhân hóa; cảm nhận mùa thu."},
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Ngày khai trường (KNTT)", "YCCĐ": "Niềm vui ngày tựu trường."},
                {"Chủ đề": "Cộng đồng", "Bài học": "Đọc: Lớp học trên đường (Cánh Diều)", "YCCĐ": "Ý nghĩa của việc học tập."},
                {"Chủ đề": "Sáng tạo", "Bài học": "Đọc: Ông tổ nghề thêu (Cánh Diều)", "YCCĐ": "Ca ngợi trí thông minh, sáng tạo."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lễ hội", "Bài học": "Đọc: Hội đua voi ở Tây Nguyên (KNTT)", "YCCĐ": "Không khí lễ hội đua voi."},
                {"Chủ đề": "Lễ hội", "Bài học": "Đọc: Đua ghe ngo (CTST)", "YCCĐ": "Nét văn hóa lễ hội Khmer."}
            ]
        },
        "Công nghệ": { # KNTT
            "Học kỳ I": [{"Chủ đề": "Tự nhiên và CN", "Bài học": "Bài 1: Tự nhiên và Công nghệ", "YCCĐ": "Phân biệt đối tượng tự nhiên/công nghệ."}, {"Chủ đề": "Đồ dùng điện", "Bài học": "Bài 2: Sử dụng đèn học", "YCCĐ": "Sử dụng đèn học an toàn."}],
            "Học kỳ II": [{"Chủ đề": "Thủ công", "Bài học": "Bài 7: Làm đồ dùng học tập", "YCCĐ": "Làm ống đựng bút/thước kẻ."}, {"Chủ đề": "Thủ công", "Bài học": "Bài 9: Làm biển báo giao thông", "YCCĐ": "Làm mô hình biển báo."}]
        }
    },

    # =================================================================================
    # KHỐI LỚP 4
    # =================================================================================
    "Lớp 4": {
        "Tin học": { # Sách: Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 1: Các thiết bị phần cứng (1 tiết)", "YCCĐ": "Phân loại thiết bị gắn liền và ngoại vi."},
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 2: Phần cứng và phần mềm (1 tiết)", "YCCĐ": "Mối quan hệ phụ thuộc giữa phần cứng, phần mềm."},
                {"Chủ đề": "B. Mạng máy tính", "Bài học": "Bài 3: Thông tin trên trang web (2 tiết)", "YCCĐ": "Nhận biết siêu văn bản, liên kết."},
                {"Chủ đề": "B. Mạng máy tính", "Bài học": "Bài 4: Tìm kiếm thông tin trên Internet (2 tiết)", "YCCĐ": "Sử dụng từ khóa tìm kiếm, lọc kết quả."},
                {"Chủ đề": "D. Đạo đức", "Bài học": "Bài 6: Bản quyền nội dung số (1 tiết)", "YCCĐ": "Tôn trọng bản quyền, không sao chép trái phép."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 8: Làm quen với Scratch (2 tiết)", "YCCĐ": "Giao diện Scratch, sân khấu, khối lệnh."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 9: Tạo chương trình đầu tiên (2 tiết)", "YCCĐ": "Lắp ghép khối lệnh sự kiện, hiển thị."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 10: Điều khiển nhân vật (2 tiết)", "YCCĐ": "Sử dụng lệnh Motion và Looks."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 13: Tạo bài trình chiếu (2 tiết)", "YCCĐ": "Tạo slide, nhập nội dung, chèn ảnh."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 14: Hiệu ứng chuyển trang (2 tiết)", "YCCĐ": "Áp dụng hiệu ứng Transitions."}
            ]
        },
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Số tự nhiên", "Bài học": "Bài 5: Dãy số tự nhiên", "YCCĐ": "Đặc điểm dãy số tự nhiên."},
                {"Chủ đề": "1. Số tự nhiên", "Bài học": "Bài 6: Viết số tự nhiên trong hệ thập phân", "YCCĐ": "Giá trị theo vị trí của chữ số."},
                {"Chủ đề": "2. Góc và Đơn vị", "Bài học": "Bài 10: Góc nhọn, góc tù, góc bẹt", "YCCĐ": "Phân biệt các loại góc."},
                {"Chủ đề": "2. Góc và Đơn vị", "Bài học": "Bài 11: Đơn vị đo góc. Độ", "YCCĐ": "Dùng thước đo góc để đo độ."},
                {"Chủ đề": "3. Phép tính", "Bài học": "Bài 25: Phép chia cho số có hai chữ số", "YCCĐ": "Chia số nhiều chữ số cho 2 chữ số."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Phân số", "Bài học": "Bài 40: Rút gọn phân số", "YCCĐ": "Chia tử và mẫu cho cùng số."},
                {"Chủ đề": "4. Phân số", "Bài học": "Bài 41: Quy đồng mẫu số các phân số", "YCCĐ": "Quy đồng mẫu số đơn giản."},
                {"Chủ đề": "5. Phép tính phân số", "Bài học": "Bài 55: Phép cộng phân số", "YCCĐ": "Cộng phân số khác mẫu."},
                {"Chủ đề": "5. Phép tính phân số", "Bài học": "Bài 57: Phép nhân phân số", "YCCĐ": "Nhân tử với tử, mẫu với mẫu."},
                {"Chủ đề": "6. Hình học", "Bài học": "Bài 60: Hình bình hành", "YCCĐ": "Nhận biết cạnh đối song song, bằng nhau."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Điều ước của vua Mi-đát (KNTT)", "YCCĐ": "Hạnh phúc từ điều giản dị."},
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Tiếng nói của cỏ cây (KNTT)", "YCCĐ": "Vẻ đẹp sống động của thiên nhiên."},
                {"Chủ đề": "Tuổi nhỏ chí lớn", "Bài học": "Đọc: Tuổi ngựa (CTST)", "YCCĐ": "Khát vọng đi xa, tình yêu mẹ."},
                {"Chủ đề": "Tuổi nhỏ chí lớn", "Bài học": "Đọc: Văn hay chữ tốt (Cánh Diều)", "YCCĐ": "Tinh thần khổ luyện của Cao Bá Quát."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Sầu riêng (KNTT)", "YCCĐ": "Miêu tả hương vị trái cây miền Nam."},
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Chợ Tết (CTST)", "YCCĐ": "Bức tranh chợ Tết vùng cao."},
                {"Chủ đề": "Khám phá thế giới", "Bài học": "Đọc: Đường đi Sa Pa (KNTT)", "YCCĐ": "Vẻ đẹp thiên nhiên Sa Pa."},
                {"Chủ đề": "Khám phá thế giới", "Bài học": "Đọc: Hơn một ngàn ngày vòng quanh trái đất (Cánh Diều)", "YCCĐ": "Hành trình thám hiểm của Ma-zen-lan."}
            ]
        },
        "Khoa học": { # KNTT
            "Học kỳ I": [{"Chủ đề": "Nước", "Bài học": "Bài 3: Vòng tuần hoàn của nước", "YCCĐ": "Vẽ sơ đồ vòng tuần hoàn."}, {"Chủ đề": "Ánh sáng", "Bài học": "Bài 8: Ánh sáng và bóng tối", "YCCĐ": "Nguyên nhân tạo bóng tối."}],
            "Học kỳ II": [{"Chủ đề": "Nấm", "Bài học": "Bài 18: Nấm và tác dụng của nấm", "YCCĐ": "Phân biệt nấm ăn/độc."}, {"Chủ đề": "Dinh dưỡng", "Bài học": "Bài 22: Các nhóm chất dinh dưỡng", "YCCĐ": "Vai trò 4 nhóm chất."}]
        },
        "Lịch sử và Địa lí": { # KNTT
            "Học kỳ I": [{"Chủ đề": "Trung du Bắc Bộ", "Bài học": "Bài 3: Thiên nhiên vùng Trung du", "YCCĐ": "Địa hình đồi bát úp, khí hậu."}, {"Chủ đề": "Thăng Long", "Bài học": "Bài 8: Văn miếu - Quốc tử giám", "YCCĐ": "Kiến trúc trường ĐH đầu tiên."}],
            "Học kỳ II": [{"Chủ đề": "Biển đảo", "Bài học": "Bài 15: Biển đảo Việt Nam", "YCCĐ": "Vị trí Hoàng Sa, Trường Sa."}, {"Chủ đề": "Tây Nguyên", "Bài học": "Bài 18: Thiên nhiên vùng Tây Nguyên", "YCCĐ": "Đất đỏ bazan, cao nguyên."}]
        },
        "Công nghệ": {
            "Học kỳ I": [{"Chủ đề": "Hoa cây cảnh", "Bài học": "Bài 2: Các loại hoa phổ biến", "YCCĐ": "Nhận biết hoa hồng, cúc, đào."}],
            "Học kỳ II": [{"Chủ đề": "Lắp ghép", "Bài học": "Bài 6: Lắp ghép mô hình xe", "YCCĐ": "Lắp xe đẩy/nôi."}, {"Chủ đề": "Đồ chơi", "Bài học": "Bài 9: Làm chong chóng", "YCCĐ": "Làm chong chóng giấy."}]
        }
    },

    # =================================================================================
    # KHỐI LỚP 5
    # =================================================================================
    "Lớp 5": {
        "Tin học": { # Sách: Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 1: Cây thư mục (1 tiết)", "YCCĐ": "Cấu trúc cây; tạo, đổi tên, xóa thư mục."},
                {"Chủ đề": "B. Mạng máy tính", "Bài học": "Bài 3: Thư điện tử (Email) (2 tiết)", "YCCĐ": "Cấu trúc email; gửi/nhận thư."},
                {"Chủ đề": "D. Đạo đức", "Bài học": "Bài 5: Bản quyền nội dung số (1 tiết)", "YCCĐ": "Tôn trọng bản quyền sản phẩm số."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 6: Định dạng văn bản nâng cao (2 tiết)", "YCCĐ": "Định dạng đoạn, căn lề, chèn bảng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 9: Biến nhớ trong Scratch (3 tiết)", "YCCĐ": "Tạo biến; dùng biến lưu điểm/thời gian."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 12: Cấu trúc rẽ nhánh (3 tiết)", "YCCĐ": "Khối lệnh Nếu... thì...; Nếu... thì... không thì..."},
                {"Chủ đề": "F. Giải quyết vấn đề", "Bài học": "Bài 15: Dự án kể chuyện tương tác (4 tiết)", "YCCĐ": "Lập trình câu chuyện/trò chơi hoàn chỉnh."}
            ]
        },
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Số thập phân", "Bài học": "Bài 8: Số thập phân", "YCCĐ": "Đọc, viết, giá trị theo hàng."},
                {"Chủ đề": "1. Số thập phân", "Bài học": "Bài 10: So sánh các số thập phân", "YCCĐ": "So sánh, sắp xếp thứ tự."},
                {"Chủ đề": "2. Phép tính", "Bài học": "Bài 15: Cộng, trừ số thập phân", "YCCĐ": "Cộng trừ thành thạo."},
                {"Chủ đề": "2. Phép tính", "Bài học": "Bài 18: Nhân số thập phân", "YCCĐ": "Nhân với số tự nhiên/thập phân."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 22: Hình tam giác", "YCCĐ": "Đặc điểm; đáy, đường cao."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Tỉ số phần trăm", "Bài học": "Bài 45: Tỉ số phần trăm", "YCCĐ": "Ý nghĩa %; chuyển phân số sang %."},
                {"Chủ đề": "4. Tỉ số phần trăm", "Bài học": "Bài 46: Giải toán về tỉ số phần trăm", "YCCĐ": "Giải 3 dạng toán % cơ bản."},
                {"Chủ đề": "5. Thể tích", "Bài học": "Bài 50: Thể tích hình lập phương", "YCCĐ": "Tính V = a x a x a."},
                {"Chủ đề": "5. Thể tích", "Bài học": "Bài 51: Thể tích hình hộp chữ nhật", "YCCĐ": "Tính V = a x b x c."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Việt Nam gấm vóc", "Bài học": "Đọc: Thư gửi các học sinh (KNTT)", "YCCĐ": "Kỳ vọng của Bác Hồ với học sinh."},
                {"Chủ đề": "Việt Nam gấm vóc", "Bài học": "Đọc: Quang cảnh làng mạc ngày mùa (KNTT)", "YCCĐ": "Vẻ đẹp trù phú làng quê."},
                {"Chủ đề": "Cánh chim hòa bình", "Bài học": "Đọc: Bài ca về trái đất (KNTT)", "YCCĐ": "Thông điệp hòa bình."},
                {"Chủ đề": "Môi trường xanh", "Bài học": "Đọc: Chuyện một khu vườn nhỏ (Cánh Diều)", "YCCĐ": "Ý thức yêu thiên nhiên."},
                {"Chủ đề": "Môi trường xanh", "Bài học": "Đọc: Kỳ diệu rừng xanh (CTST)", "YCCĐ": "Vẻ đẹp rừng xanh; bảo vệ rừng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Người công dân", "Bài học": "Đọc: Người công dân số Một (KNTT)", "YCCĐ": "Khát vọng cứu nước của Bác."},
                {"Chủ đề": "Người công dân", "Bài học": "Đọc: Thái sư Trần Thủ Độ (Cánh Diều)", "YCCĐ": "Tấm gương chí công vô tư."},
                {"Chủ đề": "Đất nước đổi mới", "Bài học": "Đọc: Trí dũng song toàn (CTST)", "YCCĐ": "Giang Văn Minh bảo vệ danh dự đất nước."}
            ]
        },
        "Khoa học": { # KNTT
            "Học kỳ I": [{"Chủ đề": "Biến đổi chất", "Bài học": "Bài 5: Sự biến đổi hóa học", "YCCĐ": "Phân biệt biến đổi lí/hóa."}, {"Chủ đề": "Năng lượng", "Bài học": "Bài 10: Năng lượng mặt trời", "YCCĐ": "Vai trò, ứng dụng NL mặt trời."}],
            "Học kỳ II": [{"Chủ đề": "Năng lượng", "Bài học": "Bài 12: Sử dụng năng lượng điện", "YCCĐ": "An toàn, tiết kiệm điện."}, {"Chủ đề": "Sinh sản", "Bài học": "Bài 18: Sự sinh sản thực vật có hoa", "YCCĐ": "Cơ quan sinh sản; hoa đơn/lưỡng tính."}]
        },
        "Lịch sử và Địa lí": { # KNTT
            "Học kỳ I": [{"Chủ đề": "Dựng nước", "Bài học": "Bài 4: Nhà Nguyễn", "YCCĐ": "Đóng góp, hạn chế nhà Nguyễn."}, {"Chủ đề": "Giữ nước", "Bài học": "Bài 8: Phong trào chống Pháp cuối TK 19", "YCCĐ": "Cần Vương; Phan Đình Phùng."}],
            "Học kỳ II": [{"Chủ đề": "Thế giới", "Bài học": "Bài 18: Các châu lục và đại dương", "YCCĐ": "Vị trí 6 châu, 4 đại dương."}, {"Chủ đề": "Châu Á", "Bài học": "Bài 19: Châu Á", "YCCĐ": "Đặc điểm tự nhiên, dân cư Châu Á."}]
        },
        "Công nghệ": {
            "Học kỳ I": [{"Chủ đề": "Sáng chế", "Bài học": "Bài 3: Tìm hiểu về thiết kế", "YCCĐ": "Ý tưởng thiết kế."}, {"Chủ đề": "Sáng chế", "Bài học": "Bài 4: Thiết kế sản phẩm đơn giản", "YCCĐ": "Thiết kế đồ dùng học tập."}],
            "Học kỳ II": [{"Chủ đề": "Lắp ráp", "Bài học": "Bài 8: Lắp ráp mô hình rô-bốt", "YCCĐ": "Lắp ráp hoàn thiện rô-bốt."}]
        }
    }
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
    Đóng vai chuyên gia giáo dục Tiểu học (Chương trình GDPT 2018).
    Hãy soạn **1 CÂU HỎI KIỂM TRA ĐỊNH KỲ** cho môn {subject} Lớp {grade}.
    
    THÔNG TIN CẤU TRÚC:
    - Bài học: {lesson_info['Bài học']}
    - Yêu cầu cần đạt (YCCĐ): {lesson_info['YCCĐ']}
    - Dạng câu hỏi: {q_type}
    - Mức độ: {level}
    - Điểm số: {points} điểm.

    YÊU CẦU NỘI DUNG:
    1. Nội dung phải chính xác, phù hợp với tâm lý lứa tuổi học sinh {grade}.
    2. Bám sát tuyệt đối vào YCCĐ đã cung cấp.
    3. Ngôn ngữ trong sáng, rõ ràng.
    4. Nếu là câu trắc nghiệm: Phải có 4 đáp án A, B, C, D (chỉ 1 đúng).
    5. Nếu là Tin học/Công nghệ: Câu hỏi phải thực tế, liên quan đến thao tác.

    OUTPUT TRẢ VỀ (Bắt buộc theo định dạng sau):
    **Câu hỏi:** [Nội dung câu hỏi đầy đủ]
    **Đáp án:** [Đáp án chi tiết và hướng dẫn chấm ngắn gọn]
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

st.markdown("<div class='content-container'>", unsafe_allow_html=True) 
st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# SIDEBAR
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
    st.warning(f"⚠️ Dữ liệu cho môn {selected_subject} - {selected_grade} đang được cập nhật. Vui lòng chọn môn khác.")
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
    
    # Lấy danh sách chủ đề duy nhất
    unique_topics = sorted(list(set([l['Chủ đề'] for l in lessons_in_term])))
    if not unique_topics:
        st.warning("Chưa có chủ đề cho học kỳ này.")
        st.stop()
    selected_topic = st.selectbox("Chọn Chủ đề:", unique_topics)

with col_b:
    # Lọc bài học theo chủ đề (Hiển thị list bài học đầy đủ)
    filtered_lessons = [l for l in lessons_in_term if l['Chủ đề'] == selected_topic]
    
    if not filtered_lessons:
         st.warning("Chưa có bài học cho chủ đề này.")
         st.stop()

    lesson_options = {f"{l['Bài học']}": l for l in filtered_lessons}
    selected_lesson_name = st.selectbox("Chọn Bài học:", list(lesson_options.keys()))
    
    # Kiểm tra key an toàn
    if selected_lesson_name not in lesson_options:
        st.stop()
        
    current_lesson_data = lesson_options[selected_lesson_name]
    st.info(f"🎯 **YCCĐ (TT 32/2018):** {current_lesson_data['YCCĐ']}")

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
    # 3.1. Hiển thị bảng tóm tắt
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

    # 3.2. Xuất file
    # --- PHẦN 1: TẠO BẢNG ĐẶC TẢ MA TRẬN ---
    matrix_text = f"BẢNG ĐẶC TẢ MA TRẬN ĐỀ THI {selected_subject.upper()} - {selected_grade.upper()}\n"
    matrix_text += "="*90 + "\n"
    matrix_text += f"{'STT':<4} | {'Chủ đề':<25} | {'Bài học':<30} | {'Dạng':<12} | {'Mức độ':<10} | {'Điểm':<5}\n"
    matrix_text += "-"*90 + "\n"
    
    for idx, item in enumerate(st.session_state.exam_list):
        topic_short = (item['topic'][:23] + '..') if len(item['topic']) > 23 else item['topic']
        lesson_short = (item['lesson'][:28] + '..') if len(item['lesson']) > 28 else item['lesson']
        row_str = f"{idx+1:<4} | {topic_short:<25} | {lesson_short:<30} | {item['type']:<12} | {item['level'][:10]:<10} | {item['points']:<5}\n"
        matrix_text += row_str
    
    matrix_text += "-"*90 + "\n"
    matrix_text += f"TỔNG SỐ CÂU: {len(st.session_state.exam_list)} câu\n"
    matrix_text += f"TỔNG ĐIỂM:   {sum(q['points'] for q in st.session_state.exam_list)} điểm\n"
    matrix_text += "="*90 + "\n\n\n"

    # --- PHẦN 2: TẠO NỘI DUNG ĐỀ THI ---
    exam_text = f"TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN\n"
    exam_text += f"ĐỀ KIỂM TRA {selected_subject.upper()} - {selected_grade.upper()}\n"
    exam_text += f"Thời gian làm bài: 40 phút\n"
    exam_text += "-"*50 + "\n\n"
    
    for idx, q in enumerate(st.session_state.exam_list):
        exam_text += f"Câu {idx+1} ({q['points']} điểm): \n"
        exam_text += f"{q['content']}\n"
        exam_text += "\n" + "."*50 + "\n\n"

    final_output_file = matrix_text + exam_text

    st.download_button(
        label="📥 Tải xuống (Đề thi + Bảng đặc tả)",
        data=final_output_file,
        file_name=f"De_thi_va_Ma_tran_{selected_subject}_{selected_grade}.txt",
        mime="text/plain",
        type="primary"
    )

else:
    st.info("Chưa có câu hỏi nào. Hãy soạn và thêm câu hỏi ở trên.")

st.markdown("</div>", unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("""
<div class="footer">
    <p style="margin: 0; font-weight: bold; color: #2c3e50;">
        🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN
    </p>
    <p style="margin: 0; font-size: 12px; color: #666;">
        Hệ thống hỗ trợ chuyên môn & Đổi mới kiểm tra đánh giá
    </p>
</div>
""", unsafe_allow_html=True)
