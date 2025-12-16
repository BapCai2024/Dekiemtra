import streamlit as st
import pandas as pd
import requests
import json
import time
from io import BytesIO

# --- 1. CẤU HÌNH TRANG (BẮT BUỘC Ở DÒNG ĐẦU TIÊN) ---
st.set_page_config(
    page_title="HỖ TRỢ RA ĐỀ THI TIỂU HỌC (KẾT NỐI TRI THỨC)",
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

# 3.1. Danh sách Môn học & Icon hiển thị ở Bước 1
SUBJECTS_DB = {
    "Lớp 1": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 2": [("Tiếng Việt", "📖"), ("Toán", "✖️")],
    "Lớp 3": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Tiếng Anh", "🇬🇧"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 4": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")],
    "Lớp 5": [("Tiếng Việt", "📖"), ("Toán", "✖️"), ("Khoa học", "🔬"), ("Lịch sử và Địa lí", "🌏"), ("Tin học", "💻"), ("Công nghệ", "🛠️")]
}

# 3.2. Dữ liệu Nội dung bài học (FULL DATA KẾT NỐI TRI THỨC)
CURRICULUM_DB = {
    "Lớp 1": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Số và Phép tính", "Bài học": "Bài 1-15: Các số đến 10, Phép cộng, phép trừ", "YCCĐ": "Đếm, đọc, viết các số trong phạm vi 10. Thực hiện phép cộng, trừ không nhớ trong phạm vi 10."},
                {"Chủ đề": "Hình học và Đo lường", "Bài học": "Bài 16-20: Hình dạng, Vị trí, Đo độ dài", "YCCĐ": "Nhận biết hình vuông, tròn, tam giác. Định vị trí trong không gian. Sử dụng thước đo độ dài."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Số và Phép tính", "Bài học": "Bài 30-50: Các số đến 100, Phép cộng, phép trừ (có nhớ)", "YCCĐ": "Đọc, viết, so sánh các số đến 100. Thực hiện phép cộng, trừ có nhớ trong phạm vi 100."},
                {"Chủ đề": "Thống kê", "Bài học": "Bài 51: Dữ liệu và biểu đồ tranh", "YCCĐ": "Thu thập, phân loại dữ liệu và đọc thông tin từ biểu đồ tranh."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Những bài học đầu tiên", "Bài học": "Bài 1-15: Các chữ cái và âm cơ bản", "YCCĐ": "Nhận biết và phát âm đúng 29 chữ cái, các âm chính. Ghép vần và đọc trơn tiếng."},
                {"Chủ đề": "Thực hành Đọc/Viết", "Bài học": "Bài 16-35: Các vần đơn giản, Tập viết chữ hoa", "YCCĐ": "Đọc trôi chảy các câu ngắn. Viết đúng chính tả các chữ đã học."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Mở rộng Vốn từ", "Bài học": "Bài 40-70: Các vần khó, Luyện tập tổng hợp", "YCCĐ": "Nhận biết và sử dụng từ chỉ sự vật, hoạt động, đặc điểm. Đọc hiểu văn bản ngắn."},
                {"Chủ đề": "Kĩ năng Nói và Nghe", "Bài học": "Luyện nói về gia đình, nhà trường", "YCCĐ": "Nói rõ ràng, mạch lạc về các chủ đề gần gũi. Kể được chuyện ngắn đã nghe."},
            ]
        }
    },
    "Lớp 2": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Số và Phép tính", "Bài học": "Bài 1-15: Ôn tập Số đến 100, Phép cộng trừ có nhớ", "YCCĐ": "Cộng, trừ có nhớ trong phạm vi 100. Giải bài toán liên quan đến cộng trừ."},
                {"Chủ đề": "Hình học và Đo lường", "Bài học": "Bài 16-25: Độ dài, khối lượng, thời gian, Hình phẳng", "YCCĐ": "Thực hiện phép tính với đơn vị đo (cm, kg, giờ, phút). Nhận biết hình tứ giác."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Số và Phép tính", "Bài học": "Bài 30-50: Số đến 1000, Phép nhân và Phép chia", "YCCĐ": "Đọc, viết, so sánh số đến 1000. Tính nhẩm, tính viết phép nhân, chia (bảng cửu chương)."},
                {"Chủ đề": "Thống kê và Xác suất", "Bài học": "Bài 51-55: Thu thập dữ liệu, Khả năng xảy ra", "YCCĐ": "Đọc và phân tích biểu đồ cột. Nêu được khả năng xảy ra của một sự kiện (chắc chắn, có thể, không thể)."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Gia đình yêu thương", "Bài học": "Bài 1-8: Câu chuyện về tình cảm gia đình", "YCCĐ": "Đọc trôi chảy văn bản. Nhận biết từ chỉ sự vật, hoạt động. Viết đoạn văn kể về người thân."},
                {"Chủ đề": "Thiên nhiên tươi đẹp", "Bài học": "Bài 9-16: Miêu tả cảnh vật, cây cối", "YCCĐ": "Mở rộng vốn từ về thiên nhiên. Luyện tập về câu cảm. Viết bài văn miêu tả ngắn."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Trường học và bạn bè", "Bài học": "Bài 17-24: Kể chuyện ở trường, Kĩ năng giao tiếp", "YCCĐ": "Luyện tập sử dụng dấu chấm, dấu phẩy. Kể lại được câu chuyện đã đọc."},
                {"Chủ đề": "Phát triển bản thân", "Bài học": "Bài 25-32: Chủ đề về lòng dũng cảm, biết ơn", "YCCĐ": "Nhận biết và sử dụng câu hỏi. Viết thư ngắn, lời nhắn."},
            ]
        }
    },
    "Lớp 3": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Số và Phép tính", "Bài học": "Bài 1-15: Số có bốn chữ số, Cộng trừ trong phạm vi 10000", "YCCĐ": "Đọc, viết, so sánh số có bốn chữ số. Thực hiện thành thạo cộng, trừ có nhớ."},
                {"Chủ đề": "Hình học và Đo lường", "Bài học": "Bài 16-25: Chu vi, Diện tích, Đơn vị đo diện tích", "YCCĐ": "Tính chu vi, diện tích hình chữ nhật, hình vuông. Đổi đơn vị đo: mét vuông, đề-xi-mét vuông."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phép tính", "Bài học": "Bài 30-45: Phép nhân, Phép chia trong phạm vi 10000", "YCCĐ": "Thực hiện nhân, chia số có bốn chữ số cho số có một chữ số. Giải các bài toán phức hợp."},
                {"Chủ đề": "Phân số (Giới thiệu)", "Bài học": "Bài 46-50: Làm quen với phân số", "YCCĐ": "Nhận biết phân số, tử số và mẫu số. Thực hiện chia đều thành các phần bằng nhau."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Khám phá thế giới", "Bài học": "Bài 1-8: Văn bản về tự nhiên và con người", "YCCĐ": "Đọc hiểu sâu hơn về nội dung. Luyện tập sử dụng từ ghép, từ láy. Viết đoạn văn miêu tả đồ vật."},
                {"Chủ đề": "Sự sẻ chia", "Bài học": "Bài 9-16: Câu chuyện về lòng nhân ái", "YCCĐ": "Nhận biết và sử dụng câu kể, câu hỏi. Mở rộng vốn từ về phẩm chất."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Hành trình kì thú", "Bài học": "Bài 17-24: Du lịch, khám phá di tích", "YCCĐ": "Viết bài văn miêu tả cảnh đẹp. Nhận biết các bộ phận chính của câu."},
                {"Chủ đề": "Khoa học và Công nghệ", "Bài học": "Bài 25-32: Văn bản thông tin về khoa học", "YCCĐ": "Tóm tắt được ý chính của văn bản thông tin. Luyện tập sử dụng dấu ngoặc kép."},
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Sản phẩm Thủ công", "Bài học": "Bài 1-4: Làm đồ chơi và vật dụng đơn giản", "YCCĐ": "Thiết kế và làm được các sản phẩm thủ công từ giấy, vải (ví dụ: bóp đựng bút)."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chăm sóc gia đình", "Bài học": "Bài 5-8: An toàn trong gia đình, Chăm sóc vật nuôi", "YCCĐ": "Nêu được nguyên tắc an toàn khi sử dụng điện. Biết cách chăm sóc một số vật nuôi phổ biến."},
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "Làm việc với máy tính", "Bài học": "Bài 1-3: Tệp, thư mục, Tổ chức thông tin", "YCCĐ": "Biết cách tạo, lưu và tìm kiếm tệp, thư mục. Nắm được khái niệm cơ bản về thông tin."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lập trình trực quan", "Bài học": "Bài 4-6: Lập trình với Scratch (Mức độ nâng cao)", "YCCĐ": "Sử dụng biến số, điều kiện rẽ nhánh (if/else) để tạo ra các chương trình tương tác."},
            ]
        }
    },
    "Lớp 4": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Số tự nhiên và Phép tính", "Bài học": "Bài 1-4: Ôn tập và Các số có nhiều chữ số", "YCCĐ": "Đọc, viết, so sánh, làm tròn các số đến lớp triệu. Nắm vững giá trị theo vị trí."},
                {"Chủ đề": "Phép tính", "Bài học": "Bài 5-9: Cộng, Trừ các số tự nhiên", "YCCĐ": "Thực hiện thành thạo phép cộng, trừ trong phạm vi các số đã học. Tính chất giao hoán, kết hợp."},
                {"Chủ đề": "Hình học và Đo lường", "Bài học": "Bài 10-14: Góc, Hai đường thẳng vuông góc, song song", "YCCĐ": "Nhận biết góc nhọn, tù, bẹt, vuông. Vẽ được hai đường thẳng vuông góc, song song đơn giản."},
                {"Chủ đề": "Phép tính", "Bài học": "Bài 15-18: Phép nhân và Phép chia", "YCCĐ": "Thực hiện nhân, chia (chia hết, chia có dư) với số có nhiều chữ số. Vận dụng tính chất phân phối."},
                {"Chủ đề": "Đo lường", "Bài học": "Bài 19-21: Đơn vị đo khối lượng và diện tích", "YCCĐ": "Sử dụng các đơn vị đo: tấn, tạ, yến, kg; km², hm², m², dm², cm² và chuyển đổi đơn vị."},
                {"Chủ đề": "Thống kê", "Bài học": "Bài 22: Biểu đồ cột", "YCCĐ": "Đọc, phân tích và lập được biểu đồ cột đơn giản."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phân số", "Bài học": "Bài 34-37: Khái niệm Phân số, Phân số bằng nhau", "YCCĐ": "Nhận biết, đọc, viết phân số. Áp dụng tính chất cơ bản để rút gọn, quy đồng mẫu số."},
                {"Chủ đề": "Phép tính với Phân số", "Bài học": "Bài 38-40: Cộng, Trừ, Nhân, Chia Phân số", "YCCĐ": "Thực hiện thành thạo các phép tính cộng, trừ, nhân, chia phân số."},
                {"Chủ đề": "Tỉ số và Tỉ lệ", "Bài học": "Bài 41-43: Tìm hai số khi biết Tổng và Hiệu", "YCCĐ": "Giải các bài toán cơ bản về tìm hai số khi biết tổng và hiệu của chúng."},
                {"Chủ đề": "Hình học", "Bài học": "Bài 50-54: Hình bình hành, Hình thoi, Diện tích", "YCCĐ": "Nhận biết đặc điểm, tính chu vi và diện tích Hình bình hành, Hình thoi."},
                {"Chủ đề": "Số thập phân (Giới thiệu)", "Bài học": "Bài 55: Giới thiệu bước đầu về Số thập phân", "YCCĐ": "Nhận biết bước đầu về số thập phân và chuyển đổi phân số thập phân sang số thập phân."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Bài 1-4: Điều ước của vua Mi-đát, Thi nhạc, v.v.", "YCCĐ": "Đọc hiểu truyện, thơ. Nhận biết danh từ, động từ. Viết đoạn văn kể chuyện."},
                {"Chủ đề": "Trải nghiệm và Khám phá", "Bài học": "Bài 5-8: Tờ báo tường của tôi, Về thăm bà, v.v.", "YCCĐ": "Đọc hiểu văn bản thông tin. Sử dụng dấu gạch ngang, dấu hai chấm. Viết thư, đơn từ."},
                {"Chủ đề": "Niềm vui sáng tạo", "Bài học": "Bài 9-12: Tiếng nói của cỏ cây, Chiếc thuyền ngoài xa, v.v.", "YCCĐ": "Nhận biết câu ghép (quan hệ nguyên nhân-kết quả). Viết bài văn miêu tả cây cối."},
                {"Chủ đề": "Quê hương và Cộng đồng", "Bài học": "Bài 13-16: Con người của những khu rừng, v.v.", "YCCĐ": "Mở rộng vốn từ về cộng đồng, quê hương. Viết bài văn thuật lại một sự việc."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Khoảnh khắc tuyệt vời", "Bài học": "Bài 17-20: Bài ca Trái Đất, v.v.", "YCCĐ": "Đọc hiểu văn bản nghệ thuật. Luyện tập về đại từ. Viết bài văn tả đồ vật."},
                {"Chủ đề": "Thế giới văn minh", "Bài học": "Bài 21-24: Văn minh lúa nước, v.v.", "YCCĐ": "Đọc hiểu văn bản khoa học. Quan hệ từ. Viết báo cáo, thuyết trình về một chủ đề."},
                {"Chủ đề": "Di sản và Phát triển", "Bài học": "Bài 25-28: Làng nghề truyền thống, v.v.", "YCCĐ": "Mở rộng vốn từ về di sản. Luyện tập về câu cảm thán. Viết bài văn miêu tả con vật."},
                {"Chủ đề": "Hòa bình và Hữu nghị", "Bài học": "Bài 29-32: Bài học từ lịch sử, v.v.", "YCCĐ": "Đọc hiểu văn bản nghị luận. Tổng kết vốn từ. Luyện tập tổng hợp, ôn tập cuối năm."},
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "Chất", "Bài học": "Bài 1-3: Tính chất, Sự chuyển thể của nước, v.v.", "YCCĐ": "Nêu được tính chất của nước. Vẽ được sơ đồ vòng tuần hoàn của nước. Nhận biết hỗn hợp."},
                {"Chủ đề": "Năng lượng", "Bài học": "Bài 4-6: Ánh sáng, Bóng tối, Âm thanh", "YCCĐ": "Giải thích được nguyên nhân có bóng tối. Nêu được vai trò và cách truyền của âm thanh."},
                {"Chủ đề": "Thực vật", "Bài học": "Bài 7-9: Đặc điểm của thực vật và Đa dạng thực vật", "YCCĐ": "Phân loại và nêu được vai trò của thực vật trong tự nhiên và đời sống con người."},
                {"Chủ đề": "Động vật", "Bài học": "Bài 10-12: Đặc điểm của động vật và Phân loại", "YCCĐ": "Phân loại động vật theo môi trường sống. Nêu được các biện pháp bảo vệ động vật."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Con người và Sức khỏe", "Bài học": "Bài 13-15: Cơ quan Hô hấp và Tuần hoàn", "YCCĐ": "Mô tả được chức năng cơ bản của hệ hô hấp, tuần hoàn. Nêu các biện pháp bảo vệ sức khỏe."},
                {"Chủ đề": "Môi trường", "Bài học": "Bài 16-18: Bảo vệ môi trường, Tài nguyên thiên nhiên", "YCCĐ": "Nêu được vai trò của tài nguyên thiên nhiên. Đề xuất các hành động bảo vệ môi trường."},
                {"Chủ đề": "Trái Đất và Không gian", "Bài học": "Bài 19-21: Trái Đất và Mặt Trời", "YCCĐ": "Mô tả được hình dạng Trái Đất, sự quay của Trái Đất tạo ra ngày và đêm. Nhận biết các hành tinh."},
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "Địa lí: Thiên nhiên", "Bài học": "Bài 1-4: Địa hình, Khí hậu và Sông ngòi Việt Nam", "YCCĐ": "Mô tả được đặc điểm chung của địa hình Việt Nam. Nêu được các loại hình thời tiết và các mùa chính."},
                {"Chủ đề": "Lịch sử: Thời kì dựng nước", "Bài học": "Bài 5-8: Nguồn gốc người Việt, Thời Hùng Vương", "YCCĐ": "Trình bày được tóm tắt về sự ra đời nhà nước Văn Lang. Nhận biết được nghề nghiệp và đời sống của người Lạc Việt."},
                {"Chủ đề": "Địa lí: Dân cư và hoạt động", "Bài học": "Bài 9-12: Dân số và Các nhóm dân tộc Việt Nam", "YCCĐ": "Mô tả được sự phân bố dân cư. Kể tên một số dân tộc tiêu biểu và nét văn hóa đặc trưng."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lịch sử: Bảo vệ độc lập", "Bài học": "Bài 13-16: Khởi nghĩa Hai Bà Trưng và Chiến thắng Bạch Đằng", "YCCĐ": "Nêu được ý nghĩa lịch sử của các sự kiện. Mô tả được vai trò của các anh hùng dân tộc."},
                {"Chủ đề": "Địa lí: Kinh tế", "Bài học": "Bài 17-20: Sản xuất nông nghiệp và Công nghiệp", "YCCĐ": "Kể tên các loại cây trồng, vật nuôi chính. Nhận biết được một số ngành công nghiệp và vai trò của nó."},
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "Máy tính và Internet", "Bài học": "Bài 1-3: Thông tin và máy tính, Mạng máy tính", "YCCĐ": "Nêu được các thành phần chính của máy tính. Biết cách truy cập Internet an toàn."},
                {"Chủ đề": "Sử dụng ứng dụng", "Bài học": "Bài 4-6: Xử lí văn bản Word và Trình chiếu PowerPoint", "YCCĐ": "Thực hiện các thao tác cơ bản: nhập văn bản, chèn hình ảnh, tạo hiệu ứng chuyển cảnh."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lập trình cơ bản", "Bài học": "Bài 7-9: Làm quen với Scratch", "YCCĐ": "Tạo được nhân vật, sử dụng các khối lệnh cơ bản (di chuyển, lặp, sự kiện) để lập trình một câu chuyện ngắn."},
                {"Chủ đề": "Thực hành", "Bài học": "Bài 10-12: Dự án sáng tạo Tin học", "YCCĐ": "Áp dụng kiến thức để hoàn thành một sản phẩm đơn giản (tờ báo tường điện tử, trò chơi nhỏ)."},
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Thủ công Kĩ thuật", "Bài học": "Bài 1-3: Vật liệu và Dụng cụ, Cắt khâu đơn giản", "YCCĐ": "Nhận biết các vật liệu cơ bản. Thực hiện các thao tác đo, cắt, khâu cơ bản để làm một sản phẩm thủ công."},
                {"Chủ đề": "Lắp ráp mô hình", "Bài học": "Bài 4-6: Lắp ráp các mô hình kĩ thuật", "YCCĐ": "Đọc và thực hiện theo hướng dẫn lắp ráp các mô hình đơn giản (ví dụ: mô hình xe lăn)."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Công nghệ Gia đình", "Bài học": "Bài 7-9: Công việc trong gia đình, Chăm sóc cây trồng", "YCCĐ": "Nêu được tầm quan trọng của việc nhà. Biết cách chăm sóc một số loại cây cảnh, rau củ thông thường."},
                {"Chủ đề": "Trang trí", "Bài học": "Bài 10-12: Thiết kế sản phẩm trang trí", "YCCĐ": "Sử dụng các vật liệu tái chế để tạo ra các sản phẩm trang trí nhà cửa đơn giản."},
            ]
        }
    },
    "Lớp 5": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "Số thập phân", "Bài học": "Bài 1-10: Khái niệm, Viết, So sánh Số thập phân", "YCCĐ": "Đọc, viết, so sánh số thập phân. Chuyển đổi giữa phân số thập phân và số thập phân."},
                {"Chủ đề": "Phép tính với Số thập phân", "Bài học": "Bài 11-20: Cộng, Trừ, Nhân Số thập phân", "YCCĐ": "Thực hiện thành thạo phép cộng, trừ, nhân số thập phân. Vận dụng giải các bài toán liên quan."},
                {"Chủ đề": "Hình học và Đo lường", "Bài học": "Bài 21-30: Hình tam giác, Hình thang, Diện tích", "YCCĐ": "Nhận biết các yếu tố và tính diện tích hình tam giác, hình thang."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Phép chia Số thập phân", "Bài học": "Bài 31-40: Phép chia Số thập phân", "YCCĐ": "Thực hiện thành thạo phép chia số thập phân cho số tự nhiên và cho số thập phân."},
                {"Chủ đề": "Tỉ số phần trăm", "Bài học": "Bài 41-45: Tỉ số phần trăm và Ứng dụng", "YCCĐ": "Nhận biết tỉ số phần trăm. Giải ba bài toán cơ bản về tỉ số phần trăm."},
                {"Chủ đề": "Đo lường Thể tích", "Bài học": "Bài 46-50: Hình hộp chữ nhật, Hình lập phương, Thể tích", "YCCĐ": "Nhận biết và tính diện tích xung quanh, toàn phần và thể tích của hình hộp chữ nhật, hình lập phương."},
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Ôn tập và Phát triển", "Bài học": "Bài 1-8: Cấu tạo từ, Luyện tập dấu câu", "YCCĐ": "Phân loại từ đơn, từ phức. Viết bài văn tả người."},
                {"Chủ đề": "Di sản và Văn hóa", "Bài học": "Bài 9-16: Văn bản về các di tích, lễ hội", "YCCĐ": "Mở rộng vốn từ về truyền thống. Luyện tập về câu ghép (quan hệ điều kiện, giả thiết)."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Bảo vệ Môi trường", "Bài học": "Bài 17-24: Các văn bản về thiên nhiên, môi trường", "YCCĐ": "Viết bài văn nghị luận ngắn về môi trường. Tổng kết ngữ pháp và dấu câu."},
                {"Chủ đề": "Tổng kết cuối cấp", "Bài học": "Bài 25-35: Ôn tập tổng hợp", "YCCĐ": "Đọc hiểu và đánh giá các thể loại văn bản. Hoàn thiện kĩ năng viết các kiểu bài tập làm văn."},
            ]
        },
        "Khoa học": {
            "Học kỳ I": [
                {"Chủ đề": "Cơ thể người", "Bài học": "Bài 1-5: Sự lớn lên và phát triển của cơ thể", "YCCĐ": "Mô tả được các giai đoạn phát triển và cách phòng tránh một số bệnh thường gặp."},
                {"Chủ đề": "Môi trường và Tài nguyên", "Bài học": "Bài 6-10: Bảo vệ nguồn nước, không khí, đất", "YCCĐ": "Nêu được vai trò và biện pháp bảo vệ các tài nguyên tự nhiên. Sử dụng tiết kiệm năng lượng."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vật chất và Năng lượng", "Bài học": "Bài 11-15: Sự biến đổi của vật chất, Nhiệt", "YCCĐ": "Phân biệt được sự biến đổi vật lí và hóa học. Nhận biết vật dẫn nhiệt, cách nhiệt."},
                {"Chủ đề": "Không gian", "Bài học": "Bài 16-20: Trái Đất và Hệ Mặt Trời", "YCCĐ": "Mô tả sự vận động của Trái Đất và các hiện tượng liên quan (ngày đêm, mùa)."},
            ]
        },
        "Lịch sử và Địa lí": {
            "Học kỳ I": [
                {"Chủ đề": "Lịch sử: Thời kì phong kiến", "Bài học": "Bài 1-8: Đinh, Tiền Lê, Lý, Trần", "YCCĐ": "Mô tả được sự kiện quan trọng của các triều đại. Nêu được ý nghĩa của các cuộc kháng chiến tiêu biểu."},
                {"Chủ đề": "Địa lí: Khu vực và Quốc gia", "Bài học": "Bài 9-16: Châu Á, Châu Âu", "YCCĐ": "Mô tả được vị trí, đặc điểm nổi bật của các châu lục. Nêu tên một số quốc gia tiêu biểu."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lịch sử: Thời kì cận hiện đại", "Bài học": "Bài 17-24: Quang Trung, Chiến thắng Điện Biên Phủ", "YCCĐ": "Trình bày được tóm tắt các sự kiện lịch sử cận đại. Nêu được ý nghĩa của sự kiện thành lập nước Việt Nam DCCH."},
                {"Chủ đề": "Địa lí: Toàn cầu", "Bài học": "Bài 25-30: Các đại dương, Thế giới", "YCCĐ": "Nhận biết các đại dương trên thế giới. Nắm được vai trò của Biển Đông."},
            ]
        },
        "Tin học": {
            "Học kỳ I": [
                {"Chủ đề": "Làm việc với Dữ liệu", "Bài học": "Bài 1-3: Bảng tính Excel cơ bản", "YCCĐ": "Nhập dữ liệu, thực hiện các phép tính cơ bản (cộng, trừ) trong bảng tính."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thiết kế và Lập trình", "Bài học": "Bài 4-6: Thiết kế bài trình chiếu nâng cao, Lập trình điều khiển", "YCCĐ": "Sử dụng hình ảnh động, âm thanh trong PowerPoint. Lập trình giải các bài toán nhỏ."},
            ]
        },
        "Công nghệ": {
            "Học kỳ I": [
                {"Chủ đề": "Kĩ thuật trong đời sống", "Bài học": "Bài 1-4: An toàn khi dùng đồ điện, Lắp ráp mạch điện đơn giản", "YCCĐ": "Thực hiện được các thao tác lắp ráp một mạch điện đơn giản (đèn pin)."},
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chế biến và Bảo quản", "Bài học": "Bài 5-8: Chế biến thực phẩm an toàn, Bảo quản đồ dùng", "YCCĐ": "Nêu được các nguyên tắc an toàn thực phẩm. Biết cách bảo quản một số đồ dùng gia đình."},
            ]
        }
    }
}

# --- 4. CÁC HÀM XỬ LÝ ---

def get_curriculum_data(grade, subject):
    """
    Lấy dữ liệu bài học từ CURRICULUM_DB
    Vì dữ liệu mới chia theo Học kỳ, nên hàm này sẽ gộp (flatten) lại
    để hiển thị trên cùng một bảng chọn.
    """
    data_by_term = CURRICULUM_DB.get(grade, {}).get(subject, {})
    
    # Nếu không có dữ liệu
    if not data_by_term:
        return []
    
    # Nếu dữ liệu dạng List (cấu trúc cũ) -> trả về luôn
    if isinstance(data_by_term, list):
        return data_by_term
        
    # Nếu dữ liệu dạng Dict (chia theo Học kỳ) -> gộp lại
    flat_list = []
    if isinstance(data_by_term, dict):
        for term, lessons in data_by_term.items():
            for lesson in lessons:
                # Tạo bản sao để không ảnh hưởng dữ liệu gốc
                lesson_copy = lesson.copy()
                # Thêm cột "Học kỳ" để người dùng dễ phân biệt
                lesson_copy['Học kỳ'] = term 
                flat_list.append(lesson_copy)
                
    return flat_list

def read_file_content(uploaded_file):
    """Đọc file upload"""
    if uploaded_file is None: return ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif uploaded_file.name.endswith(('.docx', '.doc')):
            import docx
            doc = docx.Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
            return df.to_string()
    except Exception as e:
        return f"Lỗi đọc file: {e}"
    return ""

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

def generate_exam_final(api_key, grade, subject, content):
    """Gọi AI tạo đề (có Retry)"""
    clean_key = api_key.strip()
    if not clean_key: return "⚠️ Chưa nhập API Key."

    with st.spinner("Đang kết nối máy chủ Google..."):
        model_name = find_working_model(clean_key)
    
    if not model_name:
        return "❌ Lỗi Key hoặc Mạng. Vui lòng kiểm tra lại API Key."

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={clean_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    Bạn là Tổ trưởng chuyên môn trường TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN.
    
    NHIỆM VỤ:
    Dựa TUYỆT ĐỐI vào nội dung kiến thức được cung cấp dưới đây để ra đề thi môn {subject} lớp {grade}.
    
    NỘI DUNG KIẾN THỨC ĐẦU VÀO:
    --------------------------
    {content}
    --------------------------
    
    YÊU CẦU BẮT BUỘC:
    1. **NỘI DUNG:** Chỉ sử dụng các kiến thức trong phần đầu vào. KHÔNG bịa kiến thức ngoài.
    2. **CẤU TRÚC:** 3 mức độ (M1, M2, M3).
    3. **ĐỐI TƯỢNG:** Học sinh vùng cao, ngôn ngữ dễ hiểu.
    4. **ĐỊNH DẠNG:**
       - PHẦN 1: ĐỀ KIỂM TRA (Tiêu đề: TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN).
       - PHẦN 2: HƯỚNG DẪN CHẤM VÀ MA TRẬN.
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

# Lấy danh sách môn từ SUBJECTS_DB
subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
selected_subject_full = st.selectbox("Chọn môn:", subjects_list)
selected_subject = selected_subject_full.split(" ", 1)[1]

st.markdown("---")

# BƯỚC 2: CHỌN DỮ LIỆU ĐẦU VÀO
st.subheader("2. Dữ liệu đầu vào")

tab1, tab2 = st.tabs(["✅ Chọn từ Chương trình học", "📂 Tải file Ma trận có sẵn"])

final_content_for_ai = ""

# TAB 1: DATA EDITOR (CHỌN TỪ DB)
with tab1:
    st.caption(f"Chọn các bài học trong chương trình **{selected_grade} - {selected_subject}**")
    data_source = get_curriculum_data(selected_grade, selected_subject)
    
    if not data_source:
        st.warning(f"Hiện tại code mẫu chưa có dữ liệu chi tiết cho môn này. Vui lòng dùng Tab **'Tải file Ma trận'**.")
    else:
        df = pd.DataFrame(data_source)
        df.insert(0, "Chọn", False)
        
        edited_df = st.data_editor(
            df,
            column_config={
                "Chọn": st.column_config.CheckboxColumn("Tích chọn", default=False),
                "Học kỳ": st.column_config.TextColumn("Học kỳ", width="small"),
                "Chủ đề": st.column_config.TextColumn("Chủ đề", width="small"),
                "Bài học": st.column_config.TextColumn("Tên bài học", width="medium"),
                "YCCĐ": st.column_config.TextColumn("Yêu cầu cần đạt", width="large"),
            },
            disabled=["Học kỳ", "Chủ đề", "Bài học", "YCCĐ"],
            hide_index=True,
            use_container_width=True
        )
        
        selected_rows = edited_df[edited_df["Chọn"] == True]
        if not selected_rows.empty:
            st.success(f"Đã chọn {len(selected_rows)} nội dung.")
            final_content_for_ai = "DANH SÁCH CÁC BÀI HỌC CẦN KIỂM TRA:\n"
            for index, row in selected_rows.iterrows():
                final_content_for_ai += f"- [{row['Học kỳ']}] Chủ đề: {row['Chủ đề']} | Bài: {row['Bài học']} | Yêu cầu: {row['YCCĐ']}\n"
        else:
            st.info("Hãy tích chọn vào ô 'Chọn' các bài học bạn muốn ra đề.")

# TAB 2: UPLOAD
with tab2:
    st.caption("Nếu nội dung bài học không có trong danh sách trên, bạn hãy tải file lên.")
    uploaded_file = st.file_uploader("Upload file (PDF, Word, Excel)", type=['pdf','docx','doc','xlsx'])
    if uploaded_file:
        file_txt = read_file_content(uploaded_file)
        if len(file_txt) > 50:
            st.success(f"Đã đọc file: {len(file_txt)} ký tự")
            final_content_for_ai = file_txt
        else:
            st.warning("File không đọc được hoặc quá ngắn.")

# NÚT TẠO ĐỀ
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns([1, 2])
with col_btn2:
    btn_run = st.button("🚀 TẠO ĐỀ VÀ MA TRẬN", type="primary", use_container_width=True)

st.markdown("---")

# BƯỚC 3: KẾT QUẢ
st.subheader("3. Kết quả")
container = st.container(border=True)

if "result_exam" not in st.session_state:
    st.session_state.result_exam = ""

if btn_run:
    if not final_content_for_ai:
        st.error("⚠️ Bạn chưa chọn nội dung bài học hoặc chưa tải file lên!")
    else:
        st.session_state.result_exam = generate_exam_final(api_key_input, selected_grade, selected_subject, final_content_for_ai)

if st.session_state.result_exam:
    container.markdown(st.session_state.result_exam)
    st.download_button("📥 Tải xuống (Đề + Ma trận)", st.session_state.result_exam, f"De_va_Matran_{selected_subject}.txt")

# FOOTER
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""<div class='footer'><b>🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</b><br>Hệ thống hỗ trợ chuyên môn - Đổi mới kiểm tra đánh giá theo Thông tư 27</div>""", unsafe_allow_html=True)
