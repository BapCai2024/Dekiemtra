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

# --- 3. CƠ SỞ DỮ LIỆU CHƯƠNG TRÌNH HỌC (DATA CHI TIẾT - ĐẦY ĐỦ CÁC BÀI) ---

SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

CURRICULUM_DB = {
    # ========================== KHỐI 1 (KNTT) ==========================
    "Lớp 1": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Các số 0-10", "Bài học": "Bài 1: Các số 0, 1, 2, 3, 4, 5 (3 tiết)", "YCCĐ": "Đếm, đọc, viết số trong phạm vi 5."},
                {"Chủ đề": "1. Các số 0-10", "Bài học": "Bài 2: Các số 6, 7, 8, 9, 10 (4 tiết)", "YCCĐ": "Đếm, đọc, viết số đến 10."},
                {"Chủ đề": "1. Các số 0-10", "Bài học": "Bài 3: Nhiều hơn, ít hơn, bằng nhau (2 tiết)", "YCCĐ": "So sánh số lượng, dùng từ so sánh."},
                {"Chủ đề": "2. Hình phẳng", "Bài học": "Bài 7: Hình vuông, tròn, tam giác (3 tiết)", "YCCĐ": "Nhận dạng hình phẳng."},
                {"Chủ đề": "3. Phép cộng trừ PV 10", "Bài học": "Bài 10: Luyện tập chung (3 tiết)", "YCCĐ": "Thực hiện thành thạo cộng trừ PV 10."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Số đến 100", "Bài học": "Bài 21: Số có hai chữ số (3 tiết)", "YCCĐ": "Đọc, viết, cấu tạo số 2 chữ số."},
                {"Chủ đề": "6. Cộng trừ PV 100", "Bài học": "Bài 29: Phép cộng số có 2 chữ số (2 tiết)", "YCCĐ": "Cộng không nhớ."},
                {"Chủ đề": "7. Thời gian", "Bài học": "Bài 35: Các ngày trong tuần (1 tiết)", "YCCĐ": "Biết thứ tự các ngày trong tuần."},
                {"Chủ đề": "7. Thời gian", "Bài học": "Bài 36: Thực hành xem lịch và giờ (2 tiết)", "YCCĐ": "Xem giờ đúng, xem lịch tờ."},
                {"Chủ đề": "8. Ôn tập", "Bài học": "Bài 38: Ôn tập các số và phép tính (1 tiết)", "YCCĐ": "Tổng hợp kiến thức số học."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Làm quen", "Bài học": "Bài 1: A a (2 tiết)", "YCCĐ": "Nhận biết âm a, chữ a."},
                {"Chủ đề": "Làm quen", "Bài học": "Bài 2: B b, dấu huyền (2 tiết)", "YCCĐ": "Đọc âm b, thanh huyền."},
                {"Chủ đề": "Học vần", "Bài học": "Bài 5: Ô ô, dấu nặng (2 tiết)", "YCCĐ": "Đọc viết âm ô, thanh nặng."},
                {"Chủ đề": "Ôn tập", "Bài học": "Bài 18: Ôn tập cuối học kì I (2 tiết)", "YCCĐ": "Hệ thống hóa kiến thức học kì 1."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Trường em", "Bài học": "Bài 19A: Tới trường (2 tiết)", "YCCĐ": "Đọc trơn, hiểu nội dung bài Tới trường."},
                {"Chủ đề": "Gia đình em", "Bài học": "Bài 22A: Con yêu mẹ (2 tiết)", "YCCĐ": "Hiểu tình cảm mẹ con."},
                {"Chủ đề": "Cuộc sống quanh em", "Bài học": "Bài 25D: Những con vật thông minh (2 tiết)", "YCCĐ": "Đọc hiểu truyện kể về loài vật."}
            ]
        }
    },

    # ========================== KHỐI 2 (KNTT) ==========================
    "Lớp 2": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập", "Bài học": "Bài 1: Ôn tập các số đến 100 (3 tiết)", "YCCĐ": "Củng cố chục, đơn vị, so sánh, cộng, trừ PV 100."},
                {"Chủ đề": "2. Phép cộng trừ qua 10", "Bài học": "Bài 7: Phép cộng (qua 10) (5 tiết)", "YCCĐ": "Thực hiện cộng có nhớ trong PV 20."},
                {"Chủ đề": "2. Phép cộng trừ qua 10", "Bài học": "Bài 11: Phép trừ (qua 10) (5 tiết)", "YCCĐ": "Thực hiện trừ có nhớ trong PV 20."},
                {"Chủ đề": "4. Cộng trừ PV 100", "Bài học": "Bài 20: Phép cộng (có nhớ) số có 2 chữ số (5 tiết)", "YCCĐ": "Đặt tính và tính đúng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "8. Phép nhân chia", "Bài học": "Bài 39: Bảng nhân 2 (2 tiết)", "YCCĐ": "Thuộc bảng nhân 2."},
                {"Chủ đề": "8. Phép nhân chia", "Bài học": "Bài 43: Bảng chia 2 (2 tiết)", "YCCĐ": "Thuộc bảng chia 2."},
                {"Chủ đề": "11. Độ dài", "Bài học": "Bài 55: Đề-xi-mét, Mét, Ki-lô-mét (3 tiết)", "YCCĐ": "Đổi đơn vị đo độ dài."},
                {"Chủ đề": "14. Ôn tập", "Bài học": "Bài 69: Ôn tập phép cộng, phép trừ (3 tiết)", "YCCĐ": "Luyện tập tổng hợp cuối năm."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Em lớn lên từng ngày", "Bài học": "Bài 1: Tôi là học sinh lớp 2 (4 tiết)", "YCCĐ": "Đọc hiểu văn bản, tự tin giới thiệu bản thân."},
                {"Chủ đề": "Đi học vui sao", "Bài học": "Bài 7: Cây xấu hổ (4 tiết)", "YCCĐ": "Đọc hiểu, mở rộng vốn từ về cây cối."},
                {"Chủ đề": "Mái ấm gia đình", "Bài học": "Bài 28: Trò chơi của bố (6 tiết)", "YCCĐ": "Viết đoạn văn về người thân."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quanh em", "Bài học": "Bài 1: Chuyện bốn mùa (4 tiết)", "YCCĐ": "Hiểu đặc điểm các mùa."},
                {"Chủ đề": "Giao tiếp và kết nối", "Bài học": "Bài 18: Thư viện biết đi (6 tiết)", "YCCĐ": "Viết đoạn văn giới thiệu đồ vật."},
                {"Chủ đề": "Việt Nam quê hương", "Bài học": "Bài 25: Đất nước chúng mình (4 tiết)", "YCCĐ": "Hiểu biết về danh lam thắng cảnh."}
            ]
        }
    },

    # ========================== KHỐI 3 (KNTT + Cùng Khám Phá) ==========================
    "Lớp 3": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập", "Bài học": "Bài 3: Tìm số hạng, số bị trừ, số trừ (2 tiết)", "YCCĐ": "Tìm thành phần chưa biết của phép tính."},
                {"Chủ đề": "2. Bảng nhân chia", "Bài học": "Bài 9: Bảng nhân 6, bảng chia 6 (1 tiết)", "YCCĐ": "Vận dụng bảng nhân/chia 6."},
                {"Chủ đề": "3. Hình phẳng", "Bài học": "Bài 17: Hình tròn, tâm, bán kính (1 tiết)", "YCCĐ": "Nhận biết đặc điểm hình tròn."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "8. Số đến 10.000", "Bài học": "Bài 45: Số có 4 chữ số (1 tiết)", "YCCĐ": "Đọc viết số 4 chữ số."},
                {"Chủ đề": "9. Chu vi diện tích", "Bài học": "Bài 50: Chu vi hình tam giác, tứ giác (1 tiết)", "YCCĐ": "Tính chu vi hình đa giác."},
                {"Chủ đề": "11. Số đến 100.000", "Bài học": "Bài 59: Số có 5 chữ số (1 tiết)", "YCCĐ": "Đọc viết số 5 chữ số."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Trải nghiệm thú vị", "Bài học": "Bài 1: Ngày gặp lại (3 tiết)", "YCCĐ": "Đọc hiểu, viết tin nhắn."},
                {"Chủ đề": "Mái nhà yêu thương", "Bài học": "Bài 17: Ngưỡng cửa (3 tiết)", "YCCĐ": "Kể chuyện sự tích nhà sàn."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Sắc màu thiên nhiên", "Bài học": "Bài 5: Ngày hội rừng xanh (3 tiết)", "YCCĐ": "Nghe viết chim chích bông."},
                {"Chủ đề": "Đất nước ngàn năm", "Bài học": "Bài 23: Hai Bà Trưng (3 tiết)", "YCCĐ": "Kể chuyện Hai Bà Trưng."}
            ]
        },
        "Tin học": { # Cùng Khám Phá
            "Học kỳ I": [
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 1: Thông tin và quyết định (2 tiết)", "YCCĐ": "Phân biệt thông tin và quyết định."},
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 4: Làm việc với máy tính (3 tiết)", "YCCĐ": "Thao tác chuột, bàn phím đúng cách."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "C. Tổ chức thông tin", "Bài học": "Bài 8: Sơ đồ hình cây (2 tiết)", "YCCĐ": "Hiểu cách tổ chức thư mục."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 11: Bài trình chiếu của em (2 tiết)", "YCCĐ": "Tạo slide đơn giản."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 3: Sử dụng quạt điện (2 tiết)", "YCCĐ": "Sử dụng an toàn, tiết kiệm."},
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 5: Sử dụng máy thu hình (3 tiết)", "YCCĐ": "Chọn kênh, chỉnh âm lượng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thủ công", "Bài học": "Bài 8: Làm đồ dùng học tập (3 tiết)", "YCCĐ": "Làm ống bút/thước kẻ."},
                {"Chủ đề": "Thủ công", "Bài học": "Bài 9: Làm biển báo giao thông (3 tiết)", "YCCĐ": "Làm mô hình biển báo."}
            ]
        }
    },

    # ========================== KHỐI 4 (KNTT) ==========================
    "Lớp 4": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập", "Bài học": "Bài 4: Biểu thức chứa chữ (3 tiết)", "YCCĐ": "Tính giá trị biểu thức."},
                {"Chủ đề": "2. Góc", "Bài học": "Bài 8: Góc nhọn, góc tù, góc bẹt (3 tiết)", "YCCĐ": "Nhận biết các loại góc."},
                {"Chủ đề": "4. Đơn vị đo", "Bài học": "Bài 19: Giây, thế kỉ (2 tiết)", "YCCĐ": "Đổi đơn vị thời gian."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "8. Phép nhân chia", "Bài học": "Bài 43: Nhân với số có hai chữ số (3 tiết)", "YCCĐ": "Thực hiện nhân đúng."},
                {"Chủ đề": "9. Thống kê", "Bài học": "Bài 50: Biểu đồ cột (2 tiết)", "YCCĐ": "Đọc và phân tích số liệu."},
                {"Chủ đề": "11. Phân số", "Bài học": "Bài 60: Phép cộng phân số (4 tiết)", "YCCĐ": "Cộng phân số cùng/khác mẫu."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Bài 1: Điều kì diệu (1 tiết)", "YCCĐ": "Đọc hiểu, nhận biết danh từ."},
                {"Chủ đề": "Niềm vui sáng tạo", "Bài học": "Bài 18: Đồng cỏ nở hoa (2 tiết)", "YCCĐ": "Biện pháp nhân hóa."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Sống để yêu thương", "Bài học": "Bài 4: Quả ngọt cuối mùa (2 tiết)", "YCCĐ": "Viết đoạn văn tình cảm."},
                {"Chủ đề": "Uống nước nhớ nguồn", "Bài học": "Bài 9: Sự tích con Rồng cháu Tiên (1 tiết)", "YCCĐ": "Luyện tập thành phần câu."}
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "1. Chất", "Bài học": "Bài 1: Tính chất của nước (2 tiết)", "YCCĐ": "Nêu tính chất, vai trò của nước."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 8: Ánh sáng và sự truyền ánh sáng (2 tiết)", "YCCĐ": "Vật phát sáng, vật cản sáng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Nấm", "Bài học": "Bài 19: Đặc điểm chung của nấm (2 tiết)", "YCCĐ": "Nơi sống, hình dạng của nấm."},
                {"Chủ đề": "5. Con người", "Bài học": "Bài 24: Chế độ ăn uống cân bằng (3 tiết)", "YCCĐ": "Xây dựng thực đơn hợp lý."}
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "Địa phương em", "Bài học": "Bài 2: Thiên nhiên và con người địa phương (2 tiết)", "YCCĐ": "Tìm hiểu địa phương."},
                {"Chủ đề": "Đồng bằng Bắc Bộ", "Bài học": "Bài 12: Thăng Long - Hà Nội (3 tiết)", "YCCĐ": "Lịch sử thủ đô."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Duyên hải MT", "Bài học": "Bài 18: Cố đô Huế (2 tiết)", "YCCĐ": "Di sản cố đô Huế."},
                {"Chủ đề": "Tây Nguyên", "Bài học": "Bài 23: Lễ hội cồng chiêng (2 tiết)", "YCCĐ": "Không gian văn hóa cồng chiêng."}
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 1: Phần cứng và phần mềm (2 tiết)", "YCCĐ": "Phân biệt phần cứng, phần mềm."},
                {"Chủ đề": "D. Đạo đức", "Bài học": "Bài 7: Bản quyền phần mềm (1 tiết)", "YCCĐ": "Tôn trọng bản quyền."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "E. Ứng dụng", "Bài học": "Bài 8: Tạo bài trình chiếu (2 tiết)", "YCCĐ": "Tạo slide, chèn ảnh."},
                {"Chủ đề": "F. Lập trình", "Bài học": "Bài 17: Làm quen với lập trình (2 tiết)", "YCCĐ": "Sử dụng Scratch cơ bản."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Hoa và cây cảnh", "Bài học": "Bài 4: Gieo hạt hoa trong chậu (3 tiết)", "YCCĐ": "Thực hành gieo hạt."},
                {"Chủ đề": "Hoa và cây cảnh", "Bài học": "Bài 6: Chăm sóc hoa trong chậu (3 tiết)", "YCCĐ": "Tưới nước, bón phân."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lắp ghép", "Bài học": "Bài 9: Lắp ghép mô hình robot (3 tiết)", "YCCĐ": "Lắp ráp robot đơn giản."},
                {"Chủ đề": "Lắp ghép", "Bài học": "Bài 12: Làm chuồn chuồn thăng bằng (2 tiết)", "YCCĐ": "Làm đồ chơi dân gian."}
            ]
        }
    },

    # ========================== KHỐI 5 (KNTT) ==========================
    "Lớp 5": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập", "Bài học": "Bài 4: Phân số thập phân (1 tiết)", "YCCĐ": "Nhận biết phân số thập phân."},
                {"Chủ đề": "2. Số thập phân", "Bài học": "Bài 10: Khái niệm số thập phân (3 tiết)", "YCCĐ": "Đọc viết, so sánh số thập phân."},
                {"Chủ đề": "4. Phép tính STP", "Bài học": "Bài 20: Phép trừ số thập phân (2 tiết)", "YCCĐ": "Trừ hai số thập phân."},
                {"Chủ đề": "5. Hình phẳng", "Bài học": "Bài 25: Hình tam giác. Diện tích (4 tiết)", "YCCĐ": "Tính diện tích tam giác."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "7. Tỉ số %", "Bài học": "Bài 41: Tìm giá trị phần trăm của một số (2 tiết)", "YCCĐ": "Giải toán tỉ số phần trăm."},
                {"Chủ đề": "9. Hình khối", "Bài học": "Bài 53: Thể tích hình lập phương (2 tiết)", "YCCĐ": "Tính thể tích hình lập phương."},
                {"Chủ đề": "10. Chuyển động đều", "Bài học": "Bài 60: Quãng đường, thời gian (3 tiết)", "YCCĐ": "Tính s, v, t."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Thế giới tuổi thơ", "Bài học": "Bài 1: Thanh âm của gió (1 tiết)", "YCCĐ": "Đọc hiểu, quyền trẻ em."},
                {"Chủ đề": "Con đường học tập", "Bài học": "Bài 17: Thư gửi các học sinh (1 tiết)", "YCCĐ": "Bổn phận học sinh."},
                {"Chủ đề": "Nghệ thuật", "Bài học": "Bài 27: Trí tưởng tượng phong phú (2 tiết)", "YCCĐ": "Biện pháp điệp từ."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp cuộc sống", "Bài học": "Bài 4: Hộp quà màu thiên thanh (2 tiết)", "YCCĐ": "Viết văn tả người."},
                {"Chủ đề": "Tiếp bước cha ông", "Bài học": "Bài 20: Cụ Đồ Chiểu (2 tiết)", "YCCĐ": "Nêu ý kiến tán thành."}
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "1. Chất", "Bài học": "Bài 1: Thành phần và vai trò của đất (2 tiết)", "YCCĐ": "Đất trồng cây."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 7: Vai trò của năng lượng (2 tiết)", "YCCĐ": "Nguồn năng lượng sạch."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "3. Thực vật/Động vật", "Bài học": "Bài 16: Vòng đời của động vật (2 tiết)", "YCCĐ": "Sự phát triển của động vật."},
                {"Chủ đề": "5. Con người", "Bài học": "Bài 26: Phòng tránh bị xâm hại (4 tiết)", "YCCĐ": "Kỹ năng tự bảo vệ."}
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "1. Đất nước", "Bài học": "Bài 1: Vị trí địa lí, lãnh thổ (2 tiết)", "YCCĐ": "Ý nghĩa Quốc kì, Quốc ca."},
                {"Chủ đề": "2. Quốc gia đầu tiên", "Bài học": "Bài 5: Nhà nước Văn Lang, Âu Lạc (3 tiết)", "YCCĐ": "Sự ra đời nhà nước đầu tiên."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "3. Xây dựng đất nước", "Bài học": "Bài 15: Chiến dịch Điện Biên Phủ (2 tiết)", "YCCĐ": "Ý nghĩa chiến thắng ĐBP."},
                {"Chủ đề": "5. Thế giới", "Bài học": "Bài 22: Các châu lục và đại dương (5 tiết)", "YCCĐ": "Vị trí địa lý thế giới."}
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "1. Máy tính và em", "Bài học": "Bài 1: Em làm gì với máy tính (2 tiết)", "YCCĐ": "Ứng dụng máy tính."},
                {"Chủ đề": "3. Tổ chức thông tin", "Bài học": "Bài 4: Cây thư mục (2 tiết)", "YCCĐ": "Quản lý tệp tin."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "6. Lập trình", "Bài học": "Bài 11: Cấu trúc lặp (2 tiết)", "YCCĐ": "Lập trình vòng lặp."},
                {"Chủ đề": "6. Lập trình", "Bài học": "Bài 14: Sử dụng biến (2 tiết)", "YCCĐ": "Khai báo và dùng biến."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 4: Thiết kế sản phẩm (4 tiết)", "YCCĐ": "Quy trình thiết kế."},
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 6: Sử dụng tủ lạnh (3 tiết)", "YCCĐ": "Bảo quản thực phẩm."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thủ công", "Bài học": "Bài 7: Lắp ráp xe điện chạy pin (4 tiết)", "YCCĐ": "Lắp ráp mô hình động."}
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
    subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
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
    <table style="width: 100%; font-family: 'Times New Roman';">
      <tr>
        <td style="text-align: center; font-weight: bold; vertical-align: top; width: 40%;">
          TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN<br>
          --------
        </td>
        <td style="text-align: center; font-weight: bold; vertical-align: top; width: 60%;">
          CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM<br>
          Độc lập - Tự do - Hạnh phúc<br>
          ----------------
        </td>
      </tr>
      <tr>
        <td colspan="2" style="text-align: center; font-weight: bold; font-size: 16pt; padding-top: 20px; padding-bottom: 20px;">
          ĐỀ KIỂM TRA ĐỊNH KỲ CUỐI HỌC KỲ ... MÔN {selected_subject.upper()} - {selected_grade.upper()}
        </td>
      </tr>
    </table>
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
