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

# --- 3. CƠ SỞ DỮ LIỆU CHƯƠNG TRÌNH HỌC (DATA FULL) ---
# KNTT: Kết nối tri thức | CKP: Cùng Khám Phá (Tin học) | Tiếng Việt: Tổng hợp

SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

CURRICULUM_DB = {
    # =================================================================================
    # KHỐI LỚP 1
    # =================================================================================
    "Lớp 1": {
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Các số đến 10", "Bài học": "Bài 1: Các số 0, 1, 2, 3, 4, 5 (3 tiết)", "YCCĐ": "Đếm, đọc, viết số trong phạm vi 5."},
                {"Chủ đề": "1. Các số đến 10", "Bài học": "Bài 2: Các số 6, 7, 8, 9, 10 (4 tiết)", "YCCĐ": "Đếm, đọc, viết số đến 10."},
                {"Chủ đề": "1. Các số đến 10", "Bài học": "Bài 3: Nhiều hơn, ít hơn, bằng nhau (2 tiết)", "YCCĐ": "So sánh số lượng."},
                {"Chủ đề": "1. Các số đến 10", "Bài học": "Bài 4: So sánh số (2 tiết)", "YCCĐ": "Sử dụng dấu >, <, =."},
                {"Chủ đề": "1. Các số đến 10", "Bài học": "Bài 5: Mấy và mấy (2 tiết)", "YCCĐ": "Tách và gộp số."},
                {"Chủ đề": "2. Hình phẳng", "Bài học": "Bài 7: Hình vuông, tròn, tam giác (2 tiết)", "YCCĐ": "Nhận dạng hình phẳng."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 8: Phép cộng trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép cộng."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 9: Phép trừ trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép trừ."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 10: Luyện tập chung (3 tiết)", "YCCĐ": "Vận dụng cộng trừ giải toán."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Các số PV 100", "Bài học": "Bài 21: Số có hai chữ số (3 tiết)", "YCCĐ": "Đọc viết số, cấu tạo số."},
                {"Chủ đề": "4. Các số PV 100", "Bài học": "Bài 23: Bảng các số 1-100 (2 tiết)", "YCCĐ": "Thứ tự số, so sánh số."},
                {"Chủ đề": "5. Cộng trừ PV 100", "Bài học": "Bài 29: Phép cộng số có 2 chữ số (2 tiết)", "YCCĐ": "Cộng không nhớ."},
                {"Chủ đề": "5. Cộng trừ PV 100", "Bài học": "Bài 32: Phép trừ số có 2 chữ số (2 tiết)", "YCCĐ": "Trừ không nhớ."},
                {"Chủ đề": "6. Thời gian", "Bài học": "Bài 35: Các ngày trong tuần (1 tiết)", "YCCĐ": "Xem lịch, thời khóa biểu."},
                {"Chủ đề": "6. Thời gian", "Bài học": "Bài 36: Xem giờ đúng (2 tiết)", "YCCĐ": "Xem đồng hồ giờ đúng."},
                {"Chủ đề": "7. Ôn tập", "Bài học": "Bài 38: Ôn tập cuối năm (4 tiết)", "YCCĐ": "Tổng hợp kiến thức."}
            ]
        },
        "Tiếng Việt": { # Tổng hợp
            "Học kỳ I": [
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 1: A a (2 tiết)", "YCCĐ": "Nhận biết âm a, chữ a."},
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 2: B b, dấu huyền (2 tiết)", "YCCĐ": "Đọc âm b, thanh huyền."},
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 3: C c, dấu sắc (2 tiết)", "YCCĐ": "Đọc âm c, thanh sắc."},
                {"Chủ đề": "Học vần", "Bài học": "Bài: an, at (2 tiết)", "YCCĐ": "Đọc viết vần an, at."},
                {"Chủ đề": "Học vần", "Bài học": "Bài: on, ot (2 tiết)", "YCCĐ": "Đọc viết vần on, ot."},
                {"Chủ đề": "Học vần", "Bài học": "Bài: ay, âp (2 tiết)", "YCCĐ": "Đọc viết vần ay, âp."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Gia đình", "Bài học": "Bài đọc: Ngôi nhà (KNTT)", "YCCĐ": "Đọc hiểu bài thơ về gia đình."},
                {"Chủ đề": "Gia đình", "Bài học": "Bài đọc: Làm anh (Cánh Diều)", "YCCĐ": "Trách nhiệm của anh chị em."},
                {"Chủ đề": "Thiên nhiên", "Bài học": "Bài đọc: Hoa kết trái (CTST)", "YCCĐ": "Nhận biết các loại hoa quả."},
                {"Chủ đề": "Nhà trường", "Bài học": "Bài đọc: Trường em (KNTT)", "YCCĐ": "Tình cảm với trường lớp."},
                {"Chủ đề": "Bác Hồ", "Bài học": "Bài đọc: Bác Hồ và thiếu nhi (Cánh Diều)", "YCCĐ": "Tình cảm Bác Hồ."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 2
    # =================================================================================
    "Lớp 2": {
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập", "Bài học": "Bài 1: Ôn tập các số đến 100", "YCCĐ": "Củng cố số học lớp 1."},
                {"Chủ đề": "2. Phép cộng trừ qua 10", "Bài học": "Bài 6: Bảng cộng qua 10 (3 tiết)", "YCCĐ": "Thực hiện cộng có nhớ."},
                {"Chủ đề": "2. Phép cộng trừ qua 10", "Bài học": "Bài 11: Bảng trừ qua 10 (3 tiết)", "YCCĐ": "Thực hiện trừ có nhớ."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 18: Đường thẳng, đường cong", "YCCĐ": "Nhận biết các loại đường."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 19: Điểm, đoạn thẳng", "YCCĐ": "Đo độ dài đoạn thẳng."},
                {"Chủ đề": "4. Đo lường", "Bài học": "Bài 22: Ngày, tháng", "YCCĐ": "Xem lịch."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Phép nhân chia", "Bài học": "Bài 40: Bảng nhân 2", "YCCĐ": "Thuộc bảng nhân 2."},
                {"Chủ đề": "5. Phép nhân chia", "Bài học": "Bài 41: Bảng nhân 5", "YCCĐ": "Thuộc bảng nhân 5."},
                {"Chủ đề": "5. Phép nhân chia", "Bài học": "Bài 45: Bảng chia 2", "YCCĐ": "Thuộc bảng chia 2."},
                {"Chủ đề": "6. Số đến 1000", "Bài học": "Bài 48: Đơn vị, chục, trăm, nghìn", "YCCĐ": "Cấu tạo số 3 chữ số."},
                {"Chủ đề": "6. Số đến 1000", "Bài học": "Bài 59: Phép cộng có nhớ PV 1000", "YCCĐ": "Cộng số có 3 chữ số."},
                {"Chủ đề": "7. Ôn tập", "Bài học": "Bài 70: Ôn tập chung", "YCCĐ": "Tổng hợp kiến thức."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Tôi là học sinh lớp 2 (KNTT)", "YCCĐ": "Tâm trạng ngày khai trường."},
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Ngày hôm qua đâu rồi? (KNTT)", "YCCĐ": "Giá trị thời gian."},
                {"Chủ đề": "Bạn bè", "Bài học": "Đọc: Út Tin (CTST)", "YCCĐ": "Đặc điểm nhân vật."},
                {"Chủ đề": "Thầy cô", "Bài học": "Đọc: Cô giáo lớp em (Cánh Diều)", "YCCĐ": "Tình cảm thầy trò."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Mùa nước nổi (CTST)", "YCCĐ": "Vẻ đẹp miền Tây."},
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Đường đến trường (KNTT)", "YCCĐ": "Cảnh vật đường đi học."},
                {"Chủ đề": "Bốn mùa", "Bài học": "Đọc: Chuyện bốn mùa (KNTT)", "YCCĐ": "Đặc điểm các mùa."},
                {"Chủ đề": "Bác Hồ", "Bài học": "Đọc: Ai ngoan sẽ được thưởng (CTST)", "YCCĐ": "Đức tính trung thực."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 3
    # =================================================================================
    "Lớp 3": {
        "Tin học": { # Sách: Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 1: Các thành phần của máy tính (1 tiết)", "YCCĐ": "Nhận diện thân máy, màn hình, phím, chuột."},
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 2: Chức năng các bộ phận máy tính (1 tiết)", "YCCĐ": "Biết chức năng thiết bị vào/ra."},
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 3: Làm quen với chuột máy tính (2 tiết)", "YCCĐ": "Thao tác: di chuyển, nháy, kéo thả."},
                {"Chủ đề": "A. Máy tính và em", "Bài học": "Bài 4: Làm quen với bàn phím (2 tiết)", "YCCĐ": "Khu vực phím, đặt tay đúng."},
                {"Chủ đề": "B. Mạng máy tính", "Bài học": "Bài 5: Xem tin tức, giải trí trên Internet (2 tiết)", "YCCĐ": "Truy cập web, xem thông tin."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "C. Tổ chức lưu trữ", "Bài học": "Bài 6: Sắp xếp để tìm kiếm (1 tiết)", "YCCĐ": "Sự cần thiết của sắp xếp dữ liệu."},
                {"Chủ đề": "C. Tổ chức lưu trữ", "Bài học": "Bài 7: Sơ đồ hình cây (1 tiết)", "YCCĐ": "Cấu trúc thư mục."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 8: Làm quen soạn thảo văn bản (2 tiết)", "YCCĐ": "Gõ kí tự, dấu tiếng Việt."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 9: Soạn thảo văn bản đơn giản (2 tiết)", "YCCĐ": "Gõ đoạn văn, sửa lỗi."},
                {"Chủ đề": "E. Ứng dụng tin học", "Bài học": "Bài 11: Vẽ tranh đơn giản (2 tiết)", "YCCĐ": "Sử dụng công cụ vẽ cơ bản."},
                {"Chủ đề": "F. Giải quyết vấn đề", "Bài học": "Bài 13: Luyện tập sử dụng chuột (2 tiết)", "YCCĐ": "Thành thạo chuột qua trò chơi."}
            ]
        },
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Bảng nhân chia", "Bài học": "Bài 5: Bảng nhân 6", "YCCĐ": "Thuộc bảng nhân 6."},
                {"Chủ đề": "1. Bảng nhân chia", "Bài học": "Bài 9: Bảng nhân 8", "YCCĐ": "Thuộc bảng nhân 8."},
                {"Chủ đề": "2. Góc và Hình", "Bài học": "Bài 15: Góc vuông, góc không vuông", "YCCĐ": "Dùng ê-ke kiểm tra góc."},
                {"Chủ đề": "3. Phép chia số lớn", "Bài học": "Bài 38: Chia số có 3 chữ số cho số có 1 chữ số", "YCCĐ": "Chia hết và có dư."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Số đến 100.000", "Bài học": "Bài 45: Các số trong phạm vi 100000", "YCCĐ": "Đọc viết số 5 chữ số."},
                {"Chủ đề": "5. Diện tích", "Bài học": "Bài 51: Diện tích của một hình", "YCCĐ": "Khái niệm diện tích."},
                {"Chủ đề": "5. Diện tích", "Bài học": "Bài 52: Diện tích hình chữ nhật", "YCCĐ": "Công thức S = a x b."},
                {"Chủ đề": "6. Cộng trừ PV 100.000", "Bài học": "Bài 58: Phép cộng trong phạm vi 100000", "YCCĐ": "Cộng có nhớ."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Chiếc áo mùa thu (CTST)", "YCCĐ": "Biện pháp nhân hóa."},
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Ngày khai trường (KNTT)", "YCCĐ": "Niềm vui tựu trường."},
                {"Chủ đề": "Cộng đồng", "Bài học": "Đọc: Lớp học trên đường (Cánh Diều)", "YCCĐ": "Nghị lực học tập."},
                {"Chủ đề": "Sáng tạo", "Bài học": "Đọc: Ông tổ nghề thêu (Cánh Diều)", "YCCĐ": "Ca ngợi trí thông minh."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lễ hội", "Bài học": "Đọc: Hội đua voi ở Tây Nguyên (KNTT)", "YCCĐ": "Văn hóa Tây Nguyên."},
                {"Chủ đề": "Lễ hội", "Bài học": "Đọc: Đua ghe ngo (CTST)", "YCCĐ": "Văn hóa Khmer."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [{"Chủ đề": "Tự nhiên và CN", "Bài học": "Bài 1: Tự nhiên và Công nghệ", "YCCĐ": "Phân biệt đối tượng."}, {"Chủ đề": "Đồ dùng điện", "Bài học": "Bài 2: Sử dụng đèn học", "YCCĐ": "An toàn điện."}],
            "Học kỳ II": [{"Chủ đề": "Thủ công", "Bài học": "Bài 7: Làm đồ dùng học tập", "YCCĐ": "Làm ống bút."}, {"Chủ đề": "Thủ công", "Bài học": "Bài 9: Làm biển báo giao thông", "YCCĐ": "Làm biển báo."}]
        }
    },

    # =================================================================================
    # KHỐI LỚP 4
    # =================================================================================
    "Lớp 4": {
        "Khoa học": { # KNTT - ĐẦY ĐỦ CÁC CHỦ ĐỀ
            "Học kỳ I": [
                {"Chủ đề": "1. Chất", "Bài học": "Bài 1: Tính chất của nước (2 tiết)", "YCCĐ": "Nêu tính chất không màu, không mùi, hòa tan."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 2: Sự chuyển thể của nước (2 tiết)", "YCCĐ": "Phân biệt lỏng, rắn, hơi; sự bay hơi/ngưng tụ."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 3: Vòng tuần hoàn của nước (2 tiết)", "YCCĐ": "Vẽ sơ đồ vòng tuần hoàn nước trong tự nhiên."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 5: Không khí (2 tiết)", "YCCĐ": "Nêu tính chất và vai trò của không khí."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 8: Ánh sáng và bóng tối (2 tiết)", "YCCĐ": "Vật phát sáng, vật được chiếu sáng; giải thích bóng tối."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 10: Âm thanh (2 tiết)", "YCCĐ": "Sự lan truyền âm thanh; vật phát ra âm thanh."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 11: Nhiệt độ và nhiệt kế (2 tiết)", "YCCĐ": "Cách đo nhiệt độ cơ thể và không khí."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 16: Nhu cầu sống của thực vật (2 tiết)", "YCCĐ": "Cần nước, ánh sáng, không khí, chất khoáng."},
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 18: Sự trao đổi chất ở động vật (2 tiết)", "YCCĐ": "Sơ đồ trao đổi chất ở động vật."},
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 20: Chuỗi thức ăn (2 tiết)", "YCCĐ": "Vẽ sơ đồ chuỗi thức ăn trong tự nhiên."},
                {"Chủ đề": "4. Nấm", "Bài học": "Bài 23: Các loại nấm (2 tiết)", "YCCĐ": "Phân biệt nấm ăn và nấm độc; vai trò của nấm."},
                {"Chủ đề": "5. Con người và sức khỏe", "Bài học": "Bài 26: Các nhóm chất dinh dưỡng (2 tiết)", "YCCĐ": "Vai trò của bột đường, đạm, béo, vitamin."}
            ]
        },
        "Lịch sử và Địa lí": { # KNTT - ĐẦY ĐỦ CÁC CHỦ ĐỀ
            "Học kỳ I": [
                {"Chủ đề": "1. Địa phương em", "Bài học": "Bài 1: Làm quen với bản đồ (2 tiết)", "YCCĐ": "Nhận biết các kí hiệu bản đồ, phương hướng."},
                {"Chủ đề": "2. Trung du và MN Bắc Bộ", "Bài học": "Bài 3: Thiên nhiên vùng Trung du (2 tiết)", "YCCĐ": "Mô tả địa hình đồi bát úp, khí hậu, ruộng bậc thang."},
                {"Chủ đề": "2. Trung du và MN Bắc Bộ", "Bài học": "Bài 5: Đền Hùng và lễ giỗ tổ (2 tiết)", "YCCĐ": "Kể lại truyền thuyết Hùng Vương; ý nghĩa lễ hội."},
                {"Chủ đề": "3. Đồng bằng Bắc Bộ", "Bài học": "Bài 8: Sông Hồng và văn minh lúa nước (2 tiết)", "YCCĐ": "Vai trò sông Hồng; hệ thống đê điều."},
                {"Chủ đề": "3. Đồng bằng Bắc Bộ", "Bài học": "Bài 10: Thăng Long - Hà Nội (2 tiết)", "YCCĐ": "Các tên gọi của Hà Nội; di tích Văn Miếu."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Duyên hải Miền Trung", "Bài học": "Bài 15: Biển đảo Việt Nam (2 tiết)", "YCCĐ": "Xác định Hoàng Sa, Trường Sa; vai trò kinh tế biển."},
                {"Chủ đề": "4. Duyên hải Miền Trung", "Bài học": "Bài 16: Phố cổ Hội An (2 tiết)", "YCCĐ": "Mô tả kiến trúc, di sản văn hóa Hội An."},
                {"Chủ đề": "5. Tây Nguyên", "Bài học": "Bài 18: Thiên nhiên Tây Nguyên (2 tiết)", "YCCĐ": "Đất đỏ bazan, các cao nguyên xếp tầng."},
                {"Chủ đề": "5. Tây Nguyên", "Bài học": "Bài 20: Văn hóa Cồng chiêng (2 tiết)", "YCCĐ": "Giá trị di sản văn hóa phi vật thể."}
            ]
        },
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
                {"Chủ đề": "1. Số tự nhiên", "Bài học": "Bài 6: Viết số tự nhiên hệ thập phân", "YCCĐ": "Giá trị theo vị trí."},
                {"Chủ đề": "2. Góc và Đơn vị", "Bài học": "Bài 10: Góc nhọn, tù, bẹt", "YCCĐ": "Phân biệt các loại góc."},
                {"Chủ đề": "2. Góc và Đơn vị", "Bài học": "Bài 11: Đơn vị đo góc. Độ", "YCCĐ": "Dùng thước đo góc."},
                {"Chủ đề": "3. Phép tính", "Bài học": "Bài 25: Phép chia cho số có 2 chữ số", "YCCĐ": "Chia số nhiều chữ số."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Phân số", "Bài học": "Bài 40: Rút gọn phân số", "YCCĐ": "Chia tử mẫu cho cùng số."},
                {"Chủ đề": "4. Phân số", "Bài học": "Bài 41: Quy đồng mẫu số", "YCCĐ": "Quy đồng mẫu số đơn giản."},
                {"Chủ đề": "5. Phép tính phân số", "Bài học": "Bài 55: Phép cộng phân số", "YCCĐ": "Cộng phân số khác mẫu."},
                {"Chủ đề": "5. Phép tính phân số", "Bài học": "Bài 57: Phép nhân phân số", "YCCĐ": "Nhân tử với tử, mẫu với mẫu."},
                {"Chủ đề": "6. Hình học", "Bài học": "Bài 60: Hình bình hành", "YCCĐ": "Cạnh đối song song, bằng nhau."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Điều ước của vua Mi-đát (KNTT)", "YCCĐ": "Hạnh phúc từ điều giản dị."},
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Tiếng nói của cỏ cây (KNTT)", "YCCĐ": "Vẻ đẹp của thiên nhiên."},
                {"Chủ đề": "Tuổi nhỏ chí lớn", "Bài học": "Đọc: Tuổi ngựa (CTST)", "YCCĐ": "Khát vọng đi xa."},
                {"Chủ đề": "Tuổi nhỏ chí lớn", "Bài học": "Đọc: Văn hay chữ tốt (Cánh Diều)", "YCCĐ": "Tinh thần khổ luyện."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Sầu riêng (KNTT)", "YCCĐ": "Hương vị trái cây miền Nam."},
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Chợ Tết (CTST)", "YCCĐ": "Bức tranh chợ Tết."},
                {"Chủ đề": "Khám phá thế giới", "Bài học": "Đọc: Đường đi Sa Pa (KNTT)", "YCCĐ": "Vẻ đẹp Sa Pa."},
                {"Chủ đề": "Khám phá thế giới", "Bài học": "Đọc: Hơn một ngàn ngày vòng quanh trái đất", "YCCĐ": "Hành trình Ma-zen-lan."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [{"Chủ đề": "Hoa cây cảnh", "Bài học": "Bài 2: Các loại hoa phổ biến", "YCCĐ": "Nhận biết hoa hồng, cúc, đào."}, {"Chủ đề": "Hoa cây cảnh", "Bài học": "Bài 3: Các loại cây cảnh", "YCCĐ": "Nhận biết cây cảnh thông dụng."}],
            "Học kỳ II": [{"Chủ đề": "Lắp ghép", "Bài học": "Bài 6: Lắp ghép mô hình xe", "YCCĐ": "Lắp xe đẩy/nôi."}, {"Chủ đề": "Đồ chơi", "Bài học": "Bài 9: Làm chong chóng", "YCCĐ": "Làm chong chóng giấy."}]
        }
    },

    # =================================================================================
    # KHỐI LỚP 5
    # =================================================================================
    "Lớp 5": {
        "Khoa học": { # KNTT - ĐẦY ĐỦ CÁC CHỦ ĐỀ
            "Học kỳ I": [
                {"Chủ đề": "1. Chất", "Bài học": "Bài 1: Đất và bảo vệ đất (2 tiết)", "YCCĐ": "Thành phần của đất; biện pháp bảo vệ đất."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 3: Hỗn hợp và dung dịch (2 tiết)", "YCCĐ": "Phân biệt hỗn hợp, dung dịch; tách chất."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 5: Sự biến đổi hóa học (2 tiết)", "YCCĐ": "Phân biệt biến đổi lí học và hóa học."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 8: Năng lượng mặt trời (2 tiết)", "YCCĐ": "Vai trò chiếu sáng, sưởi ấm; ứng dụng pin mặt trời."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 9: Năng lượng chất đốt (2 tiết)", "YCCĐ": "Các loại chất đốt; sử dụng an toàn, tiết kiệm."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 10: Năng lượng gió và nước chảy (2 tiết)", "YCCĐ": "Ứng dụng chạy thuyền buồm, thủy điện."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 12: Sử dụng năng lượng điện (2 tiết)", "YCCĐ": "Mạch điện đơn giản; vật dẫn/cách điện; an toàn điện."},
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 16: Sự sinh sản của thực vật (2 tiết)", "YCCĐ": "Thụ phấn, thụ tinh; cơ quan sinh sản."},
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 19: Sự sinh sản của động vật (2 tiết)", "YCCĐ": "Đẻ trứng và đẻ con; vòng đời của côn trùng."},
                {"Chủ đề": "4. Con người và sức khỏe", "Bài học": "Bài 22: Sự sinh sản ở người (2 tiết)", "YCCĐ": "Quá trình thụ tinh; sự phát triển của thai nhi."},
                {"Chủ đề": "4. Con người và sức khỏe", "Bài học": "Bài 25: Chăm sóc sức khỏe tuổi dậy thì (2 tiết)", "YCCĐ": "Vệ sinh cá nhân; phòng tránh xâm hại."}
            ]
        },
        "Lịch sử và Địa lí": { # KNTT - ĐẦY ĐỦ CÁC CHỦ ĐỀ
            "Học kỳ I": [
                {"Chủ đề": "1. Đất nước dựng xây", "Bài học": "Bài 1: Nước Văn Lang - Âu Lạc (2 tiết)", "YCCĐ": "Thời gian, địa điểm ra đời; đời sống vật chất/tinh thần."},
                {"Chủ đề": "1. Đất nước dựng xây", "Bài học": "Bài 4: Nhà Nguyễn (2 tiết)", "YCCĐ": "Sự thành lập; đóng góp về văn hóa, giáo dục."},
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 6: Khởi nghĩa Hai Bà Trưng (2 tiết)", "YCCĐ": "Nguyên nhân, diễn biến, ý nghĩa cuộc khởi nghĩa."},
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 8: Phong trào chống Pháp (2 tiết)", "YCCĐ": "Trương Định, Nguyễn Trung Trực; phong trào Cần Vương."},
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 10: Cách mạng tháng Tám 1945 (2 tiết)", "YCCĐ": "Sự kiện Bác Hồ đọc Tuyên ngôn Độc lập."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 12: Chiến dịch Điện Biên Phủ (3 tiết)", "YCCĐ": "Diễn biến 56 ngày đêm; ý nghĩa lịch sử."},
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 14: Chiến dịch Hồ Chí Minh (2 tiết)", "YCCĐ": "Giải phóng miền Nam; thống nhất đất nước."},
                {"Chủ đề": "3. Thế giới", "Bài học": "Bài 18: Các châu lục và đại dương (2 tiết)", "YCCĐ": "Vị trí 6 châu lục, 4 đại dương; đặc điểm nổi bật."},
                {"Chủ đề": "3. Thế giới", "Bài học": "Bài 19: Châu Á (2 tiết)", "YCCĐ": "Vị trí, diện tích, khí hậu, dân cư Châu Á."},
                {"Chủ đề": "3. Thế giới", "Bài học": "Bài 21: Các nước láng giềng (2 tiết)", "YCCĐ": "Lào, Campuchia, Trung Quốc (thủ đô, địa hình)."}
            ]
        },
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
