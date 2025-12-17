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

# --- 3. CƠ SỞ DỮ LIỆU CHƯƠNG TRÌNH HỌC (DATA CHI TIẾT - ĐẦY ĐỦ CÁC BÀI) ---

SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

CURRICULUM_DB = {

    # =================================================================================
    # KHỐI LỚP 1 (KNTT)
    # =================================================================================
    "Lớp 1": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 1: Các số 0, 1, 2, 3, 4, 5 (Tr8) (1 tiết)", "YCCĐ": "Đếm, đọc, viết các số trong phạm vi 10."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 2: Các số 6, 7, 8, 9, 10 (Tr14) (1 tiết)", "YCCĐ": "Đếm, đọc, viết các số trong phạm vi 10."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 3: Nhiều hơn, ít hơn, bằng nhau (Tr20) (1 tiết)", "YCCĐ": "Nhận biết cách so sánh số PV 10."},
                {"Chủ đề": "2. Làm quen với hình phẳng", "Bài học": "Hình vuông, hình tròn, hình TG, hình CN (Tr48) (1 tiết)", "YCCĐ": "Nhận dạng được hình vuông, tròn, tam giác, chữ nhật."},
                {"Chủ đề": "3. Phép cộng, phép trừ trong phạm vi 10", "Bài học": "Phép cộng trong phạm vi 10 (T56) (1 tiết)", "YCCĐ": "Nhận biết ý nghĩa, thực hiện cộng không nhớ PV 10."},
                {"Chủ đề": "3. Phép cộng, phép trừ trong phạm vi 10", "Bài học": "Phép trừ trong phạm vi 10 (T68) (1 tiết)", "YCCĐ": "Thực hiện phép trừ không nhớ PV 10."},
                {"Chủ đề": "4. Làm quen với một số hình khối", "Bài học": "Khối lập phương, khối hộp CN (Tr92) (2 tiết)", "YCCĐ": "Nhận dạng được khối lập phương, khối hộp chữ nhật."},
                {"Chủ đề": "5. Ôn tập học kì 1", "Bài học": "Ôn tập các số trong phạm vi 10 (Tr102) (1 tiết)", "YCCĐ": "Ôn tập phép cộng, phép trừ không nhớ PV 10."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Các số đến 100", "Bài học": "Bài 21: Số có hai chữ số (Tr4) (1 tiết)", "YCCĐ": "Nhận biết được chục và đơn vị, số tròn chục."},
                {"Chủ đề": "7. Độ dài và đo độ dài", "Bài học": "Bài 26: Xăng - ti - mét (Tr34) (1 tiết)", "YCCĐ": "Đọc và viết được số đo độ dài trong phạm vi 100 cm."},
                {"Chủ đề": "8. Phép cộng và phép trừ (không nhớ) trong pv100", "Bài học": "Bài 29: Phép cộng số có hai chữ số với số có một chữ số (Tr44) (2 tiết)", "YCCĐ": "Thực hiện được phép cộng không nhớ PV 100."},
                {"Chủ đề": "9. Thời gian: Giờ và lịch", "Bài học": "Bài 34: Xem giờ đúng trên đồng hồ (Tr72) (1 tiết)", "YCCĐ": "Nhận biết và đọc được giờ đúng trên đồng hồ."},
                {"Chủ đề": "10. Ôn tập cuối năm", "Bài học": "Bài 39: ÔT các số và PT trong PV 100 (Tr94) (1 tiết)", "YCCĐ": "Ôn tập các số và phép tính trong phạm vi 100."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Làm quen với tiếng việt", "Bài học": "Bài 1A: a, b (2 tiết)", "YCCĐ": "Học chữ ghi âm."},
                {"Chủ đề": "Học chữ ghi âm", "Bài học": "Bài 1C: ô, ơ (2 tiết)", "YCCĐ": "Viết đúng chữ thường, chữ số."},
                {"Chủ đề": "Học chữ ghi âm", "Bài học": "Bài 2C: g, gh (2 tiết)", "YCCĐ": "Tăng số lần đọc cá nhân và luyện viết."},
                {"Chủ đề": "Học chữ ghi vần", "Bài học": "Bài 5C: ua, ưa, ia (2 tiết)", "YCCĐ": "Tích hợp học thông qua chơi."},
                {"Chủ đề": "Học chữ ghi vần", "Bài học": "Bài 7C: êu, iu, ưu (3 tiết)", "YCCĐ": "Nói rõ ràng, thành câu, nhìn vào người nghe khi nói."},
                {"Chủ đề": "Ôn tập", "Bài học": "Bài 9C: ôn tập giữa học kì I (2 tiết)", "YCCĐ": "Ôn tập, thực hành học thông qua chơi."},
                {"Chủ đề": "Ôn tập", "Bài học": "Bài 18: Ôn tập cuối học kì I (2 tiết)", "YCCĐ": "Ôn tập cuối HK I."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Trường em", "Bài học": "Bài 19A: Tới trường (Tiết 1, 3)", "YCCĐ": "Đọc đúng 40-50 tiếng/phút; Trả lời câu hỏi đơn giản."},
                {"Chủ đề": "Em là búp măng non", "Bài học": "Bài 20A: Bạn bè tuổi thơ (Tiết 1, 3)", "YCCĐ": "Viết đúng chính tả đoạn văn 30-40 chữ."},
                {"Chủ đề": "Cuộc sống quanh em", "Bài học": "Bài 21A: Những âm thanh kì diệu (Tiết 1, 3)", "YCCĐ": "Giới thiệu ngắn về bản thân, gia đình."},
                {"Chủ đề": "Gia đình em", "Bài học": "Bài 22A: Con yêu mẹ (Tiết 1, 3)", "YCCĐ": "Tích hợp học thông qua chơi và bình đẳng giới."},
                {"Chủ đề": "Cuộc sống quanh em", "Bài học": "Bài 25D: Những con vật thông minh (Tiết 1, 3)", "YCCĐ": "Đọc đúng và rõ ràng đoạn văn ngắn."},
                {"Chủ đề": "Ôn tập", "Bài học": "Bài 34D: Em được yêu thương + Ôn tập (Tiết 1, 3)", "YCCĐ": "Ôn tập cuối năm."}
            ]
        }
    },  # <--- Đã thêm dấu đóng ngoặc nhọn ở đây

    # =================================================================================
    # KHỐI LỚP 2 (KNTT)
    # =================================================================================
    "Lớp 2": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập và bổ sung", "Bài học": "Bài 1: Ôn tập các số đến 100 (3 tiết)", "YCCĐ": "Củng cố chục, đơn vị, so sánh, cộng, trừ PV 100."},
                {"Chủ đề": "2. Phép cộng, phép trừ trong phạm vi 20", "Bài học": "Bài 7: Phép cộng (qua10) trong pv 20 (5 tiết)", "YCCĐ": "Thực hiện phép cộng có nhớ PV 20."},
                {"Chủ đề": "2. Phép cộng, phép trừ trong phạm vi 20", "Bài học": "Bài 11: Phép trừ (qua 10) trong pv 20 (5 tiết)", "YCCĐ": "Thực hiện phép trừ có nhớ PV 20."},
                {"Chủ đề": "3. Làm quen với khối lượng, dung tích", "Bài học": "Bài 15: Nặng hơn, nhẹ hơn. Ki - lô- gam (3 tiết)", "YCCĐ": "Nhận biết Nặng hơn, nhẹ hơn, Ki-lô-Gam."},
                {"Chủ đề": "4. Phép cộng, phép trừ có nhớ trong phạm vi 100", "Bài học": "Bài 20: Phép cộng (có nhớ) số có hai chữ số với số có hai chữ số (5 tiết)", "YCCĐ": "Thực hiện phép cộng có nhớ PV 100."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "8. Phép nhân, phép chia", "Bài học": "Bài 39: Bảng nhân 2 (2 tiết)", "YCCĐ": "Vận dụng được bảng nhân 2 trong tính toán."},
                {"Chủ đề": "8. Phép nhân, phép chia", "Bài học": "Bài 43: Bảng chia 2 (2 tiết)", "YCCĐ": "Vận dụng được bảng chia 2 trong tính toán."},
                {"Chủ đề": "10. Các số trong phạm vi 1000", "Bài học": "Bài 48: Đơn vị, chục, trăm, nghìn (2 tiết)", "YCCĐ": "Nhận biết đơn vị, chục, trăm, nghìn."},
                {"Chủ đề": "11. Độ dài và đơn vị đo độ dài. Tiền VN", "Bài học": "Bài 55: Đề - xi - mét. Mét. Ki-lô-mét (3 tiết)", "YCCĐ": "Đọc và mô tả được các số liệu."},
                {"Chủ đề": "12. Phép cộng, phép trừ trong phạm vi 1000", "Bài học": "Bài 60: Phép cộng (có nhớ) trong phạm vi 1000 (4 tiết)", "YCCĐ": "Thực hiện phép cộng có nhớ PV 1000."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "EM LỚN LÊN TỪNG NGÀY", "Bài học": "Bài 1: Tôi là học sinh lớp 2 (4 tiết)", "YCCĐ": "Biết nêu và trả lời câu hỏi về nội dung văn bản."},
                {"Chủ đề": "ĐI HỌC VUI SAO", "Bài học": "Bài 7: Cây xấu hổ (4 tiết)", "YCCĐ": "Tích hợp KNS: GDHS mạnh dạn tự tin."},
                {"Chủ đề": "NIỀM VUI TUỔI THƠ", "Bài học": "Bài 24: Nặn đồ chơi (6 tiết)", "YCCĐ": "Mở rộng vốn từ đồ chơi; Dấu phẩy. Viết đoạn văn tả đồ chơi."},
                {"Chủ đề": "MÁI ẤM GIA ĐÌNH", "Bài học": "Bài 28: Trò chơi của bố (6 tiết)", "YCCĐ": "Viết đoạn văn thể hiện tình cảm với người thân."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "VẺ ĐẸP QUANH EM", "Bài học": "Bài 1: Chuyện bốn mùa (4 tiết)", "YCCĐ": "GDHS có ý thức giữ gìn bảo vệ thiên nhiên."},
                {"Chủ đề": "HÀNH TRÌNH XANH CỦA EM", "Bài học": "Bài 10: Khủng long (6 tiết)", "YCCĐ": "Viết đoạn văn giới thiệu tranh ảnh về một con vật."},
                {"Chủ đề": "GIAO TIẾP VÀ KẾT NỐI", "Bài học": "Bài 18: Thư viện biết đi (6 tiết)", "YCCĐ": "Viết đoạn văn giới thiệu một đồ dùng học tập."},
                {"Chủ đề": "VIỆT NAM QUÊ HƯƠNG EM", "Bài học": "Bài 25: Đất nước chúng mình (4 tiết)", "YCCĐ": "Kể chuyện Thánh Gióng."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 3 (KNTT)
    # =================================================================================
    "Lớp 3": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập và bổ sung", "Bài học": "Bài 3: Tìm số hạng trong một tổng; Tìm số bị trừ, số trừ (2 tiết)", "YCCĐ": "Tìm được số hạng chưa biết, số bị trừ, số trừ."},
                {"Chủ đề": "2. Bảng nhân, bảng chia", "Bài học": "Bài 9: Bảng nhân 6, bảng chia 6 (1 tiết)", "YCCĐ": "Hình thành bảng nhân, chia và vận dụng tính nhẩm."},
                {"Chủ đề": "3. Làm quen với hình phẳng, hình khối", "Bài học": "Bài 17: Hình tròn. Tâm, bán kính, đường kính (1 tiết)", "YCCĐ": "Nhận biết hình tròn, tâm, bán kính, đường kính."},
                {"Chủ đề": "4. Phép nhân, phép chia trong phạm vi 100", "Bài học": "Bài 28: Bài toán giải bằng hai phép tính (1 tiết)", "YCCĐ": "Vận dụng giải các bài toán liên quan."},
                {"Chủ đề": "5. Một số đơn vị đo độ dài, khối lượng, dung tích, nhiệt độ", "Bài học": "Bài 33: Nhiệt độ. Đv đo nhiệt độ (1 tiết)", "YCCĐ": "Sử dụng được đơn vị đo mm, kg, ml để đo."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "8. Các số đến 10 000", "Bài học": "Bài 45: Số có 4 chữ số (1 tiết)", "YCCĐ": "Đọc, viết được các số trong phạm vi 10 000."},
                {"Chủ đề": "9. Chu vi, diện tích một số hình phẳng", "Bài học": "Bài 50: Chu vi hình tam giác, hình tứ giác (1 tiết)", "YCCĐ": "Tính được chu vi các hình."},
                {"Chủ đề": "11. Các số đến 100 000", "Bài học": "Bài 59: Số có 5 chữ số (1 tiết)", "YCCĐ": "Biết cách đọc, viết và so sánh các số có năm chữ số."},
                {"Chủ đề": "13. Xem đồng hồ. Tháng - năm. Tiền Việt Nam", "Bài học": "Bài 67: Thực hành xem đồng hồ, xem lịch (2 tiết)", "YCCĐ": "Đọc được giờ chính xác đến từng phút."},
                {"Chủ đề": "15. Làm quen với yếu tố thống kê, xác suất", "Bài học": "Bài 74: Khả năng xảy ra của một sự kiện (1 tiết)", "YCCĐ": "Nhận biết cách thu thập, phân loại, ghi chép số liệu."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Những trải nghiệm thú vị", "Bài học": "B1: Ngày gặp lại (Tr10) (3 tiết)", "YCCĐ": "Nghe - viết: Em yêu mùa hè. Viết tin nhắn."},
                {"Chủ đề": "Công trường rộng mở", "Bài học": "Bài 11: Lời giải toán đặc biệt (3 tiết)", "YCCĐ": "Nghe - viết: Lời giải toán đặc biệt. Kể chuyện Đội viên tương lai."},
                {"Chủ đề": "Mái nhà yêu thương", "Bài học": "B17: Ngưỡng cửa (Tr82) (3 tiết)", "YCCĐ": "Nghe - viết: Đồ đạc trong nhà. Kể chuyện Sự tích nhà sàn."},
                {"Chủ đề": "Mái ấm gia đình", "Bài học": "Bài 31: Người làm đồ chơi (Trang 137) (3 tiết)", "YCCĐ": "Nghe - viết: Người làm đồ chơi. Viết thư."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Những sắc màu TN", "Bài học": "Bài 5: ngày hội rừng xanh (Trang 23) (3 tiết)", "YCCĐ": "Nghe - viết: Chim chích bông. Nói và nghe: Rừng."},
                {"Chủ đề": "Bài học từ cuộc sống", "Bài học": "Bài 13: Mèo đi câu cá (Trang 55) (3 tiết)", "YCCĐ": "Nghe - viết: Bài học của gấu. Nói và nghe: Cùng vui làm việc."},
                {"Chủ đề": "Đất nước ngàn năm", "Bài học": "Bài 23: Hai bà trưng (Trang 102) (3 tiết)", "YCCĐ": "Nghe - viết: Hai Bà Trưng. Kể chuyện Hai Bà Trưng."},
                {"Chủ đề": "Trái đất của chúng mình", "Bài học": "B28: Những điều nhỏ tớ làm cho trái đất (Tr122) (4 tiết)", "YCCĐ": "Viết đoạn văn kể lại một việc làm góp phần bảo vệ môi trường."}
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 1. Thông tin và quyết định (2 tiết)", "YCCĐ": "Hiểu thông tin và xử lí thông tin."},
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 4. Làm việc với máy tính (3 tiết)", "YCCĐ": "Thực hành làm việc với máy tính."},
                {"Chủ đề": "Mạng máy tính và Internet", "Bài học": "Bài 6. Khám phá thông tin trên Internet (2 tiết)", "YCCĐ": "Xem tin và giải trí trên trang web."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Tổ chức lưu trữ, tìm kiếm và trao đổi thông tin", "Bài học": "Bài 8. Sơ đồ hình cây. Tổ chức thông tin trong máy tính (2 tiết)", "YCCĐ": "Làm quen với thư mục lưu trữ thông tin."},
                {"Chủ đề": "Ứng dụng tin học", "Bài học": "Bài 11. Bài trình chiếu của em (2 tiết)", "YCCĐ": "Làm quen với bài trình chiếu đơn giản."},
                {"Chủ đề": "Giải quyết vấn đề với sự trợ giúp của máy tính", "Bài học": "Bài 15. Công việc được thực hiện theo điều kiện (2 tiết)", "YCCĐ": "Thực hiện công việc theo các bước."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Công nghệ và đời sống", "Bài học": "Bài 1: Tự nhiên và công nghệ (2 tiết)", "YCCĐ": "Kể tên và nêu công dụng sản phẩm công nghệ."},
                {"Chủ đề": "Công nghệ và đời sống", "Bài học": "Bài 3: Sử dụng quạt điện (2 tiết)", "YCCĐ": "Sử dụng quạt điện đúng cách và an toàn."},
                {"Chủ đề": "Công nghệ và đời sống", "Bài học": "Bài 5: Sử dụng máy thu hình (3 tiết)", "YCCĐ": "Tác dụng của máy thu hình."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thủ công kĩ thuật", "Bài học": "Bài 7: Dụng cụ và vật liệu làm thủ công (3 tiết)", "YCCĐ": "Sử dụng dụng cụ làm thủ công."},
                {"Chủ đề": "Thủ công kĩ thuật", "Bài học": "Bài 8: Làm đồ dùng học tập (3 tiết)", "YCCĐ": "Làm thước kẻ."},
                {"Chủ đề": "Thủ công kĩ thuật", "Bài học": "Bài 9: Làm biển báo giao thông (3 tiết)", "YCCĐ": "Tìm hiểu và làm mô hình biển báo giao thông."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 4 (KNTT)
    # =================================================================================
    "Lớp 4": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập và bổ sung", "Bài học": "Bài 4: Biểu thức chứa chữ (3 tiết)", "YCCĐ": "Nhận biết biểu thức chứa chữ."},
                {"Chủ đề": "2. Góc và đơn vị đo góc", "Bài học": "Bài 8: Góc nhọn, góc tù, góc bẹt (3 tiết)", "YCCĐ": "Dạy học STEM: Góc biến hình."},
                {"Chủ đề": "3. Số có nhiều chữ số", "Bài học": "Bài 14: So sánh các số có nhiều chữ số (2 tiết)", "YCCĐ": "So sánh các số có nhiều chữ số."},
                {"Chủ đề": "4. Một số đơn vị đo đại lượng", "Bài học": "Bài 19: Giây, thế kỉ (2 tiết)", "YCCĐ": "Nhận biết Giây, thế kỉ."},
                {"Chủ đề": "5. Phép cộng và phép trừ", "Bài học": "Bài 25: Tìm hai số khi biết tổng và hiệu của hai số đó (2 tiết)", "YCCĐ": "Tìm hai số khi biết tổng và hiệu."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "8. Phép nhân, phép chia", "Bài học": "Bài 43: Nhân với số có hai chữ số (3 tiết)", "YCCĐ": "Thực hiện Nhân với số có hai chữ số."},
                {"Chủ đề": "9. Làm quen với yếu tố thống kê, xác suất", "Bài học": "Bài 50: Biểu đồ cột (2 tiết)", "YCCĐ": "Đọc và mô tả được các số liệu ở dạng biểu đồ cột."},
                {"Chủ đề": "10. Phân số, khái niệm phân số", "Bài học": "Bài 56: Rút gọn phân số (2 tiết)", "YCCĐ": "Thực hiện Rút gọn phân số."},
                {"Chủ đề": "11. Phép cộng, phép trừ phân số", "Bài học": "Bài 60: Phép cộng phân số (4 tiết)", "YCCĐ": "Cộng hai phân số có cùng/khác mẫu số."},
                {"Chủ đề": "13. Ôn tập cuối năm", "Bài học": "Bài 71: Ôn tập hình học và đo lường (2 tiết)", "YCCĐ": "Ôn tập diện tích, chu vi các hình; đo lường."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Bài 1: Đọc: Điều kì diệu (1 tiết)", "YCCĐ": "Đọc đúng 80-90 tiếng/phút; Nhận biết Danh từ."},
                {"Chủ đề": "Trải nghiệm và khám phá", "Bài học": "Bài 12: Đọc: Nhà phát minh 6 tuổi (2 tiết)", "YCCĐ": "Tìm hiểu cách viết bài văn kể lại 1 câu chuyện."},
                {"Chủ đề": "Niềm vui sáng tạo", "Bài học": "Bài 18: Đọc: Đồng cỏ nở hoa (2 tiết)", "YCCĐ": "Nhận biết Biện pháp nhân hoá."},
                {"Chủ đề": "Chắp cánh ước mơ", "Bài học": "Bài 25: Đọc: Bay cùng ước mơ (1 tiết)", "YCCĐ": "Kể về ước mơ của mình."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Sống để yêu thương", "Bài học": "Bài 4: Đọc: Quả ngọt cuối mùa (2 tiết)", "YCCĐ": "Viết đoạn văn nêu tình cảm, cảm xúc về một nhân vật."},
                {"Chủ đề": "Uống nước nhớ nguồn", "Bài học": "Bài 9: Đọc: Sự tích con Rồng, cháu Tiên (1 tiết)", "YCCĐ": "Luyện tập về hai thành phần chính của câu."},
                {"Chủ đề": "Quê hương trong tôi", "Bài học": "Bài 17: Đọc: Cây đa quê hương (1 tiết)", "YCCĐ": "Nhận biết Trạng ngữ chỉ phương tiện. Viết văn miêu tả cây cối."},
                {"Chủ đề": "Vì một thế giới bình yên", "Bài học": "Bài 25: Đọc: Khu bảo tồn động vật hoang dã Ngô rông- gô – rô (1 tiết)", "YCCĐ": "Tích hợp ND BVMT: Cần phải bảo vệ các loài động vật hoang dã."}
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "1. Chất", "Bài học": "Bài 1: Tính chất của nước và nước với cuộc sống (2 tiết)", "YCCĐ": "Nêu tính chất của nước và vai trò của nó."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 6: Gió, bão và phòng chống bão (2 tiết)", "YCCĐ": "Hiểu về Gió, bão và cách phòng chống."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 8: Ánh sáng và sự truyền ánh sáng (2 tiết)", "YCCĐ": "Hiểu về Ánh sáng và sự truyền ánh sáng."},
                {"Chủ đề": "3. Thực vật và động vật", "Bài học": "Bài 16: Động vật cần gì để sống? (3 tiết)", "YCCĐ": "Nhận diện những hủ tục trong chăn nuôi tại địa phương."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Nấm", "Bài học": "Bài 19: Đặc điểm chung của nấm (2 tiết)", "YCCĐ": "Nhận biết Đặc điểm chung của nấm."},
                {"Chủ đề": "5. Con người và sức khoẻ", "Bài học": "Bài 24: Chế độ ăn uống cân bằng (3 tiết)", "YCCĐ": "Xây dựng Chế độ ăn uống cân bằng."},
                {"Chủ đề": "5. Con người và sức khoẻ", "Bài học": "Bài 27: Phòng tránh đuối nước (2 tiết)", "YCCĐ": "Phòng tránh đuối nước."},
                {"Chủ đề": "6. Sinh vật và môi trường", "Bài học": "Bài 30: Vai trò của thực vật trong chuỗi thức ăn (3 tiết)", "YCCĐ": "Vai trò của thực vật trong chuỗi thức ăn."}
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "1. Địa phương em", "Bài học": "Bài 2. Thiên nhiên và con người ở địa phương em (2 tiết)", "YCCĐ": "Biết về Thiên nhiên và con người địa phương."},
                {"Chủ đề": "2. Trung du và vùng núi Bắc Bộ", "Bài học": "Bài 7: Đền Hùng và lễ giỗ Tổ Hùng Vương (2 tiết)", "YCCĐ": "Tuyên truyền một số lễ hội dân tộc ở nơi em ở."},
                {"Chủ đề": "3. Đồng bằng Bắc Bộ", "Bài học": "Bài 12: Thăng Long – Hà Nội (3 tiết)", "YCCĐ": "Nắm được sự kiện, lịch sử Thăng Long – Hà Nội."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Duyên hải miền Trung", "Bài học": "Bài 18: Cố đô Huế (2 tiết)", "YCCĐ": "Tìm hiểu và bảo vệ quần thể di tích cố đô Huế."},
                {"Chủ đề": "5. Tây Nguyên", "Bài học": "Bài 23: Lễ hội cồng chiêng Tây Nguyên (2 tiết)", "YCCĐ": "Kể tên các lễ hội tại địa phương em."},
                {"Chủ đề": "6. Nam Bộ", "Bài học": "Bài 27: Thành phố Hồ Chí Minh (2 tiết)", "YCCĐ": "Lịch sử Thành phố Hồ Chí Minh."}
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "CHỦ ĐỀ A: MÁY TÍNH VÀ EM", "Bài học": "Bài 1: Phần cứng và phần mềm máy tính (2 tiết)", "YCCĐ": "Luyện tập về phần cứng và phần mềm."},
                {"Chủ đề": "CHỦ ĐỀ B: MẠNG MÁY TÍNH VÀ INTERNET", "Bài học": "Bài 3: Thông tin trên trang web (2 tiết)", "YCCĐ": "Lí thuyết về thông tin trên trang web."},
                {"Chủ đề": "CHỦ ĐỀ D: ĐẠO ĐỨC, PHÁP LUẬT VÀ VĂN HOÁ TRONG MÔI TRƯỜNG SỐ", "Bài học": "Bài 7: Bản quyền phần mềm (1 tiết)", "YCCĐ": "Lí thuyết về Bản quyền phần mềm."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "CHỦ ĐỀ E: ỨNG DỤNG TIN HỌC", "Bài học": "Bài 8: Tạo bài trình chiếu (2 tiết)", "YCCĐ": "Lý thuyết và thực hành Tạo bài trình chiếu."},
                {"Chủ đề": "CHỦ ĐỀ CON E 2 (LỰA CHỌN)", "Bài học": "Bài 16: Luyện tập gõ bàn phím (1 tiết)", "YCCĐ": "Thực hành Luyện tập gõ bàn phím."},
                {"Chủ đề": "CHỦ ĐỀ F: GIẢI QUYẾT VẤN ĐỀ VỚI SỰ TRỢ GIÚP CỦA MÁY TÍNH", "Bài học": "Bài 17: Làm quen với lập trình (2 tiết)", "YCCĐ": "Lý thuyết và thực hành Làm quen với lập trình."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 1: Lợi ích của hoa, cây cảnh đối với đời sống (3 tiết)", "YCCĐ": "Nêu được lợi ích của hoa và cây cảnh."},
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 4: Gieo hạt hoa, cây cảnh trong chậu (3 tiết)", "YCCĐ": "Tóm tắt được nội dung các bước gieo hạt."},
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 6: Chăm sóc hoa, cây cảnh trong chậu (3 tiết)", "YCCĐ": "Thực hiện được các công việc chủ yếu để chăm sóc."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "2. Lắp ghép kĩ thuật", "Bài học": "Bài 7: Giới thiệu bộ lắp ghép mô hình kĩ thuật (2 tiết)", "YCCĐ": "Kể tên, nhận biết các chi tiết của bộ lắp ghép."},
                {"Chủ đề": "2. Lắp ghép kĩ thuật", "Bài học": "Bài 9: Lắp ghép mô hình robot (3 tiết)", "YCCĐ": "Lựa chọn và sử dụng được chi tiết để lắp ghép."},
                {"Chủ đề": "2. Lắp ghép kĩ thuật", "Bài học": "Bài 12: Làm chuồn chuồn thăng bằng (2 tiết)", "YCCĐ": "Làm được đồ chơi dân gian."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 5 (KNTT)
    # =================================================================================
    "Lớp 5": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập và bổ sung", "Bài học": "Bài 4: Phân số thập phân (1 tiết)", "YCCĐ": "Ôn tập về phân số thập phân."},
                {"Chủ đề": "2. Số thập phân", "Bài học": "Bài 10. Khái niệm số thập phân (3 tiết)", "YCCĐ": "Biết khái niệm, cách so sánh các số thập phân."},
                {"Chủ đề": "4. CÁC PHÉP TÍNH VỚI SỐ THẬP PHÂN", "Bài học": "Bài 20. Phép trừ số thập phân (2 tiết)", "YCCĐ": "Thực hiện được phép trừ số thập phân."},
                {"Chủ đề": "5. MỘT SỐ HÌNH PHẲNG. CHU VI VÀ DIỆN TÍCH", "Bài học": "Bài 25. Hình tam giác. Diện tích hình tam giác (4 tiết)", "YCCĐ": "Biết đặc điểm của hình tam giác, cách tính diện tích."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "7. TỈ SỐ VÀ CÁC BÀI TOÁN LIÊN QUAN", "Bài học": "Bài 41. Tìm giá trị phần trăm của một số (2 tiết)", "YCCĐ": "Tìm được giá trị phần trăm của một số."},
                {"Chủ đề": "9. DIỆN TÍCH VÀ THỂ TÍCH CỦA MỘT SỐ HÌNH KHỐI", "Bài học": "Bài 53. Thể tích của hình lập phương (2 tiết)", "YCCĐ": "Tính được thể tích của hình lập phương."},
                {"Chủ đề": "10. SỐ ĐO THỜI GIAN. VẬN TỐC. CÁC BÀI TOÁN LIÊN QUAN ĐẾN CHUYỂN ĐỘNG ĐỀU", "Bài học": "Bài 60. Quãng đường, thời gian của một chuyển động đều (3 tiết)", "YCCĐ": "Tính toán Quãng đường, thời gian, vận tốc."},
                {"Chủ đề": "11. MỘT SỐ YẾU TỐ THỐNG KÊ VÀ XÁC SUẤT", "Bài học": "Bài 64. Biểu đồ hình quạt tròn (2 tiết)", "YCCĐ": "Thu thập, phân loại, sắp xếp các số liệu."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Thế giới tuổi thơ", "Bài học": "Bài 1. Thanh âm của gió – Trang 8 (1 tiết)", "YCCĐ": "Quyền vui chơi của trẻ em. Yêu thiên nhiên, bảo vệ thiên nhiên."},
                {"Chủ đề": "THIÊN NHIÊN KÌ THÚ", "Bài học": "Bài 9. Trước cổng trời – Trang 46 (1 tiết)", "YCCĐ": "Tích hợp về Công viên địa chất toàn cầu Cao nguyên đá Đồng Văn."},
                {"Chủ đề": "Trên con đường học tập", "Bài học": "Bài 17. Thư gửi các học sinh – Trang 89 (1 tiết)", "YCCĐ": "Quyền học tập. Đạo đức Hồ Chí Minh."},
                {"Chủ đề": "Nghệ thuật muôn màu", "Bài học": "Bài 27. Trí tưởng tượng phong phú – Trang 127 (2 tiết)", "YCCĐ": "Biết Biện pháp điệp từ, điệp ngữ."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp cuộc sống", "Bài học": "Bài 4. Hộp quà màu thiên thanh (2 tiết)", "YCCĐ": "Viết bài văn tả người."},
                {"Chủ đề": "Hương sắc trăm miền", "Bài học": "Bài 13. Đàn t'rưng – tiếng ca đại ngàn (1 tiết)", "YCCĐ": "Liên kết câu bằng từ ngữ thay thế."},
                {"Chủ đề": "Tiếp bước cha ông", "Bài học": "Bài 20. Cụ Đồ Chiểu (2 tiết)", "YCCĐ": "Viết đoạn văn nêu ý kiến tán thành."},
                {"Chủ đề": "Thế giới của chúng ta", "Bài học": "Bài 25. Bài ca trái đất (1 tiết)", "YCCĐ": "Tích hợp vệ sinh môi trường - GD Quốc phòng An ninh."}
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "1. CHẤT", "Bài học": "Bài 1: Thành phần và vai trò của đất đối với cây trồng (2 tiết)", "YCCĐ": "Biết các thành phần của đất và vai trò của nó với cây trồng."},
                {"Chủ đề": "1. CHẤT", "Bài học": "Bài 4: Đặc điểm của chất ở trạng thái rắn, lỏng, khí (2 tiết)", "YCCĐ": "Đặc điểm của chất ở trạng thái rắn, lỏng, khí. Sự biến đổi trạng thái của chất."},
                {"Chủ đề": "2. NĂNG LƯỢNG", "Bài học": "Bài 7: Vai trò của năng lượng (2 tiết)", "YCCĐ": "Một số nguồn năng lượng va vai trò của năng lượng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "3. THỰC VẬT VÀ ĐỘNG VẬT", "Bài học": "Bài 16: Vòng đời và sự phát triển của động vật (2 tiết)", "YCCĐ": "Sự sinh sản vòng đời và sự phát triển của động vật."},
                {"Chủ đề": "5. CON NGƯỜI VÀ SỨC KHỎE", "Bài học": "Bài 25: Chăm sóc sức khoẻ tuổi dậy thì (3 tiết)", "YCCĐ": "Chăm sóc sức khoẻ tuổi dậy thì."},
                {"Chủ đề": "5. CON NGƯỜI VÀ SỨC KHỎE", "Bài học": "Bài 26: Phòng tránh bị xâm hại (4 tiết)", "YCCĐ": "Phòng tránh bị xâm hại. Quyền được an toàn."}
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "1. ĐẤT NƯỚC VÀ CON NGƯỜI VIỆT NAM", "Bài học": "Bài 1: Vị trí địa lí, lãnh thổ, đơn vị hành chính, Quốc kì, Quốc huy, Quốc ca (2 tiết)", "YCCĐ": "Ý nghĩa của Quốc kì, Quốc huy, Quốc ca."},
                {"Chủ đề": "2. NHỮNG QUỐC GIA ĐẦU TIÊN TRÊN LÃNH THỔ VIỆT NAM", "Bài học": "Bài 5: Nhà nước Văn Lang, Nhà nước Âu Lạc (3 tiết)", "YCCĐ": "Sự ra đời của nước Văn Lang, Âu Lạc."},
                {"Chủ đề": "3. XÂY DỰNG VÀ BẢO VỆ ĐẤT NƯỚC VIỆT NAM", "Bài học": "Bài 10: Triều Trần xây dựng đất nước và kháng chiến chống quân Mông – Nguyên xâm lược (4 tiết)", "YCCĐ": "Nét chính của các cuộc kháng chiến,."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "3. XÂY DỰNG VÀ BẢO VỆ ĐẤT NƯỚC VIỆT NAM", "Bài học": "Bài 15: Chiến dịch Điện Biên Phủ năm 1954 (2 tiết)", "YCCĐ": "Chiến dịch Điện Biên Phủ."},
                {"Chủ đề": "4. CÁC NƯỚC LÁNG GIỀNG", "Bài học": "Bài 18: Nước Cộng hoà Nhân dân Trung Hoa (2 tiết)", "YCCĐ": "Vị trí địa lí, một số đặc điểm cơ bản của Trung Quốc."},
                {"Chủ đề": "5. TÌM HIỂU THẾ GIỚI", "Bài học": "Bài 22: Các châu lục và đại dương trên thế giới (5 tiết)", "YCCĐ": "Vị trí địa lí của các châu lục, Đại dương,."}
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "CHỦ ĐỀ 1: MÁY TÍNH VÀ EM", "Bài học": "Bài 1. Em có thể làm gì với máy tính? (2 tiết)", "YCCĐ": "Ứng dụng của máy tính trong đời sống."},
                {"Chủ đề": "CHỦ ĐỀ 3: TỔ CHỨC LƯU TRỮ, TÌM KIẾM VÀ TRAO ĐỔI THÔNG TIN", "Bài học": "Bài 4. Cây thư mục (2 tiết)", "YCCĐ": "Tổ chức thông tin trong máy tính."},
                {"Chủ đề": "CHỦ ĐỀ 5: ỨNG DỤNG TIN HỌC", "Bài học": "Bài 6. Định dạng kí tự và bố trí hình ảnh trong văn bản (2 tiết)", "YCCĐ": "Định dạng các kí tự, trình bày văn bản."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "CHỦ ĐỀ 6: GIẢI QUYẾT VẤN ĐỀ VỚI SỰ TRỢ GIÚP CỦA MÁY TÍNH", "Bài học": "Bài 11. Cấu trúc lặp (2 tiết)", "YCCĐ": "Lập trình trực quan, các cấu trúc trong vòng lặp."},
                {"Chủ đề": "CHỦ ĐỀ 6: GIẢI QUYẾT VẤN ĐỀ VỚI SỰ TRỢ GIÚP CỦA MÁY TÍNH", "Bài học": "Bài 14. Sử dụng biến trong chương trình (2 tiết)", "YCCĐ": "Sử dụng biến trong chương trình."},
                {"Chủ đề": "CHỦ ĐỀ 6: GIẢI QUYẾT VẤN ĐỀ VỚI SỰ TRỢ GIÚP CỦA MÁY TÍNH", "Bài học": "Bài 16. Từ kịch bản đến chương trình (2 tiết)", "YCCĐ": "Từ kịch bản đến chương trình."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "PHẦN MỘT. CÔNG NGHỆ VÀ ĐỜI SỐNG", "Bài học": "Bài 1. Vai trò của công nghệ (2 tiết)", "YCCĐ": "Vai trò của công nghệ."},
                {"Chủ đề": "PHẦN MỘT. CÔNG NGHỆ VÀ ĐỜI SỐNG", "Bài học": "Bài 4. Thiết kế sản phẩm (4 tiết)", "YCCĐ": "Tìm hiểu cách thiết kế các loại sản phẩm."},
                {"Chủ đề": "PHẦN MỘT. CÔNG NGHỆ VÀ ĐỜI SỐNG", "Bài học": "Bài 6. Sử dụng tủ lạnh (3 tiết)", "YCCĐ": "Sử dụng tủ lạnh."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "PHẦN II: THỦ CÔNG KĨ THUẬT", "Bài học": "Bài 7. Lắp ráp mô hình xe điện chạy bằng pin (4 tiết)", "YCCĐ": "Quy trình lắp ráp mô hình kĩ thuật,."},
                {"Chủ đề": "PHẦN II: THỦ CÔNG KĨ THUẬT", "Bài học": "Bài 9. Mô hình điện mặt trời (4 tiết)", "YCCĐ": "Lắp ráp mô hình điện mặt trời."}
            ]
        }
    }
}

# --- 4. CÁC HÀM XỬ LÝ (GIỮ NGUYÊN) ---

def find_working_model(api_key):
    # ... (code for finding model omitted) ...
    preferred_models = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro',
        'gemini-1.5-pro-latest',
        'gemini-1.0-pro',
        'gemini-pro'
    ]
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            available_models = [
                m['name'].replace('models/', '')
                for m in data.get('models', [])
                if 'generateContent' in m.get('supportedGenerationMethods', [])
            ]
            for p in preferred_models:
                if p in available_models:
                    return p
            if available_models:
                return available_models
            return None
        return None
    except:
        return None

def generate_single_question(api_key, grade, subject, lesson_info, q_type, level, points):
    clean_key = api_key.strip()
    if not clean_key: return "⚠️ Chưa nhập API Key."

    model_name = find_working_model(clean_key)
    if not model_name:
        return "❌ Không tìm thấy model phù hợp. Vui lòng kiểm tra lại API Key hoặc thử lại sau."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
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
    max_retries = 3
    base_delay = 2
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['candidates']['content']['parts']['text']
            elif response.status_code == 404:
                return f"Lỗi Model (404): Model '{model_name}' không tìm thấy. Google có thể đã đổi tên model."
            elif response.status_code == 429:
                time.sleep(base_delay * (2 ** attempt))
                continue
            else:
                return f"Lỗi API ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Lỗi mạng: {e}"
    return "⚠️ Hệ thống đang quá tải. Vui lòng đợi 1-2 phút rồi thử lại."

# --- 5. QUẢN LÝ STATE (GIỮ NGUYÊN) ---

if "exam_list" not in st.session_state:
    st.session_state.exam_list = []
if "current_preview" not in st.session_state:
    st.session_state.current_preview = ""
if "temp_question_data" not in st.session_state:
    st.session_state.temp_question_data = None

# --- 6. GIAO DIỆN CHÍNH (THAY ĐỔI PHẦN TẢI XUỐNG) ---

st.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
    <h1 style='color: #007BFF;'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>
    <i>Hệ thống hỗ trợ chuyên môn & Đổi mới kiểm tra đánh giá</i>
</div>
""", unsafe_allow_html=True)

# SIDEBAR (GIỮ NGUYÊN)
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

# BƯỚC 1: CHỌN LỚP - MÔN (GIỮ NGUYÊN)
col1, col2 = st.columns(2)
with col1:
    selected_grade = st.selectbox("Chọn Khối Lớp:", list(SUBJECTS_DB.keys()))
with col2:
    subjects_list = [f"{s} {s}" for s in SUBJECTS_DB[selected_grade]]
    selected_subject_full = st.selectbox("Chọn Môn Học:", subjects_list)
    selected_subject = selected_subject_full.split(" ", 1)

raw_data = CURRICULUM_DB.get(selected_grade, {}).get(selected_subject, {})
if not raw_data:
    st.warning(f"⚠️ Dữ liệu cho môn {selected_subject} - {selected_grade} đang được cập nhật. Vui lòng chọn môn khác.")
    st.stop()

# BƯỚC 2: BỘ SOẠN CÂU HỎI (GIỮ NGUYÊN LOGIC)
st.markdown("---")
st.subheader("🛠️ Soạn thảo câu hỏi theo Ma trận")

col_a, col_b = st.columns(2)
with col_a:
    all_terms = list(raw_data.keys())
    selected_term = st.selectbox("Chọn Học kỳ:", all_terms)
    lessons_in_term = raw_data[selected_term]
    unique_topics = sorted(list(set([l['Chủ đề'] for l in lessons_in_term])))
    if not unique_topics:
        st.warning("Chưa có chủ đề cho học kỳ này.")
        st.stop()
    selected_topic = st.selectbox("Chọn Chủ đề:", unique_topics)

with col_b:
    filtered_lessons = [l for l in lessons_in_term if l['Chủ đề'] == selected_topic]
    if not filtered_lessons:
        st.warning("Chưa có bài học cho chủ đề này.")
        st.stop()
    lesson_options = {f"{l['Bài học']}": l for l in filtered_lessons}
    selected_lesson_name = st.selectbox("Chọn Bài học:", list(lesson_options.keys()))

if selected_lesson_name not in lesson_options:
    st.stop()
current_lesson_data = lesson_options[selected_lesson_name]
st.info(f"🎯 **YCCĐ (Tham khảo):** {current_lesson_data['YCCĐ']}")

col_x, col_y, col_z = st.columns(3)
with col_x:
    q_type = st.selectbox("Dạng câu hỏi:", ["Trắc nghiệm (4 lựa chọn)", "Đúng/Sai", "Điền khuyết", "Nối đôi", "Tự luận", "Giải toán có lời văn"])
with col_y:
    level = st.selectbox("Mức độ nhận thức:", ["Mức 1: Biết (Nhận biết)", "Mức 2: Hiểu (Thông hiểu)", "Mức 3: Vận dụng (Giải quyết vấn đề)"])
with col_z:
    points = st.number_input("Điểm số:", min_value=0.25, max_value=10.0, step=0.25, value=1.0)

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

if st.session_state.current_preview:
    st.markdown("### 👁️ Xem trước câu hỏi:")
    with st.container():
        st.markdown(f"""
<div style='border: 1px solid #ccc; padding: 15px; border-radius: 5px; background-color: #f9f9f9;'>
{st.session_state.current_preview}
</div>
""", unsafe_allow_html=True)
    c1, c2 = st.columns()
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

    # 3.1. Hiển thị bảng tóm tắt (GIỮ NGUYÊN)
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

    # 3.2. Xuất file (ĐÃ THAY ĐỔI ĐỊNH DẠNG)
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
    matrix_text += f"TỔNG ĐIỂM: {sum(q['points'] for q in st.session_state.exam_list)} điểm\n"
    matrix_text += "="*90 + "\n\n\n"

    # --- PHẦN 2: TẠO NỘI DUNG ĐỀ THI ---
    # Sử dụng HTML/CSS cơ bản để giả lập định dạng Nghị định 30 (Font Times New Roman, Cỡ 14)
    exam_content_html = f"""
<div style='font-family: "Times New Roman", Times, serif; font-size: 14pt; line-height: 1.5;'>
    <p style='text-align: center;'>TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</p>
    <h2 style='text-align: center; font-weight: bold;'>ĐỀ KIỂM TRA {selected_subject.upper()} - {selected_grade.upper()}</h2>
    <p style='text-align: center; font-style: italic;'>Thời gian làm bài: 40 phút</p>
    <p style='text-align: center;'>&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;&mdash;</p>
"""

    for idx, q in enumerate(st.session_state.exam_list):
        exam_content_html += f"""
        <p style='margin-top: 20px;'><b>Câu {idx+1}</b> ({q['points']} điểm): </p>
        <p style='margin-left: 20px;'>{q['content'].replace('**Câu hỏi:**', '').replace('**Đáp án:**', '<br><b>Đáp án:</b>')}</p>
        <p style='margin-top: 10px; margin-bottom: 10px; border-bottom: 1px dashed #ccc;'></p>
"""
    exam_content_html += "</div>"

    # Kết hợp Ma trận (Text) và Nội dung Đề thi (HTML)
    final_output_file = matrix_text + exam_content_html

    # Thay đổi file_name và mime type để người dùng tải về dưới dạng .doc (Word)
    st.download_button(
        label="📥 Tải xuống (Đề thi + Bảng đặc tả) - Định dạng Word",
        data=final_output_file,
        file_name=f"De_thi_va_Ma_tran_{selected_subject}_{selected_grade}.doc",
        mime="application/msword",
        type="primary"
    )

    st.markdown("""
    <p style="color: red; font-weight: bold;">
    *Lưu ý: Chức năng tải xuống xuất file với đuôi '.doc' và sử dụng định dạng HTML cơ bản (Times New Roman, cỡ 14) để giả lập chuẩn Nghị định 30. Bạn cần mở file này bằng Microsoft Word và kiểm tra, căn chỉnh lại để đảm bảo đúng định dạng theo yêu cầu chuyên môn.*
    </p>
    """, unsafe_allow_html=True)

else:
    st.info("Chưa có câu hỏi nào. Hãy soạn và thêm câu hỏi ở trên.")
    st.markdown("<div style='margin-bottom: 200px;'></div>", unsafe_allow_html=True)

# --- FOOTER ---

st.markdown("""
<footer style='text-align: center; padding: 10px; border-top: 1px solid #ccc;'>
    🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN
</footer>
""", unsafe_allow_html=True)
