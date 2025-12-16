import streamlit as st
import pandas as pd
import requests
import json
import time
from io import BytesIO

# --- 1. CẤU HÌNH TRANG (BẮT BUỘC Ở DÒNG ĐẦU TIÊN) ---
st.set_page_config(
    page_title="HỖ TRỢ RA ĐỀ THI TIỂU HỌC (GDPT 2018)",
    page_icon="📚",
    layout="wide"
)

# --- 2. CSS GIAO DIỆN ---
st.markdown("""
<style>
    .main-title { text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;}
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; text-align: center; padding: 10px; border-top: 1px solid #ddd; z-index: 99;}
    footer {visibility: hidden;}
    div[data-testid="stDataEditor"] { border: 1px solid #ccc; border-radius: 5px; }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { font-size: 16px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. CƠ SỞ DỮ LIỆU ---

# 3.1. Danh sách Môn học & Icon
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tiếng Anh", "🇬🇧"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

# 3.2. Dữ liệu Nội dung bài học (FULL DATA KẾT NỐI TRI THỨC & CÙNG KHÁM PHÁ)
CURRICULUM_DB = {
    # ---------------- LỚP 1 ----------------
    "Lớp 1": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Các số đến 10", "Bài học": "Bài 1: Nhiều hơn, ít hơn (2 tiết)", "YCCĐ": "So sánh số lượng đồ vật."},
                {"Chủ đề": "Các số đến 10", "Bài học": "Bài 4: Số 4, Số 5 (2 tiết)", "YCCĐ": "Đếm, đọc, viết, so sánh số 4, 5."},
                {"Chủ đề": "Phép cộng, trừ", "Bài học": "Bài 12: Phép cộng trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép cộng không nhớ trong phạm vi 10."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 18: Hình vuông, hình tròn, hình tam giác (1 tiết)", "YCCĐ": "Nhận biết các hình phẳng cơ bản."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Các số đến 100", "Bài học": "Bài 27: Số có hai chữ số (3 tiết)", "YCCĐ": "Đọc, viết, so sánh số có hai chữ số."},
                {"Chủ đề": "Cộng, trừ có nhớ", "Bài học": "Bài 34: Phép cộng dạng 29 + 5 (4 tiết)", "YCCĐ": "Thực hiện phép cộng có nhớ trong phạm vi 100."},
                {"Chủ đề": "Đo lường", "Bài học": "Bài 50: Xem đồng hồ (1 tiết)", "YCCĐ": "Nhận biết kim giờ, kim phút và xem giờ đúng."},
                {"Chủ đề": "Ôn tập cuối năm", "Bài học": "Ôn tập cuối năm (4 tiết)", "YCCĐ": "Hệ thống hóa kiến thức toàn năm học."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Làm quen (Âm/Chữ)", "Bài học": "Bài 1: A a (2 tiết) [KNTT]", "YCCĐ": "Nhận biết, đọc, viết âm a, chữ a."},
                {"Chủ đề": "Làm quen (Âm/Chữ)", "Bài học": "Bài 2: B b, dấu huyền (2 tiết) [CTST]", "YCCĐ": "Đọc đúng âm b và thanh huyền. Nhận diện tiếng 'bà'."},
                {"Chủ đề": "Làm quen (Âm/Chữ)", "Bài học": "Bài 4: E e, Ê ê (2 tiết) [Cánh Diều]", "YCCĐ": "Phân biệt e và ê. Tìm tiếng có âm e, ê."},
                {"Chủ đề": "Đọc hiểu truyện", "Bài học": "Bài: Kể chuyện Cây táo của Ba (1 tiết) [KNTT]", "YCCĐ": "Nghe và nắm được chi tiết chính của câu chuyện."},
                {"Chủ đề": "Đọc hiểu", "Bài học": "Bài đọc: Ve và Kiến (2 tiết) [Cánh Diều]", "YCCĐ": "Đọc trơn đoạn văn ngắn, hiểu bài học về sự chăm chỉ."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chủ điểm: Gia đình", "Bài học": "Bài: Ngôi nhà (2 tiết) [KNTT]", "YCCĐ": "Đọc hiểu bài thơ về tình yêu ngôi nhà, gia đình."},
                {"Chủ đề": "Chủ điểm: Thiên nhiên", "Bài học": "Bài: Hoa kết trái (2 tiết) [CTST]", "YCCĐ": "Nhận biết các loại hoa và quả qua bài thơ."},
                {"Chủ đề": "Chủ điểm: Nhà trường", "Bài học": "Bài: Mời vào (2 tiết) [Cánh Diều]", "YCCĐ": "Đọc bài thơ, hiểu về phép lịch sự khi khách đến nhà/lớp."},
                {"Chủ đề": "Ôn tập", "Bài học": "Ôn tập cuối năm: Đọc mở rộng (4 tiết)", "YCCĐ": "Đọc hiểu văn bản truyện/thơ khoảng 70-80 chữ."},
            ]
        }
    },
    
    # ---------------- LỚP 2 ----------------
    "Lớp 2": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Ôn tập và Bổ sung", "Bài học": "Bài 1: Ôn tập về số và phép cộng, phép trừ (3 tiết)", "YCCĐ": "Củng cố cộng, trừ không nhớ trong 100."},
                {"Chủ đề": "Cộng trừ 100", "Bài học": "Bài 9: Phép cộng có nhớ trong phạm vi 100 (4 tiết)", "YCCĐ": "Thực hiện thành thạo cộng có nhớ trong 100."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 16: Đường thẳng, đường cong (1 tiết)", "YCCĐ": "Nhận biết và phân biệt đường thẳng, đường cong."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Số đến 1000", "Bài học": "Bài 30: Số có ba chữ số (4 tiết)", "YCCĐ": "Đọc, viết, so sánh số có ba chữ số."},
                {"Chủ đề": "Phép nhân, chia", "Bài học": "Bài 45: Bảng nhân 4 (2 tiết)", "YCCĐ": "Học thuộc và vận dụng bảng nhân 4."},
                {"Chủ đề": "Đo lường", "Bài học": "Bài 52: Giới thiệu về 1/2, 1/3, 1/4 (2 tiết)", "YCCĐ": "Nhận biết phân số đơn giản."},
                {"Chủ đề": "Thống kê", "Bài học": "Bài 56: Thu thập, phân loại, kiểm đếm (1 tiết)", "YCCĐ": "Thu thập dữ liệu và lập bảng thống kê."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Tôi là học sinh lớp 2 (3 tiết) [KNTT]", "YCCĐ": "Hiểu nội dung bài đọc về ngày khai trường."},
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Ngày hôm qua đâu rồi? (2 tiết) [Cánh Diều]", "YCCĐ": "Đọc thuộc lòng bài thơ, hiểu giá trị thời gian."},
                {"Chủ đề": "Bạn bè", "Bài học": "Đọc: Út Tin (3 tiết) [CTST]", "YCCĐ": "Hiểu đặc điểm nhân vật qua ngoại hình và tính cách."},
                {"Chủ đề": "Thầy cô", "Bài học": "Đọc: Cô giáo lớp em (2 tiết) [Cánh Diều]", "YCCĐ": "Cảm nhận tình cảm cô trò qua bài thơ."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quanh em", "Bài học": "Đọc: Chuyện bốn mùa (3 tiết) [KNTT]", "YCCĐ": "Hiểu đặc điểm của các mùa Xuân, Hạ, Thu, Đông."},
                {"Chủ đề": "Thiên nhiên", "Bài học": "Đọc: Mùa nước nổi (2 tiết) [CTST]", "YCCĐ": "Cảm nhận vẻ đẹp đặc trưng của miền Tây mùa nước nổi."},
                {"Chủ đề": "Đất nước", "Bài học": "Đọc: Tre Việt Nam (2 tiết) [Cánh Diều]", "YCCĐ": "Hiểu hình ảnh cây tre tượng trưng cho phẩm chất người Việt."},
                {"Chủ đề": "Ôn tập", "Bài học": "Đọc mở rộng: Những người bạn nhỏ (2 tiết)", "YCCĐ": "Đọc hiểu văn bản thông tin về loài vật."},
            ]
        }
    },
    
    # ---------------- LỚP 3 ----------------
    "Lớp 3": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Ôn tập", "Bài học": "Bài 1: Ôn tập các số trong phạm vi 1000 (3 tiết)", "YCCĐ": "Củng cố đọc, viết, so sánh số có 3 chữ số."},
                {"Chủ đề": "Số đến 10000", "Bài học": "Bài 10: Các số trong phạm vi 10000 (4 tiết)", "YCCĐ": "Đọc, viết, so sánh số có 4 chữ số."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 22: Chu vi hình tam giác, hình tứ giác (2 tiết)", "YCCĐ": "Tính chu vi các hình đã học."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phép tính", "Bài học": "Bài 34: Phép nhân số có 4 chữ số với số có 1 chữ số (3 tiết)", "YCCĐ": "Thực hiện phép nhân và đặt tính đúng."},
                {"Chủ đề": "Phân số", "Bài học": "Bài 46: Giới thiệu về phân số (2 tiết)", "YCCĐ": "Nhận biết phân số (tử số, mẫu số)."},
                {"Chủ đề": "Đo lường", "Bài học": "Bài 54: Đơn vị đo diện tích: xăng-ti-mét vuông (2 tiết)", "YCCĐ": "Nhận biết đơn vị cm² và áp dụng tính diện tích."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Chiếc áo mùa thu (3 tiết) [CTST]", "YCCĐ": "Cảm nhận vẻ đẹp của thiên nhiên mùa thu."},
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Lễ chào cờ đặc biệt (2 tiết) [Cánh Diều]", "YCCĐ": "Hiểu ý nghĩa thiêng liêng của lễ chào cờ tại Trường Sa."},
                {"Chủ đề": "Cộng đồng", "Bài học": "Đọc: Bài học đầu tiên của thỏ con (2 tiết) [KNTT]", "YCCĐ": "Rút ra bài học về cách giao tiếp, ứng xử lễ phép."},
                {"Chủ đề": "Sáng tạo", "Bài học": "Đọc: Ông tổ nghề thêu (2 tiết) [Cánh Diều]", "YCCĐ": "Hiểu về sự thông minh, sáng tạo của danh nhân Trần Quốc Khái."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Bảo vệ Tổ quốc", "Bài học": "Đọc: Các em nhỏ và cụ già (3 tiết) [KNTT]", "YCCĐ": "Hiểu về sự quan tâm, chia sẻ giữa mọi người."},
                {"Chủ đề": "Thiên nhiên kì thú", "Bài học": "Đọc: Giọt sương (2 tiết) [CTST]", "YCCĐ": "Cảm nhận vẻ đẹp tinh khiết của thiên nhiên buổi sớm."},
                {"Chủ đề": "Thể thao & Nghệ thuật", "Bài học": "Đọc: Cùng vui chơi (2 tiết) [Cánh Diều]", "YCCĐ": "Hiểu lợi ích của việc vui chơi, rèn luyện sức khỏe."},
                {"Chủ đề": "Ôn tập", "Bài học": "Ôn tập cuối năm (8 tiết)", "YCCĐ": "Đọc hiểu văn bản đa dạng (truyện, thơ, văn bản thông tin)."},
            ]
        },
        "Công nghệ": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Sản phẩm Thủ công", "Bài học": "Bài 1-4: Làm đồ chơi và vật dụng đơn giản", "YCCĐ": "Thiết kế và làm được các sản phẩm thủ công từ giấy, vải (ví dụ: bóp đựng bút)."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chăm sóc gia đình", "Bài học": "Bài 5-8: An toàn trong gia đình, Chăm sóc vật nuôi", "YCCĐ": "Nêu được nguyên tắc an toàn khi sử dụng điện. Biết cách chăm sóc một số vật nuôi phổ biến."},
            ]
        },
        "Tin học": { # Cùng Khám Phá
            "Học kỳ I": [
                {"Chủ đề": "Làm việc với máy tính", "Bài học": "Bài 1-3: Tệp, thư mục, Tổ chức thông tin", "YCCĐ": "Biết cách tạo, lưu và tìm kiếm tệp, thư mục. Nắm được khái niệm cơ bản về thông tin."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lập trình trực quan", "Bài học": "Bài 4-6: Lập trình với Scratch (Mức độ nâng cao)", "YCCĐ": "Sử dụng biến số, điều kiện rẽ nhánh (if/else) để tạo ra các chương trình tương tác."},
            ]
        }
    },

    # ---------------- LỚP 4 ----------------
    "Lớp 4": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Số tự nhiên", "Bài học": "Chương 1: Các số đến lớp triệu", "YCCĐ": "Đọc, viết, so sánh, làm tròn các số đến lớp triệu. Nắm vững giá trị theo vị trí."},
                {"Chủ đề": "Phép tính", "Bài học": "Chương 2: Bốn phép tính với số tự nhiên", "YCCĐ": "Thực hiện thành thạo phép cộng, trừ, nhân, chia (có dư) số tự nhiên. Vận dụng tính chất."},
                {"Chủ đề": "Hình học và Đo lường", "Bài học": "Chương 3: Góc, Đường thẳng vuông góc, song song", "YCCĐ": "Nhận biết góc nhọn, tù, bẹt, vuông. Vẽ được hai đường thẳng vuông góc, song song đơn giản."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phân số", "Bài học": "Chương 5: Phân số", "YCCĐ": "Nhận biết, đọc, viết, rút gọn, quy đồng mẫu số phân số. Áp dụng tính chất cơ bản."},
                {"Chủ đề": "Phép tính với Phân số", "Bài học": "Chương 6: Phép tính với phân số, Tỉ số, Tỉ lệ", "YCCĐ": "Thực hiện thành thạo cộng, trừ, nhân, chia phân số. Giải bài toán tìm hai số khi biết tổng/hiệu."},
                {"Chủ đề": "Hình học", "Bài học": "Chương 7: Hình bình hành, Hình thoi, Diện tích", "YCCĐ": "Nhận biết đặc điểm, tính chu vi và diện tích Hình bình hành, Hình thoi."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Điều ước của vua Mi-đát (2 tiết) [KNTT]", "YCCĐ": "Hiểu ý nghĩa: Hạnh phúc không chỉ nằm ở vàng bạc."},
                {"Chủ đề": "Tuổi nhỏ làm việc nhỏ", "Bài học": "Đọc: Tuổi ngựa (2 tiết) [CTST]", "YCCĐ": "Cảm nhận ước mơ bay bổng và tình yêu mẹ của bạn nhỏ."},
                {"Chủ đề": "Chân dung của em", "Bài học": "Đọc: Văn hay chữ tốt (2 tiết) [Cánh Diều]", "YCCĐ": "Hiểu về sự kiên trì luyện tập của Cao Bá Quát."},
                {"Chủ đề": "Trải nghiệm", "Bài học": "Đọc: Ở Vương quốc Tương Lai (2 tiết) [KNTT]", "YCCĐ": "Đọc văn bản kịch, hiểu về ước mơ sáng tạo của trẻ em."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Sầu riêng (2 tiết) [KNTT]", "YCCĐ": "Cảm nhận vẻ đẹp đặc sắc của trái cây miền Nam."},
                {"Chủ đề": "Thế giới muôn màu", "Bài học": "Đọc: Hơn một ngàn ngày vòng quanh Trái Đất (2 tiết) [CTST]", "YCCĐ": "Đọc hiểu văn bản thông tin về hành trình của Ma-zen-lan."},
                {"Chủ đề": "Khám phá", "Bài học": "Đọc: Đường đi Sa Pa (2 tiết) [Cánh Diều]", "YCCĐ": "Cảm nhận vẻ đẹp huyền ảo của thiên nhiên Sa Pa."},
                {"Chủ đề": "Ôn tập", "Bài học": "Đọc mở rộng: Con sẻ (2 tiết) [KNTT]", "YCCĐ": "Hiểu về lòng dũng cảm và tình mẫu tử thiêng liêng."},
            ]
        },
        "Khoa học": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Chất và sự biến đổi", "Bài học": "Bài 1-6: Tính chất của nước, Ánh sáng, Âm thanh", "YCCĐ": "Nêu được tính chất, sự chuyển thể của nước. Giải thích hiện tượng ánh sáng, bóng tối và cách truyền âm."},
                {"Chủ đề": "Thực vật và Động vật", "Bài học": "Bài 7-12: Sự đa dạng và vai trò", "YCCĐ": "Phân loại và nêu được vai trò của thực vật, động vật đối với môi trường."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Con người và Sức khỏe", "Bài học": "Bài 13-15: Cơ quan Hô hấp và Tuần hoàn", "YCCĐ": "Mô tả được chức năng cơ bản của hệ hô hấp, tuần hoàn. Nêu các biện pháp bảo vệ sức khỏe."},
                {"Chủ đề": "Môi trường và Tài nguyên", "Bài học": "Bài 16-21: Bảo vệ môi trường, Tài nguyên thiên nhiên, Trái Đất", "YCCĐ": "Đề xuất các hành động bảo vệ môi trường. Mô tả được sự quay của Trái Đất tạo ra ngày và đêm."},
            ]
        },
        "Lịch sử và Địa lí": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Địa lí", "Bài học": "Phần Địa lí: Thiên nhiên, Dân cư và hoạt động", "YCCĐ": "Mô tả được đặc điểm chung của địa hình, khí hậu Việt Nam. Kể tên một số dân tộc tiêu biểu."},
                {"Chủ đề": "Lịch sử", "Bài học": "Phần Lịch sử: Thời kì dựng nước (Văn Lang - Âu Lạc)", "YCCĐ": "Trình bày được tóm tắt về sự ra đời nhà nước Văn Lang. Nhận biết được nghề nghiệp và đời sống của người Lạc Việt."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lịch sử", "Bài học": "Phần Lịch sử: Bảo vệ độc lập", "YCCĐ": "Nêu được ý nghĩa lịch sử của các sự kiện chống ngoại xâm tiêu biểu (Hai Bà Trưng, Bạch Đằng)."},
                {"Chủ đề": "Địa lí", "Bài học": "Phần Địa lí: Kinh tế Việt Nam", "YCCĐ": "Kể tên các loại cây trồng, vật nuôi chính. Nhận biết được một số ngành công nghiệp và vai trò của nó."},
            ]
        },
        "Tin học": { # Cùng Khám Phá
            "Học kỳ I": [
                {"Chủ đề": "Máy tính và Internet", "Bài học": "Chủ đề 1: Xử lí thông tin, Mạng máy tính", "YCCĐ": "Nêu được các bước xử lí thông tin. Biết cách truy cập Internet an toàn."},
                {"Chủ đề": "Sử dụng ứng dụng", "Bài học": "Chủ đề 2: Làm quen với Word và PowerPoint", "YCCĐ": "Thực hiện các thao tác cơ bản: nhập văn bản, chèn hình ảnh, tạo hiệu ứng chuyển cảnh."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lập trình trực quan", "Bài học": "Chủ đề 3: Lập trình với Scratch (Nâng cao)", "YCCĐ": "Sử dụng các khối lệnh điều khiển, biến số để lập trình một câu chuyện hoặc trò chơi nhỏ."},
                {"Chủ đề": "Thực hành", "Bài học": "Chủ đề 4: Dự án sáng tạo Tin học", "YCCĐ": "Áp dụng kiến thức để hoàn thành một sản phẩm đơn giản (tờ báo tường điện tử, trò chơi nhỏ)."},
            ]
        },
        "Công nghệ": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Thủ công Kĩ thuật", "Bài học": "Bài 1-3: Vật liệu và Dụng cụ, Cắt khâu đơn giản", "YCCĐ": "Nhận biết các vật liệu cơ bản. Thực hiện các thao tác đo, cắt, khâu cơ bản để làm một sản phẩm thủ công."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Công nghệ Gia đình", "Bài học": "Bài 7-9: Công việc trong gia đình, Chăm sóc cây trồng", "YCCĐ": "Nêu được tầm quan trọng của việc nhà. Biết cách chăm sóc một số loại cây cảnh, rau củ thông thường."},
            ]
        }
    },

    # ---------------- LỚP 5 ----------------
    "Lớp 5": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Ôn tập", "Bài học": "Bài 1: Ôn tập về phân số (2 tiết)", "YCCĐ": "Củng cố kiến thức về phân số, rút gọn, quy đồng."},
                {"Chủ đề": "Số thập phân", "Bài học": "Bài 5: Khái niệm số thập phân (3 tiết)", "YCCĐ": "Nhận biết số thập phân và giá trị của các chữ số."},
                {"Chủ đề": "Phép tính", "Bài học": "Bài 12: Phép nhân số thập phân (3 tiết)", "YCCĐ": "Thực hiện thành thạo phép nhân số thập phân."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 20: Diện tích hình tam giác (2 tiết)", "YCCĐ": "Nêu công thức và tính diện tích hình tam giác."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phép chia", "Bài học": "Bài 27: Phép chia số thập phân (4 tiết)", "YCCĐ": "Thực hiện thành thạo phép chia số thập phân."},
                {"Chủ đề": "Tỉ số", "Bài học": "Bài 32: Tỉ số phần trăm (3 tiết)", "YCCĐ": "Giải các bài toán cơ bản về tỉ số phần trăm."},
                {"Chủ đề": "Thể tích", "Bài học": "Bài 40: Thể tích hình hộp chữ nhật (3 tiết)", "YCCĐ": "Tính thể tích hình hộp chữ nhật và hình lập phương."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Thế giới tuổi thơ", "Bài học": "Đọc: Thanh âm của gió (2 tiết) [KNTT]", "YCCĐ": "Cảm nhận vẻ đẹp thiên nhiên và kỉ niệm tuổi thơ."},
                {"Chủ đề": "Khung trời tuổi thơ", "Bài học": "Đọc: Chiều biên giới (2 tiết) [CTST]", "YCCĐ": "Cảm nhận vẻ đẹp hùng vĩ và thơ mộng của biên giới."},
                {"Chủ đề": "Người công dân", "Bài học": "Đọc: Chuyện một khu vườn nhỏ (2 tiết) [Cánh Diều]", "YCCĐ": "Ý thức yêu thiên nhiên, bảo vệ môi trường sống."},
                {"Chủ đề": "Hòa bình", "Bài học": "Đọc: Bài ca về trái đất (2 tiết) [KNTT]", "YCCĐ": "Hiểu khát vọng hòa bình của nhân loại."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Đất nước đổi mới", "Bài học": "Đọc: Trí dũng song toàn (2 tiết) [KNTT]", "YCCĐ": "Ca ngợi sự thông minh, dũng cảm của Giang Văn Minh."},
                {"Chủ đề": "Vì cuộc sống bình yên", "Bài học": "Đọc: Thái sư Trần Thủ Độ (2 tiết) [Cánh Diều]", "YCCĐ": "Hiểu về sự gương mẫu, nghiêm minh của Trần Thủ Độ."},
                {"Chủ đề": "Chủ quyền quốc gia", "Bài học": "Đọc: Phong cảnh đền Hùng (2 tiết) [CTST]", "YCCĐ": "Ca ngợi vẻ đẹp tráng lệ và thiêng liêng của vùng đất Tổ."},
                {"Chủ đề": "Ôn tập", "Bài học": "Đọc mở rộng: Đất nước (2 tiết) [KNTT]", "YCCĐ": "Cảm nhận tình yêu đất nước thiết tha qua bài thơ."},
            ]
        },
        "Khoa học": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Cơ thể người", "Bài học": "Bài 1: Sự lớn lên và phát triển (2 tiết)", "YCCĐ": "Mô tả được các giai đoạn phát triển của cơ thể."},
                {"Chủ đề": "Sức khỏe", "Bài học": "Bài 4: Phòng tránh bệnh sốt rét, sốt xuất huyết (2 tiết)", "YCCĐ": "Nêu được nguyên nhân và biện pháp phòng bệnh."},
                {"Chủ đề": "Môi trường", "Bài học": "Bài 8: Bảo vệ môi trường nước (2 tiết)", "YCCĐ": "Nêu vai trò và đề xuất giải pháp bảo vệ nguồn nước."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vật chất", "Bài học": "Bài 11: Sự biến đổi của chất (2 tiết)", "YCCĐ": "Phân biệt biến đổi vật lí và hóa học."},
                {"Chủ đề": "Năng lượng", "Bài học": "Bài 14: Nhiệt và vật dẫn nhiệt (2 tiết)", "YCCĐ": "Nhận biết vật dẫn nhiệt tốt và kém."},
                {"Chủ đề": "Không gian", "Bài học": "Bài 18: Trái Đất và Mặt Trời (2 tiết)", "YCCĐ": "Mô tả sự vận động của Trái Đất và các hiện tượng."},
            ]
        },
        "Lịch sử và Địa lí": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Địa lí: Châu lục", "Bài học": "Bài 1: Vị trí địa lí và đặc điểm tự nhiên Châu Á (2 tiết)", "YCCĐ": "Mô tả được vị trí và đặc điểm tự nhiên cơ bản của Châu Á."},
                {"Chủ đề": "Lịch sử: Thời phong kiến", "Bài học": "Bài 8: Đinh, Tiền Lê, Lý, Trần (3 tiết)", "YCCĐ": "Trình bày được các sự kiện quan trọng trong thời kỳ độc lập."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Địa lí: Toàn cầu", "Bài học": "Bài 15: Các đại dương trên thế giới (2 tiết)", "YCCĐ": "Kể tên và xác định vị trí các đại dương."},
                {"Chủ đề": "Lịch sử: Hiện đại", "Bài học": "Bài 20: Chiến thắng Điện Biên Phủ (3 tiết)", "YCCĐ": "Nêu được ý nghĩa lịch sử của chiến thắng Điện Biên Phủ."},
            ]
        },
        "Tin học": { # Cùng Khám Phá
            "Học kỳ I": [
                {"Chủ đề": "Dữ liệu", "Bài học": "Bài 1: Làm quen với Bảng tính (3 tiết)", "YCCĐ": "Nhập dữ liệu, thực hiện các phép tính cơ bản (cộng, trừ, nhân, chia) trong Excel."},
                {"Chủ đề": "Lập trình", "Bài học": "Bài 3: Lập trình với ngôn ngữ khối lệnh (Scratch) nâng cao (4 tiết)", "YCCĐ": "Sử dụng các cấu trúc điều khiển (rẽ nhánh, lặp) và biến số."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thiết kế", "Bài học": "Bài 5: Thiết kế bài trình chiếu nâng cao (3 tiết)", "YCCĐ": "Sử dụng hình ảnh động, âm thanh và liên kết trong PowerPoint."},
                {"Chủ đề": "Dự án", "Bài học": "Bài 7: Dự án tổng hợp cuối cấp (5 tiết)", "YCCĐ": "Áp dụng tổng hợp kiến thức để tạo ra sản phẩm sáng tạo."},
            ]
        },
        "Công nghệ": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Kĩ thuật", "Bài học": "Bài 1: An toàn khi dùng đồ điện trong gia đình (2 tiết)", "YCCĐ": "Nêu được nguyên tắc sử dụng an toàn các thiết bị điện."},
                {"Chủ đề": "Kĩ thuật", "Bài học": "Bài 2: Lắp ráp mạch điện đơn giản (3 tiết)", "YCCĐ": "Lắp ráp được mạch điện thắp sáng đơn giản (ví dụ: đèn pin)."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Gia đình", "Bài học": "Bài 4: Chế biến thực phẩm an toàn (2 tiết)", "YCCĐ": "Nêu được nguyên tắc vệ sinh, an toàn trong chế biến thực phẩm."},
                {"Chủ đề": "Gia đình", "Bài học": "Bài 5: Bảo quản đồ dùng trong gia đình (2 tiết)", "YCCĐ": "Biết cách sắp xếp và bảo quản đồ dùng cá nhân, đồ dùng chung."},
            ]
        }
    }
}

# --- 4. CÁC HÀM XỬ LÝ ---

def get_curriculum_data(grade, subject):
    """
    Lấy dữ liệu bài học từ CURRICULUM_DB và gộp lại (flatten)
    """
    data_by_term = CURRICULUM_DB.get(grade, {}).get(subject, {})
    
    if not data_by_term:
        return []
    
    flat_list = []
    if isinstance(data_by_term, dict):
        for term, lessons in data_by_term.items():
            for lesson in lessons:
                lesson_copy = lesson.copy()
                lesson_copy['Học kỳ'] = term 
                flat_list.append(lesson_copy)
                
    return flat_list

def find_working_model(api_key):
    """Tự động tìm model phù hợp"""
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(list_url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            chat_models = [m['name'] for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])]
            preferred = ['models/gemini-1.5-pro', 'models/gemini-1.5-flash', 'models/gemini-pro', 'models/gemini-1.0-pro']
            for p in preferred:
                for real_model in chat_models:
                    if p in real_model: return real_model
            if chat_models: return chat_models[0]
        return None
    except:
        return None

def generate_exam_final(api_key, grade, subject, content_matrix):
    """Gọi AI tạo đề dựa trên Ma trận đã cấu hình"""
    clean_key = api_key.strip()
    if not clean_key: return "⚠️ Chưa nhập API Key."

    with st.spinner("Đang kết nối máy chủ Google..."):
        model_name = find_working_model(clean_key)
    
    if not model_name:
        return "❌ Lỗi Key hoặc Mạng. Vui lòng kiểm tra lại API Key."

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={clean_key}"
    headers = {'Content-Type': 'application/json'}
    
    # Prompt chi tiết cho ma trận
    prompt = f"""
    Bạn là Tổ trưởng chuyên môn trường TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN.
    
    NHIỆM VỤ:
    Ra đề thi môn {subject} lớp {grade} dựa trên **BẢNG MA TRẬN CHI TIẾT** dưới đây.
    
    BẢNG MA TRẬN ĐỀ THI (Yêu cầu tuân thủ chính xác số lượng và loại câu hỏi cho từng bài):
    --------------------------
    {content_matrix}
    --------------------------
    
    HƯỚNG DẪN DẠNG CÂU HỎI:
    - TN: Trắc nghiệm (có thể là: Nhiều lựa chọn ABCD, Đúng/Sai, Điền khuyết, hoặc Nối - tùy theo yêu cầu trong ma trận).
    - TL: Tự luận.
    
    YÊU CẦU BẮT BUỘC:
    1. **TUÂN THỦ MA TRẬN:** Chỉ ra câu hỏi cho các bài học có trong bảng trên, đúng số lượng và số điểm đã quy định.
    2. **NỘI DUNG:** Bám sát Yêu cầu cần đạt (YCCĐ). Không ra kiến thức ngoài chương trình.
    3. **ĐỐI TƯỢNG:** Ngôn ngữ trong sáng, ngắn gọn, phù hợp học sinh vùng cao.
    4. **ĐỊNH DẠNG ĐẦU RA:** Trình bày thành 2 phần:
       - PHẦN 1: ĐỀ KIỂM TRA (Tiêu đề: TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN). Các câu hỏi đánh số liên tục. Bên cạnh mỗi câu ghi rõ số điểm. Ví dụ: Câu 1 (0.5 điểm).
       - PHẦN 2: HƯỚNG DẪN CHẤM VÀ MA TRẬN (Liệt kê đáp án chi tiết và Ma trận tổng hợp).
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # Retry mechanism
    for attempt in range(3):
        try:
            if attempt > 0:
                st.toast(f"Hệ thống đang bận, thử lại lần {attempt+1}...")
                time.sleep(3 + (attempt * 2))

            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                try:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                except:
                    return "⚠️ AI không trả về nội dung. Hãy thử lại."
            elif response.status_code == 429:
                continue 
            else:
                return f"⚠️ Lỗi từ Google ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Lỗi mạng: {e}"

    return "⚠️ Hệ thống Google đang quá tải (Lỗi 429). Vui lòng đợi 1-2 phút sau rồi ấn lại nút Tạo đề."

# --- 5. GIAO DIỆN CHÍNH (MAIN UI) ---

st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.header("🔑 CẤU HÌNH API")
    api_key_input = st.text_input("Dán API Key vào đây:", type="password")
    
    if st.button("Kiểm tra kết nối"):
        clean_k = api_key_input.strip()
        if not clean_k:
            st.error("Chưa nhập Key!")
        else:
            found_model = find_working_model(clean_k)
            if found_model:
                st.success(f"✅ Ổn định! ({found_model})")
            else:
                st.error("❌ Key sai hoặc lỗi mạng.")
    st.markdown("---")
    st.info("Hệ thống sử dụng dữ liệu sách 'Kết nối tri thức với cuộc sống'.")

# BƯỚC 1: CHỌN LỚP & MÔN
st.subheader("1. Chọn Lớp & Môn Học")

selected_grade = st.radio("Chọn khối:", list(SUBJECTS_DB.keys()), horizontal=True)

colors = {"Lớp 1": "#D32F2F", "Lớp 2": "#E65100", "Lớp 3": "#F57F17", "Lớp 4": "#2E7D32", "Lớp 5": "#1565C0"}
st.markdown(f"<div style='background-color:{colors[selected_grade]}; color:white; padding:5px; border-radius:5px; text-align:center;'>Đang làm việc với: {selected_grade}</div>", unsafe_allow_html=True)

# Lấy danh sách môn
subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
selected_subject_full = st.selectbox("Chọn môn:", subjects_list)
selected_subject = selected_subject_full.split(" ", 1)[1]

st.markdown("---")

# BƯỚC 2: XÂY DỰNG MA TRẬN ĐỀ THI
st.subheader("2. Xây dựng Ma trận Đề thi")
st.info("👇 Hãy nhập số lượng câu hỏi và điểm số cho từng bài học vào bảng dưới đây.")

# Lấy dữ liệu bài học
data_source = get_curriculum_data(selected_grade, selected_subject)

if not data_source:
    st.warning("Chưa có dữ liệu bài học cho môn này.")
else:
    # Tạo DataFrame từ dữ liệu nguồn
    df = pd.DataFrame(data_source)
    
    # THÊM CÁC CỘT CẤU HÌNH MA TRẬN
    # Cấu hình Trắc nghiệm
    df["Dạng TN"] = "Nhiều lựa chọn (ABCD)" # Mặc định
    df["Số câu TN"] = 0
    df["Điểm TN"] = 1.0
    
    # Cấu hình Tự luận
    df["Dạng TL"] = "Tự luận"
    df["Số câu TL"] = 0
    df["Điểm TL"] = 2.0

    # Hiển thị bảng Data Editor
    edited_df = st.data_editor(
        df,
        column_config={
            "Học kỳ": st.column_config.TextColumn("Học kỳ", width="small", disabled=True),
            "Chủ đề": st.column_config.TextColumn("Chủ đề", width="small", disabled=True),
            "Bài học": st.column_config.TextColumn("Tên bài học", width="medium", disabled=True),
            "YCCĐ": st.column_config.TextColumn("Yêu cầu cần đạt", width="medium", disabled=True),
            
            # Cấu hình cột Trắc nghiệm (TN)
            "Dạng TN": st.column_config.SelectboxColumn(
                "Loại câu TN",
                help="Chọn dạng trắc nghiệm",
                width="small",
                options=[
                    "Nhiều lựa chọn (ABCD)",
                    "Đúng/Sai",
                    "Điền khuyết",
                    "Nối đôi"
                ],
                required=True,
            ),
            "Số câu TN": st.column_config.NumberColumn(
                "SL TN",
                help="Số lượng câu trắc nghiệm",
                min_value=0,
                max_value=20,
                step=1,
                width="small"
            ),
            "Điểm TN": st.column_config.NumberColumn(
                "Điểm/Câu TN",
                min_value=0.0,
                max_value=10.0,
                step=0.25,
                width="small"
            ),

            # Cấu hình cột Tự luận (TL)
            "Dạng TL": st.column_config.SelectboxColumn(
                "Loại câu TL",
                width="small",
                options=[
                    "Tự luận (Thường)",
                    "Vận dụng cao",
                    "Giải toán có lời văn"
                ]
            ),
            "Số câu TL": st.column_config.NumberColumn(
                "SL TL",
                min_value=0,
                max_value=10,
                step=1,
                width="small"
            ),
            "Điểm TL": st.column_config.NumberColumn(
                "Điểm/Câu TL",
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                width="small"
            ),
        },
        hide_index=True,
        use_container_width=True
    )

    # TÍNH TOÁN TỔNG QUÁT MA TRẬN
    # Lọc ra những dòng người dùng đã nhập số câu > 0
    selected_matrix = edited_df[ (edited_df["Số câu TN"] > 0) | (edited_df["Số câu TL"] > 0) ]
    
    total_questions = selected_matrix["Số câu TN"].sum() + selected_matrix["Số câu TL"].sum()
    total_score = (selected_matrix["Số câu TN"] * selected_matrix["Điểm TN"]).sum() + (selected_matrix["Số câu TL"] * selected_matrix["Điểm TL"]).sum()
    
    st.write(f"📊 **Tổng hợp Ma trận:** {total_questions} câu hỏi | Tổng điểm: {total_score} điểm")
    
    if total_score != 10:
        st.warning(f"⚠️ Tổng điểm hiện tại là **{total_score}**. Hãy điều chỉnh để tổng bằng 10 điểm.")
    else:
        st.success("✅ Tổng điểm đã chuẩn (10 điểm).")

    # Chuẩn bị nội dung gửi cho AI
    final_content_for_ai = ""
    if not selected_matrix.empty:
        final_content_for_ai = "CHI TIẾT MA TRẬN ĐỀ THI CẦN TẠO:\n"
        for index, row in selected_matrix.iterrows():
            final_content_for_ai += f"""
            - Bài: {row['Bài học']} ({row['YCCĐ']})
              + Trắc nghiệm: {row['Số câu TN']} câu (Dạng: {row['Dạng TN']}, {row['Điểm TN']} điểm/câu)
              + Tự luận: {row['Số câu TL']} câu (Dạng: {row['Dạng TL']}, {row['Điểm TL']} điểm/câu)
            """

# NÚT TẠO ĐỀ
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns([1, 2])
with col_btn2:
    btn_run = st.button("🚀 TẠO ĐỀ THI THEO MA TRẬN", type="primary", use_container_width=True)

st.markdown("---")

# BƯỚC 3: KẾT QUẢ
st.subheader("3. Kết quả")
container = st.container(border=True)

if "result_exam" not in st.session_state:
    st.session_state.result_exam = ""

if btn_run:
    if not final_content_for_ai:
        st.error("⚠️ Bạn chưa nhập số lượng câu hỏi vào bảng trên!")
    else:
        st.session_state.result_exam = generate_exam_final(api_key_input, selected_grade, selected_subject, final_content_for_ai)

if st.session_state.result_exam:
    container.markdown(st.session_state.result_exam)
    st.download_button("📥 Tải xuống (Đề + Ma trận)", st.session_state.result_exam, f"De_thi_{selected_subject}.txt")

# FOOTER
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""<div class='footer'><b>🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</b><br>Hệ thống hỗ trợ chuyên môn - Đổi mới kiểm tra đánh giá theo Thông tư 27</div>""", unsafe_allow_html=True)
