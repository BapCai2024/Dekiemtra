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

# --- 2. CSS GIAO DIỆN (Đã thêm CSS cho Footer) ---
st.markdown("""
<style>
    .main-title { text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;}
    .question-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #1565C0; margin-bottom: 10px; }
    div.stButton > button:first-child { border-radius: 5px; }
    
    /* CSS cho Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        color: #333;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        border-top: 1px solid #ddd;
        z-index: 100;
    }
    .content-container {
        padding-bottom: 60px; /* Tạo khoảng trống để không bị footer che */
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CƠ SỞ DỮ LIỆU ĐẦY ĐỦ ---
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tiếng Anh", "🇬🇧"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

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
                {"Chủ đề": "Thủ công Kĩ thuật", "Bài học": "Bài 1-4: Làm đồ chơi và vật dụng đơn giản", "YCCĐ": "Thiết kế và làm được các sản phẩm thủ công từ giấy, vải (ví dụ: bóp đựng bút)."},
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
                {"Chủ đề": "Kĩ thuật", "Bài học": "Bài 1-3: Vật liệu và Dụng cụ, Cắt khâu đơn giản", "YCCĐ": "Nhận biết các vật liệu cơ bản. Thực hiện các thao tác đo, cắt, khâu cơ bản để làm một sản phẩm thủ công."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Gia đình", "Bài học": "Bài 7-9: Công việc trong gia đình, Chăm sóc cây trồng", "YCCĐ": "Nêu được tầm quan trọng của việc nhà. Biết cách chăm sóc một số loại cây cảnh, rau củ thông thường."},
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

st.markdown("<div class='content-container'>", unsafe_allow_html=True) # Wrapper cho nội dung chính
st.markdown("<h1 class='main-title'>HỖ TRỢ RA ĐỀ THI TIỂU HỌC 🏫</h1>", unsafe_allow_html=True)

# SIDEBAR API
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
    st.warning("⚠️ Chưa có dữ liệu cho môn này. Vui lòng cập nhật CURRICULUM_DB.")
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
    unique_topics = list(set([l['Chủ đề'] for l in lessons_in_term]))
    
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
    selected_lesson_name = st.selectbox("Chọn Bài học (có số tiết):", list(lesson_options.keys()))
    
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
    # 3.1. Hiển thị bảng tóm tắt trên web
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

    # 3.2. Xây dựng nội dung file tải về
    
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

st.markdown("</div>", unsafe_allow_html=True) # Đóng content container

# --- FOOTER (Được thêm vào cuối cùng) ---
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
