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

# --- 3. CƠ SỞ DỮ LIỆU CHƯƠNG TRÌNH HỌC (DATA CHI TIẾT) ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

CURRICULUM_DB = {
    # ========================== LỚP 1 ==========================
    "Lớp 1": {
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Các số đến 10", "Bài học": "Bài 1: Các số 0, 1, 2, 3, 4, 5 (3 tiết)", "YCCĐ": "Nhận biết, đọc, viết các số đến 5."},
                {"Chủ đề": "Các số đến 10", "Bài học": "Bài 2: Các số 6, 7, 8, 9, 10 (4 tiết)", "YCCĐ": "Nhận biết, đọc, viết các số đến 10."},
                {"Chủ đề": "Phép cộng, trừ phạm vi 10", "Bài học": "Bài 8: Phép cộng trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép cộng và vận dụng vào tình huống đơn giản."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 13: Hình tam giác, hình vuông, hình tròn (2 tiết)", "YCCĐ": "Nhận dạng đúng các hình phẳng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Các số đến 100", "Bài học": "Bài 21: Số có hai chữ số (3 tiết)", "YCCĐ": "Đọc, viết, phân tích cấu tạo số có hai chữ số."},
                {"Chủ đề": "Phép cộng, trừ phạm vi 100", "Bài học": "Bài 28: Phép cộng trừ không nhớ trong phạm vi 100 (4 tiết)", "YCCĐ": "Đặt tính và tính đúng."},
                {"Chủ đề": "Thời gian", "Bài học": "Bài 33: Xem đồng hồ, ngày tháng (2 tiết)", "YCCĐ": "Biết xem giờ đúng và lịch tờ."}
            ]
        },
        "Tiếng Việt": { # KNTT + CTST + Cánh Diều
            "Học kỳ I": [
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 1: A a (KNTT)", "YCCĐ": "Nhận biết và đọc đúng âm a."},
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 2: B b, dấu huyền (CTST)", "YCCĐ": "Đọc đúng âm b và thanh huyền."},
                {"Chủ đề": "Học vần", "Bài học": "Bài 35: an, at (Cánh Diều)", "YCCĐ": "Đọc trơn từ ngữ chứa vần an, at."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Gia đình", "Bài học": "Bài đọc: Ngôi nhà (KNTT)", "YCCĐ": "Đọc hiểu bài thơ về tình cảm gia đình."},
                {"Chủ đề": "Thiên nhiên", "Bài học": "Bài đọc: Hoa kết trái (CTST)", "YCCĐ": "Nhận biết các loài hoa quả qua bài thơ."},
                {"Chủ đề": "Nhà trường", "Bài học": "Bài đọc: Trường em (Cánh Diều)", "YCCĐ": "Hiểu tình cảm gắn bó với ngôi trường."}
            ]
        }
    },

    # ========================== LỚP 2 ==========================
    "Lớp 2": {
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Phép cộng, trừ có nhớ", "Bài học": "Bài 5: Phép cộng qua 10 (3 tiết)", "YCCĐ": "Thực hiện phép cộng có nhớ trong phạm vi 20."},
                {"Chủ đề": "Phép cộng, trừ có nhớ", "Bài học": "Bài 12: Bảng trừ (3 tiết)", "YCCĐ": "Vận dụng bảng trừ để tính nhẩm."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 18: Đường thẳng, đường cong (1 tiết)", "YCCĐ": "Nhận biết và vẽ được đường thẳng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phép nhân, chia", "Bài học": "Bài 40: Bảng nhân 2, Bảng nhân 5 (3 tiết)", "YCCĐ": "Thuộc bảng nhân và áp dụng tính toán."},
                {"Chủ đề": "Các số đến 1000", "Bài học": "Bài 48: Đơn vị, chục, trăm, nghìn (2 tiết)", "YCCĐ": "Nhận biết hàng và giá trị chữ số."}
            ]
        },
        "Tiếng Việt": { # Đa dạng bộ sách
            "Học kỳ I": [
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Tôi là học sinh lớp 2 (KNTT)", "YCCĐ": "Hiểu tâm trạng ngày khai trường."},
                {"Chủ đề": "Bạn bè", "Bài học": "Đọc: Út Tin (CTST)", "YCCĐ": "Nhận biết đặc điểm ngoại hình nhân vật."},
                {"Chủ đề": "Thầy cô", "Bài học": "Đọc: Cô giáo lớp em (Cánh Diều)", "YCCĐ": "Cảm thụ bài thơ về cô giáo."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Mùa nước nổi (CTST)", "YCCĐ": "Hiểu vẻ đẹp miền Tây mùa nước nổi."},
                {"Chủ đề": "Bốn mùa", "Bài học": "Đọc: Chuyện bốn mùa (KNTT)", "YCCĐ": "Phân biệt đặc điểm các mùa trong năm."}
            ]
        }
    },

    # ========================== LỚP 3 ==========================
    "Lớp 3": {
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Bảng nhân, chia", "Bài học": "Bài 5: Bảng nhân 6, 7 (2 tiết)", "YCCĐ": "Vận dụng bảng nhân giải toán."},
                {"Chủ đề": "Góc và Hình", "Bài học": "Bài 15: Góc vuông, góc không vuông (1 tiết)", "YCCĐ": "Nhận biết góc bằng ê-ke."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Số đến 100.000", "Bài học": "Bài 45: Các số trong phạm vi 100000 (3 tiết)", "YCCĐ": "Đọc viết số có 5 chữ số."},
                {"Chủ đề": "Diện tích", "Bài học": "Bài 52: Diện tích hình chữ nhật (2 tiết)", "YCCĐ": "Nhớ và vận dụng công thức tính diện tích."}
            ]
        },
        "Tin học": { # Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 1: Các thành phần của máy tính (1 tiết)", "YCCĐ": "Gọi tên đúng các bộ phận cơ bản: Chuột, Bàn phím, Màn hình, Thân máy."},
                {"Chủ đề": "Máy tính và em", "Bài học": "Bài 3: Làm quen với chuột máy tính (2 tiết)", "YCCĐ": "Thực hiện thao tác: nháy chuột, kéo thả chuột."},
                {"Chủ đề": "Mạng máy tính", "Bài học": "Bài 5: Xem tin tức và giải trí trên Internet (2 tiết)", "YCCĐ": "Truy cập được trang web thiếu nhi phù hợp."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Soạn thảo văn bản", "Bài học": "Bài 8: Làm quen với soạn thảo văn bản (2 tiết)", "YCCĐ": "Gõ được các kí tự và dấu tiếng Việt đơn giản."},
                {"Chủ đề": "Công cụ vẽ", "Bài học": "Bài 11: Vẽ tranh đơn giản (2 tiết)", "YCCĐ": "Sử dụng công cụ Paint hoặc tương đương để vẽ hình cơ bản."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Chiếc áo mùa thu (CTST)", "YCCĐ": "Hiểu nội dung và hình ảnh nhân hóa."},
                {"Chủ đề": "Cộng đồng", "Bài học": "Đọc: Lớp học trên đường (Cánh Diều)", "YCCĐ": "Hiểu ý nghĩa của việc học tập."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lễ hội", "Bài học": "Đọc: Hội đua voi ở Tây Nguyên (KNTT)", "YCCĐ": "Nắm được không khí và diễn biến hội đua."}
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [{"Chủ đề": "Tự nhiên", "Bài học": "Bài 1: Tự nhiên và Công nghệ (2 tiết)", "YCCĐ": "Phân biệt đối tượng tự nhiên và sản phẩm công nghệ."}],
            "Học kỳ II": [{"Chủ đề": "Thủ công", "Bài học": "Bài 7: Làm đồ dùng học tập (3 tiết)", "YCCĐ": "Làm được ống đựng bút hoặc thước kẻ."}]
        }
    },

    # ========================== LỚP 4 ==========================
    "Lớp 4": {
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Số tự nhiên", "Bài học": "Bài 5: Dãy số tự nhiên (1 tiết)", "YCCĐ": "Nhận biết đặc điểm dãy số tự nhiên."},
                {"Chủ đề": "Góc và Đơn vị", "Bài học": "Bài 10: Góc nhọn, góc tù, góc bẹt (2 tiết)", "YCCĐ": "Dùng thước đo góc để nhận biết."},
                {"Chủ đề": "Phép tính", "Bài học": "Bài 25: Phép chia cho số có hai chữ số (3 tiết)", "YCCĐ": "Thực hiện chia và thử lại."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phân số", "Bài học": "Bài 40: Rút gọn phân số (2 tiết)", "YCCĐ": "Biết cách chia cả tử và mẫu cho cùng một số."},
                {"Chủ đề": "Phân số", "Bài học": "Bài 55: Phép cộng phân số (2 tiết)", "YCCĐ": "Cộng hai phân số cùng mẫu và khác mẫu."}
            ]
        },
        "Tin học": { # Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "Phần cứng và Phần mềm", "Bài học": "Bài 1: Các thiết bị phần cứng (1 tiết)", "YCCĐ": "Phân biệt thiết bị vào/ra (Bàn phím, Màn hình, Máy in)."},
                {"Chủ đề": "Thông tin và dữ liệu", "Bài học": "Bài 3: Thông tin trên trang web (2 tiết)", "YCCĐ": "Nhận biết siêu văn bản, liên kết trên web."},
                {"Chủ đề": "Soạn thảo văn bản", "Bài học": "Bài 5: Chèn ảnh vào văn bản (2 tiết)", "YCCĐ": "Chèn và thay đổi kích thước ảnh trong Word."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lập trình Scratch", "Bài học": "Bài 8: Làm quen với Scratch (2 tiết)", "YCCĐ": "Nhận biết giao diện và vùng lập trình."},
                {"Chủ đề": "Lập trình Scratch", "Bài học": "Bài 10: Điều khiển nhân vật (2 tiết)", "YCCĐ": "Sử dụng lệnh di chuyển và xoay."},
                {"Chủ đề": "Đa phương tiện", "Bài học": "Bài 13: Tạo bài trình chiếu (2 tiết)", "YCCĐ": "Tạo slide đơn giản với tiêu đề và nội dung."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Điều ước của vua Mi-đát (KNTT)", "YCCĐ": "Hiểu thông điệp về hạnh phúc và lòng tham."},
                {"Chủ đề": "Tuổi nhỏ", "Bài học": "Đọc: Tuổi ngựa (CTST)", "YCCĐ": "Cảm nhận ước mơ và tình yêu mẹ."},
                {"Chủ đề": "Ý chí", "Bài học": "Đọc: Văn hay chữ tốt (Cánh Diều)", "YCCĐ": "Ca ngợi sự kiên trì khổ luyện."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Sầu riêng (KNTT)", "YCCĐ": "Miêu tả hương vị đặc biệt của trái cây."},
                {"Chủ đề": "Khám phá", "Bài học": "Đọc: Đường đi Sa Pa (KNTT)", "YCCĐ": "Cảm nhận vẻ đẹp thiên nhiên hùng vĩ."}
            ]
        },
        "Khoa học": { # KNTT
            "Học kỳ I": [{"Chủ đề": "Nước", "Bài học": "Bài 3: Vòng tuần hoàn của nước (2 tiết)", "YCCĐ": "Vẽ sơ đồ vòng tuần hoàn."}],
            "Học kỳ II": [{"Chủ đề": "Nấm", "Bài học": "Bài 18: Nấm và tác dụng (2 tiết)", "YCCĐ": "Kể tên nấm ăn được và nấm độc."}]
        },
        "Lịch sử và Địa lí": { # KNTT
            "Học kỳ I": [{"Chủ đề": "Trung du Bắc Bộ", "Bài học": "Bài 3: Thiên nhiên vùng Trung du (2 tiết)", "YCCĐ": "Mô tả địa hình đồi bát úp."}],
            "Học kỳ II": [{"Chủ đề": "Duyên hải Miền Trung", "Bài học": "Bài 15: Biển đảo Việt Nam (2 tiết)", "YCCĐ": "Xác định vị trí Hoàng Sa, Trường Sa."}]
        },
        "Công nghệ": {
            "Học kỳ I": [{"Chủ đề": "Hoa và cây cảnh", "Bài học": "Bài 2: Các loại hoa phổ biến (2 tiết)", "YCCĐ": "Nhận biết hoa hồng, hoa cúc, hoa đào."}],
            "Học kỳ II": [{"Chủ đề": "Lắp ghép", "Bài học": "Bài 6: Lắp ghép mô hình xe (3 tiết)", "YCCĐ": "Sử dụng bộ lắp ghép kĩ thuật."}]
        }
    },

    # ========================== LỚP 5 ==========================
    "Lớp 5": {
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Số thập phân", "Bài học": "Bài 8: Số thập phân (3 tiết)", "YCCĐ": "Đọc, viết, so sánh số thập phân."},
                {"Chủ đề": "Các phép tính", "Bài học": "Bài 15: Cộng, trừ số thập phân (3 tiết)", "YCCĐ": "Thực hiện tính đúng và giải toán."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 22: Hình tam giác (2 tiết)", "YCCĐ": "Nhận biết đáy và đường cao."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Tỉ số phần trăm", "Bài học": "Bài 45: Tỉ số phần trăm (2 tiết)", "YCCĐ": "Hiểu ý nghĩa tỉ số phần trăm."},
                {"Chủ đề": "Thể tích", "Bài học": "Bài 50: Thể tích hình lập phương (2 tiết)", "YCCĐ": "Vận dụng công thức tính thể tích."}
            ]
        },
        "Tin học": { # Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "Quản lý tệp", "Bài học": "Bài 1: Cây thư mục (1 tiết)", "YCCĐ": "Sắp xếp và quản lý thư mục khoa học."},
                {"Chủ đề": "Mạng máy tính", "Bài học": "Bài 3: Thư điện tử (Email) (2 tiết)", "YCCĐ": "Biết cách soạn và gửi email đơn giản."},
                {"Chủ đề": "Bản quyền", "Bài học": "Bài 5: Bản quyền nội dung số (1 tiết)", "YCCĐ": "Hiểu và tôn trọng bản quyền khi dùng Internet."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lập trình Scratch", "Bài học": "Bài 9: Biến nhớ trong Scratch (3 tiết)", "YCCĐ": "Sử dụng biến để tính điểm hoặc đếm thời gian."},
                {"Chủ đề": "Lập trình Scratch", "Bài học": "Bài 12: Cấu trúc rẽ nhánh (3 tiết)", "YCCĐ": "Sử dụng khối lệnh 'Nếu... thì...'."},
                {"Chủ đề": "Dự án", "Bài học": "Bài 15: Dự án kể chuyện tương tác (4 tiết)", "YCCĐ": "Tạo sản phẩm hoàn chỉnh."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Việt Nam gấm vóc", "Bài học": "Đọc: Thư gửi các học sinh (KNTT)", "YCCĐ": "Hiểu mong muốn của Bác Hồ với học sinh."},
                {"Chủ đề": "Cánh chim hòa bình", "Bài học": "Đọc: Bài ca về trái đất (KNTT)", "YCCĐ": "Yêu hòa bình, ghét chiến tranh."},
                {"Chủ đề": "Môi trường", "Bài học": "Đọc: Chuyện một khu vườn nhỏ (Cánh Diều)", "YCCĐ": "Ý thức bảo vệ thiên nhiên."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Người công dân", "Bài học": "Đọc: Người công dân số Một (KNTT)", "YCCĐ": "Hiểu tâm tư cứu nước của Bác Hồ."},
                {"Chủ đề": "Đất nước đổi mới", "Bài học": "Đọc: Trí dũng song toàn (CTST)", "YCCĐ": "Ca ngợi sự khôn khéo và dũng cảm."}
            ]
        },
        "Khoa học": { # KNTT
            "Học kỳ I": [{"Chủ đề": "Sự biến đổi chất", "Bài học": "Bài 5: Sự biến đổi hóa học (2 tiết)", "YCCĐ": "Phân biệt biến đổi lí học và hóa học."}],
            "Học kỳ II": [{"Chủ đề": "Năng lượng", "Bài học": "Bài 12: Sử dụng năng lượng điện (2 tiết)", "YCCĐ": "An toàn và tiết kiệm điện."}]
        },
        "Lịch sử và Địa lí": { # KNTT
            "Học kỳ I": [{"Chủ đề": "Xây dựng đất nước", "Bài học": "Bài 4: Nhà Nguyễn (2 tiết)", "YCCĐ": "Nêu được một số đóng góp và hạn chế."}],
            "Học kỳ II": [{"Chủ đề": "Thế giới", "Bài học": "Bài 18: Các châu lục (3 tiết)", "YCCĐ": "Nhận biết vị trí các châu lục trên bản đồ."}]
        },
        "Công nghệ": {
            "Học kỳ I": [{"Chủ đề": "Sáng chế", "Bài học": "Bài 3: Tìm hiểu về thiết kế (2 tiết)", "YCCĐ": "Hình thành ý tưởng thiết kế đơn giản."}],
            "Học kỳ II": [{"Chủ đề": "Lắp ráp", "Bài học": "Bài 8: Lắp ráp mô hình rô-bốt (4 tiết)", "YCCĐ": "Hoàn thiện mô hình rô-bốt từ bộ kĩ thuật."}]
        }
    }
}

# --- 4. CÁC HÀM XỬ LÝ (GIỮ NGUYÊN LOGIC) ---

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
    Đóng vai giáo viên {subject} Lớp {grade}.
    Hãy viết **1 CÂU HỎI KIỂM TRA** với yêu cầu sau:
    - Bài học: {lesson_info['Bài học']}
    - Yêu cầu cần đạt: {lesson_info['YCCĐ']}
    - Dạng câu hỏi: {q_type}
    - Mức độ nhận thức: {level}
    - Điểm số: {points} điểm.

    OUTPUT TRẢ VỀ (Bắt buộc theo định dạng sau, không thêm lời dẫn):
    **Câu hỏi:** [Nội dung câu hỏi]
    **Đáp án:** [Đáp án chi tiết]
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

# Lấy dữ liệu môn học (Có kiểm tra lỗi)
raw_data = CURRICULUM_DB.get(selected_grade, {}).get(selected_subject, {})

if not raw_data:
    st.warning("⚠️ Đang cập nhật dữ liệu cho môn này. Vui lòng chọn môn khác.")
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
    unique_topics = list(set([l['Chủ đề'] for l in lessons_in_term]))
    if not unique_topics:
        st.warning("Chưa có chủ đề cho học kỳ này.")
        st.stop()
    selected_topic = st.selectbox("Chọn Chủ đề:", unique_topics)

with col_b:
    # Lọc bài học theo chủ đề
    filtered_lessons = [l for l in lessons_in_term if l['Chủ đề'] == selected_topic]
    
    if not filtered_lessons:
         st.warning("Chưa có bài học cho chủ đề này.")
         st.stop()

    lesson_options = {f"{l['Bài học']}": l for l in filtered_lessons}
    selected_lesson_name = st.selectbox("Chọn Bài học (có số tiết):", list(lesson_options.keys()))
    
    # Kiểm tra key an toàn (Tránh lỗi KeyError khi đổi chủ đề nhanh)
    if selected_lesson_name not in lesson_options:
        st.stop()
        
    current_lesson_data = lesson_options[selected_lesson_name]
    st.info(f"🎯 **YCCĐ:** {current_lesson_data['YCCĐ']}")

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
    matrix_text += "="*80 + "\n"
    matrix_text += f"{'STT':<5} | {'Chủ đề':<20} | {'Bài học':<30} | {'Dạng':<15} | {'Mức độ':<15} | {'Điểm':<5}\n"
    matrix_text += "-"*80 + "\n"
    
    for idx, item in enumerate(st.session_state.exam_list):
        topic_short = (item['topic'][:18] + '..') if len(item['topic']) > 18 else item['topic']
        lesson_short = (item['lesson'][:28] + '..') if len(item['lesson']) > 28 else item['lesson']
        row_str = f"{idx+1:<5} | {topic_short:<20} | {lesson_short:<30} | {item['type']:<15} | {item['level']:<15} | {item['points']:<5}\n"
        matrix_text += row_str
    
    matrix_text += "-"*80 + "\n"
    matrix_text += f"TỔNG SỐ CÂU: {len(st.session_state.exam_list)} câu\n"
    matrix_text += f"TỔNG ĐIỂM:   {sum(q['points'] for q in st.session_state.exam_list)} điểm\n"
    matrix_text += "="*80 + "\n\n\n"

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
