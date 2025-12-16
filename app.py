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
import os
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ Thống Hỗ Trợ Ra Đề Tiểu Học", page_icon="🏫", layout="wide")

# --- QUẢN LÝ THƯ MỤC DỮ LIỆU CỨNG ---
DATA_FOLDER = "matrix_data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# --- QUẢN LÝ SESSION (ĐÃ SỬA LỖI KHỞI TẠO) ---
if 'step' not in st.session_state: st.session_state.step = 'home'
if 'selected_subject' not in st.session_state: st.session_state.selected_subject = ''
# --- Dòng dưới đây là dòng đã được thêm để sửa lỗi AttributeError ---
if 'selected_grade' not in st.session_state: st.session_state.selected_grade = 'Lớp 1' 
if 'selected_color' not in st.session_state: st.session_state.selected_color = ''
if 'topic_df' not in st.session_state: st.session_state.topic_df = None 
if 'matrix_df_display' not in st.session_state: st.session_state.matrix_df_display = None
if 'auto_config' not in st.session_state: st.session_state.auto_config = {}

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
    
    .floating-author-badge {
        position: fixed; bottom: 20px; right: 20px; background-color: white; padding: 10px 15px;
        border-radius: 50px; box-shadow: 0 4px 15px rgba(0,0,0,0.15); border: 2px solid #0984e3; z-index: 9999;
        display: flex; align-items: center; gap: 12px; transition: transform 0.3s ease;
    }
    .floating-author-badge:hover {transform: scale(1.05);}
    .author-avatar {width: 40px; height: 40px; border-radius: 50%; border: 2px solid #dfe6e9;}
    .author-info {display: flex; flex-direction: column; line-height: 1.2;}
    .author-name {font-weight: bold; color: #2d3436; font-size: 14px;}
    .author-link {font-size: 11px; color: #0984e3; text-decoration: none; font-weight: 600;}

    .main-title {font-family: 'Times New Roman', serif; font-size: 30px; font-weight: bold; text-align: center; text-transform: uppercase; color: #2c3e50; margin-bottom: 20px;}
    .subject-card {padding: 20px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 18px; cursor: pointer; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;}
    .subject-card:hover {transform: scale(1.05);}
    .bg-blue {background-color: #3498db;} .bg-green {background-color: #2ecc71;} .bg-red {background-color: #e74c3c;}
    .bg-purple {background-color: #9b59b6;} .bg-orange {background-color: #e67e22;} .bg-teal {background-color: #1abc9c;}
    
    .step-box {border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 15px; background-color: #fcfcfc;}
    .step-header {font-weight: bold; color: #2980b9; margin-bottom: 10px; font-size: 16px;}
</style>
""", unsafe_allow_html=True)

SUBJECTS_DATA = [
    {"name": "Toán", "icon": "📐", "color": "#3498db", "class": "bg-blue"},
    {"name": "Tiếng Việt", "icon": "📚", "color": "#e74c3c", "class": "bg-red"},
    {"name": "Tin học", "icon": "💻", "color": "#9b59b6", "class": "bg-purple"},
    {"name": "Khoa học/TNXH", "icon": "🌱", "color": "#2ecc71", "class": "bg-green"},
    {"name": "Lịch sử & Địa lí", "icon": "🌏", "color": "#e67e22", "class": "bg-orange"},
    {"name": "Công nghệ", "icon": "🛠️", "color": "#1abc9c", "class": "bg-teal"},
]

def show_floating_badge():
    st.markdown("""
    <div class="floating-author-badge">
        <img src="https://api.dicebear.com/9.x/avataaars/svg?seed=BapCai&backgroundColor=b6e3f4" class="author-avatar">
        <div class="author-info">
            <span class="author-name">BapCai</span>
            <a href="#" class="author-link">🌐 Trang chủ tác giả</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- HÀM HỖ TRỢ ---
def save_uploaded_template(uploaded_file):
    if uploaded_file is not None:
        try:
            file_path = os.path.join(DATA_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
            return True
        except Exception: return False
    return False

def delete_matrix_file(filename):
    try:
        file_path = os.path.join(DATA_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception: pass
    return False

def get_matrix_files():
    try:
        if os.path.exists(DATA_FOLDER):
            return [f for f in os.listdir(DATA_FOLDER) if f.endswith(('.xlsx', '.xls', '.docx', '.pdf', '.csv'))]
    except Exception: pass
    return []

def read_file_content(file_obj, is_local=False):
    try:
        if is_local:
            file_path = os.path.join(DATA_FOLDER, file_obj)
            ext = os.path.splitext(file_obj)[1].lower()
            if ext == '.docx': return "\n".join([p.text for p in Document(file_path).paragraphs])
            elif ext == '.pdf': return "\n".join([page.extract_text() for page in pypdf.PdfReader(file_path).pages])
            elif ext in ['.xlsx', '.xls']: return pd.read_excel(file_path).to_string()
            elif ext == '.csv': return pd.read_csv(file_path).to_string()
        else:
            if file_obj.name.endswith('.docx'): return "\n".join([p.text for p in Document(file_obj).paragraphs])
            elif file_obj.name.endswith('.pdf'): return "\n".join([page.extract_text() for page in pypdf.PdfReader(file_obj).pages])
            elif file_obj.name.endswith(('.xlsx', '.xls')): return pd.read_excel(file_obj).to_string()
            elif file_obj.name.endswith('.csv'): return pd.read_csv(file_obj).to_string()
            else: return file_obj.read().decode("utf-8")
    except: return ""

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
    
    # Header: Chỉ tên trường
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(3.5)
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    run
# --- CHÂN TRANG ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>© 2025 - Trần Ngọc Hải - Trường PTDTBT Tiểu học Giàng Chu Phìn - ĐT: 0944 134 973</div>", unsafe_allow_html=True)
