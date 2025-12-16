import streamlit as st
import pandas as pd
import requests
import json
import time
from io import BytesIO

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="HỖ TRỢ RA ĐỀ THI TIỂU HỌC",
    page_icon="✏️",
    layout="wide"
)

# --- CSS GIAO DIỆN ---
st.markdown("""
<style>
    .main-title { text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;}
    .grade-box { padding: 5px; border-radius: 5px; font-weight: bold; text-align: center; color: white;}
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f8f9fa; text-align: center; padding: 10px; border-top: 1px solid #ddd; z-index: 99;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- DỮ LIỆU ---
CURRICULUM_DB = {
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
        
        # --- BỔ SUNG CÁC MÔN MỚI ---
        
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
    }
}

import streamlit as st

# 1. Dán toàn bộ cấu trúc CURRICULUM_DB đã cập nhật ở trên vào đây
CURRICULUM_DB = {
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
    }
}


# 2. Xây dựng giao diện Streamlit
st.set_page_config(layout="wide")
st.title("📚 Chương trình Giáo dục Phổ thông 2018 - Lớp 4 (KNTT)")
st.subheader("Dữ liệu phân phối chương trình và Yêu cầu Cần Đạt (YCCĐ)")

# Lặp qua các Khối lớp (Ở đây chỉ có Lớp 4)
for grade, subjects in CURRICULUM_DB.items():
    # Expander Cấp 1: Lớp học
    with st.expander(f"⭐ Chi tiết {grade}", expanded=True):
        
        # Lấy danh sách tên môn học và tạo 3 cột
        subject_list = list(subjects.keys())
        num_subjects = len(subject_list)
        
        # Số cột tối đa là 3, tạo hàng động dựa trên số lượng môn học
        cols = st.columns(3) 

        # Lặp qua các Môn học và phân bổ vào các cột
        for i, subject in enumerate(subject_list):
            data = subjects[subject]
            
            # Tính toán chỉ số cột (0, 1, 2, 0, 1, 2, ...)
            col_index = i % 3
            
            with cols[col_index]:
                st.markdown(f"### 📖 {subject}")

                # Lặp qua Học kỳ (Học kỳ I, Học kỳ II)
                for term, lessons in data.items():
                    # Expander Cấp 2: Học kỳ (Nút trổ xuống)
                    # Mở rộng Expander Học kỳ I mặc định
                    expanded_state = (term == "Học kỳ I") 
                    
                    with st.expander(f"📝 {term}", expanded=expanded_state):
                        
                        # Hiển thị từng bài học
                        for lesson in lessons:
                            st.markdown(f"""
                            **🎯 Chủ đề:** {lesson['Chủ đề']}
                            
                            **📚 Bài học:** `{lesson['Bài học']}`
                            
                            **✅ YCCĐ:** *{lesson['YCCĐ']}*
                            ---
                            """)
                # Thêm khoảng trắng giữa các môn học nếu cần
                st.markdown("---")

# 3. Hướng dẫn sử dụng
st.sidebar.title("Hướng dẫn")
st.sidebar.info("Sử dụng các nút mở rộng (Expander) để xem chi tiết các bài học theo Môn học và Học kỳ.")
# --- HÀM 1: ĐỌC FILE UPLOAD ---
def read_file_content(uploaded_file):
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

# --- HÀM 2: TỰ ĐỘNG TÌM MODEL ---
def find_working_model(api_key):
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

# --- HÀM 3: GỌI AI VỚI CƠ CHẾ CHỐNG LỖI 429 ---
def generate_exam_final(api_key, grade, subject, content):
    clean_key = api_key.strip()
    if not clean_key: return "⚠️ Chưa nhập API Key."

    with st.spinner("Đang kết nối máy chủ Google..."):
        model_name = find_working_model(clean_key)
    
    if not model_name:
        return "❌ Lỗi Key hoặc Mạng. Vui lòng kiểm tra lại API Key."

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={clean_key}"
    headers = {'Content-Type': 'application/json'}
    
    # PROMPT ĐƯỢC CẬP NHẬT: Yêu cầu bám sát file và xuất cả ma trận
    prompt = f"""
    Bạn là Tổ trưởng chuyên môn trường TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN.
    
    NHIỆM VỤ:
    Dựa TUYỆT ĐỐI vào nội dung văn bản (Ma trận/Đặc tả) tôi cung cấp dưới đây để ra đề thi môn {subject} lớp {grade}.
    
    NỘI DUNG VĂN BẢN ĐẦU VÀO:
    --------------------------
    {content}
    --------------------------
    
    YÊU CẦU BẮT BUỘC:
    1. **NỘI DUNG:** Chỉ được sử dụng các đơn vị kiến thức có trong văn bản đầu vào ở trên. KHÔNG được tự ý bịa ra kiến thức nằm ngoài file này.
    2. **CẤU TRÚC:** Đề thi phải đúng theo các mức độ (M1, M2, M3) đã mô tả trong văn bản đầu vào.
    3. **ĐỐI TƯỢNG:** Ngôn ngữ trong sáng, ngắn gọn, phù hợp học sinh vùng cao.
    4. **ĐỊNH DẠNG ĐẦU RA:** Phải trình bày thành 2 phần rõ ràng:
       - PHẦN 1: ĐỀ KIỂM TRA (Có tiêu đề "TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN" ở trên cùng).
       - PHẦN 2: HƯỚNG DẪN CHẤM VÀ MA TRẬN ĐỀ (Liệt kê đáp án đúng và ma trận câu hỏi tương ứng).
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    # CƠ CHẾ RETRY (THỬ LẠI KHI GẶP LỖI 429)
    max_retries = 3 # Số lần thử lại tối đa
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                st.toast(f"Hệ thống đang bận, đang thử lại lần {attempt+1}...")
                time.sleep(3 + (attempt * 2)) # Chờ 3s, 5s... tăng dần

            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                try:
                    return response.json()['candidates'][0]['content']['parts'][0]['text']
                except:
                    return "⚠️ AI không trả về nội dung. Hãy thử file khác."
            
            elif response.status_code == 429:
                # Nếu gặp lỗi 429 (Too Many Requests), vòng lặp sẽ tiếp tục thử lại
                continue 
            
            else:
                return f"⚠️ Lỗi từ Google ({response.status_code}): {response.text}"
                
        except Exception as e:
            return f"Lỗi mạng: {e}"

    return "⚠️ Hệ thống Google đang quá tải (Lỗi 429). Vui lòng đợi 1-2 phút sau rồi ấn lại nút Tạo đề."

# --- GIAO DIỆN CHÍNH ---
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
    st.info("Hệ thống đã tích hợp cơ chế chống nghẽn mạng (Anti-429 Error).")

# BƯỚC 1: CHỌN LỚP & MÔN
st.subheader("1. Chọn Lớp & Môn Học")
selected_grade = st.radio("Chọn khối:", list(SUBJECTS_DB.keys()), horizontal=True)

# Hiển thị màu lớp đẹp hơn
colors = {"Lớp 1": "#D32F2F", "Lớp 2": "#E65100", "Lớp 3": "#F57F17", "Lớp 4": "#2E7D32", "Lớp 5": "#1565C0"}
st.markdown(f"<div style='background-color:{colors[selected_grade]}; color:white; padding:5px; border-radius:5px; text-align:center;'>Đang làm việc với: {selected_grade}</div>", unsafe_allow_html=True)

# Lấy môn học
subjects_list = [f"{s[1]} {s[0]}" for s in SUBJECTS_DB[selected_grade]]
selected_subject_full = st.selectbox("Chọn môn:", subjects_list)
selected_subject = selected_subject_full.split(" ", 1)[1]

st.markdown("---")

# BƯỚC 2: UPLOAD & XỬ LÝ
c1, c2 = st.columns([1, 1], gap="large")

with c1:
    st.subheader("2. Dữ liệu đầu vào")
    st.info("💡 Lưu ý: AI sẽ chỉ lấy kiến thức CÓ TRONG FILE này để ra đề.")
    uploaded_file = st.file_uploader("Upload Ma trận/Đặc tả (PDF, Word, Excel)", type=['pdf','docx','doc','xlsx'])
    
    file_txt = ""
    if uploaded_file:
        file_txt = read_file_content(uploaded_file)
        if len(file_txt) > 50:
            st.success(f"✅ Đã đọc nội dung file ({len(file_txt)} ký tự)")
        else:
            st.warning("⚠️ File trống hoặc không đọc được chữ. Hãy kiểm tra lại.")
    
    st.write("")
    btn_run = st.button("🚀 TẠO ĐỀ VÀ MA TRẬN", type="primary", use_container_width=True)

with c2:
    st.subheader("3. Kết quả")
    container = st.container(border=True)
    
    if "result_exam" not in st.session_state:
        st.session_state.result_exam = ""
        
    if btn_run:
        if not uploaded_file:
            st.warning("⚠️ Vui lòng upload file ma trận trước!")
        elif len(file_txt) < 50:
             st.error("⚠️ Nội dung file quá ngắn hoặc không đọc được.")
        else:
            st.session_state.result_exam = generate_exam_final(api_key_input, selected_grade, selected_subject, file_txt)

    # Hiển thị
    if st.session_state.result_exam:
        container.markdown(st.session_state.result_exam)
        # Nút tải xuống cập nhật tên
        st.download_button("📥 Tải xuống (Đề + Ma trận)", st.session_state.result_exam, f"De_va_Matran_{selected_subject}.txt")

# FOOTER
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""<div class='footer'><b>🏫 TRƯỜNG PTDTBT TIỂU HỌC GIÀNG CHU PHÌN</b><br>Hệ thống hỗ trợ chuyên môn - Đổi mới kiểm tra đánh giá theo Thông tư 27</div>""", unsafe_allow_html=True)
