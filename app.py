# =======================
# app.py – Streamlit App
# =======================

import streamlit as st
import google.generativeai as genai
import io
from docx import Document

# =======================
# CẤU HÌNH API (GIỮ NGUYÊN KEY CỦA BẠN)
# =======================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# =======================
# CURRICULUM_DB – CTGDPT 2018 – TT27
# Lớp 1–2: Toán, Tiếng Việt (Kết nối tri thức)
# =======================

CURRICULUM_DB = {
    "Lớp 1": {
        "Toán": {
            "bo_sach": "Kết nối tri thức",
            "Học kỳ I": {
                "Làm quen với Toán học": {
                    "Toán học quanh ta": {
                        "yccd": [
                            "Nhận biết được toán học có trong các tình huống quen thuộc.",
                            "Bước đầu hình thành hứng thú học tập môn Toán."
                        ]
                    }
                },
                "Các số đến 10": {
                    "Các số 1, 2, 3": {
                        "yccd": [
                            "Nhận biết, đọc, viết được các số 1, 2, 3.",
                            "So sánh được các số trong phạm vi 3."
                        ]
                    },
                    "Các số 4, 5": {
                        "yccd": [
                            "Nhận biết, đọc, viết được các số 4, 5.",
                            "So sánh được các số trong phạm vi 5."
                        ]
                    }
                }
            },
            "Học kỳ II": {
                "Phép cộng, phép trừ trong phạm vi 10": {
                    "Phép cộng": {
                        "yccd": [
                            "Thực hiện được phép cộng trong phạm vi 10."
                        ]
                    },
                    "Phép trừ": {
                        "yccd": [
                            "Thực hiện được phép trừ trong phạm vi 10."
                        ]
                    }
                }
            }
        },
        "Tiếng Việt": {
            "bo_sach": "Kết nối tri thức",
            "Học kỳ I": {
                "Học vần": {
                    "Âm và chữ a, ă, â": {
                        "yccd": [
                            "Nhận biết được âm và chữ a, ă, â.",
                            "Đọc, viết được các tiếng, từ có chứa a, ă, â."
                        ]
                    }
                }
            },
            "Học kỳ II": {
                "Tập đọc": {
                    "Đọc đoạn ngắn": {
                        "yccd": [
                            "Đọc trôi chảy đoạn văn ngắn.",
                            "Hiểu nội dung chính của đoạn đã đọc."
                        ]
                    }
                }
            }
        }
    },

    "Lớp 2": {
        "Toán": {
            "bo_sach": "Kết nối tri thức",
            "Học kỳ I": {
                "Các số đến 100": {
                    "Các số trong phạm vi 100": {
                        "yccd": [
                            "Đọc, viết, so sánh các số trong phạm vi 100."
                        ]
                    }
                }
            },
            "Học kỳ II": {
                "Phép nhân, phép chia": {
                    "Phép nhân": {
                        "yccd": [
                            "Nhận biết phép nhân là phép cộng các số hạng bằng nhau."
                        ]
                    },
                    "Phép chia": {
                        "yccd": [
                            "Nhận biết phép chia là phép tách thành các phần bằng nhau."
                        ]
                    }
                }
            }
        },
        "Tiếng Việt": {
            "bo_sach": "Kết nối tri thức",
            "Học kỳ I": {
                "Đọc": {
                    "Đọc hiểu văn bản": {
                        "yccd": [
                            "Hiểu nội dung chính của văn bản ngắn."
                        ]
                    }
                }
            },
            "Học kỳ II": {
                "Tập làm văn": {
                    "Viết đoạn văn ngắn": {
                        "yccd": [
                            "Viết được đoạn văn ngắn theo chủ đề quen thuộc."
                        ]
                    }
                }
            }
        }
    }
}

# =======================
# TEST NHANH (CÓ THỂ XOÁ SAU)
# =======================
st.title("Test CURRICULUM_DB")
st.write(list(CURRICULUM_DB.keys()))
