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

# --- 3. CƠ SỞ DỮ LIỆU ĐẦY ĐỦ (FULL DATABASE) ---
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
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 1: Các số 0, 1, 2, 3, 4, 5 (3 tiết)", "YCCĐ": "Đếm, đọc, viết các số trong phạm vi 5."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 2: Các số 6, 7, 8, 9, 10 (4 tiết)", "YCCĐ": "Đếm, đọc, viết các số từ 6 đến 10."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 3: Nhiều hơn, ít hơn, bằng nhau (2 tiết)", "YCCĐ": "So sánh số lượng giữa hai nhóm đối tượng."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 4: So sánh số (2 tiết)", "YCCĐ": "Sử dụng dấu >, <, = để so sánh các số PV 10."},
                {"Chủ đề": "1. Các số từ 0 đến 10", "Bài học": "Bài 5: Mấy và mấy (2 tiết)", "YCCĐ": "Làm quen với tách số và gộp số."},
                {"Chủ đề": "2. Làm quen với hình phẳng", "Bài học": "Bài 6: Luyện tập chung (2 tiết)", "YCCĐ": "Củng cố về đếm, đọc, viết, so sánh số."},
                {"Chủ đề": "2. Làm quen với hình phẳng", "Bài học": "Bài 7: Hình vuông, hình tròn, hình tam giác, hình chữ nhật (3 tiết)", "YCCĐ": "Nhận dạng và gọi tên đúng các hình phẳng."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 8: Phép cộng trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép cộng; hiểu ý nghĩa thêm vào/gộp lại."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 9: Phép trừ trong phạm vi 10 (3 tiết)", "YCCĐ": "Thực hiện phép trừ; hiểu ý nghĩa bớt đi/tách ra."},
                {"Chủ đề": "3. Phép cộng, trừ PV 10", "Bài học": "Bài 10: Luyện tập chung (3 tiết)", "YCCĐ": "Vận dụng cộng trừ giải quyết tình huống thực tế."},
                {"Chủ đề": "4. Làm quen khối hình", "Bài học": "Bài 14: Khối lập phương, khối hộp chữ nhật (2 tiết)", "YCCĐ": "Nhận dạng khối lập phương, khối hộp chữ nhật."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Các số đến 100", "Bài học": "Bài 21: Số có hai chữ số (3 tiết)", "YCCĐ": "Đọc, viết, nhận biết cấu tạo số có hai chữ số."},
                {"Chủ đề": "5. Các số đến 100", "Bài học": "Bài 22: So sánh số có hai chữ số (2 tiết)", "YCCĐ": "Biết cách so sánh hai số có hai chữ số."},
                {"Chủ đề": "5. Các số đến 100", "Bài học": "Bài 23: Bảng các số từ 1 đến 100 (2 tiết)", "YCCĐ": "Nhận biết thứ tự số; số liền trước, liền sau."},
                {"Chủ đề": "6. Cộng, trừ PV 100", "Bài học": "Bài 29: Phép cộng số có hai chữ số với số có một chữ số (2 tiết)", "YCCĐ": "Cộng không nhớ; đặt tính rồi tính."},
                {"Chủ đề": "6. Cộng, trừ PV 100", "Bài học": "Bài 30: Phép cộng số có hai chữ số với số có hai chữ số (2 tiết)", "YCCĐ": "Cộng không nhớ số có 2 chữ số."},
                {"Chủ đề": "6. Cộng, trừ PV 100", "Bài học": "Bài 32: Phép trừ số có hai chữ số cho số có một chữ số (2 tiết)", "YCCĐ": "Trừ không nhớ; đặt tính rồi tính."},
                {"Chủ đề": "7. Thời gian, Đo lường", "Bài học": "Bài 35: Các ngày trong tuần (1 tiết)", "YCCĐ": "Biết thứ tự các ngày trong tuần; đọc thời khóa biểu."},
                {"Chủ đề": "7. Thời gian, Đo lường", "Bài học": "Bài 36: Thực hành xem lịch và giờ (2 tiết)", "YCCĐ": "Xem giờ đúng trên đồng hồ; xem lịch tờ."},
                {"Chủ đề": "8. Ôn tập cuối năm", "Bài học": "Bài 38: Ôn tập các số và phép tính (3 tiết)", "YCCĐ": "Tổng hợp kiến thức số học và phép tính."},
                {"Chủ đề": "8. Ôn tập cuối năm", "Bài học": "Bài 39: Ôn tập hình học và đo lường (2 tiết)", "YCCĐ": "Tổng hợp kiến thức hình học, đo lường, giải toán."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 1: A a (2 tiết)", "YCCĐ": "Nhận biết, đọc, viết đúng âm a, chữ a."},
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 2: B b, dấu huyền (2 tiết)", "YCCĐ": "Đọc đúng âm b, thanh huyền; tiếng bà."},
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 3: C c, dấu sắc (2 tiết)", "YCCĐ": "Đọc đúng âm c, thanh sắc; tiếng cá."},
                {"Chủ đề": "Làm quen chữ cái", "Bài học": "Bài 4: E e, Ê ê (2 tiết)", "YCCĐ": "Phân biệt e và ê; tiếng bè, bê."},
                {"Chủ đề": "Học vần", "Bài học": "Bài 16: M m, N n (2 tiết)", "YCCĐ": "Đọc, viết đúng âm m, n và từ ngữ ứng dụng."},
                {"Chủ đề": "Học vần", "Bài học": "Bài 25: ng, ngh (2 tiết)", "YCCĐ": "Phân biệt quy tắc chính tả ng/ngh."},
                {"Chủ đề": "Học vần", "Bài học": "Bài 36: am, ap (2 tiết)", "YCCĐ": "Đọc trơn, hiểu nghĩa từ ngữ chứa vần am, ap."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chủ điểm: Gia đình", "Bài học": "Bài đọc: Ngôi nhà (2 tiết)", "YCCĐ": "Đọc trơn bài thơ; hiểu tình cảm yêu thương gia đình."},
                {"Chủ đề": "Chủ điểm: Gia đình", "Bài học": "Bài đọc: Quà của bố (2 tiết)", "YCCĐ": "Hiểu tình cảm của người bố qua những món quà đơn sơ."},
                {"Chủ đề": "Chủ điểm: Thiên nhiên", "Bài học": "Bài đọc: Hoa kết trái (2 tiết)", "YCCĐ": "Nhận biết tên gọi, đặc điểm các loại hoa quả."},
                {"Chủ đề": "Chủ điểm: Nhà trường", "Bài học": "Bài đọc: Trường em (2 tiết)", "YCCĐ": "Hiểu vẻ đẹp ngôi trường và tình cảm thầy trò."},
                {"Chủ đề": "Chủ điểm: Bác Hồ", "Bài học": "Bài đọc: Bác Hồ và thiếu nhi (2 tiết)", "YCCĐ": "Cảm nhận tình thương yêu của Bác dành cho thiếu nhi."},
                {"Chủ đề": "Chủ điểm: Đất nước", "Bài học": "Bài đọc: Hồ Gươm (2 tiết)", "YCCĐ": "Biết truyền thuyết Hồ Gươm và vẻ đẹp thủ đô."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 2 (KNTT)
    # =================================================================================
    "Lớp 2": {
        "Toán": {
            "Học kỳ I": [
                {"Chủ đề": "1. Ôn tập và bổ sung", "Bài học": "Bài 1: Ôn tập các số đến 100 (2 tiết)", "YCCĐ": "Củng cố đọc, viết, so sánh số trong phạm vi 100."},
                {"Chủ đề": "2. Phép cộng, trừ qua 10", "Bài học": "Bài 6: Bảng cộng (qua 10) (3 tiết)", "YCCĐ": "Thực hiện thành thạo cộng qua 10 trong phạm vi 20."},
                {"Chủ đề": "2. Phép cộng, trừ qua 10", "Bài học": "Bài 7: Bảng trừ (qua 10) (3 tiết)", "YCCĐ": "Thực hiện thành thạo trừ qua 10 trong phạm vi 20."},
                {"Chủ đề": "2. Phép cộng, trừ qua 10", "Bài học": "Bài 13: Bài toán về nhiều hơn, ít hơn (2 tiết)", "YCCĐ": "Giải bài toán có lời văn dạng nhiều hơn/ít hơn."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 18: Đường thẳng, đường cong (1 tiết)", "YCCĐ": "Nhận biết, phân biệt đường thẳng và đường cong."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 19: Điểm, đoạn thẳng (1 tiết)", "YCCĐ": "Nhận biết điểm, đoạn thẳng; đo độ dài đoạn thẳng."},
                {"Chủ đề": "4. Đo lường", "Bài học": "Bài 22: Ngày, tháng (2 tiết)", "YCCĐ": "Biết xem lịch tháng; số ngày trong các tháng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "5. Phép nhân, chia", "Bài học": "Bài 40: Bảng nhân 2 (2 tiết)", "YCCĐ": "Thành lập và học thuộc bảng nhân 2."},
                {"Chủ đề": "5. Phép nhân, chia", "Bài học": "Bài 41: Bảng nhân 5 (2 tiết)", "YCCĐ": "Thành lập và học thuộc bảng nhân 5."},
                {"Chủ đề": "5. Phép nhân, chia", "Bài học": "Bài 45: Bảng chia 2 (2 tiết)", "YCCĐ": "Dựa vào bảng nhân 2 lập bảng chia 2; tính nhẩm."},
                {"Chủ đề": "6. Các số đến 1000", "Bài học": "Bài 48: Đơn vị, chục, trăm, nghìn (2 tiết)", "YCCĐ": "Nhận biết hàng đơn vị, chục, trăm của số có 3 chữ số."},
                {"Chủ đề": "6. Các số đến 1000", "Bài học": "Bài 59: Phép cộng (có nhớ) trong PV 1000 (3 tiết)", "YCCĐ": "Thực hiện cộng có nhớ số có 3 chữ số."},
                {"Chủ đề": "6. Các số đến 1000", "Bài học": "Bài 62: Phép trừ (có nhớ) trong PV 1000 (3 tiết)", "YCCĐ": "Thực hiện trừ có nhớ số có 3 chữ số."},
                {"Chủ đề": "7. Ôn tập cuối năm", "Bài học": "Bài 70: Ôn tập chung (3 tiết)", "YCCĐ": "Hệ thống kiến thức toán học cả năm."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Tôi là học sinh lớp 2 (2 tiết)", "YCCĐ": "Hiểu sự thay đổi, trưởng thành khi lên lớp 2."},
                {"Chủ đề": "Em là học sinh", "Bài học": "Đọc: Ngày hôm qua đâu rồi? (2 tiết)", "YCCĐ": "Hiểu giá trị thời gian; biết làm việc có ích."},
                {"Chủ đề": "Bạn bè", "Bài học": "Đọc: Út Tin (2 tiết)", "YCCĐ": "Nhận biết đặc điểm ngoại hình, tính cách nhân vật."},
                {"Chủ đề": "Bạn bè", "Bài học": "Đọc: Tóc xoăn và tóc thẳng (2 tiết)", "YCCĐ": "Tôn trọng sự khác biệt của bạn bè."},
                {"Chủ đề": "Thầy cô", "Bài học": "Đọc: Cô giáo lớp em (2 tiết)", "YCCĐ": "Cảm nhận tình yêu thương của cô giáo."},
                {"Chủ đề": "Vòng tay yêu thương", "Bài học": "Đọc: Bà nội, bà ngoại (2 tiết)", "YCCĐ": "Cảm nhận tình cảm bà cháu sâu sắc."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Mùa nước nổi (2 tiết)", "YCCĐ": "Nhận biết vẻ đẹp thiên nhiên miền Tây mùa nước nổi."},
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Đường đến trường (2 tiết)", "YCCĐ": "Cảm nhận vẻ đẹp thân thuộc cảnh vật đường đi học."},
                {"Chủ đề": "Bốn mùa", "Bài học": "Đọc: Chuyện bốn mùa (2 tiết)", "YCCĐ": "Hiểu đặc điểm, ích lợi của Xuân, Hạ, Thu, Đông."},
                {"Chủ đề": "Thiên nhiên", "Bài học": "Đọc: Loài chim học xây tổ (2 tiết)", "YCCĐ": "Hiểu tập tính của các loài chim; bài học về sự kiên trì."},
                {"Chủ đề": "Bác Hồ", "Bài học": "Đọc: Ai ngoan sẽ được thưởng (2 tiết)", "YCCĐ": "Hiểu bài học về lòng trung thực và tình cảm Bác Hồ."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 3
    # =================================================================================
    "Lớp 3": {
        "Tin học": { # Sách: Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 1: Các thành phần của máy tính (1 tiết)", "YCCĐ": "Nhận diện, gọi tên: Thân máy, Màn hình, Bàn phím, Chuột."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 2: Chức năng các bộ phận máy tính (1 tiết)", "YCCĐ": "Biết chức năng cơ bản của thiết bị vào, ra, thân máy."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 3: Làm quen với chuột máy tính (2 tiết)", "YCCĐ": "Cầm chuột đúng; thao tác: di chuyển, nháy, kéo thả."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 4: Làm quen với bàn phím máy tính (2 tiết)", "YCCĐ": "Nhận biết khu vực phím chính; đặt tay đúng vị trí xuất phát."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 5: Xem tin tức, giải trí trên Internet (2 tiết)", "YCCĐ": "Truy cập trang web thiếu nhi; nêu ví dụ thông tin trên mạng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chủ đề C: Tổ chức lưu trữ", "Bài học": "Bài 6: Sắp xếp để tìm kiếm (1 tiết)", "YCCĐ": "Giải thích sự cần thiết của việc sắp xếp dữ liệu."},
                {"Chủ đề": "Chủ đề C: Tổ chức lưu trữ", "Bài học": "Bài 7: Sơ đồ hình cây (1 tiết)", "YCCĐ": "Nhận biết cấu trúc cây thư mục; ổ đĩa, thư mục, tệp."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 8: Làm quen với soạn thảo văn bản (2 tiết)", "YCCĐ": "Kích hoạt phần mềm; gõ kí tự, dấu tiếng Việt (Telex/Vni)."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 9: Soạn thảo văn bản đơn giản (2 tiết)", "YCCĐ": "Gõ đoạn văn ngắn; di chuyển con trỏ; xóa sửa lỗi."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 11: Vẽ tranh đơn giản (2 tiết)", "YCCĐ": "Sử dụng công cụ vẽ (Paint) để vẽ hình cơ bản, tô màu."},
                {"Chủ đề": "Chủ đề F: Giải quyết vấn đề", "Bài học": "Bài 13: Luyện tập sử dụng chuột (2 tiết)", "YCCĐ": "Thành thạo thao tác chuột qua phần mềm trò chơi."}
            ]
        },
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Bảng nhân, bảng chia", "Bài học": "Bài 5: Bảng nhân 6 (2 tiết)", "YCCĐ": "Thành lập và thuộc bảng nhân 6; giải toán."},
                {"Chủ đề": "1. Bảng nhân, bảng chia", "Bài học": "Bài 6: Bảng chia 6 (2 tiết)", "YCCĐ": "Dựa vào bảng nhân 6 lập bảng chia 6."},
                {"Chủ đề": "1. Bảng nhân, bảng chia", "Bài học": "Bài 9: Bảng nhân 8 (2 tiết)", "YCCĐ": "Thành lập và thuộc bảng nhân 8; tính nhẩm."},
                {"Chủ đề": "2. Góc và Hình", "Bài học": "Bài 15: Góc vuông, góc không vuông (1 tiết)", "YCCĐ": "Nhận biết góc vuông; dùng ê-ke kiểm tra."},
                {"Chủ đề": "3. Phép chia số lớn", "Bài học": "Bài 38: Chia số có 3 chữ số cho số có 1 chữ số (3 tiết)", "YCCĐ": "Thực hiện phép chia hết và chia có dư."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Số đến 100.000", "Bài học": "Bài 45: Các số trong phạm vi 100000 (3 tiết)", "YCCĐ": "Đọc, viết, so sánh số có 5 chữ số."},
                {"Chủ đề": "5. Diện tích", "Bài học": "Bài 51: Diện tích của một hình (1 tiết)", "YCCĐ": "Làm quen biểu tượng diện tích; so sánh diện tích."},
                {"Chủ đề": "5. Diện tích", "Bài học": "Bài 52: Diện tích hình chữ nhật (2 tiết)", "YCCĐ": "Vận dụng quy tắc tính diện tích hình chữ nhật."},
                {"Chủ đề": "5. Diện tích", "Bài học": "Bài 53: Diện tích hình vuông (2 tiết)", "YCCĐ": "Vận dụng quy tắc tính diện tích hình vuông."},
                {"Chủ đề": "6. Cộng trừ PV 100.000", "Bài học": "Bài 58: Phép cộng trong phạm vi 100000 (2 tiết)", "YCCĐ": "Đặt tính và cộng có nhớ trong phạm vi 100.000."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Chiếc áo mùa thu (2 tiết)", "YCCĐ": "Nhận biết biện pháp nhân hóa; vẻ đẹp mùa thu."},
                {"Chủ đề": "Măng non", "Bài học": "Đọc: Ngày khai trường (2 tiết)", "YCCĐ": "Niềm vui, sự náo nức ngày tựu trường."},
                {"Chủ đề": "Cộng đồng", "Bài học": "Đọc: Lớp học trên đường (2 tiết)", "YCCĐ": "Ý nghĩa, sự cần thiết của việc học tập."},
                {"Chủ đề": "Cộng đồng", "Bài học": "Đọc: Khi cả nhà bé tí (2 tiết)", "YCCĐ": "Niềm vui sum họp gia đình qua trí tưởng tượng."},
                {"Chủ đề": "Sáng tạo", "Bài học": "Đọc: Ông tổ nghề thêu (2 tiết)", "YCCĐ": "Ca ngợi trí thông minh, sáng tạo của Trần Quốc Khái."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Lễ hội quê hương", "Bài học": "Đọc: Hội đua voi ở Tây Nguyên (2 tiết)", "YCCĐ": "Không khí tưng bừng, mạnh mẽ của lễ hội đua voi."},
                {"Chủ đề": "Lễ hội quê hương", "Bài học": "Đọc: Đua ghe ngo (2 tiết)", "YCCĐ": "Nét văn hóa lễ hội đặc sắc của đồng bào Khmer."},
                {"Chủ đề": "Thiên nhiên kì thú", "Bài học": "Đọc: Cóc kiện Trời (2 tiết)", "YCCĐ": "Giải thích hiện tượng mưa; ca ngợi sự đoàn kết."},
                {"Chủ đề": "Thiên nhiên kì thú", "Bài học": "Đọc: Mưa (2 tiết)", "YCCĐ": "Cảm nhận vẻ đẹp, sự sinh động của cơn mưa rào."}
            ]
        },
        "Công nghệ": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "Tự nhiên và Công nghệ", "Bài học": "Bài 1: Tự nhiên và Công nghệ (2 tiết)", "YCCĐ": "Phân biệt đối tượng tự nhiên và sản phẩm công nghệ."},
                {"Chủ đề": "Sử dụng đồ dùng điện", "Bài học": "Bài 2: Sử dụng đèn học (2 tiết)", "YCCĐ": "Nhận biết bộ phận đèn học; sử dụng an toàn, đúng cách."},
                {"Chủ đề": "Sử dụng đồ dùng điện", "Bài học": "Bài 3: Sử dụng quạt điện (2 tiết)", "YCCĐ": "Biết các loại quạt; sử dụng an toàn, tiết kiệm điện."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Thủ công kĩ thuật", "Bài học": "Bài 7: Làm đồ dùng học tập (3 tiết)", "YCCĐ": "Lựa chọn vật liệu, làm được ống đựng bút/thước kẻ."},
                {"Chủ đề": "Thủ công kĩ thuật", "Bài học": "Bài 8: Làm biển báo giao thông (3 tiết)", "YCCĐ": "Làm mô hình biển báo giao thông từ vật liệu đơn giản."},
                {"Chủ đề": "Thủ công kĩ thuật", "Bài học": "Bài 9: Làm đồ chơi đơn giản (3 tiết)", "YCCĐ": "Làm được đồ chơi (máy bay giấy/chong chóng) đúng quy trình."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 4
    # =================================================================================
    "Lớp 4": {
        "Tin học": { # Sách: Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 1: Các thiết bị phần cứng (1 tiết)", "YCCĐ": "Phân loại thiết bị gắn liền (thân, màn) và ngoại vi."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 2: Phần cứng và phần mềm (1 tiết)", "YCCĐ": "Hiểu mối quan hệ phụ thuộc giữa phần cứng và phần mềm."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 3: Thông tin trên trang web (2 tiết)", "YCCĐ": "Nhận biết siêu văn bản, liên kết; thao tác truy cập."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 4: Tìm kiếm thông tin trên Internet (2 tiết)", "YCCĐ": "Sử dụng máy tìm kiếm (Google); tìm theo từ khóa."},
                {"Chủ đề": "Chủ đề D: Đạo đức, pháp luật", "Bài học": "Bài 6: Bản quyền nội dung số (1 tiết)", "YCCĐ": "Giải thích sự cần thiết tôn trọng bản quyền; không sao chép trái phép."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 8: Làm quen với Scratch (2 tiết)", "YCCĐ": "Nhận biết giao diện Scratch; sân khấu, nhân vật, khối lệnh."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 9: Tạo chương trình đầu tiên (2 tiết)", "YCCĐ": "Lắp ghép khối lệnh sự kiện, hiển thị để nhân vật hoạt động."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 10: Điều khiển nhân vật (2 tiết)", "YCCĐ": "Sử dụng lệnh Motion (Di chuyển) và Looks (Hiển thị)."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 13: Tạo bài trình chiếu (2 tiết)", "YCCĐ": "Tạo slide có tiêu đề, nội dung; chèn hình ảnh minh họa."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 14: Hiệu ứng chuyển trang (2 tiết)", "YCCĐ": "Chọn và áp dụng hiệu ứng chuyển slide (Transitions) hợp lí."}
            ]
        },
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Số tự nhiên", "Bài học": "Bài 5: Dãy số tự nhiên (1 tiết)", "YCCĐ": "Nhận biết đặc điểm dãy số tự nhiên; số liền trước, sau."},
                {"Chủ đề": "1. Số tự nhiên", "Bài học": "Bài 6: Viết số tự nhiên trong hệ thập phân (1 tiết)", "YCCĐ": "Viết, đọc số; nhận biết giá trị chữ số theo vị trí."},
                {"Chủ đề": "2. Góc và Đơn vị", "Bài học": "Bài 10: Góc nhọn, góc tù, góc bẹt (2 tiết)", "YCCĐ": "Nhận biết, phân biệt các loại góc bằng thước đo góc."},
                {"Chủ đề": "2. Góc và Đơn vị", "Bài học": "Bài 11: Đơn vị đo góc. Độ (1 tiết)", "YCCĐ": "Biết đơn vị đo góc là độ; dùng thước đo góc."},
                {"Chủ đề": "3. Phép tính số tự nhiên", "Bài học": "Bài 25: Phép chia cho số có hai chữ số (3 tiết)", "YCCĐ": "Thực hiện phép chia số nhiều chữ số cho 2 chữ số."},
                {"Chủ đề": "3. Phép tính số tự nhiên", "Bài học": "Bài 27: Thương có chữ số 0 (2 tiết)", "YCCĐ": "Thực hiện chia trong trường hợp thương có chữ số 0."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Phân số", "Bài học": "Bài 40: Rút gọn phân số (2 tiết)", "YCCĐ": "Biết chia tử và mẫu cho cùng số để rút gọn phân số."},
                {"Chủ đề": "4. Phân số", "Bài học": "Bài 41: Quy đồng mẫu số các phân số (2 tiết)", "YCCĐ": "Thực hiện quy đồng mẫu số trường hợp đơn giản."},
                {"Chủ đề": "5. Phép tính phân số", "Bài học": "Bài 55: Phép cộng phân số (2 tiết)", "YCCĐ": "Cộng hai phân số cùng mẫu và khác mẫu số."},
                {"Chủ đề": "5. Phép tính phân số", "Bài học": "Bài 57: Phép nhân phân số (2 tiết)", "YCCĐ": "Nhân tử với tử, mẫu với mẫu."},
                {"Chủ đề": "6. Hình học", "Bài học": "Bài 60: Hình bình hành (1 tiết)", "YCCĐ": "Nhận biết đặc điểm cạnh đối song song và bằng nhau."},
                {"Chủ đề": "6. Hình học", "Bài học": "Bài 61: Hình thoi (1 tiết)", "YCCĐ": "Nhận biết đặc điểm cặp cạnh đối song song và 4 cạnh bằng nhau."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Điều ước của vua Mi-đát (2 tiết)", "YCCĐ": "Hiểu thông điệp: Hạnh phúc không nằm ở vàng bạc."},
                {"Chủ đề": "Mỗi người một vẻ", "Bài học": "Đọc: Tiếng nói của cỏ cây (2 tiết)", "YCCĐ": "Cảm nhận vẻ đẹp, sự sống động của thiên nhiên."},
                {"Chủ đề": "Tuổi nhỏ chí lớn", "Bài học": "Đọc: Tuổi ngựa (2 tiết)", "YCCĐ": "Cảm nhận khát vọng đi xa và tình yêu mẹ của bạn nhỏ."},
                {"Chủ đề": "Tuổi nhỏ chí lớn", "Bài học": "Đọc: Văn hay chữ tốt (2 tiết)", "YCCĐ": "Ca ngợi tinh thần kiên trì, khổ luyện của Cao Bá Quát."},
                {"Chủ đề": "Trải nghiệm", "Bài học": "Đọc: Ở Vương quốc Tương Lai (2 tiết)", "YCCĐ": "Đọc văn bản kịch; hiểu ước mơ sáng tạo của trẻ em."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Sầu riêng (2 tiết)", "YCCĐ": "Nhận biết nghệ thuật miêu tả hương vị đặc sắc của trái cây."},
                {"Chủ đề": "Vẻ đẹp quê hương", "Bài học": "Đọc: Chợ Tết (2 tiết)", "YCCĐ": "Cảm nhận bức tranh giàu màu sắc, vui tươi của chợ Tết."},
                {"Chủ đề": "Khám phá thế giới", "Bài học": "Đọc: Đường đi Sa Pa (2 tiết)", "YCCĐ": "Cảm nhận vẻ đẹp biến đổi kì ảo của thiên nhiên Sa Pa."},
                {"Chủ đề": "Khám phá thế giới", "Bài học": "Đọc: Hơn một ngàn ngày vòng quanh trái đất (2 tiết)", "YCCĐ": "Hiểu hành trình dũng cảm thám hiểm thế giới của Ma-zen-lan."},
                {"Chủ đề": "Tình yêu cuộc sống", "Bài học": "Đọc: Con sẻ (2 tiết)", "YCCĐ": "Ca ngợi lòng dũng cảm và tình mẫu tử thiêng liêng."}
            ]
        },
        "Khoa học": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Chất", "Bài học": "Bài 3: Vòng tuần hoàn của nước (2 tiết)", "YCCĐ": "Vẽ và chú thích sơ đồ vòng tuần hoàn nước."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 5: Không khí (2 tiết)", "YCCĐ": "Nêu tính chất không màu, không mùi; vai trò của không khí."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 8: Ánh sáng và bóng tối (2 tiết)", "YCCĐ": "Giải thích nguyên nhân tạo bóng tối; vật cản sáng."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 10: Âm thanh (2 tiết)", "YCCĐ": "Nêu sự lan truyền âm thanh; vật phát ra âm thanh rung động."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 11: Nhiệt độ và nhiệt kế (2 tiết)", "YCCĐ": "Biết cách sử dụng nhiệt kế đo nhiệt độ cơ thể/không khí."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 16: Nhu cầu sống của thực vật (2 tiết)", "YCCĐ": "Cây cần nước, ánh sáng, không khí, chất khoáng để sống."},
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 20: Chuỗi thức ăn (2 tiết)", "YCCĐ": "Vẽ sơ đồ chuỗi thức ăn đơn giản trong tự nhiên."},
                {"Chủ đề": "4. Nấm", "Bài học": "Bài 23: Các loại nấm (2 tiết)", "YCCĐ": "Phân biệt nấm ăn và nấm độc; ích lợi của nấm."},
                {"Chủ đề": "5. Con người và sức khỏe", "Bài học": "Bài 26: Các nhóm chất dinh dưỡng (2 tiết)", "YCCĐ": "Kể tên 4 nhóm chất; vai trò của bột đường, đạm, béo."}
            ]
        },
        "Lịch sử và Địa lí": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Địa phương em", "Bài học": "Bài 1: Làm quen với bản đồ (2 tiết)", "YCCĐ": "Nhận biết các kí hiệu bản đồ, xác định phương hướng."},
                {"Chủ đề": "2. Trung du Bắc Bộ", "Bài học": "Bài 3: Thiên nhiên vùng Trung du (2 tiết)", "YCCĐ": "Mô tả địa hình đồi bát úp, khí hậu lạnh mùa đông."},
                {"Chủ đề": "2. Trung du Bắc Bộ", "Bài học": "Bài 5: Đền Hùng và lễ giỗ tổ (2 tiết)", "YCCĐ": "Kể lại truyền thuyết Hùng Vương; ý nghĩa lễ hội Đền Hùng."},
                {"Chủ đề": "3. Đồng bằng Bắc Bộ", "Bài học": "Bài 8: Sông Hồng và văn minh lúa nước (2 tiết)", "YCCĐ": "Nêu vai trò sông Hồng; hệ thống đê điều."},
                {"Chủ đề": "3. Đồng bằng Bắc Bộ", "Bài học": "Bài 10: Thăng Long - Hà Nội (2 tiết)", "YCCĐ": "Nêu các tên gọi của Hà Nội qua các thời kì; Văn Miếu."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Duyên hải Miền Trung", "Bài học": "Bài 15: Biển đảo Việt Nam (2 tiết)", "YCCĐ": "Xác định vị trí Hoàng Sa, Trường Sa; vai trò kinh tế biển."},
                {"Chủ đề": "4. Duyên hải Miền Trung", "Bài học": "Bài 16: Phố cổ Hội An (2 tiết)", "YCCĐ": "Mô tả kiến trúc, di sản văn hóa Phố cổ Hội An."},
                {"Chủ đề": "5. Tây Nguyên", "Bài học": "Bài 18: Thiên nhiên Tây Nguyên (2 tiết)", "YCCĐ": "Mô tả đặc điểm đất đỏ bazan và các cao nguyên xếp tầng."},
                {"Chủ đề": "5. Tây Nguyên", "Bài học": "Bài 20: Văn hóa Cồng chiêng (2 tiết)", "YCCĐ": "Nêu giá trị di sản văn hóa phi vật thể Cồng chiêng."}
            ]
        },
        "Công nghệ": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 2: Các loại hoa phổ biến (2 tiết)", "YCCĐ": "Nhận biết tên, đặc điểm hoa hồng, cúc, đào, mai."},
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 3: Các loại cây cảnh phổ biến (2 tiết)", "YCCĐ": "Nhận biết cây cảnh thông dụng; ý nghĩa trang trí."},
                {"Chủ đề": "1. Hoa và cây cảnh", "Bài học": "Bài 4: Trồng cây con trong chậu (3 tiết)", "YCCĐ": "Thực hiện đúng quy trình trồng cây con trong chậu."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "2. Lắp ghép kĩ thuật", "Bài học": "Bài 6: Lắp ghép mô hình xe (3 tiết)", "YCCĐ": "Lắp được mô hình xe đẩy/xe nôi từ bộ lắp ghép."},
                {"Chủ đề": "2. Lắp ghép kĩ thuật", "Bài học": "Bài 7: Lắp ghép mô hình máy bay (3 tiết)", "YCCĐ": "Lắp được mô hình máy bay từ bộ lắp ghép kĩ thuật."},
                {"Chủ đề": "3. Đồ chơi dân gian", "Bài học": "Bài 9: Làm chong chóng (2 tiết)", "YCCĐ": "Làm được chong chóng giấy quay được theo quy trình."}
            ]
        }
    },

    # =================================================================================
    # KHỐI LỚP 5
    # =================================================================================
    "Lớp 5": {
        "Tin học": { # Sách: Cùng Khám Phá (NXB ĐH Huế)
            "Học kỳ I": [
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 1: Cây thư mục (1 tiết)", "YCCĐ": "Nhận biết cấu trúc cây thư mục; tạo, đổi tên, xóa thư mục."},
                {"Chủ đề": "Chủ đề A: Máy tính và em", "Bài học": "Bài 2: Tìm kiếm tệp và thư mục (1 tiết)", "YCCĐ": "Sử dụng công cụ tìm kiếm trong máy tính để tìm tệp."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 3: Thư điện tử (Email) (2 tiết)", "YCCĐ": "Biết cấu trúc email; soạn, gửi, nhận thư đơn giản."},
                {"Chủ đề": "Chủ đề B: Mạng máy tính", "Bài học": "Bài 4: An toàn khi sử dụng Email (1 tiết)", "YCCĐ": "Nhận biết thư rác; không mở thư lạ; bảo mật mật khẩu."},
                {"Chủ đề": "Chủ đề D: Đạo đức, pháp luật", "Bài học": "Bài 5: Bản quyền nội dung số (1 tiết)", "YCCĐ": "Hiểu khái niệm bản quyền; tôn trọng sản phẩm số."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học", "Bài học": "Bài 6: Định dạng văn bản nâng cao (2 tiết)", "YCCĐ": "Định dạng đoạn văn, căn lề, giãn dòng; chèn bảng biểu."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học (Scratch)", "Bài học": "Bài 9: Biến nhớ trong Scratch (3 tiết)", "YCCĐ": "Tạo biến nhớ; dùng biến lưu điểm số/thời gian trong game."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học (Scratch)", "Bài học": "Bài 10: Sử dụng biến trong tính toán (2 tiết)", "YCCĐ": "Sử dụng các phép toán cộng, trừ, nhân, chia với biến."},
                {"Chủ đề": "Chủ đề E: Ứng dụng tin học (Scratch)", "Bài học": "Bài 12: Cấu trúc rẽ nhánh (3 tiết)", "YCCĐ": "Sử dụng khối lệnh 'Nếu... thì...' và 'Nếu... thì... không thì...'."},
                {"Chủ đề": "Chủ đề F: Giải quyết vấn đề", "Bài học": "Bài 15: Dự án kể chuyện tương tác (4 tiết)", "YCCĐ": "Vận dụng lập trình tạo câu chuyện/trò chơi hoàn chỉnh."}
            ]
        },
        "Toán": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Số thập phân", "Bài học": "Bài 8: Số thập phân (3 tiết)", "YCCĐ": "Đọc, viết số thập phân; hiểu giá trị theo hàng."},
                {"Chủ đề": "1. Số thập phân", "Bài học": "Bài 9: Hàng của số thập phân (2 tiết)", "YCCĐ": "Xác định hàng phần mười, phần trăm, phần nghìn."},
                {"Chủ đề": "1. Số thập phân", "Bài học": "Bài 10: So sánh các số thập phân (2 tiết)", "YCCĐ": "So sánh hai số thập phân; sắp xếp thứ tự."},
                {"Chủ đề": "2. Phép tính số thập phân", "Bài học": "Bài 15: Cộng, trừ số thập phân (3 tiết)", "YCCĐ": "Đặt tính, tính đúng cộng trừ thập phân; giải toán."},
                {"Chủ đề": "2. Phép tính số thập phân", "Bài học": "Bài 18: Nhân số thập phân (3 tiết)", "YCCĐ": "Nhân số thập phân với số tự nhiên và số thập phân."},
                {"Chủ đề": "3. Hình học", "Bài học": "Bài 22: Hình tam giác (2 tiết)", "YCCĐ": "Nhận biết đặc điểm; xác định đáy, đường cao."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "4. Tỉ số phần trăm", "Bài học": "Bài 45: Tỉ số phần trăm (2 tiết)", "YCCĐ": "Hiểu ý nghĩa %; viết phân số dưới dạng %."},
                {"Chủ đề": "4. Tỉ số phần trăm", "Bài học": "Bài 46: Giải toán về tỉ số phần trăm (3 tiết)", "YCCĐ": "Giải 3 dạng toán cơ bản về tỉ số phần trăm."},
                {"Chủ đề": "5. Thể tích", "Bài học": "Bài 50: Thể tích hình lập phương (2 tiết)", "YCCĐ": "Tính thể tích hình lập phương V = a x a x a."},
                {"Chủ đề": "5. Thể tích", "Bài học": "Bài 51: Thể tích hình hộp chữ nhật (2 tiết)", "YCCĐ": "Tính thể tích hình hộp chữ nhật V = a x b x c."},
                {"Chủ đề": "6. Ôn tập", "Bài học": "Bài 65: Ôn tập về số và phép tính (3 tiết)", "YCCĐ": "Hệ thống hóa kiến thức số học lớp 5."}
            ]
        },
        "Tiếng Việt": {
            "Học kỳ I": [
                {"Chủ đề": "Việt Nam gấm vóc", "Bài học": "Đọc: Thư gửi các học sinh (2 tiết)", "YCCĐ": "Hiểu tình cảm, kỳ vọng của Bác Hồ với học sinh."},
                {"Chủ đề": "Việt Nam gấm vóc", "Bài học": "Đọc: Quang cảnh làng mạc ngày mùa (2 tiết)", "YCCĐ": "Cảm nhận vẻ đẹp trù phú, màu vàng đặc trưng làng quê."},
                {"Chủ đề": "Cánh chim hòa bình", "Bài học": "Đọc: Bài ca về trái đất (2 tiết)", "YCCĐ": "Hiểu thông điệp: Trái đất là của trẻ em, cần hòa bình."},
                {"Chủ đề": "Cánh chim hòa bình", "Bài học": "Đọc: Những con sếu bằng giấy (2 tiết)", "YCCĐ": "Tố cáo tội ác chiến tranh; khát vọng hòa bình."},
                {"Chủ đề": "Môi trường xanh", "Bài học": "Đọc: Chuyện một khu vườn nhỏ (2 tiết)", "YCCĐ": "Ý thức yêu thiên nhiên, làm đẹp môi trường sống."},
                {"Chủ đề": "Môi trường xanh", "Bài học": "Đọc: Kỳ diệu rừng xanh (2 tiết)", "YCCĐ": "Cảm nhận vẻ đẹp bí ẩn rừng xanh; ý thức bảo vệ rừng."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "Người công dân", "Bài học": "Đọc: Người công dân số Một (2 tiết)", "YCCĐ": "Hiểu tâm trạng day dứt, khát vọng cứu nước của Bác."},
                {"Chủ đề": "Người công dân", "Bài học": "Đọc: Thái sư Trần Thủ Độ (2 tiết)", "YCCĐ": "Ca ngợi tấm gương chí công vô tư của Trần Thủ Độ."},
                {"Chủ đề": "Đất nước đổi mới", "Bài học": "Đọc: Trí dũng song toàn (2 tiết)", "YCCĐ": "Ca ngợi Giang Văn Minh mưu trí, bất khuất."},
                {"Chủ đề": "Đất nước đổi mới", "Bài học": "Đọc: Tiếng rao đêm (2 tiết)", "YCCĐ": "Ca ngợi hành động xả thân cứu người của thương binh."},
                {"Chủ đề": "Nhớ nguồn", "Bài học": "Đọc: Nghĩa thầy trò (2 tiết)", "YCCĐ": "Ca ngợi truyền thống tôn sư trọng đạo của dân tộc."}
            ]
        },
        "Khoa học": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Chất", "Bài học": "Bài 1: Đất và bảo vệ đất (2 tiết)", "YCCĐ": "Nêu thành phần của đất; biện pháp bảo vệ đất."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 3: Hỗn hợp và dung dịch (2 tiết)", "YCCĐ": "Phân biệt hỗn hợp, dung dịch; tách chất."},
                {"Chủ đề": "1. Chất", "Bài học": "Bài 5: Sự biến đổi hóa học (2 tiết)", "YCCĐ": "Phân biệt biến đổi lí học (giữ nguyên) và hóa học (tạo chất mới)."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 8: Năng lượng mặt trời (2 tiết)", "YCCĐ": "Nêu vai trò chiếu sáng, sưởi ấm; ứng dụng pin mặt trời."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 9: Năng lượng chất đốt (2 tiết)", "YCCĐ": "Kể tên chất đốt; sử dụng an toàn, tiết kiệm."},
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 10: Năng lượng gió và nước chảy (2 tiết)", "YCCĐ": "Ứng dụng chạy thuyền buồm, thủy điện."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "2. Năng lượng", "Bài học": "Bài 12: Sử dụng năng lượng điện (2 tiết)", "YCCĐ": "Lắp mạch điện đơn giản; vật dẫn/cách điện; an toàn điện."},
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 16: Sự sinh sản của thực vật (2 tiết)", "YCCĐ": "Mô tả thụ phấn, thụ tinh; chỉ cơ quan sinh sản."},
                {"Chủ đề": "3. Thực vật và Động vật", "Bài học": "Bài 19: Sự sinh sản của động vật (2 tiết)", "YCCĐ": "Phân biệt động vật đẻ trứng và đẻ con; vòng đời côn trùng."},
                {"Chủ đề": "4. Con người và sức khỏe", "Bài học": "Bài 22: Sự sinh sản ở người (2 tiết)", "YCCĐ": "Sơ lược quá trình thụ tinh; sự phát triển thai nhi."},
                {"Chủ đề": "4. Con người và sức khỏe", "Bài học": "Bài 25: Chăm sóc sức khỏe tuổi dậy thì (2 tiết)", "YCCĐ": "Thực hiện vệ sinh cá nhân; phòng tránh xâm hại."}
            ]
        },
        "Lịch sử và Địa lí": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Đất nước dựng xây", "Bài học": "Bài 1: Nước Văn Lang - Âu Lạc (2 tiết)", "YCCĐ": "Nêu thời gian, địa điểm ra đời; đời sống vật chất/tinh thần."},
                {"Chủ đề": "1. Đất nước dựng xây", "Bài học": "Bài 4: Nhà Nguyễn (2 tiết)", "YCCĐ": "Sự thành lập; đóng góp về văn hóa, giáo dục; hạn chế."},
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 6: Khởi nghĩa Hai Bà Trưng (2 tiết)", "YCCĐ": "Nguyên nhân, diễn biến, ý nghĩa cuộc khởi nghĩa."},
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 8: Phong trào chống Pháp (2 tiết)", "YCCĐ": "Kể về Trương Định, Nguyễn Trung Trực, phong trào Cần Vương."},
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 10: Cách mạng tháng Tám 1945 (2 tiết)", "YCCĐ": "Sự kiện 2/9/1945 Bác Hồ đọc Tuyên ngôn Độc lập."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 12: Chiến dịch Điện Biên Phủ (3 tiết)", "YCCĐ": "Trình bày diễn biến 56 ngày đêm; ý nghĩa 'lừng lẫy năm châu'."},
                {"Chủ đề": "2. Bảo vệ tổ quốc", "Bài học": "Bài 14: Chiến dịch Hồ Chí Minh (2 tiết)", "YCCĐ": "Giải phóng miền Nam; thống nhất đất nước 1975."},
                {"Chủ đề": "3. Thế giới", "Bài học": "Bài 18: Các châu lục và đại dương (2 tiết)", "YCCĐ": "Nhận biết vị trí 6 châu lục, 4 đại dương trên bản đồ."},
                {"Chủ đề": "3. Thế giới", "Bài học": "Bài 19: Châu Á (2 tiết)", "YCCĐ": "Nêu vị trí, diện tích, khí hậu, dân cư tiêu biểu của Châu Á."},
                {"Chủ đề": "3. Thế giới", "Bài học": "Bài 21: Các nước láng giềng (2 tiết)", "YCCĐ": "Đặc điểm tự nhiên, dân cư Lào, Campuchia, Trung Quốc."}
            ]
        },
        "Công nghệ": { # KNTT
            "Học kỳ I": [
                {"Chủ đề": "1. Sáng chế", "Bài học": "Bài 3: Tìm hiểu về thiết kế (2 tiết)", "YCCĐ": "Hiểu khái niệm thiết kế; hình thành ý tưởng, phác thảo."},
                {"Chủ đề": "1. Sáng chế", "Bài học": "Bài 4: Thiết kế sản phẩm đơn giản (3 tiết)", "YCCĐ": "Vận dụng kiến thức thiết kế sản phẩm phục vụ học tập/vui chơi."},
                {"Chủ đề": "1. Sáng chế", "Bài học": "Bài 5: Dự án thiết kế của em (3 tiết)", "YCCĐ": "Thực hiện dự án thiết kế hoàn chỉnh theo nhóm."}
            ],
            "Học kỳ II": [
                {"Chủ đề": "2. Lắp ráp kĩ thuật", "Bài học": "Bài 8: Lắp ráp mô hình rô-bốt (4 tiết)", "YCCĐ": "Đọc bản vẽ, lựa chọn chi tiết, lắp ráp hoàn thiện rô-bốt."},
                {"Chủ đề": "2. Lắp ráp kĩ thuật", "Bài học": "Bài 9: Lắp ráp mô hình nhà nổi (4 tiết)", "YCCĐ": "Lắp ráp được mô hình nhà nổi; kiểm tra hoạt động."}
            ]
        }
    }
}

# --- 4. CÁC HÀM XỬ LÝ (GIỮ NGUYÊN LOGIC) ---

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
