import streamlit as st
import google.generativeai as genai
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import io
import pypdf
import re
import json

# Import dữ liệu cứng (nếu có)
try:
    from data_matrices import SAMPLE_MATRICES
except ImportError:
    SAMPLE_MATRICES = {}

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🏫", layout="wide")

# --- QUẢN LÝ SESSION ---
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = ''
if 'selected_color' not in st.session_state: st.session_state.selected_color = ''
if 'topic_df' not in st.session_state: st.session_state.topic_df = None 
if 'auto_config' not in st.session_state: st.session_state.auto_config = {}

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    /* 1. ẨN GIAO DIỆN MẶC ĐỊNH */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* 2. THẺ TÁC GIẢ NỔI (FLOATING BADGE) */
    .floating-author-badge {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: white;
        padding: 10px 15px;
        border-radius: 50px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        border: 2px solid #0984e3;
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: transform 0.3s ease;
    }
    .floating-author-badge:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
    .author-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 2px solid #dfe6e9;
    }
    .author-info {
        display: flex;
        flex-direction: column;
        line-height: 1.2;
    }
    .author-name {
        font-weight: bold;
        color: #2d3436;
        font-size: 14px;
    }
    .author-link {
        font-size: 11px;
        color: #0984e3;
        text-decoration: none;
        font-weight: 600;
    }
    .author-link:hover {text-decoration: underline;}

    /* STYLE CHÍNH */
    .main-title {font-family: 'Times New Roman', serif; font-size: 30px; font-weight: bold; text-align: center; text-transform: uppercase; color: #2c3e50; margin-bottom: 20px;}
    .subject-card {padding: 20px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 18px; cursor: pointer; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;}
    .subject-card:hover {transform: scale(1.05);}
    .bg-blue {background-color: #3498db;} .bg-green {background-color: #2ecc71;} .bg-red {background-color: #e74c3c;}
    .bg-purple {background-color: #9b59b6;} .bg-orange {background-color: #e67e22;} .bg-teal {background-color: #1abc9c;}
</style>
""", unsafe_allow_html=True)

SUBJECTS_DATA = [
    {"name": "Toán", "icon": "📐", "color": "#3498db", "class": "bg-blue"},
    {"name": "Tiếng Việt", "icon": "📚", "color": "#e74c3c", "class": "bg-red"},
    {"name": "Tin học", "icon": "💻", "color": "#9b59b6", "class": "bg-purple"},
    {"name": "Khoa học", "icon": "🔬", "color": "#2ecc71", "class": "bg-green"},
    {"name": "Lịch sử & Địa lí", "icon": "🌏", "color": "#e67e22", "class": "bg-orange"},
    {"name": "Công nghệ", "icon": "🛠️", "color": "#1abc9c", "class": "bg-teal"},
]

# --- HÀM HIỂN THỊ ICON TÁC GIẢ ---
def show_floating_badge():
    st.markdown("""
    <div class="floating-author-badge">
        <img src="https://api.dicebear.com/9.x/avataaars/svg?seed=BapCai&backgroundColor=b6e3f4" class="author-avatar">
        <div class="author-info">
            <span class="author-name">BapCai</span>
            <a href="https://www.google.com" target="_blank" class="author-link">🌐 Trang chủ tác giả</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- XỬ LÝ WORD ---
def clean_text_for_word(text):
    if not text: return ""
    text = str(text)
    patterns = [r"^Tuyệt vời.*?\n", r"^Dưới đây là.*?\n", r"^Chắc chắn rồi.*?\n", r"^Chào bạn.*?\n"]
    for p in patterns: text = re.sub(p, "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"(PHÒNG GD|TRƯỜNG|SỞ GIÁO DỤC|CỘNG HÒA XÃ HỘI).*?(Họ và tên|Lớp).*?\n", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.replace("**", "").replace("##", "").replace("###", "").strip()

def create_docx_file(school_name, exam_name, student_info, content_body, answer_key):
    doc = Document()
    try:
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(13)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except: pass
    
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    cell_
