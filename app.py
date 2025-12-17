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

# --- 3. CƠ SỞ DỮ LIỆU TỪ 5 FILE KẾ HOẠCH DẠY HỌC ---

SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

CURRICULUM_DB = {
    # ========================== KHỐI 1 (Kế hoạch dạy học Khối 1) ==========================
    "Lớp 1": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 1: Các số 0, 1, 2, 3, 4, 5 (Tr8) (3 tiết)", "YCCĐ": "Đếm, đọc, viết các số trong phạm vi 5."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 2: Các số 6, 7, 8, 9, 10 (Tr14) (4 tiết)", "YCCĐ": "Đếm, đọc, viết các số trong phạm vi 10."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 3: Nhiều hơn, ít hơn, bằng nhau (Tr20) (2 tiết)", "YCCĐ": "Nhận biết cách so sánh số lượng."},
                {"Chủ đề": "2. Làm quen với hình phẳng", "Bài học": "Bài 7: Hình vuông, tròn, tam giác, chữ nhật (Tr48) (3 tiết)", "YCCĐ": "Nhận dạng được các hình phẳng."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 8: Phép cộng trong phạm vi 10 (Tr56) (4 tiết)", "YCCĐ": "Thực hiện phép cộng, hiểu ý nghĩa gộp lại."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 9: Phép trừ trong phạm vi 10 (Tr68) (4 tiết)", "YCCĐ": "Thực hiện phép trừ, hiểu ý nghĩa tách ra."},
                {"Chủ đề": "4. Hình khối", "Bài học": "Bài 14: Khối lập phương, khối hộp chữ nhật (Tr92) (2 tiết)", "YCCĐ": "Nhận dạng khối lập phương, khối hộp CN."},
                {"Chủ đề": "5. Ôn tập HK1", "Bài học": "Bài 20: Ôn tập chung (Tr116) (2 tiết)", "YCCĐ": "Tổng hợp kiến thức học kì 1."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Các số đến 100", "Bài học": "Bài 21: Số có hai chữ số (Tr4) (3 tiết)", "YCCĐ": "Nhận biết chục, đơn vị."},
                {"Chủ đề": "7. Độ dài", "Bài học": "Bài 26: Đơn vị đo độ dài (Tr34) (2 tiết)", "YCCĐ": "Làm quen với xăng-ti-mét."},
                {"Chủ đề": "8. Phép cộng trừ PV 100", "Bài học": "Bài 29: Phép cộng số có 2 chữ số (Tr44) (2 tiết)", "YCCĐ": "Cộng không nhớ trong phạm vi 100."},
                {"Chủ đề": "9. Thời gian", "Bài học": "Bài 35: Các ngày trong tuần (Tr76) (1 tiết)", "YCCĐ": "Biết thứ tự các ngày trong tuần."},
                {"Chủ đề": "9. Thời gian", "Bài học": "Bài 36: Thực hành xem lịch và giờ (Tr80) (2 tiết)", "YCCĐ": "Xem giờ đúng, xem lịch."},
                {"Chủ đề": "10. Ôn tập cuối năm", "Bài học": "Bài 38: Ôn tập các số và phép tính (Tr88) (3 tiết)", "YCCĐ": "Ôn tập tổng hợp cuối năm."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Làm quen", "Bài học": "Bài 1: A a, B b (2 tiết)", "YCCĐ": "Nhận biết, đọc viết âm a, b."},
                {"Chủ đề": "Học vần", "Bài học": "Bài 5: Ô ô, Ơ ơ (2 tiết)", "YCCĐ": "Đọc viết âm ô, ơ, dấu thanh."},
                {"Chủ đề": "Học vần", "Bài học": "Bài 20: K k, Kh kh (2 tiết)", "YCCĐ": "Phân biệt k/kh, quy tắc chính tả."},
                {"Chủ đề": "Ôn tập", "Bài học": "Bài 18: Ôn tập và kể chuyện (2 tiết)", "YCCĐ": "Củng cố âm vần đã học."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Trường em", "Bài học": "Bài: Trường em (2 tiết)", "YCCĐ": "Đọc hiểu bài văn, tình cảm với trường."},
                {"Chủ đề": "Gia đình", "Bài học": "Bài: Bàn tay mẹ (2 tiết)", "YCCĐ": "Hiểu tình cảm mẹ con."},
                {"Chủ đề": "Thiên nhiên", "Bài học": "Bài: Hoa mai vàng (2 tiết)", "YCCĐ": "Nhận biết vẻ đẹp thiên nhiên."}
            ]
        }
    },

    # ========================== KHỐI 2 (Kế hoạch dạy học Khối 2) ==========================
    "Lớp 2": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập và bổ sung", "Bài học": "Bài 1: Ôn tập các số đến 100 (3 tiết)", "YCCĐ": "Đọc, viết, so sánh số đến 100."},
                {"Chủ đề": "2. Phép cộng trừ qua 10", "Bài học": "Bài 7: Phép cộng (qua 10) trong PV 20 (5 tiết)", "YCCĐ": "Thực hiện cộng có nhớ."},
                {"Chủ đề": "2. Phép cộng trừ qua 10", "Bài học": "Bài 11: Phép trừ (qua 10) trong PV 20 (5 tiết)", "YCCĐ": "Thực hiện trừ có nhớ."},
                {"Chủ đề": "4. Cộng trừ có nhớ PV 100", "Bài học": "Bài 20: Phép cộng (có nhớ) số có 2 chữ số (5 tiết)", "YCCĐ": "Đặt tính và tính đúng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "8. Phép nhân chia", "Bài học": "Bài 39: Bảng nhân 2 (2 tiết)", "YCCĐ": "Vận dụng bảng nhân 2."},
                {"Chủ đề": "8. Phép nhân chia", "Bài học": "Bài 43: Bảng chia 2 (2 tiết)", "YCCĐ": "Vận dụng bảng chia 2."},
                {"Chủ đề": "10. Số đến 1000", "Bài học": "Bài 48: Đơn vị, chục, trăm, nghìn (2 tiết)", "YCCĐ": "Cấu tạo số 3 chữ số."},
                {"Chủ đề": "12. Cộng trừ PV 1000", "Bài học": "Bài 60: Phép cộng (có nhớ) trong PV 1000 (4 tiết)", "YCCĐ": "Cộng có nhớ số 3 chữ số."},
                {"Chủ đề": "14. Ôn tập cuối năm", "Bài học": "Bài 69: Ôn tập phép cộng, phép trừ (3 tiết)", "YCCĐ": "Tổng hợp kiến thức."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Em lớn lên từng ngày", "Bài học": "Bài 1: Tôi là học sinh lớp 2 (4 tiết)", "YCCĐ": "Đọc hiểu, tự giới thiệu bản thân."},
                {"Chủ đề": "Đi học vui sao", "Bài học": "Bài 7: Cây xấu hổ (4 tiết)", "YCCĐ": "Tích hợp KNS: Mạnh dạn, tự tin."},
                {"Chủ đề": "Niềm vui tuổi thơ", "Bài học": "Bài 24: Nặn đồ chơi (6 tiết)", "YCCĐ": "Viết đoạn văn tả đồ chơi."},
                {"Chủ đề": "Mái ấm gia đình", "Bài học": "Bài 28: Trò chơi của bố (6 tiết)", "YCCĐ": "Viết đoạn văn về người thân."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quanh em", "Bài học": "Bài 1: Chuyện bốn mùa (4 tiết)", "YCCĐ": "Ý thức bảo vệ thiên nhiên."},
                {"Chủ đề": "Hành trình xanh", "Bài học": "Bài 10: Khủng long (6 tiết)", "YCCĐ": "Viết đoạn văn giới thiệu con vật."},
                {"Chủ đề": "Việt Nam quê hương", "Bài học": "Bài 25: Đất nước chúng mình (4 tiết)", "YCCĐ": "Kể chuyện Thánh Gióng."}
            ]
        }
    },

    # ========================== KHỐI 3 (Kế hoạch dạy học Khối 3) ==========================
    "Lớp 3": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập", "Bài học": "Bài 3: Tìm thành phần trong phép tính (2 tiết)", "YCCĐ": "Tìm số hạng, số bị trừ, số trừ."},
                {"Chủ đề": "2. Bảng nhân chia", "Bài học": "Bài 9: Bảng nhân 6, bảng chia 6 (2 tiết)", "YCCĐ": "Vận dụng bảng 6."},
                {"Chủ đề": "3. Hình phẳng", "Bài học": "Bài 17: Hình tròn, tâm, bán kính (1 tiết)", "YCCĐ": "Nhận biết đặc điểm hình tròn."},
                {"Chủ đề": "5. Đơn vị đo", "Bài học": "Bài 33: Nhiệt độ, đơn vị đo nhiệt độ (1 tiết)", "YCCĐ": "Biết đo nhiệt độ cơ thể."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "8. Số đến 10.000", "Bài học": "Bài 45: Số có 4 chữ số (2 tiết)", "YCCĐ": "Đọc viết số 4 chữ số."},
                {"Chủ đề": "9. Chu vi diện tích", "Bài học": "Bài 50: Chu vi hình tam giác, tứ giác (1 tiết)", "YCCĐ": "Tính chu vi hình đa giác."},
                {"Chủ đề": "11. Số đến 100.000", "Bài học": "Bài 59: Số có 5 chữ số (2 tiết)", "YCCĐ": "Đọc viết, so sánh số 5 chữ số."},
                {"Chủ đề": "13. Xem đồng hồ", "Bài học": "Bài 67: Thực hành xem đồng hồ (2 tiết)", "YCCĐ": "Xem giờ chính xác từng phút."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Trải nghiệm thú vị", "Bài học": "Bài 1: Ngày gặp lại (3 tiết)", "YCCĐ": "Nghe viết: Em yêu mùa hè. Viết tin nhắn."},
                {"Chủ đề": "Mái nhà yêu thương", "Bài học": "Bài 17: Ngưỡng cửa (3 tiết)", "YCCĐ": "Kể chuyện: Sự tích nhà sàn."},
                {"Chủ đề": "Mái ấm gia đình", "Bài học": "Bài 31: Người làm đồ chơi (3 tiết)", "YCCĐ": "Viết thư cho người thân."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Sắc màu thiên nhiên", "Bài học": "Bài 5: Ngày hội rừng xanh (3 tiết)", "YCCĐ": "Nghe viết: Chim chích bông."},
                {"Chủ đề": "Đất nước ngàn năm", "Bài học": "Bài 23: Hai Bà Trưng (3 tiết)", "YCCĐ": "Kể chuyện Hai Bà Trưng."},
                {"Chủ đề": "Trái đất của chúng mình", "Bài học": "Bài 28: Những điều nhỏ tớ làm cho Trái Đất (4 tiết)", "YCCĐ": "Viết đoạn văn về bảo vệ môi trường."}
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 1: Thông tin và quyết định (2 tiết)", "YCCĐ": "Hiểu vai trò thông tin."},
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 4: Làm việc với máy tính (3 tiết)", "YCCĐ": "Thao tác đúng với chuột, bàn phím."},
                {"Chủ đề": "Mạng máy tính", "Bài học": "Bài 6: Khám phá thông tin trên Internet (2 tiết)", "YCCĐ": "Xem tin tức, giải trí trên web."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Tổ chức thông tin", "Bài học": "Bài 8: Sơ đồ hình cây (2 tiết)", "YCCĐ": "Tổ chức thông tin trong máy tính."},
                {"Chủ đề": "Ứng dụng tin học", "Bài học": "Bài 11: Bài trình chiếu của em (2 tiết)", "YCCĐ": "Tạo slide trình chiếu đơn giản."},
                {"Chủ đề": "Giải quyết vấn đề", "Bài học": "Bài 15: Công việc thực hiện theo điều kiện (2 tiết)", "YCCĐ": "Hiểu cấu trúc rẽ nhánh."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 1: Tự nhiên và công nghệ (2 tiết)", "YCCĐ": "Phân biệt đối tượng tự nhiên/công nghệ."},
                {"Chủ đề": "Sử dụng đồ điện", "Bài học": "Bài 3: Sử dụng quạt điện (2 tiết)", "YCCĐ": "Sử dụng quạt an toàn."},
                {"Chủ đề": "Sử dụng đồ điện", "Bài học": "Bài 5: Sử dụng máy thu hình (3 tiết)", "YCCĐ": "Tác dụng, cách dùng Tivi."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thủ công", "Bài học": "Bài 7: Dụng cụ và vật liệu thủ công (3 tiết)", "YCCĐ": "Sử dụng kéo, thước, giấy."},
                {"Chủ đề": "Thủ công", "Bài học": "Bài 9: Làm biển báo giao thông (3 tiết)", "YCCĐ": "Làm mô hình biển báo."}
            ]
        }
    },

    # ========================== KHỐI 4 (Kế hoạch dạy học Khối 4) ==========================
    "Lớp 4": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập", "Bài học": "Bài 4: Biểu thức chứa chữ (3 tiết)", "YCCĐ": "Tính giá trị biểu thức."},
                {"Chủ đề": "2. Góc", "Bài học": "Bài 8: Góc nhọn, tù, bẹt (3 tiết)", "YCCĐ": "STEM: Góc biến hình."},
                {"Chủ đề": "3. Số lớn", "Bài học": "Bài 14: So sánh số nhiều chữ số (2 tiết)", "YCCĐ": "So sánh, xếp thứ tự số lớn."},
                {"Chủ đề": "5. Phép tính", "Bài học": "Bài 25: Tìm hai số khi biết tổng và hiệu (2 tiết)", "YCCĐ": "Giải toán tổng - hiệu."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "8. Phép nhân chia", "Bài học": "Bài 43: Nhân với số có 2 chữ số (3 tiết)", "YCCĐ": "Thực hiện nhân đúng."},
                {"Chủ đề": "9. Thống kê", "Bài học": "Bài 50: Biểu đồ cột (2 tiết)", "YCCĐ": "Đọc, mô tả số liệu."},
                {"Chủ đề": "10. Phân số", "Bài học": "Bài 56: Rút gọn phân số (2 tiết)", "YCCĐ": "Rút gọn về tối giản."},
                {"Chủ đề": "13. Ôn tập", "Bài học": "Bài 71: Ôn tập hình học (2 tiết)", "YCCĐ": "Ôn tập chu vi, diện tích."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Bài 1: Đọc Điều kì diệu (1 tiết)", "YCCĐ": "Nhận biết danh từ."},
                {"Chủ đề": "Trải nghiệm", "Bài học": "Bài 12: Nhà phát minh 6 tuổi (2 tiết)", "YCCĐ": "Viết bài văn kể chuyện."},
                {"Chủ đề": "Sáng tạo", "Bài học": "Bài 18: Đồng cỏ nở hoa (2 tiết)", "YCCĐ": "Biện pháp nhân hóa."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Yêu thương", "Bài học": "Bài 4: Quả ngọt cuối mùa (2 tiết)", "YCCĐ": "Viết đoạn văn biểu cảm."},
                {"Chủ đề": "Quê hương", "Bài học": "Bài 17: Cây đa quê hương (1 tiết)", "YCCĐ": "Viết văn miêu tả cây cối."},
                {"Chủ đề": "Bình yên", "Bài học": "Bài 25: Khu bảo tồn động vật (1 tiết)", "YCCĐ": "Giáo dục bảo vệ môi trường."}
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "Chất", "Bài học": "Bài 1: Tính chất của nước (2 tiết)", "YCCĐ": "Vai trò của nước với cuộc sống."},
                {"Chủ đề": "Năng lượng", "Bài học": "Bài 8: Ánh sáng và sự truyền ánh sáng (2 tiết)", "YCCĐ": "Vật phát sáng, vật cản sáng."},
                {"Chủ đề": "Thực vật", "Bài học": "Bài 16: Động vật cần gì để sống (3 tiết)", "YCCĐ": "Nhu cầu sống của động vật."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Nấm", "Bài học": "Bài 19: Đặc điểm chung của nấm (2 tiết)", "YCCĐ": "Nhận biết các loại nấm."},
                {"Chủ đề": "Con người", "Bài học": "Bài 24: Chế độ ăn uống cân bằng (3 tiết)", "YCCĐ": "Xây dựng thực đơn hợp lý."},
                {"Chủ đề": "Sinh vật", "Bài học": "Bài 30: Vai trò thực vật trong chuỗi thức ăn (3 tiết)", "YCCĐ": "Vẽ sơ đồ chuỗi thức ăn."}
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "Địa phương em", "Bài học": "Bài 2: Thiên nhiên con người địa phương (2 tiết)", "YCCĐ": "Tìm hiểu địa phương."},
                {"Chủ đề": "Trung du Bắc Bộ", "Bài học": "Bài 7: Đền Hùng và lễ giỗ Tổ (2 tiết)", "YCCĐ": "Lễ hội Đền Hùng."},
                {"Chủ đề": "Đồng bằng Bắc Bộ", "Bài học": "Bài 12: Thăng Long - Hà Nội (3 tiết)", "YCCĐ": "Lịch sử thủ đô."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Duyên hải MT", "Bài học": "Bài 18: Cố đô Huế (2 tiết)", "YCCĐ": "Bảo tồn di tích cố đô Huế."},
                {"Chủ đề": "Tây Nguyên", "Bài học": "Bài 23: Lễ hội cồng chiêng (2 tiết)", "YCCĐ": "Không gian văn hóa cồng chiêng."},
                {"Chủ đề": "Nam Bộ", "Bài học": "Bài 27: Thành phố Hồ Chí Minh (2 tiết)", "YCCĐ": "Lịch sử Sài Gòn - TP.HCM."}
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 1: Phần cứng và phần mềm (2 tiết)", "YCCĐ": "Phân biệt phần cứng, phần mềm."},
                {"Chủ đề": "Mạng máy tính", "Bài học": "Bài 3: Thông tin trên trang web (2 tiết)", "YCCĐ": "Nhận biết thông tin trên web."},
                {"Chủ đề": "Đạo đức", "Bài học": "Bài 7: Bản quyền phần mềm (1 tiết)", "YCCĐ": "Tôn trọng bản quyền."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Ứng dụng", "Bài học": "Bài 8: Tạo bài trình chiếu (2 tiết)", "YCCĐ": "Tạo slide cơ bản."},
                {"Chủ đề": "Luyện tập", "Bài học": "Bài 16: Luyện tập gõ bàn phím (1 tiết)", "YCCĐ": "Gõ phím đúng cách."},
                {"Chủ đề": "Lập trình", "Bài học": "Bài 17: Làm quen với lập trình (2 tiết)", "YCCĐ": "Làm quen Scratch."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Hoa và cây cảnh", "Bài học": "Bài 1: Lợi ích của hoa, cây cảnh (3 tiết)", "YCCĐ": "Nêu lợi ích trang trí."},
                {"Chủ đề": "Hoa và cây cảnh", "Bài học": "Bài 4: Gieo hạt hoa trong chậu (3 tiết)", "YCCĐ": "Các bước gieo hạt."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lắp ghép", "Bài học": "Bài 7: Bộ lắp ghép mô hình kĩ thuật (2 tiết)", "YCCĐ": "Nhận biết chi tiết lắp ghép."},
                {"Chủ đề": "Lắp ghép", "Bài học": "Bài 9: Lắp ghép robot (3 tiết)", "YCCĐ": "Lắp ráp mô hình robot."},
                {"Chủ đề": "Lắp ghép", "Bài học": "Bài 12: Làm chuồn chuồn thăng bằng (2 tiết)", "YCCĐ": "Làm đồ chơi dân gian."}
            ]
        }
    },

    # ========================== KHỐI 5 (Kế hoạch dạy học Khối 5) ==========================
    "Lớp 5": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Ôn tập", "Bài học": "Bài 4: Phân số thập phân (1 tiết)", "YCCĐ": "Nhận biết phân số thập phân."},
                {"Chủ đề": "Số thập phân", "Bài học": "Bài 10: Khái niệm số thập phân (3 tiết)", "YCCĐ": "Đọc viết, so sánh số thập phân."},
                {"Chủ đề": "Phép tính", "Bài học": "Bài 20: Phép trừ số thập phân (2 tiết)", "YCCĐ": "Trừ hai số thập phân."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 25: Hình tam giác. Diện tích (4 tiết)", "YCCĐ": "Đặc điểm, diện tích tam giác."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Tỉ số %", "Bài học": "Bài 41: Tìm giá trị phần trăm của một số (2 tiết)", "YCCĐ": "Giải toán về tỉ số phần trăm."},
                {"Chủ đề": "Hình khối", "Bài học": "Bài 53: Thể tích hình lập phương (2 tiết)", "YCCĐ": "Tính thể tích hình lập phương."},
                {"Chủ đề": "Chuyển động", "Bài học": "Bài 60: Quãng đường, thời gian (3 tiết)", "YCCĐ": "Bài toán chuyển động đều."},
                {"Chủ đề": "Thống kê", "Bài học": "Bài 64: Biểu đồ hình quạt tròn (2 tiết)", "YCCĐ": "Đọc, phân tích biểu đồ quạt."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Thế giới tuổi thơ", "Bài học": "Bài 1: Thanh âm của gió (1 tiết)", "YCCĐ": "Quyền vui chơi trẻ em."},
                {"Chủ đề": "Con đường học tập", "Bài học": "Bài 17: Thư gửi các học sinh (1 tiết)", "YCCĐ": "Bổn phận học sinh."},
                {"Chủ đề": "Nghệ thuật", "Bài học": "Bài 27: Trí tưởng tượng phong phú (2 tiết)", "YCCĐ": "Biện pháp điệp từ."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp cuộc sống", "Bài học": "Bài 4: Hộp quà màu thiên thanh (2 tiết)", "YCCĐ": "Viết văn tả người."},
                {"Chủ đề": "Tiếp bước cha ông", "Bài học": "Bài 20: Cụ Đồ Chiểu (2 tiết)", "YCCĐ": "Viết đoạn văn nêu ý kiến."},
                {"Chủ đề": "Thế giới", "Bài học": "Bài 25: Bài ca trái đất (1 tiết)", "YCCĐ": "Giáo dục bảo vệ môi trường."}
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "Chất", "Bài học": "Bài 1: Thành phần và vai trò của đất (2 tiết)", "YCCĐ": "Đất với cây trồng."},
                {"Chủ đề": "Chất", "Bài học": "Bài 4: Đặc điểm chất rắn, lỏng, khí (2 tiết)", "YCCĐ": "Sự biến đổi trạng thái."},
                {"Chủ đề": "Năng lượng", "Bài học": "Bài 7: Vai trò của năng lượng (2 tiết)", "YCCĐ": "Nguồn năng lượng sạch."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Động vật", "Bài học": "Bài 16: Vòng đời động vật (2 tiết)", "YCCĐ": "Sự phát triển của động vật."},
                {"Chủ đề": "Con người", "Bài học": "Bài 25: Chăm sóc sức khỏe tuổi dậy thì (3 tiết)", "YCCĐ": "Vệ sinh tuổi dậy thì."},
                {"Chủ đề": "Con người", "Bài học": "Bài 26: Phòng tránh bị xâm hại (4 tiết)", "YCCĐ": "Quyền được an toàn."}
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "Đất nước", "Bài học": "Bài 1: Vị trí địa lí, lãnh thổ (2 tiết)", "YCCĐ": "Ý nghĩa Quốc kì, Quốc ca."},
                {"Chủ đề": "Dựng nước", "Bài học": "Bài 5: Nhà nước Văn Lang, Âu Lạc (3 tiết)", "YCCĐ": "Buổi đầu dựng nước."},
                {"Chủ đề": "Giữ nước", "Bài học": "Bài 10: Triều Trần kháng chiến chống Mông-Nguyên (4 tiết)", "YCCĐ": "Hào khí Đông A."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Xây dựng đất nước", "Bài học": "Bài 15: Chiến dịch Điện Biên Phủ (2 tiết)", "YCCĐ": "Chiến thắng lịch sử."},
                {"Chủ đề": "Láng giềng", "Bài học": "Bài 18: Trung Quốc (2 tiết)", "YCCĐ": "Đặc điểm tự nhiên Trung Quốc."},
                {"Chủ đề": "Thế giới", "Bài học": "Bài 22: Các châu lục và đại dương (5 tiết)", "YCCĐ": "Địa lý thế giới."}
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 1: Em làm gì với máy tính (2 tiết)", "YCCĐ": "Ứng dụng máy tính."},
                {"Chủ đề": "Tổ chức thông tin", "Bài học": "Bài 4: Cây thư mục (2 tiết)", "YCCĐ": "Tổ chức tệp tin."},
                {"Chủ đề": "Soạn thảo", "Bài học": "Bài 6: Định dạng văn bản (2 tiết)", "YCCĐ": "Trình bày văn bản đẹp."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lập trình", "Bài học": "Bài 11: Cấu trúc lặp (2 tiết)", "YCCĐ": "Lập trình vòng lặp."},
                {"Chủ đề": "Lập trình", "Bài học": "Bài 14: Sử dụng biến (2 tiết)", "YCCĐ": "Biến nhớ trong chương trình."},
                {"Chủ đề": "Lập trình", "Bài học": "Bài 16: Từ kịch bản đến chương trình (2 tiết)", "YCCĐ": "Hoàn thiện dự án."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Đời sống", "Bài học": "Bài 1: Vai trò của công nghệ (2 tiết)", "YCCĐ": "Công nghệ trong đời sống."},
                {"Chủ đề": "Thiết kế", "Bài học": "Bài 4: Thiết kế sản phẩm (4 tiết)", "YCCĐ": "Quy trình thiết kế."},
                {"Chủ đề": "Đời sống", "Bài học": "Bài 6: Sử dụng tủ lạnh (3 tiết)", "YCCĐ": "Bảo quản thực phẩm."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thủ công", "Bài học": "Bài 7: Lắp ráp xe điện chạy pin (4 tiết)", "YCCĐ": "Lắp ráp mô hình động."},
                {"Chủ đề": "Thủ công", "Bài học": "Bài 9: Mô hình điện mặt trời (4 tiết)", "YCCĐ": "Năng lượng sạch."}
            ]
        }
    }
}

# --- 4. CÁC HÀM XỬ LÝ (LOGIC GIỮ NGUYÊN) ---

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
            if available: return available[0]
        return None
    except:
        return None

def generate_single_question(api_key, grade, subject, lesson_info, q_type, level, points):
    clean_key = api_key.strip()
    if not clean_key: return "⚠️ Chưa nhập API Key."
    
    model_name = find_working_model(clean_key)
    if not model_name: return "❌ Lỗi Key hoặc Mạng."

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
    
    # Retry mechanism for 429
    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            else:
                return f"Lỗi API ({response.status_code})"
        except Exception as e:
            return f"Lỗi: {e}"
    return "⚠️ Quá tải, thử lại sau."

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
    # Lấy tên môn học, bỏ icon
    if selected_subject_full:
        selected_subject = selected_subject_full.split(" ", 1)[1]
    else:
        selected_subject = ""

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

    # 3.2. Xuất file WORD CHUẨN NĐ 30
    
    # --- PHẦN 1: TẠO MA TRẬN ĐẶC TẢ (Dạng Bảng Text cho dễ nhìn trong Word) ---
    matrix_text = "MA TRẬN ĐỀ THI\n"
    matrix_text += "="*60 + "\n"
    for idx, item in enumerate(st.session_state.exam_list):
        matrix_text += f"Câu {idx+1}: {item['lesson']} - {item['type']} - {item['level']} - {item['points']}đ\n"
    matrix_text += "="*60 + "\n"
    matrix_text += f"TỔNG SỐ CÂU: {len(st.session_state.exam_list)}\n"
    matrix_text += f"TỔNG ĐIỂM:   {sum(q['points'] for q in st.session_state.exam_list)}\n"

    # --- PHẦN 2: TẠO NỘI DUNG ĐỀ THI HTML (Giả lập Word) ---
    exam_content_html = f"""
    <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
    <head>
        <meta charset="utf-8">
        <title>De Thi</title>
        <style>
            body {{ font-family: 'Times New Roman'; font-size: 14pt; line-height: 1.5; }}
            .header-table {{ width: 100%; margin-bottom: 20px; }}
            .header-left {{ text-align: center; font-weight: bold; width: 40%; vertical-align: top; }}
            .header-right {{ text-align: center; font-weight: bold; width: 60%; vertical-align: top; }}
            .title {{ text-align: center; font-weight: bold; font-size: 16pt; margin: 20px 0; }}
            .question {{ margin-bottom: 10pt; text-align: justify; }}
            .answer {{ margin-top: 5pt; font-style: italic; color: #555; }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td class="header-left">
                    PHÒNG GD&ĐT HUYỆN ĐỒNG VĂN<br>
                    TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN<br>
                    --------------------
                </td>
                <td class="header-right">
                    CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM<br>
                    Độc lập - Tự do - Hạnh phúc<br>
                    --------------------
                </td>
            </tr>
        </table>

        <div class="title">ĐỀ KIỂM TRA ĐỊNH KỲ MÔN {selected_subject.upper()} - {selected_grade.upper()}</div>
        <p style="text-align: center;"><i>Thời gian làm bài: 40 phút (Không kể thời gian giao đề)</i></p>
        <hr>

        <h3>I. MA TRẬN ĐẶC TẢ ĐỀ THI</h3>
        <pre style="font-family: 'Times New Roman'; font-size: 13pt;">{matrix_text}</pre>
        
        <h3>II. NỘI DUNG ĐỀ BÀI</h3>
    """

    for idx, q in enumerate(st.session_state.exam_list):
        # Xử lý nội dung câu hỏi để hiển thị đẹp
        clean_content = q['content'].replace('**Câu hỏi:**', '').replace('**Đáp án:**', '<br><b>Đáp án:</b>')
        clean_content = clean_content.replace('\n', '<br>')
        
        exam_content_html += f"""
        <div class="question">
            <b>Câu {idx+1} ({q['points']} điểm):</b> {clean_content}
        </div>
        """
    
    exam_content_html += "</body></html>"

    st.download_button(
        label="📥 Tải xuống (Đề thi + Bảng đặc tả) - Chuẩn Word NĐ 30",
        data=exam_content_html,
        file_name=f"De_thi_{selected_subject}_{selected_grade}.doc",
        mime="application/msword",
        type="primary"
    )
    
    st.caption("Lưu ý: File tải về là dạng .doc, bạn hãy mở bằng Microsoft Word để có định dạng chuẩn nhất.")

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
