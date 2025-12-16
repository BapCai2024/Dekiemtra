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

# --- 3. CƠ SỞ DỮ LIỆU CHƯƠNG TRÌNH HỌC (DATA CHI TIẾT 100%) ---
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
                {"Chủ đề": "1. Các số 0-10", "Bài học": "Bài 1: Các số 0, 1, 2, 3, 4, 5 (3 tiết)", "YCCĐ": "Đếm, đọc, viết số đến 5."},
                {"Chủ đề": "1. Các số 0-10", "Bài học": "Bài 2: Các số 6, 7, 8, 9, 10 (4 tiết)", "YCCĐ": "Đếm, đọc, viết số đến 10."},
                {"Chủ đề": "1. Các số 0-10", "Bài học": "Bài 3: Nhiều hơn, ít hơn, bằng nhau (2 tiết)", "YCCĐ": "So sánh số lượng."},
                {"Chủ đề": "1. Các số 0-10", "Bài học": "Bài 4: So sánh số (2 tiết)", "YCCĐ": "Dấu >, <, =."},
                {"Chủ đề": "1. Các số 0-10", "Bài học": "Bài 5: Mấy và mấy (2 tiết)", "YCCĐ": "Cấu tạo số (tách/gộp)."},
                {"Chủ đề": "2. Hình phẳng", "Bài học": "Bài 7: Hình vuông, tròn, tam giác (3 tiết)", "YCCĐ": "Nhận dạng hình phẳng."},
                {"Chủ đề": "3. Phép cộng trừ PV 10", "Bài học": "Bài 8: Phép cộng trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện cộng, viết phép tính."},
                {"Chủ đề": "3. Phép cộng trừ PV 10", "Bài học": "Bài 9: Phép trừ trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện trừ, viết phép tính."},
                {"Chủ đề": "4. Khối hình", "Bài học": "Bài 14: Khối lập phương, khối hộp chữ nhật (2 tiết)", "YCCĐ": "Nhận dạng khối hình."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Số đến 100", "Bài học": "Bài 21: Số có hai chữ số (3 tiết)", "YCCĐ": "Đọc, viết, cấu tạo số 2 chữ số."},
                {"Chủ đề": "5. Số đến 100", "Bài học": "Bài 23: Bảng các số 1-100 (2 tiết)", "YCCĐ": "Thứ tự số, số liền trước/sau."},
                {"Chủ đề": "6. Cộng trừ PV 100", "Bài học": "Bài 29: Phép cộng số có 2 chữ số (2 tiết)", "YCCĐ": "Cộng không nhớ."},
                {"Chủ đề": "6. Cộng trừ PV 100", "Bài học": "Bài 32: Phép trừ số có 2 chữ số (2 tiết)", "YCCĐ": "Trừ không nhớ."},
                {"Chủ đề": "7. Thời gian", "Bài học": "Bài 35: Các ngày trong tuần (1 tiết)", "YCCĐ": "Xem lịch tuần."},
                {"Chủ đề": "7. Thời gian", "Bài học": "Bài 36: Xem giờ đúng (2 tiết)", "YCCĐ": "Xem đồng hồ."},
                {"Chủ đề": "8. Ôn tập", "Bài học": "Bài 38: Ôn tập cuối năm (4 tiết)", "YCCĐ": "Tổng hợp kiến thức."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Làm quen", "Bài học": "Bài 1: A a (2 tiết)", "YCCĐ": "Nhận biết âm a, chữ a."},
                {"Chủ đề": "Làm quen", "Bài học": "Bài 2: B b, dấu huyền (2 tiết)", "YCCĐ": "Đọc âm b, thanh huyền."},
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

    # =================================================================================
    # KHỐI LỚP 2 (KNTT)
    # =================================================================================
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

    # =================================================================================
    # KHỐI LỚP 3
    # =================================================================================
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
        "Tin học": { # Cùng Khám Phá
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
        "Công nghệ": { # KNTT - ĐẦY ĐỦ
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

    # =================================================================================
    # KHỐI LỚP 4
    # =================================================================================
    "Lớp 4": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Số tự nhiên", "Bài học": "Bài 5: Dãy số tự nhiên (1 tiết)", "YCCĐ": "Đặc điểm dãy số tự nhiên."},
                {"Chủ đề": "Góc", "Bài học": "Bài 10: Góc nhọn, tù, bẹt (2 tiết)", "YCCĐ": "Phân biệt góc."},
                {"Chủ đề": "Phép tính", "Bài học": "Bài 25: Phép chia số có 2 chữ số (3 tiết)", "YCCĐ": "Chia số lớn."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phân số", "Bài học": "Bài 40: Rút gọn phân số (2 tiết)", "YCCĐ": "Rút gọn phân số."},
                {"Chủ đề": "Phân số", "Bài học": "Bài 55: Phép cộng phân số (2 tiết)", "YCCĐ": "Cộng khác mẫu."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 60: Hình bình hành (1 tiết)", "YCCĐ": "Đặc điểm hình bình hành."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Điều ước của vua Mi-đát (2 tiết)", "YCCĐ": "Bài học về lòng tham."},
                {"Chủ đề": "Tuổi nhỏ chí lớn", "Bài học": "Đọc: Văn hay chữ tốt (2 tiết)", "YCCĐ": "Sự khổ luyện."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Sầu riêng (2 tiết)", "YCCĐ": "Vẻ đẹp trái cây."},
                {"Chủ đề": "Khám phá", "Bài học": "Đọc: Đường đi Sa Pa (2 tiết)", "YCCĐ": "Cảnh đẹp Sa Pa."}
            ]
        },
        "Khoa học": { # KNTT - ĐẦY ĐỦ
            "Học kỳ I": [
                {"Chủ đề": "Chất", "Bài học": "Bài 1: Tính chất của nước (2 tiết)", "YCCĐ": "Không màu, không mùi, hòa tan."},
                {"Chủ đề": "Chất", "Bài học": "Bài 2: Sự chuyển thể của nước (2 tiết)", "YCCĐ": "Đông đặc, nóng chảy, bay hơi."},
                {"Chủ đề": "Chất", "Bài học": "Bài 3: Vòng tuần hoàn của nước (2 tiết)", "YCCĐ": "Vẽ sơ đồ vòng tuần hoàn."},
                {"Chủ đề": "Chất", "Bài học": "Bài 4: Sự ô nhiễm và bảo vệ nguồn nước (2 tiết)", "YCCĐ": "Nguyên nhân ô nhiễm, cách bảo vệ."},
                {"Chủ đề": "Chất", "Bài học": "Bài 5: Không khí (2 tiết)", "YCCĐ": "Thành phần không khí, vai trò ô-xi."},
                {"Chủ đề": "Năng lượng", "Bài học": "Bài 8: Ánh sáng và bóng tối (2 tiết)", "YCCĐ": "Vật phát sáng, vật cản sáng."},
                {"Chủ đề": "Năng lượng", "Bài học": "Bài 10: Âm thanh (2 tiết)", "YCCĐ": "Nguồn phát âm, sự lan truyền."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thực vật", "Bài học": "Bài 16: Nhu cầu sống của thực vật (2 tiết)", "YCCĐ": "Cần nước, ánh sáng, không khí."},
                {"Chủ đề": "Động vật", "Bài học": "Bài 18: Sự trao đổi chất ở động vật (2 tiết)", "YCCĐ": "Lấy vào và thải ra."},
                {"Chủ đề": "Chuỗi thức ăn", "Bài học": "Bài 20: Chuỗi thức ăn trong tự nhiên (2 tiết)", "YCCĐ": "Mối quan hệ thức ăn."},
                {"Chủ đề": "Nấm", "Bài học": "Bài 23: Các loại nấm (2 tiết)", "YCCĐ": "Nấm ăn và nấm độc."},
                {"Chủ đề": "Dinh dưỡng", "Bài học": "Bài 26: Các nhóm chất dinh dưỡng (2 tiết)", "YCCĐ": "4 nhóm chất dinh dưỡng."}
            ]
        },
        "Lịch sử và Địa lí": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Địa phương", "Bài học": "Bài 1: Làm quen bản đồ (2 tiết)", "YCCĐ": "Đọc bản đồ."},
                {"Chủ đề": "Trung du Bắc Bộ", "Bài học": "Bài 3: Thiên nhiên Trung du (2 tiết)", "YCCĐ": "Đồi bát úp."},
                {"Chủ đề": "Đồng bằng Bắc Bộ", "Bài học": "Bài 8: Sông Hồng (2 tiết)", "YCCĐ": "Vai trò sông Hồng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Duyên hải", "Bài học": "Bài 15: Biển đảo Việt Nam (2 tiết)", "YCCĐ": "Chủ quyền biển đảo."},
                {"Chủ đề": "Tây Nguyên", "Bài học": "Bài 20: Văn hóa Cồng chiêng (2 tiết)", "YCCĐ": "Di sản văn hóa."}
            ]
        },
        "Tin học": { # Cùng Khám Phá
            "Học kỳ I": [
                {"Chủ đề": "Phần cứng", "Bài học": "Bài 1: Thiết bị phần cứng (1 tiết)", "YCCĐ": "Thiết bị vào/ra."},
                {"Chủ đề": "Mạng", "Bài học": "Bài 3: Thông tin trên web (2 tiết)", "YCCĐ": "Siêu văn bản."},
                {"Chủ đề": "Đạo đức", "Bài học": "Bài 6: Bản quyền số (1 tiết)", "YCCĐ": "Tôn trọng bản quyền."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Scratch", "Bài học": "Bài 8: Làm quen Scratch (2 tiết)", "YCCĐ": "Giao diện Scratch."},
                {"Chủ đề": "Trình chiếu", "Bài học": "Bài 13: Tạo bài trình chiếu (2 tiết)", "YCCĐ": "Tạo slide cơ bản."}
            ]
        },
        "Công nghệ": { # KNTT - ĐẦY ĐỦ
            "Học kỳ I": [
                {"Chủ đề": "Hoa và cây cảnh", "Bài học": "Bài 1: Lợi ích của hoa và cây cảnh (2 tiết)", "YCCĐ": "Nêu lợi ích trang trí, làm đẹp."},
                {"Chủ đề": "Hoa và cây cảnh", "Bài học": "Bài 2: Các loại hoa phổ biến (2 tiết)", "YCCĐ": "Nhận biết hoa hồng, cúc, đào."},
                {"Chủ đề": "Hoa và cây cảnh", "Bài học": "Bài 3: Các loại cây cảnh phổ biến (2 tiết)", "YCCĐ": "Nhận biết cây lưỡi hổ, kim tiền."},
                {"Chủ đề": "Trồng hoa", "Bài học": "Bài 4: Gieo hạt và trồng cây con (3 tiết)", "YCCĐ": "Thực hiện gieo hạt trong chậu."},
                {"Chủ đề": "Trồng hoa", "Bài học": "Bài 5: Trồng và chăm sóc hoa trong chậu (3 tiết)", "YCCĐ": "Tưới nước, bón phân cho hoa."},
                {"Chủ đề": "Trồng hoa", "Bài học": "Bài 6: Chậu và giá thể trồng hoa (2 tiết)", "YCCĐ": "Chọn chậu và đất trồng phù hợp."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lắp ghép kĩ thuật", "Bài học": "Bài 7: Bộ lắp ghép mô hình kĩ thuật (2 tiết)", "YCCĐ": "Nhận biết các chi tiết trong bộ lắp ghép."},
                {"Chủ đề": "Lắp ghép kĩ thuật", "Bài học": "Bài 8: Lắp ghép mô hình cái đu (2 tiết)", "YCCĐ": "Lắp được cái đu đúng quy trình."},
                {"Chủ đề": "Lắp ghép kĩ thuật", "Bài học": "Bài 9: Lắp ghép mô hình rô-bốt (2 tiết)", "YCCĐ": "Lắp được rô-bốt đơn giản."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 5
    # =================================================================================
    "Lớp 5": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Số thập phân", "Bài học": "Bài 8: Số thập phân (3 tiết)", "YCCĐ": "Đọc viết số thập phân."},
                {"Chủ đề": "Phép tính", "Bài học": "Bài 15: Cộng trừ số thập phân (3 tiết)", "YCCĐ": "Tính đúng cộng trừ."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 22: Hình tam giác (2 tiết)", "YCCĐ": "Diện tích tam giác."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Tỉ số %", "Bài học": "Bài 45: Tỉ số phần trăm (2 tiết)", "YCCĐ": "Khái niệm %."},
                {"Chủ đề": "Thể tích", "Bài học": "Bài 50: Hình lập phương (2 tiết)", "YCCĐ": "Thể tích hình lập phương."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Việt Nam gấm vóc", "Bài học": "Đọc: Thư gửi các học sinh (2 tiết)", "YCCĐ": "Tình cảm Bác Hồ."},
                {"Chủ đề": "Môi trường", "Bài học": "Đọc: Chuyện một khu vườn nhỏ (2 tiết)", "YCCĐ": "Yêu thiên nhiên."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Người công dân", "Bài học": "Đọc: Người công dân số Một (2 tiết)", "YCCĐ": "Lòng yêu nước."},
                {"Chủ đề": "Đất nước đổi mới", "Bài học": "Đọc: Trí dũng song toàn (2 tiết)", "YCCĐ": "Sự mưu trí."}
            ]
        },
        "Khoa học": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Chất", "Bài học": "Bài 1: Đất và bảo vệ đất (2 tiết)", "YCCĐ": "Thành phần của đất."},
                {"Chủ đề": "Chất", "Bài học": "Bài 5: Sự biến đổi hóa học (2 tiết)", "YCCĐ": "Biến đổi lí/hóa."},
                {"Chủ đề": "Năng lượng", "Bài học": "Bài 8: Năng lượng mặt trời (2 tiết)", "YCCĐ": "Ứng dụng NL mặt trời."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Điện", "Bài học": "Bài 12: Sử dụng năng lượng điện (2 tiết)", "YCCĐ": "An toàn điện."},
                {"Chủ đề": "Sinh sản", "Bài học": "Bài 19: Sự sinh sản động vật (2 tiết)", "YCCĐ": "Đẻ trứng/đẻ con."}
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "Dựng nước", "Bài học": "Bài 1: Văn Lang - Âu Lạc (2 tiết)", "YCCĐ": "Nguồn gốc dân tộc."},
                {"Chủ đề": "Chống Pháp", "Bài học": "Bài 8: Phong trào Cần Vương (2 tiết)", "YCCĐ": "Phan Đình Phùng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Châu Á", "Bài học": "Bài 19: Châu Á (2 tiết)", "YCCĐ": "Địa lý Châu Á."},
                {"Chủ đề": "Thế giới", "Bài học": "Bài 18: Các châu lục (2 tiết)", "YCCĐ": "Vị trí các châu lục."}
            ]
        },
        "Tin học": { # Cùng Khám Phá
            "Học kỳ I": [
                {"Chủ đề": "Quản lý tệp", "Bài học": "Bài 1: Cây thư mục (1 tiết)", "YCCĐ": "Quản lý thư mục."},
                {"Chủ đề": "Email", "Bài học": "Bài 3: Thư điện tử (2 tiết)", "YCCĐ": "Gửi nhận email."},
                {"Chủ đề": "Bản quyền", "Bài học": "Bài 5: Bản quyền số (1 tiết)", "YCCĐ": "Tôn trọng bản quyền."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Scratch", "Bài học": "Bài 9: Biến nhớ (3 tiết)", "YCCĐ": "Sử dụng biến."},
                {"Chủ đề": "Scratch", "Bài học": "Bài 12: Cấu trúc rẽ nhánh (3 tiết)", "YCCĐ": "Câu lệnh điều kiện."}
            ]
        },
        "Công nghệ": { # KNTT - ĐẦY ĐỦ
            "Học kỳ I": [
                {"Chủ đề": "Công nghệ đời sống", "Bài học": "Bài 1: Công nghệ trong đời sống (2 tiết)", "YCCĐ": "Vai trò của công nghệ."},
                {"Chủ đề": "Sáng chế", "Bài học": "Bài 2: Sáng chế kĩ thuật (2 tiết)", "YCCĐ": "Quy trình sáng chế."},
                {"Chủ đề": "Thiết kế", "Bài học": "Bài 3: Tìm hiểu về thiết kế (2 tiết)", "YCCĐ": "Ý tưởng và phác thảo."},
                {"Chủ đề": "Thiết kế", "Bài học": "Bài 4: Thiết kế sản phẩm đơn giản (3 tiết)", "YCCĐ": "Thiết kế đồ chơi/đồ dùng."},
                {"Chủ đề": "Thiết kế", "Bài học": "Bài 5: Dự án thiết kế của em (3 tiết)", "YCCĐ": "Thực hiện dự án nhóm."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Sử dụng điện thoại", "Bài học": "Bài 6: Sử dụng điện thoại (2 tiết)", "YCCĐ": "Sử dụng điện thoại đúng cách, văn minh."},
                {"Chủ đề": "Sử dụng tủ lạnh", "Bài học": "Bài 7: Sử dụng tủ lạnh (2 tiết)", "YCCĐ": "Bảo quản thực phẩm an toàn."},
                {"Chủ đề": "Lắp ráp mô hình", "Bài học": "Bài 8: Lắp ráp mô hình xe điện chạy pin (4 tiết)", "YCCĐ": "Lắp ráp và vận hành mô hình xe."}
            ]
        }
    }
}

# --- 4. CÁC HÀM XỬ LÝ ---

def find_working_model(api_key):
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
