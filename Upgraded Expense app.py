import streamlit as st
import pandas as pd
import sqlite3
import os, json, datetime, time, base64, io
import plotly.graph_objects as go
import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

st.set_page_config(
    page_title="Expense Tracker Pro",
    layout="wide",
    page_icon="💸",
    initial_sidebar_state="collapsed"
)

# ── GROQ KEY — paste your key here ───────────────────────────────
GROQ_API_KEY = "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"

# ── CONSTANTS ─────────────────────────────────────────────────────
DB_FILE    = "expenses.db"
IMG_DIR    = "receipts"
MAX_IMG_KB = 700
CATEGORIES = ["Groceries","Food","Travel","Shopping","Bills","Health","Other"]
CAT_COLOR  = {"Groceries":"#FF9F40","Food":"#FF6384","Travel":"#36A2EB",
               "Shopping":"#9966FF","Bills":"#4BC0C0","Health":"#FF6B6B","Other":"#C9CBCF"}
CAT_ICON   = {"Groceries":"🛒","Food":"🍔","Travel":"✈️",
               "Shopping":"🛍️","Bills":"📄","Health":"💊","Other":"📦"}
os.makedirs(IMG_DIR, exist_ok=True)

if "scan_buffer" not in st.session_state:
    st.session_state.scan_buffer = []
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "scan_raw_bytes" not in st.session_state:
    st.session_state.scan_raw_bytes = None
if "scan_confirmed" not in st.session_state:
    st.session_state.scan_confirmed = False


# ================================================================
# CSS — pure CSS rules only, NO <style>/<link> wrapper tags here.
# inject_css() wraps them at call time so Streamlit renders them
# correctly instead of printing the content as visible text.
# ================================================================
DARK_CSS = """
/* 1. Removed .stDeployButton from this hidden list */
#MainMenu, footer, [data-testid='stDecoration'] {display:none!important;}

/* Deploy button: hide everything in toolbar EXCEPT the deploy button */
[data-testid='stToolbar'] > *:not([data-testid='stDeployButton']) {display:none!important;}

/* 2. Changed position to relative so it doesn't mask your content */
header[data-testid='stHeader'] {background:#080E1C!important; border-bottom:1px solid rgba(99,102,241,.12)!important; position: relative!important;}
[data-testid='stSidebar'] {display:none!important;}
html,body,[data-testid='stAppViewContainer'] {font-family:'Inter',sans-serif;background:#080E1C;color:#E2E8F0;}

/* Force ALL Streamlit text elements to be visible in dark mode */
[data-testid='stMarkdownContainer'] p,
[data-testid='stMarkdownContainer'] span,
[data-testid='stMarkdownContainer'] li,
[data-testid='stMarkdownContainer'] strong,
[data-testid='stMarkdownContainer'] em,
[data-testid='stCaptionContainer'] p,
[data-testid='stText'] {color:#E2E8F0 !important;}
[data-testid='stWidgetLabel'] p,
label, .stRadio label, .stCheckbox label,
[data-baseweb='radio'] label {color:#94A3B8 !important;}
[data-testid='stAlert'] p {color:#0F172A !important;}
.block-container {padding-top:3.5rem!important;padding-left:1.2rem!important;padding-right:1.2rem!important;max-width:1400px!important;}

[data-baseweb='tab-list'] {background:rgba(0,0,0,.3)!important;border-radius:12px!important;padding:4px!important;gap:2px!important;border:1px solid rgba(255,255,255,.07)!important;margin-bottom:10px!important;}
[data-baseweb='tab'] {background:transparent!important;border:none!important;border-radius:8px!important;color:#64748B!important;font-weight:500!important;font-size:.82rem!important;padding:7px 16px!important;transition:all .18s!important;}
[data-baseweb='tab']:hover {background:rgba(99,102,241,.18)!important;color:#A5B4FC!important;}
[aria-selected='true'][data-baseweb='tab'] {background:rgba(99,102,241,.35)!important;color:#C7D2FE!important;font-weight:700!important;}
[data-baseweb='tab-highlight'] {background:transparent!important;}
[data-baseweb='tab-border'] {display:none!important;}
.kpi {background:rgba(20,30,50,.95);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:16px 18px;margin-bottom:8px;transition:all .25s;}
.kpi:hover {border-color:rgba(99,102,241,.4);transform:translateY(-2px);box-shadow:0 8px 24px rgba(99,102,241,.12);}
.kpi-label {font-size:.67rem;text-transform:uppercase;color:#475569;font-weight:600;letter-spacing:.09em;margin-bottom:4px;}
.kpi-value {font-size:1.5rem;font-weight:800;color:#F8FAFC;line-height:1.1;}
.kpi-sub {font-size:.74rem;margin-top:4px;font-weight:500;}
.ph {margin-bottom:.9rem;padding-bottom:.7rem;border-bottom:1px solid rgba(255,255,255,.07);}
.ph-title {font-size:1.25rem;font-weight:800;color:#F8FAFC;letter-spacing:-.02em;}
.ph-sub {font-size:.78rem;color:#475569;margin-top:2px;}
.bx-alert {background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.28);border-left:3px solid #F87171;border-radius:10px;padding:11px 15px;margin:5px 0;}
.bx-good {background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.28);border-left:3px solid #10B981;border-radius:10px;padding:11px 15px;margin:5px 0;}
.bx-info {background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.28);border-left:3px solid #6366F1;border-radius:10px;padding:11px 15px;margin:5px 0;}
.bx-warn {background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.28);border-left:3px solid #FBBF24;border-radius:10px;padding:11px 15px;margin:5px 0;}
.ch-title {font-size:.96rem;font-weight:700;color:#F8FAFC;margin:18px 0 3px 0;}
.ch-sub {font-size:.77rem;color:#475569;margin-bottom:10px;}
.notif {border-radius:9px;padding:9px 13px;margin:4px 0;border:1px solid rgba(255,255,255,.07);background:rgba(20,30,50,.95);}
.notif-unread {border-left:3px solid #6366F1;background:rgba(99,102,241,.1);}
.notif-title {font-weight:700;font-size:.83rem;color:#F1F5F9;}
.notif-body {font-size:.77rem;color:#64748B;margin-top:2px;}
.notif-time {font-size:.64rem;color:#475569;margin-top:2px;}
.pill {display:inline-block;padding:2px 9px;border-radius:20px;font-size:.68rem;font-weight:600;margin-right:3px;}
.pb-wrap {background:rgba(255,255,255,.06);border-radius:999px;height:7px;overflow:hidden;margin:6px 0;}
.pb-bar {height:100%;border-radius:999px;transition:width .8s cubic-bezier(.4,0,.2,1);}
.stButton>button,.stFormSubmitButton>button,[data-testid='stFormSubmitButton']>button {background:linear-gradient(135deg,#6366F1,#4F46E5)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-weight:600!important;transition:all .18s!important;}
.stDownloadButton>button,[data-testid='stDownloadButton']>button {background:linear-gradient(135deg,#10B981,#059669)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-weight:600!important;}
.stDownloadButton>button:hover,[data-testid='stDownloadButton']>button:hover {background:linear-gradient(135deg,#34D399,#10B981)!important;}
.stButton>button:hover,.stFormSubmitButton>button:hover,[data-testid='stFormSubmitButton']>button:hover {background:linear-gradient(135deg,#818CF8,#6366F1)!important;transform:translateY(-1px)!important;box-shadow:0 5px 18px rgba(99,102,241,.3)!important;}
[data-testid='stCameraInput'] button {background:linear-gradient(135deg,#6366F1,#4F46E5)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-weight:600!important;}
[data-testid='stFileUploaderDropzone'] {background:rgba(20,32,54,.9) !important;border:2px dashed rgba(99,102,241,.5) !important;border-radius:12px !important;}
[data-testid='stFileUploaderDropzone'] p,[data-testid='stFileUploaderDropzone'] small,[data-testid='stFileUploaderDropzone'] span {color:#CBD5E1 !important;}
section[data-testid='stFileUploaderDropzone'] button {background:linear-gradient(135deg,#6366F1,#4F46E5) !important;color:#ffffff !important;border:none !important;}
[data-testid='stPopover'] > button,[data-testid='stPopover'] button {color:#E2E8F0 !important;background:rgba(30,41,59,.8) !important;border:1px solid rgba(255,255,255,.1) !important;border-radius:8px !important;}
[data-testid='stNumberInput'] input,[data-testid='stTextInput'] input {background:rgba(30,41,59,.7)!important;border:1px solid rgba(255,255,255,.07)!important;border-radius:8px!important;color:#E2E8F0!important;}
[data-testid='stTextArea'] textarea {background:rgba(30,41,59,.7)!important;border:1px solid rgba(255,255,255,.07)!important;border-radius:8px!important;color:#E2E8F0!important;}
[data-testid='stDateInput'] input {background:rgba(30,41,59,.7)!important;border:1px solid rgba(255,255,255,.07)!important;border-radius:8px!important;color:#E2E8F0!important;}
[data-testid='stSelectbox'] div {background:rgba(30,41,59,.7)!important;border:1px solid rgba(255,255,255,.07)!important;border-radius:8px!important;}
[data-testid='stDataFrame'] {border-radius:10px!important;overflow:hidden!important;}
[data-testid='stExpander'] {border:1px solid rgba(255,255,255,.07)!important;border-radius:10px!important;background:rgba(10,16,30,.5)!important;}
[data-testid='stExpander'] summary,[data-testid='stExpander'] summary p {color:#E2E8F0!important;}
[data-testid='stSlider'] label,[data-testid='stSlider'] p {color:#E2E8F0!important;}
[data-testid='stToggle'] label,[data-testid='stToggle'] p {color:#E2E8F0!important;}
[data-testid='stRadio'] label,[data-testid='stRadio'] p {color:#E2E8F0!important;}

/* 4. New rule positioning the deploy button perfectly in the top right corner */
[data-testid='stDeployButton'], .stDeployButton {
    display: inline-block !important;
    position: fixed !important;
    top: 24px !important;
    right: 24px !important;
    z-index: 999999 !important;
}
[data-testid='stDeployButton'] > button, .stDeployButton > button {
    background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 6px 16px !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2) !important;
    transition: all 0.2s ease !important;
}
[data-testid='stDeployButton'] > button:hover, .stDeployButton > button:hover {
    background: linear-gradient(135deg, #818CF8, #6366F1) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important;
}
"""


LIGHT_CSS = """
/* 1. Removed .stDeployButton from this hidden list */
#MainMenu, footer, [data-testid='stDecoration'] {display:none!important;}

/* Deploy button: hide everything in toolbar EXCEPT the deploy button */
[data-testid='stToolbar'] > *:not([data-testid='stDeployButton']) {display:none!important;}

/* 2. Changed position to relative so it doesn't mask your content */
header[data-testid='stHeader'] {background:#E7ECF3!important; border-bottom:1px solid rgba(15,23,42,.08)!important; position: relative!important;}
[data-testid='stSidebar'] {display:none!important;}
html,body,[data-testid='stAppViewContainer'] {font-family:'Inter',sans-serif;background:#F1F4F9;color:#1E293B;}

/* Force ALL Streamlit text elements to be visible in light mode */
[data-testid='stMarkdownContainer'] p,
[data-testid='stMarkdownContainer'] span,
[data-testid='stMarkdownContainer'] li,
[data-testid='stMarkdownContainer'] strong,
[data-testid='stMarkdownContainer'] em,
[data-testid='stCaptionContainer'] p,
[data-testid='stText'] {color:#1E293B !important;}
[data-testid='stWidgetLabel'] p,
label, .stRadio label, .stCheckbox label,
[data-baseweb='radio'] label {color:#54607A !important;}
[data-testid='stAlert'] p {color:#1E293B !important;}
.block-container {padding-top:3.5rem!important;padding-left:1.2rem!important;padding-right:1.2rem!important;max-width:1400px!important;}

[data-baseweb='tab-list'] {background:rgba(99,102,241,.08)!important;border-radius:12px!important;padding:4px!important;gap:2px!important;border:1px solid rgba(0,0,0,.08)!important;margin-bottom:10px!important;}
[data-baseweb='tab'] {background:transparent!important;border:none!important;border-radius:8px!important;color:#54607A!important;font-weight:500!important;font-size:.82rem!important;padding:7px 16px!important;transition:all .18s!important;}
[data-baseweb='tab']:hover {background:rgba(99,102,241,.14)!important;color:#4338CA!important;}
[aria-selected='true'][data-baseweb='tab'] {background:#FFFFFF!important;color:#4338CA!important;font-weight:700!important;box-shadow:0 1px 4px rgba(15,23,42,.08)!important;}
[data-baseweb='tab-highlight'] {background:transparent!important;}
[data-baseweb='tab-border'] {display:none!important;}
.kpi {background:#FFFFFF;border:1px solid rgba(15,23,42,.07);border-radius:14px;padding:16px 18px;margin-bottom:8px;transition:all .25s;box-shadow:0 1px 3px rgba(15,23,42,.04);}
.kpi:hover {border-color:rgba(99,102,241,.3);transform:translateY(-2px);box-shadow:0 8px 20px rgba(99,102,241,.12);}
.kpi-label {font-size:.67rem;text-transform:uppercase;color:#64748B;font-weight:600;letter-spacing:.09em;margin-bottom:4px;}
.kpi-value {font-size:1.5rem;font-weight:800;color:#1E293B;line-height:1.1;}
.kpi-sub {font-size:.74rem;margin-top:4px;font-weight:500;}
.ph {margin-bottom:.9rem;padding-bottom:.7rem;border-bottom:1px solid rgba(15,23,42,.08);}
.ph-title {font-size:1.25rem;font-weight:800;color:#1E293B;letter-spacing:-.02em;}
.ph-sub {font-size:.78rem;color:#64748B;margin-top:2px;}
.bx-alert {background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);border-left:3px solid #F87171;border-radius:10px;padding:11px 15px;margin:5px 0;}
.bx-good {background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.3);border-left:3px solid #10B981;border-radius:10px;padding:11px 15px;margin:5px 0;}
.bx-info {background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.3);border-left:3px solid #6366F1;border-radius:10px;padding:11px 15px;margin:5px 0;}
.bx-warn {background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.3);border-left:3px solid #FBBF24;border-radius:10px;padding:11px 15px;margin:5px 0;}
.ch-title {font-size:.96rem;font-weight:700;color:#1E293B;margin:18px 0 3px 0;}
.ch-sub {font-size:.77rem;color:#64748B;margin-bottom:10px;}
.notif {border-radius:9px;padding:9px 13px;margin:4px 0;border:1px solid rgba(15,23,42,.07);background:#FFFFFF;box-shadow:0 1px 2px rgba(15,23,42,.03);}
.notif-unread {border-left:3px solid #6366F1;background:rgba(99,102,241,.08);}
.notif-title {font-weight:700;font-size:.83rem;color:#1E293B;}
.notif-body {font-size:.77rem;color:#54607A;margin-top:2px;}
.notif-time {font-size:.64rem;color:#94A3B8;margin-top:2px;}
.pill {display:inline-block;padding:2px 9px;border-radius:20px;font-size:.68rem;font-weight:600;margin-right:3px;}
.pb-wrap {background:rgba(15,23,42,.07);border-radius:999px;height:7px;overflow:hidden;margin:6px 0;}
.pb-bar {height:100%;border-radius:999px;transition:width .8s cubic-bezier(.4,0,.2,1);}
.stButton>button,.stFormSubmitButton>button,[data-testid='stFormSubmitButton']>button {background:linear-gradient(135deg,#6366F1,#4F46E5)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-weight:600!important;transition:all .18s!important;}
.stButton>button:hover,.stFormSubmitButton>button:hover,[data-testid='stFormSubmitButton']>button:hover {background:linear-gradient(135deg,#818CF8,#6366F1)!important;transform:translateY(-1px)!important;box-shadow:0 5px 18px rgba(99,102,241,.3)!important;}
[data-testid='stCameraInput'] button {background:linear-gradient(135deg,#6366F1,#4F46E5)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-weight:600!important;}
.stDownloadButton>button,[data-testid='stDownloadButton']>button {background:linear-gradient(135deg,#10B981,#059669)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-weight:600!important;}
.stDownloadButton>button:hover,[data-testid='stDownloadButton']>button:hover {background:linear-gradient(135deg,#34D399,#10B981)!important;}
[data-testid='stNumberInput'] input,[data-testid='stTextInput'] input {background:#FFFFFF!important;border:1px solid rgba(15,23,42,.14)!important;border-radius:8px!important;color:#1E293B!important;}
[data-testid='stTextArea'] textarea {background:#FFFFFF!important;border:1px solid rgba(15,23,42,.14)!important;border-radius:8px!important;color:#1E293B!important;}
[data-testid='stDateInput'] input {background:#FFFFFF!important;border:1px solid rgba(15,23,42,.14)!important;border-radius:8px!important;color:#1E293B!important;}
[data-testid='stSelectbox'] div {background:#FFFFFF!important;border:1px solid rgba(15,23,42,.14)!important;border-radius:8px!important;}
[data-testid='stDataFrame'] {border-radius:10px!important;overflow:hidden!important;}
[data-testid='stExpander'] {border:1px solid rgba(15,23,42,.08)!important;border-radius:10px!important;background:#FFFFFF!important;}
[data-testid='stExpander'] summary,[data-testid='stExpander'] summary p {color:#1E293B!important;}
[data-testid='stMetricLabel'] p,[data-testid='stMetricValue'] {color:#1E293B!important;}
[data-testid='stMetricDelta'] {color:#1E293B!important;}
[data-testid='stSlider'] label,[data-testid='stSlider'] p,[data-testid='stSlider'] span {color:#54607A!important;}
[data-testid='stToggle'] label,[data-testid='stToggle'] p {color:#1E293B!important;}
[data-testid='stRadio'] label,[data-testid='stRadio'] p {color:#1E293B!important;}
[data-testid='stCheckbox'] label,[data-testid='stCheckbox'] p {color:#1E293B!important;}
[data-testid='stNumberInput'] button {background:#F1F4F9!important;color:#1E293B!important;border:1px solid rgba(15,23,42,.14)!important;}
/* File uploader: keep dark so white text is always readable */
[data-testid='stFileUploaderDropzone'] {background:rgba(30,41,60,.88) !important;border:2px dashed rgba(99,102,241,.55) !important;border-radius:12px !important;}
[data-testid='stFileUploaderDropzone'] p,[data-testid='stFileUploaderDropzone'] small,[data-testid='stFileUploaderDropzone'] span {color:#E2E8F0 !important;}
section[data-testid='stFileUploaderDropzone'] button {background:linear-gradient(135deg,#6366F1,#4F46E5) !important;color:#ffffff !important;border:none !important;}
/* Notification bell / popover button always visible */
[data-testid='stPopover'] > button,[data-testid='stPopover'] button {color:#1E293B !important;background:#FFFFFF !important;border:1px solid rgba(15,23,42,.12) !important;border-radius:8px !important;}
[data-testid='stPopover'] > button:hover,[data-testid='stPopover'] button:hover {background:#F1F4F9 !important;}
[data-baseweb='select'] div,[data-baseweb='select'] span,[data-baseweb='select'] input {color:#0F172A !important;}
[data-baseweb='popover'] li,[data-baseweb='popover'] [role='option'] {color:#1E293B !important;background:#FFFFFF !important;}
[data-baseweb='popover'] li:hover,[data-baseweb='popover'] [role='option']:hover {background:#F1F4F9 !important;}
[data-testid='stMultiSelect'] span,[data-testid='stMultiSelect'] div {color:#1E293B !important;}
[data-baseweb='tag'] {background:rgba(99,102,241,.18) !important;color:#312E81 !important;}

/* 4. Positions the deploy button in the top right corner over light backgrounds */
[data-testid='stDeployButton'], .stDeployButton {
    display: inline-block !important;
    position: fixed !important;
    top: 24px !important;
    right: 24px !important;
    z-index: 999999 !important;
}
[data-testid='stDeployButton'] > button, .stDeployButton > button {
    background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 6px 16px !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15) !important;
    transition: all 0.2s ease !important;
}
[data-testid='stDeployButton'] > button:hover, .stDeployButton > button:hover {
    background: linear-gradient(135deg, #818CF8, #6366F1) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.25) !important;
}
"""

# ── KEY FIX: wrap CSS in <style> tag at injection time, not in the string itself
def inject_css():
    css = DARK_CSS if st.session_state.theme == "dark" else LIGHT_CSS
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def inject_js():
    st.markdown("""<script>
(function(){
    /* KPI counter animation */
    function anim(){
        document.querySelectorAll('.kpi-value[data-target]').forEach(function(el){
            if(el.dataset.done) return;
            var t=parseFloat(el.dataset.target);
            if(isNaN(t)) return;
            el.dataset.done='1';
            var s=0;
            var iv=setInterval(function(){
                s+=t/56; if(s>=t){s=t;clearInterval(iv);}
                el.textContent='Rs.'+Math.round(s).toLocaleString('en-IN');
            },16);
        });
    }
    setTimeout(anim,300);
    new MutationObserver(function(){setTimeout(anim,300);})
        .observe(document.body,{childList:true,subtree:true});

    /* Floating Deploy button injected via JS — always visible top-right */
    function addDeployBtn(){
        if(document.getElementById('js-deploy-btn')) return;
        var btn=document.createElement('a');
        btn.id='js-deploy-btn';
        btn.href='https://share.streamlit.io/';
        btn.target='_blank';
        btn.innerHTML='&#128640; Deploy';
        btn.style.cssText='position:fixed;top:14px;right:16px;z-index:2147483647;'
            +'background:linear-gradient(135deg,#6366F1,#4F46E5);'
            +'color:#fff;border-radius:8px;font-size:.78rem;font-weight:700;'
            +'padding:6px 16px;text-decoration:none;letter-spacing:.02em;'
            +'box-shadow:0 4px 14px rgba(99,102,241,.35);'
            +'transition:all .2s ease;display:inline-block;';
        btn.onmouseover=function(){
            this.style.transform='translateY(-1px)';
            this.style.boxShadow='0 7px 22px rgba(99,102,241,.5)';
            this.style.background='linear-gradient(135deg,#818CF8,#6366F1)';
        };
        btn.onmouseout=function(){
            this.style.transform='';
            this.style.boxShadow='0 4px 14px rgba(99,102,241,.35)';
            this.style.background='linear-gradient(135deg,#6366F1,#4F46E5)';
        };
        document.body.appendChild(btn);
    }
    setTimeout(addDeployBtn,600);
    new MutationObserver(function(){setTimeout(addDeployBtn,300);})
        .observe(document.body,{childList:true,subtree:true});

    /* Camera flash effect — white screen burst on capture */
    function setupCameraFlash(){
        var fl=document.getElementById('cam-flash-overlay');
        if(!fl){
            fl=document.createElement('div');
            fl.id='cam-flash-overlay';
            fl.style.cssText='position:fixed;top:0;left:0;right:0;bottom:0;'
                +'background:#ffffff;opacity:0;pointer-events:none;'
                +'z-index:2147483645;';
            document.body.appendChild(fl);
        }
        function doFlash(){
            fl.style.transition='none';
            fl.style.opacity='0.92';
            setTimeout(function(){
                fl.style.transition='opacity 0.55s ease-out';
                fl.style.opacity='0';
            },90);
        }
        /* Attach to every button inside Streamlit's camera widget */
        document.querySelectorAll('[data-testid="stCameraInput"] button').forEach(function(btn){
            if(btn._flashReady) return;
            btn._flashReady=true;
            btn.addEventListener('click',doFlash);
        });
    }
    setTimeout(setupCameraFlash,1000);
    new MutationObserver(function(){setTimeout(setupCameraFlash,400);})
        .observe(document.body,{childList:true,subtree:true});
})();
</script>""", unsafe_allow_html=True)

# ── DATABASE ──────────────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_FILE) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, time TEXT DEFAULT '',
            category TEXT DEFAULT 'Other', amount REAL DEFAULT 0,
            description TEXT DEFAULT '', standard_name TEXT DEFAULT '',
            quantity REAL DEFAULT 1, unit_price REAL DEFAULT 0,
            receipt_file TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS notifications(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT, ntype TEXT, title TEXT, body TEXT, is_read INTEGER DEFAULT 0);
        INSERT OR IGNORE INTO settings VALUES('monthly_budget','5000');
        INSERT OR IGNORE INTO settings VALUES('daily_budget','500');
        INSERT OR IGNORE INTO settings VALUES('budget_locked','0');
        """)
init_db()

def qone(sql,p=()):
    with sqlite3.connect(DB_FILE) as c: return c.execute(sql,p).fetchone()
def qall(sql,p=()):
    with sqlite3.connect(DB_FILE) as c: return c.execute(sql,p).fetchall()
def qrun(sql,p=()):
    with sqlite3.connect(DB_FILE) as c: c.execute(sql,p); c.commit()
def qmany(sql,rows):
    with sqlite3.connect(DB_FILE) as c: c.executemany(sql,rows); c.commit()
def load_df():
    with sqlite3.connect(DB_FILE) as c:
        return pd.read_sql("SELECT * FROM expenses ORDER BY date DESC,time DESC",c)
def get_s(k,d="0"):
    r=qone("SELECT value FROM settings WHERE key=?",(k,)); return r[0] if r else d
def save_s(k,v): qrun("INSERT OR REPLACE INTO settings VALUES(?,?)",(k,str(v)))

# ── NOTIFICATIONS ─────────────────────────────────────────────────
def notify(ntype,title,body=""):
    today=datetime.date.today().strftime('%Y-%m-%d')
    if qone("SELECT id FROM notifications WHERE title=? AND created LIKE ?",(title,today+"%")): return
    qrun("INSERT INTO notifications(created,ntype,title,body) VALUES(?,?,?,?)",
         (datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),ntype,title,body))

def unread_count():
    r=qone("SELECT COUNT(*) FROM notifications WHERE is_read=0"); return r[0] if r else 0

def check_item_notifs(items):
    df=load_df()
    for it in items:
        name=str(it.get("standard_name","")).strip().title()
        up=float(it.get("unit_price",0) or 0)
        if not name or up<=0: continue
        hist=df[(df['standard_name']==name)&(df['unit_price']>0)].sort_values('date')
        if len(hist)<=1:
            notify("new",f"New: {name}",f"First purchase Rs.{round(up,2)} — tracking started!")
        else:
            prev=hist.iloc[-2]['unit_price']
            if prev>0:
                chg=(up-prev)/prev*100
                if chg>=5: notify("price",f"{name} expensive!",f"Rs.{round(prev)} to Rs.{round(up)} (+{round(chg,1)}%)")
                elif chg<=-5: notify("price",f"{name} cheaper!",f"Rs.{round(prev)} to Rs.{round(up)} ({round(chg,1)}%)")

def check_budget_notifs(df):
    mb=float(get_s("monthly_budget","5000")); db_v=float(get_s("daily_budget","500"))
    today=datetime.date.today()
    if df.empty: return
    df_m=df[df['date'].str.startswith(today.strftime('%Y-%m'))]
    df_t=df[df['date']==today.strftime('%Y-%m-%d')]
    tm=df_m['amount'].sum() if not df_m.empty else 0
    tt=df_t['amount'].sum() if not df_t.empty else 0
    if tt>db_v: notify("budget",f"Daily limit crossed: Rs.{round(tt)}",f"Over by Rs.{round(tt-db_v)}")
    if tm>mb: notify("budget",f"Monthly budget over: Rs.{round(tm)}",f"Budget Rs.{round(mb)}")
    elif tm>mb*.8: notify("budget","80% monthly budget used",f"Rs.{round(tm)} of Rs.{round(mb)}")

# ── IMAGE HELPERS ─────────────────────────────────────────────────
def compress_and_save(src,handwriting=False):
    # Single enhancement pass — this is the ONLY place enhancement
    # happens. img_to_b64() reads this file back as-is for the AI.
    img=Image.open(src).convert('RGB')
    w,h=img.size
    if w<1200: img=img.resize((1200,int(h*1200/w)),Image.LANCZOS)
    if max(img.size)>2000: img.thumbnail((2000,2000),Image.LANCZOS)
    img=img.filter(ImageFilter.SHARPEN)
    if handwriting:
        img=img.convert('L').convert('RGB')  # grayscale makes ink lines pop
        img=ImageEnhance.Contrast(img).enhance(2.2)
        img=ImageEnhance.Sharpness(img).enhance(2.6)
    else:
        img=ImageEnhance.Contrast(img).enhance(1.35)
        img=ImageEnhance.Sharpness(img).enhance(1.7)
    q=92
    while q>=40:
        buf=io.BytesIO(); img.save(buf,"JPEG",quality=q)
        if buf.tell()/1024<=MAX_IMG_KB: break
        q-=8
    fname=f"rcpt_{datetime.date.today()}_{int(time.time())}.jpg"
    with open(os.path.join(IMG_DIR,fname),'wb') as f: f.write(buf.getvalue())
    return fname

def img_to_b64(path):
    # NOTE: the image on disk was already enhanced once by
    # compress_and_save() (sharpened, contrast/sharpness boosted).
    # Do NOT re-enhance here — applying filters twice compounds
    # artifacts (halos, blown contrast) and makes digits HARDER
    # for the AI to read correctly. Just ensure sane size + encode.
    img=Image.open(path).convert('RGB')
    w,h=img.size
    if w<1200: img=img.resize((1200,int(h*1200/w)),Image.LANCZOS)
    if max(img.size)>2000: img.thumbnail((2000,2000),Image.LANCZOS)
    buf=io.BytesIO(); img.save(buf,"JPEG",quality=95)
    return base64.b64encode(buf.getvalue()).decode()

# ── GROQ AI ───────────────────────────────────────────────────────
GROQ_PROMPT="""You are a receipt OCR tool. Your ONLY job is to READ what is PRINTED on the receipt — exactly as it appears, character by character, digit by digit. You are NOT a calculator. DO NOT add, sum, compute, or derive any number. Every number you return must be physically visible on the receipt image.

═══ GRAND TOTAL ═══
Find the final payable amount printed on the receipt. It is labeled with one of:
  Total · Grand Total · Net Total · Net Amount · Net Payable · Amount Due · Total Payable · Amount Payable · Total Bill · Bill Amount · To Pay · Payable · Final Amount

How to find it:
  • Look near the BOTTOM of the receipt
  • It is the amount the customer actually paid — after any discounts
  • If both "Sub Total: 450" and "Total: 432" appear → grand_total = 432 (the FINAL one)
  • COPY the number digit by digit exactly as printed: if it says 892.50 → write 892.50, NOT 892, NOT 893
  • Digit confusion check — look twice at every digit: 6vs8 · 1vs7 · 0vsO · 5vsS · 9vs4 · 2vsZ · 3vs8

═══ LINE ITEMS ═══
  • Count all product/service lines on the receipt. Return EXACTLY that many items — no more, no less.
  • Original_Description: copy the text EXACTLY as printed, word for word
  • Unit_Price: the per-unit price EXACTLY as printed on that line. READ it — do not compute it.
  • Amount: the line total EXACTLY as printed on that line. READ it — do not compute it.
  • Quantity: the quantity EXACTLY as printed. If not shown, use 1.
  • SKIP: GST · SGST · CGST · VAT · tax breakdown lines · discount lines · sub-total lines · store name/address/phone

═══ HANDWRITTEN RECEIPTS ═══
  Trace each character stroke by stroke. Re-read every digit twice. If a digit is ambiguous, pick the most visually likely one and write it — do not average or round.

CRITICAL: You are a READER not a CALCULATOR. Every single number in your output must be a number you can physically see printed on the receipt. Return ONLY this JSON:
{"grand_total":<exact printed total — READ from receipt>,"items":[{"Original_Description":"exact text from receipt","Standard_Name":"clean name","Quantity":<as printed>,"Unit_Price":<exact price as printed>,"Amount":<exact line total as printed>,"Category":"Groceries or Food or Travel or Shopping or Bills or Health or Other","Time":"HH:MM AM/PM or NOT_FOUND"}]}"""

def groq_scan(image_path,scan_date,scan_time):
    b64=img_to_b64(image_path)
    resp=requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization":f"Bearer {GROQ_API_KEY}","Content-Type":"application/json"},
        json={"model":"meta-llama/llama-4-scout-17b-16e-instruct",
              "messages":[{"role":"user","content":[
                  {"type":"text","text":GROQ_PROMPT},
                  {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],
              "temperature":0.05,"max_tokens":4000},timeout=90)
    if resp.status_code!=200:
        raise Exception(f"Groq {resp.status_code}: {resp.json().get('error',{}).get('message',resp.text)}")
    txt=resp.json()['choices'][0]['message']['content'].strip()
    for m in ["```json","```"]:
        if m in txt: txt=txt.split(m)[1].split("```")[0].strip(); break
    # Find the first JSON object { or array [
    s_obj=txt.find('{'); s_arr=txt.find('[')
    if s_obj>=0 and (s_arr<0 or s_obj<s_arr): txt=txt[s_obj:]
    elif s_arr>=0: txt=txt[s_arr:]
    parsed=json.loads(txt)
    # New format: {"grand_total": X, "items": [...]}
    grand_total=0.0
    if isinstance(parsed,dict):
        items_raw=parsed.get("items",[])
        try: grand_total=float(parsed.get("grand_total",0) or 0)
        except: grand_total=0.0
    else:
        items_raw=parsed  # old format fallback: plain array
    # Only fall back if AI found NO total at all (blank/null)
    if grand_total==0:
        items_amt_sum=sum(float(it.get("Amount",0) or 0) for it in items_raw)
        if items_amt_sum>0:
            grand_total=round(items_amt_sum,2)  # last resort: sum items
    valid=set(CATEGORIES); items=[]
    for item in items_raw:
        q=float(item.get("Quantity",1) or 1); up=float(item.get("Unit_Price",0) or 0)
        t=str(item.get("Time","NOT_FOUND")).strip(); cat=item.get("Category","Other").strip().title()
        items.append({"date":scan_date,"time":scan_time if t in ("NOT_FOUND","","None") else t,
                      "category":cat if cat in valid else "Other",
                      "amount":float(item.get("Amount",q*up) or q*up),
                      "description":str(item.get("Original_Description","")).strip(),
                      "standard_name":str(item.get("Standard_Name","Unknown")).strip().title(),
                      "quantity":q,"unit_price":up,"receipt_file":""})
    return items,grand_total

# ── CHART HELPER ──────────────────────────────────────────────────
CHART_CFG = {"scrollZoom":False,"doubleClick":"reset","displayModeBar":True,
             "modeBarButtonsToRemove":["select2d","lasso2d"]}

def style_fig(fig,h=400,xt="",yt="",xa=0,leg=True):
    dark=st.session_state.theme=="dark"
    tc='#94A3B8' if dark else '#5B6B82'
    gc='rgba(255,255,255,.04)' if dark else 'rgba(15,23,42,.07)'
    lb='rgba(15,23,42,.85)' if dark else 'rgba(255,255,255,.92)'
    fig.update_layout(height=h,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=tc,size=11),margin=dict(t=28,b=55,l=50,r=18),showlegend=leg,
        legend=dict(font=dict(color=tc,size=10),bgcolor=lb,borderwidth=1,bordercolor=gc),
        xaxis=dict(title=dict(text=xt,font=dict(color=tc,size=11)),tickfont=dict(color=tc,size=10),
                   gridcolor=gc,tickangle=xa,showgrid=True,linecolor=gc),
        yaxis=dict(title=dict(text=yt,font=dict(color=tc,size=11)),tickfont=dict(color=tc,size=10),
                   gridcolor=gc,showgrid=True,linecolor=gc))
    return fig

def sch(fig,key="ch"):
    st.plotly_chart(fig,use_container_width=True,config=CHART_CFG,key=key)

def ch(title,sub=""):
    st.markdown(f'<div class="ch-title">{title}</div>'+
                (f'<div class="ch-sub">{sub}</div>' if sub else ""),unsafe_allow_html=True)

def kpi(label,val,sub,good=True,delay="0s"):
    c="#10B981" if good else "#F87171"
    num=val.replace("Rs.","").replace(",","").strip()
    st.markdown(
        f'<div class="kpi" style="animation:fadeInUp .5s {delay} ease both">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" data-target="{num}">{val}</div>'
        f'<div class="kpi-sub" style="color:{c}">{sub} {"✅" if good else "⚠️"}</div>'
        f'</div>',unsafe_allow_html=True)

def box(cls,text): st.markdown(f'<div class="{cls}">{text}</div>',unsafe_allow_html=True)

def pill(cat):
    c=CAT_COLOR.get(cat,"#C9CBCF"); icon=CAT_ICON.get(cat,"")
    return f'<span class="pill" style="background:{c}22;color:{c};border:1px solid {c}44">{icon} {cat}</span>'

def pbar(pct,color="#6366F1"):
    w=f"{round(min(pct,1)*100,1)}%"
    bg='linear-gradient(90deg,#F87171,#EF4444)' if pct>=1 else f'linear-gradient(90deg,{color},#818CF8)'
    return f'<div class="pb-wrap"><div class="pb-bar" style="width:{w};background:{bg}"></div></div>'

def ph(title,sub=""):
    st.markdown(f'<div class="ph"><div class="ph-title">{title}</div>'+
                (f'<div class="ph-sub">{sub}</div>' if sub else "")+'</div>',unsafe_allow_html=True)

# ================================================================
# APP HEADER — logo + greeting + theme toggle + today + bell
# ================================================================
def render_header(df):
    dark=st.session_state.theme=="dark"
    today=datetime.date.today()
    db_v=float(get_s("daily_budget","500"))
    df_t=df[df['date']==today.strftime('%Y-%m-%d')] if not df.empty else pd.DataFrame()
    tt=df_t['amount'].sum() if not df_t.empty else 0
    n=unread_count()
    h=datetime.datetime.now().hour
    greet="🌅 Good Morning" if h<12 else ("☀️ Good Afternoon" if h<17 else "🌙 Good Evening")
    txt_c="#F8FAFC" if dark else "#0F172A"
    sub_c="#94A3B8" if dark else "#5B6B82"

    col1,col2,col3=st.columns([4,4,2])
    with col1:
        st.markdown(
            f'<div style="padding:6px 0 4px;">'
            f'<div style="font-size:1.3rem;font-weight:800;color:{txt_c};">'
            f'💸 <span style="color:#818CF8;">Expense</span> Tracker Pro</div>'
            f'<div style="font-size:.75rem;color:{sub_c};margin-top:1px;">'
            f'{greet} &nbsp;·&nbsp; {today.strftime("%A, %d %B %Y")}</div>'
            f'</div>',unsafe_allow_html=True)
    with col2:
        # Deploy button — right-aligned in the middle column
        st.markdown(
            '<div style="display:flex;justify-content:flex-end;align-items:center;height:100%;padding:4px 0;">'
            '<a href="https://share.streamlit.io/" target="_blank" id="header-deploy-btn" '
            'style="display:inline-flex;align-items:center;gap:6px;padding:7px 18px;'
            'background:linear-gradient(135deg,#6366F1,#4F46E5);color:#fff;border-radius:8px;'
            'font-size:.78rem;font-weight:700;text-decoration:none;'
            'box-shadow:0 4px 12px rgba(99,102,241,.25);'
            'transition:all 0.2s ease;white-space:nowrap;"'
            ' onmouseover="this.style.transform=\'translateY(-1px)\';this.style.boxShadow=\'0 6px 20px rgba(99,102,241,.4)\'"'
            ' onmouseout="this.style.transform=\'\';this.style.boxShadow=\'0 4px 12px rgba(99,102,241,.25)\'">'
            '🚀 Deploy</a>'
            '</div>',
            unsafe_allow_html=True)
    with col3:
        r1,r2,r3=st.columns([1,1,1])
        with r1:
            mode_label="☀️" if dark else "🌙"
            mode_tip="Light Mode" if dark else "Dark Mode"
            if st.button(mode_label,key="theme_btn",help=mode_tip,use_container_width=True):
                st.session_state.theme="light" if dark else "dark"
                st.rerun()
        with r2:
            tc="#10B981" if tt<=db_v else "#F87171"
            st.markdown(
                f'<div style="text-align:center;padding:2px 0;">'
                f'<div style="font-size:.58rem;color:#64748B;font-weight:600;text-transform:uppercase;">Today</div>'
                f'<div style="font-size:.9rem;font-weight:700;color:{tc};">Rs.{round(tt)}</div>'
                f'</div>',unsafe_allow_html=True)
        with r3:
            bell="🔔"+str(n) if n>0 else "🔔"
            with st.popover(bell,use_container_width=True):
                st.markdown("**Notifications**")
                rows=qall("SELECT id,created,ntype,title,body,is_read FROM notifications ORDER BY id DESC LIMIT 20")
                if not rows: st.caption("No alerts yet.")
                else:
                    for _,created,_,title,body,is_read in rows:
                        cls="notif" if is_read else "notif notif-unread"
                        st.markdown(f'<div class="{cls}"><div class="notif-title">{title}</div>'
                                    f'<div class="notif-body">{body}</div>'
                                    f'<div class="notif-time">{created}</div></div>',unsafe_allow_html=True)
                    c1,c2=st.columns(2)
                    with c1:
                        if st.button("✅ Mark read",use_container_width=True,key="mr"):
                            qrun("UPDATE notifications SET is_read=1"); st.rerun()
                    with c2:
                        if st.button("🗑️ Clear",use_container_width=True,key="cn"):
                            qrun("DELETE FROM notifications"); st.rerun()

    # thin line
    bdr="rgba(99,102,241,.12)" if dark else "rgba(99,102,241,.18)"
    st.markdown(f'<div style="height:1px;background:{bdr};margin:4px 0 8px;"></div>',unsafe_allow_html=True)

# ================================================================
# DASHBOARD
# ================================================================
def page_dashboard(df):
    ph("📊 Dashboard","Your complete spending overview")
    mb=float(get_s("monthly_budget","5000")); db_v=float(get_s("daily_budget","500"))
    today=datetime.date.today(); this_m=today.strftime('%Y-%m')
    nxt=datetime.date(today.year+1,1,1) if today.month==12 else datetime.date(today.year,today.month+1,1)
    dim=(nxt-datetime.timedelta(days=1)).day; dp=today.day; dl=dim-dp
    df_m=df[df['date'].str.startswith(this_m)] if not df.empty else pd.DataFrame()
    df_t=df[df['date']==today.strftime('%Y-%m-%d')] if not df.empty else pd.DataFrame()
    tm=df_m['amount'].sum() if not df_m.empty else 0
    tt=df_t['amount'].sum() if not df_t.empty else 0
    rem=mb-tm; avg=tm/max(dp,1); proj=avg*dim; safe=rem/max(dl,1)

    k1,k2,k3,k4,k5=st.columns(5)
    with k1: kpi("Month Spent",f"Rs.{round(tm)}",f"of Rs.{round(mb)}",tm<=mb,"0s")
    with k2: kpi("Today Spent",f"Rs.{round(tt)}",f"limit Rs.{round(db_v)}",tt<=db_v,"0.08s")
    with k3: kpi("Remaining",f"Rs.{round(rem)}",f"{dl} days left",rem>=0,"0.16s")
    with k4: kpi("Avg / Day",f"Rs.{round(avg)}","this month",avg<=db_v,"0.24s")
    with k5: kpi("Projected EOM",f"Rs.{round(proj)}","Will overshoot" if proj>mb else "On track",proj<=mb,"0.32s")

    pct=min(tm/mb,1.0) if mb>0 else 0
    st.markdown(f"**Monthly Budget — {round(pct*100,1)}% used**")
    st.markdown(pbar(pct),unsafe_allow_html=True)
    if proj>mb:    box("bx-alert",f"Overspend by <b>Rs.{round(proj-mb)}</b> at this pace. Safe daily: <b>Rs.{round(safe)}</b>")
    elif pct>=0.8: box("bx-warn",f"<b>{round(pct*100)}% used.</b> Stay under Rs.{round(safe)}/day")
    else:          box("bx-good",f"On track — <b>{round(pct*100)}%</b> used. Rs.{round(safe)}/day for {dl} days")

    if df_m.empty:
        box("bx-info","No expenses recorded this month yet. Go to <b>🧾 Scan Receipt</b> to scan a bill, or use <b>Manual Entry</b> inside that tab to add items by hand.")
        return
    st.divider()

    cp,cr=st.columns([3,2])
    with cp:
        with st.expander("📂 Spending by Category (click ▶ to expand)",expanded=True):
            cat_df=df_m.groupby('category',as_index=False)['amount'].sum().sort_values('amount',ascending=False)
            cat_df['pct']=cat_df['amount']/cat_df['amount'].sum()*100
            dark=st.session_state.theme=="dark"
            tc='#E2E8F0' if dark else '#1E293B'; bg='#080E1C' if dark else '#F1F4F9'
            fig=go.Figure(go.Pie(
                labels=cat_df['category'],values=cat_df['amount'],hole=0.42,
                marker=dict(colors=[CAT_COLOR.get(c,'#C9CBCF') for c in cat_df['category']],line=dict(color=bg,width=3)),
                texttemplate="<b>%{label}</b><br>Rs.%{value:,.0f}",
                textfont=dict(size=11,color='white'),textposition='auto',sort=False,
                hovertemplate="<b>%{label}</b><br>Rs.%{value:,.0f} (%{percent})<extra></extra>"))
            fig.add_annotation(text=f"<b>Rs.{round(tm)}</b>",x=0.5,y=0.5,font=dict(size=13,color=tc),showarrow=False)
            fig.update_layout(height=340,paper_bgcolor='rgba(0,0,0,0)',font=dict(color=tc),margin=dict(t=5,b=5,l=5,r=5),showlegend=False)
            sch(fig,"pie_cat")
            pills="".join([pill(r['category'])+f" <b>Rs.{round(r['amount'])}</b>&nbsp;" for _,r in cat_df.iterrows()])
            st.markdown(f'<div style="margin-top:6px;line-height:2.2;">{pills}</div>',unsafe_allow_html=True)
    with cr:
        ch("All Transactions","Every item — click any column header to sort")
        if not df.empty:
            tx=df[['date','category','standard_name','quantity','unit_price','amount']].copy()
            tx.columns=['Date','Cat','Item','Qty','₹/unit','Total ₹']
            tx['Date']=pd.to_datetime(tx['Date']).dt.strftime('%d/%m/%y')
            tx['Qty']=tx['Qty'].apply(lambda x: f"{int(x)}" if float(x)==int(float(x)) else f"{x:.1f}")
            tx['₹/unit']=tx['₹/unit'].apply(lambda x: f"{x:.2f}")
            tx['Total ₹']=tx['Total ₹'].apply(lambda x: f"{x:.2f}")
            st.dataframe(tx,use_container_width=True,hide_index=True,height=400)
        else:
            box("bx-info","No transactions yet.")
    st.divider()

    ch("🔔 Price Change Alerts","Items with 5%+ price change since first purchase")
    alerts=[]
    if not df.empty:
        for item in df['standard_name'].dropna().unique():
            idf=df[(df['standard_name']==item)&(df['unit_price']>0)].sort_values('date')
            if len(idf)>=2:
                fp=idf.iloc[0]['unit_price']; lp=idf.iloc[-1]['unit_price']
                fd=idf.iloc[0]['date']; ld=idf.iloc[-1]['date']
                chg=(lp-fp)/fp*100 if fp>0 else 0
                if abs(chg)>=5: alerts.append((item,fp,lp,chg,fd,ld))
    if alerts:
        alerts.sort(key=lambda x:abs(x[3]),reverse=True)
        a1,a2=st.columns(2)
        for idx,(item,fp,lp,chg,fd,ld) in enumerate(alerts[:8]):
            cls="bx-alert" if chg>0 else "bx-good"; c="#F87171" if chg>0 else "#10B981"
            with (a1 if idx%2==0 else a2):
                box(cls,f"<b>{item}</b><span style='float:right;color:{c};font-weight:800'>{round(chg,1)}%</span><br>"
                    f"<span style='color:#64748B;font-size:.75rem'>Rs.{round(fp,2)} → Rs.{round(lp,2)} ({fd} to {ld})</span>")
    else:
        box("bx-info","No price changes yet. Need 2+ purchases of same item.")

# ================================================================
# AI SCANNER
# ================================================================
def page_scanner():
    ph("🧾 Scan Receipt","Printed · Thermal · Handwritten — AI reads every item automatically")
    key_ok=(GROQ_API_KEY!="PASTE_YOUR_gsk_KEY_HERE" and len(GROQ_API_KEY)>20 and GROQ_API_KEY.startswith("gsk_"))
    ai_t,manual_t=st.tabs(["🧠 AI Scan","✏️ Manual Entry"])
    with ai_t:
        if not key_ok:
            box("bx-alert","Groq key not set! Open app.py line 13 → paste key from console.groq.com/keys (free)"); return
        c1,c2=st.columns([1,1])
        with c1:
            method=st.radio("Input:",["📁 Upload Image","📷 Camera"],horizontal=True,key="scan_method")
            pic=None
            if "Upload" in method:
                uf=st.file_uploader("Receipt",type=["jpg","jpeg","png"],label_visibility="collapsed")
                if uf: pic=uf
            else:
                cam=st.camera_input("Capture",label_visibility="collapsed")
                if cam: pic=cam
        with c2:
            box("bx-info","<b>Scan Receipt</b><br><br>✅ Thermal / printed bills<br>✅ Handwritten receipts<br>✅ Printed invoices &amp; slips<br>✅ GST/VAT auto-ignored<br>✅ Review &amp; edit before saving<br>🔔 Auto price alerts")
        # ── Store image in session state — only reset when image actually changes
        if pic:
            _rb=pic.getvalue() if hasattr(pic,'getvalue') else pic.read()
            if _rb:
                import hashlib
                _nhash=hashlib.md5(_rb[:2048]).hexdigest()
                if _nhash!=st.session_state.get('_scan_hash'):
                    st.session_state['_scan_raw']=_rb
                    st.session_state['_scan_hash']=_nhash
                    for _k in ['edit_rotate','edit_brightness','edit_contrast','edit_filter',
                                '__cx1__','__cy1__','__cx2__','__cy2__']:
                        st.session_state.pop(_k,None)

        _raw=st.session_state.get('_scan_raw')
        if not _raw:
            box("bx-info","📷 Upload a receipt or take a photo above to start scanning")
        else:
            dark=st.session_state.theme=="dark"
            tc_e="#F1F5F9" if dark else "#1E293B"
            sc_e="#94A3B8" if dark else "#5B6B82"
            pil_orig=Image.open(io.BytesIO(_raw)).convert('RGB')
            W0,H0=pil_orig.size

            # ── Crop: live sliders + red box drawn directly on the image ──
            # (No iframe/JS bridge — fully native, instant, 100% reliable)
            st.markdown(f'<b style="color:{tc_e};font-size:.9rem;">✂️ Step 1 — Crop: move sliders to frame the receipt from any direction</b>',unsafe_allow_html=True)
            sl1,sl2=st.columns(2)
            with sl1:
                st.slider("⬅ Left edge %",0,95,0,key="crop_x1")
                st.slider("⬆ Top edge %",0,95,0,key="crop_y1")
            with sl2:
                st.slider("➡ Right edge %",5,100,100,key="crop_x2")
                st.slider("⬇ Bottom edge %",5,100,100,key="crop_y2")
            cx1=int(st.session_state.get('crop_x1',0))
            cy1=int(st.session_state.get('crop_y1',0))
            cx2=int(st.session_state.get('crop_x2',100))
            cy2=int(st.session_state.get('crop_y2',100))
            cx2=max(cx2,cx1+5); cy2=max(cy2,cy1+5)

            # Draw red crop box live on a preview-sized copy
            _prev=pil_orig.copy()
            if _prev.width>800: _prev=_prev.resize((800,int(_prev.height*800/_prev.width)),Image.LANCZOS)
            Wp,Hp=_prev.size
            x1p=int(Wp*cx1/100); y1p=int(Hp*cy1/100)
            x2p=int(Wp*cx2/100); y2p=int(Hp*cy2/100)
            _ov=Image.new('RGBA',(Wp,Hp),(0,0,0,140))
            _ovd=ImageDraw.Draw(_ov)
            _ovd.rectangle([x1p,y1p,x2p,y2p],fill=(0,0,0,0))
            _ovd.rectangle([x1p,y1p,x2p,y2p],outline=(255,50,50,255),width=4)
            _hs=14
            for _hx,_hy in [(x1p,y1p),(x2p,y1p),(x1p,y2p),(x2p,y2p),
                             ((x1p+x2p)//2,y1p),((x1p+x2p)//2,y2p),
                             (x1p,(y1p+y2p)//2),(x2p,(y1p+y2p)//2)]:
                _ovd.rectangle([_hx-_hs//2,_hy-_hs//2,_hx+_hs//2,_hy+_hs//2],fill=(255,50,50,255))
            _crop_vis=Image.alpha_composite(_prev.convert('RGBA'),_ov).convert('RGB')
            st.image(_crop_vis,use_container_width=True,
                caption=f"Red box = area that will be scanned · {x2p-x1p}×{y2p-y1p}px on screen · Drag sliders above to reposition any edge")

            cropped_img=pil_orig.crop((int(W0*cx1/100),int(H0*cy1/100),int(W0*cx2/100),int(H0*cy2/100)))

            # ── Edit controls ────────────────────────────────────────────
            def _apply_edits(base):
                r=st.session_state.get('edit_rotate',0)
                b=float(st.session_state.get('edit_brightness',1.0))
                c=float(st.session_state.get('edit_contrast',1.0))
                f=st.session_state.get('edit_filter','Original')
                out=base.copy()
                if r!=0: out=out.rotate(-r,expand=True)
                if f=='Grayscale': out=out.convert('L').convert('RGB')
                elif f=='B&W Sharp':
                    out=ImageOps.autocontrast(out.convert('L'),cutoff=2).convert('RGB')
                    out=ImageEnhance.Contrast(out).enhance(2.5)
                elif f=='Auto-Enhance':
                    out=ImageOps.autocontrast(out.convert('L'),cutoff=1).convert('RGB')
                if abs(b-1.0)>0.01: out=ImageEnhance.Brightness(out).enhance(b)
                if abs(c-1.0)>0.01: out=ImageEnhance.Contrast(out).enhance(c)
                return out

            with st.expander("✏️ Step 2 — Rotate · Brightness · Contrast · Filter",expanded=False):
                ea,eb,ec=st.columns([1,1,1])
                with ea:
                    st.markdown(f'<b style="color:{tc_e};">🔄 Rotate</b>',unsafe_allow_html=True)
                    rb1,rb2,rb3=st.columns(3)
                    with rb1:
                        if st.button("↺ 90°",use_container_width=True,key="rot_l"):
                            st.session_state['edit_rotate']=(st.session_state.get('edit_rotate',0)-90)%360; st.rerun()
                    with rb2:
                        if st.button("↻ 90°",use_container_width=True,key="rot_r"):
                            st.session_state['edit_rotate']=(st.session_state.get('edit_rotate',0)+90)%360; st.rerun()
                    with rb3:
                        if st.button("⟳",use_container_width=True,key="rot_0"):
                            st.session_state['edit_rotate']=0; st.rerun()
                    st.caption(f"Angle: {st.session_state.get('edit_rotate',0)}°")
                with eb:
                    st.markdown(f'<b style="color:{tc_e};">☀️ Brightness &amp; Contrast</b>',unsafe_allow_html=True)
                    st.slider("Brightness",0.3,2.5,1.0,0.05,key="edit_brightness")
                    st.slider("Contrast",0.3,3.0,1.0,0.05,key="edit_contrast")
                with ec:
                    st.markdown(f'<b style="color:{tc_e};">🔍 Filter</b>',unsafe_allow_html=True)
                    st.radio("Filter",["Original","Auto-Enhance","Grayscale","B&W Sharp"],key="edit_filter",label_visibility="collapsed")
                    st.caption("B&W Sharp = best for faded thermal/handwritten receipts")

            # ── Preview — uses the EXACT same enhancement compress_and_save()
            # will apply, so what you see here is truly what the AI receives
            # (previously the preview used different settings than the real
            # scan — this caused the preview to look different from the
            # actual image sent, which was misleading).
            edit_img=_apply_edits(cropped_img)
            _hw_preview=st.session_state.get('hw_mode',False)
            prev_img=edit_img.copy()
            prev_img=prev_img.filter(ImageFilter.SHARPEN)
            if _hw_preview:
                prev_img=prev_img.convert('L').convert('RGB')
                prev_img=ImageEnhance.Contrast(prev_img).enhance(2.2)
                prev_img=ImageEnhance.Sharpness(prev_img).enhance(2.6)
            else:
                prev_img=ImageEnhance.Contrast(prev_img).enhance(1.35)
                prev_img=ImageEnhance.Sharpness(prev_img).enhance(1.7)
            pw,ph_=prev_img.size
            st.markdown(f'<div style="font-weight:800;color:{tc_e};margin:12px 0 4px;border-left:4px solid #10B981;padding-left:10px;">📸 Step 3 — Preview — exactly what the AI will receive</div>',unsafe_allow_html=True)
            st.image(prev_img,use_container_width=True,
                caption=f"{pw}x{ph_}px · Rot:{st.session_state.get('edit_rotate',0)}° · Brightness:{st.session_state.get('edit_brightness',1.0):.1f} · Filter:{st.session_state.get('edit_filter','Original')}"
                        +(" · Handwriting mode ON" if _hw_preview else ""))
            st.caption("✅ Text should look crisp, not overly contrasty or 'burnt'. If it looks harsh, lower Contrast/Sharpness above.")

            # ── Scan button — NO CHECKBOX, always visible ─────────────────
            st.markdown(f'<p style="font-size:.82rem;color:{sc_e};margin:4px 0 8px;">Review the preview above, then scan when ready.</p>',unsafe_allow_html=True)
            sc_btn_col,hw_col=st.columns([2,1])
            with hw_col:
                hw_mode=st.toggle("📝 Handwritten receipt",key="hw_mode")
            with sc_btn_col:
                if st.button("🧾 Scan Receipt with AI",use_container_width=True,key="scan_btn",type="primary"):
                    with st.spinner("Scanning — reading every item + total from receipt..."):
                        try:
                            _buf=io.BytesIO(); edit_img.save(_buf,"JPEG",quality=95); _buf.seek(0)
                            fname=compress_and_save(_buf,handwriting=hw_mode)
                            fpath=os.path.join(IMG_DIR,fname)
                            today=datetime.date.today().strftime('%Y-%m-%d')
                            now2=datetime.datetime.now().strftime('%I:%M %p')
                            items,grand_total=groq_scan(fpath,today,now2)
                            for it in items: it["receipt_file"]=fname
                            st.session_state.scan_buffer.extend(items)
                            st.session_state['scan_grand_total']=grand_total
                            st.toast(f"✅ {len(items)} items extracted!",icon="🎉")
                        except json.JSONDecodeError: st.error("AI gave unexpected output — try again.")
                        except Exception as e: st.error(f"Scan error: {e}")
        if st.session_state.scan_buffer:
            st.markdown("---")
            buf_df=pd.DataFrame(st.session_state.scan_buffer)
            show=buf_df[["date","time","category","standard_name","description","quantity","unit_price","amount"]].copy()
            items_sum=round(show['amount'].astype(float).sum(),2)
            grand_total_ai=float(st.session_state.get('scan_grand_total',0) or 0)
            dark=st.session_state.theme=="dark"
            tc_s="#F8FAFC" if dark else "#1E293B"
            sc_s="#94A3B8" if dark else "#5B6B82"
            bg_card="rgba(22,32,52,.92)" if dark else "rgba(248,251,255,.97)"
            bdr_c="rgba(255,255,255,.08)" if dark else "rgba(0,0,0,.09)"
            # ── Unified Receipt Total — single truth that syncs everywhere ──
            st.markdown(f'''<div style="font-size:1.05rem;font-weight:800;color:{tc_s};margin:14px 0 8px;
            border-left:4px solid #FBBF24;padding-left:10px;">💰 Receipt Total — syncs to Dashboard, Charts &amp; Price Trends</div>''',unsafe_allow_html=True)
            tot_left,tot_right=st.columns([1,2])
            with tot_left:
                grand_total=st.number_input(
                    "Receipt Total (Rs.)",
                    min_value=0.0,
                    value=float(grand_total_ai if grand_total_ai>0 else items_sum),
                    format="%.2f",step=0.5,key="edited_gt")
                # ALWAYS sync to session state so it flows everywhere
                st.session_state['scan_grand_total']=grand_total
                st.markdown(f'<div style="font-size:.72rem;color:{sc_s};margin-top:4px;">Type the amount printed at the bottom of your receipt. This number is saved to the database and drives every chart and report.</div>',unsafe_allow_html=True)
            with tot_right:
                diff=round(grand_total-items_sum,2)
                adj_note=""
                if abs(diff)>0.01:
                    adj_note=f'<div style="color:#FBBF24;font-size:.8rem;margin-top:6px;">⚖️ A <b>Receipt Adjustment of Rs.{diff:+.2f}</b> will be added automatically on save to make the database match your total exactly.</div>'
                else:
                    adj_note=f'<div style="color:#10B981;font-size:.8rem;margin-top:6px;">✅ Items sum equals receipt total — no adjustment needed.</div>'
                st.markdown(f'''<div style="background:{bg_card};border:1px solid {bdr_c};border-radius:12px;padding:14px 18px;">
                <div style="font-size:.72rem;font-weight:700;color:{tc_s};margin-bottom:8px;text-transform:uppercase;letter-spacing:.05em;">Summary</div>
                <div style="display:flex;gap:20px;flex-wrap:wrap;">
                  <div><div style="font-size:.68rem;color:{sc_s};">AI Read from Receipt</div>
                       <div style="font-size:1.15rem;font-weight:800;color:#6366F1;">Rs.{grand_total_ai:.2f}</div></div>
                  <div><div style="font-size:.68rem;color:{sc_s};">Items in Table Sum</div>
                       <div style="font-size:1.15rem;font-weight:800;color:#10B981;">Rs.{items_sum:.2f}</div></div>
                  <div><div style="font-size:.68rem;color:{sc_s};">Your Corrected Total</div>
                       <div style="font-size:1.15rem;font-weight:800;color:#FBBF24;">Rs.{grand_total:.2f}</div></div>
                </div>
                {adj_note}
                </div>''',unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:.82rem;font-weight:700;color:{tc_s};margin:14px 0 4px;">📋 Extracted Items — click any cell to correct</div>',unsafe_allow_html=True)
            edited=st.data_editor(show,num_rows="dynamic",use_container_width=True,key="scan_ed",
                column_config={"date":st.column_config.TextColumn("Date (YYYY-MM-DD)"),
                               "time":st.column_config.TextColumn("Time"),
                               "category":st.column_config.SelectboxColumn("Category",options=CATEGORIES),
                               "unit_price":st.column_config.NumberColumn("Unit Price (Rs.)",format="%.2f"),
                               "amount":st.column_config.NumberColumn("✏️ Item Total",format="%.2f"),
                               "quantity":st.column_config.NumberColumn("Qty",format="%.2f"),
                               "standard_name":st.column_config.TextColumn("Item Name"),
                               "description":st.column_config.TextColumn("Description/Note")})
            sv,cl=st.columns(2)
            with sv:
                if st.button("✅ Save All",use_container_width=True,key="save_scan"):
                    rf=[it.get("receipt_file","") for it in st.session_state.scan_buffer]
                    rows=[]; saved=[]
                    for i,(_,row) in enumerate(edited.iterrows()):
                        q=float(row['quantity'] or 1); up=float(row['unit_price'] or 0)
                        # Use edited Total directly — do NOT recalculate from qty*price
                        amt=float(row.get('amount') or 0) or round(q*up,2)
                        rows.append((str(row['date']),str(row.get('time','')),str(row['category']),round(amt,2),
                                     str(row.get('description','')),str(row['standard_name']),q,up,rf[i] if i<len(rf) else ""))
                        saved.append({"standard_name":row['standard_name'],"unit_price":up})
                    qmany("INSERT INTO expenses(date,time,category,amount,description,standard_name,quantity,unit_price,receipt_file) VALUES(?,?,?,?,?,?,?,?,?)",rows)
                    # ── Sync corrected total: add Receipt Adjustment if needed ──
                    _gt=float(st.session_state.get('scan_grand_total',0) or 0)
                    _saved_sum=round(sum(r[3] for r in rows),2)
                    _adj=round(_gt-_saved_sum,2)
                    if abs(_adj)>0.01 and _gt>0:
                        _adj_date=rows[0][0] if rows else datetime.date.today().strftime('%Y-%m-%d')
                        _adj_time=rows[0][1] if rows else ""
                        _adj_file=rows[0][8] if rows else ""
                        qmany("INSERT INTO expenses(date,time,category,amount,description,standard_name,quantity,unit_price,receipt_file) VALUES(?,?,?,?,?,?,?,?,?)",
                              [(_adj_date,_adj_time,"Other",_adj,f"Receipt Adjustment (Total corrected to Rs.{_gt})","Receipt Adjustment",1,_adj,_adj_file)])
                    check_item_notifs(saved); st.session_state.scan_buffer=[]
                    st.session_state['scan_grand_total']=0
                    st.toast("Saved! Total Rs.{} reflected in dashboard & charts.".format(round(_gt if _gt>0 else _saved_sum,2)),icon="✅"); st.rerun()
            with cl:
                if st.button("🗑️ Discard",use_container_width=True,key="discard_scan"):
                    st.session_state.scan_buffer=[]; st.rerun()
    with manual_t:
        with st.form("mf",clear_on_submit=True):
            r1,r2=st.columns(2)
            with r1:
                m_date=st.date_input("Date",datetime.date.today(),format="DD/MM/YYYY")
                m_cat=st.selectbox("Category",CATEGORIES)
                m_std=st.text_input("Item Name",placeholder="e.g. Milk, Toor Dal")
                m_desc=st.text_input("Note (optional)")
            with r2:
                m_qty=st.number_input("Quantity",min_value=0.1,value=1.0,step=0.5,format="%.1f")
                m_price=st.number_input("Price/unit (Rs.)",min_value=0.0,value=0.0,format="%.2f")
                c=CAT_COLOR.get(m_cat,"#6366F1")
                st.markdown(f'<div style="margin-top:12px;padding:18px;background:rgba(99,102,241,.1);'
                            f'border:1px solid rgba(99,102,241,.2);border-radius:12px;text-align:center;">'
                            f'<div style="font-size:.68rem;text-transform:uppercase;color:#64748B;font-weight:600;">TOTAL</div>'
                            f'<div style="font-size:2rem;font-weight:800;color:{c};">Rs.{round(m_qty*m_price,2)}</div>'
                            +pill(m_cat)+'</div>',unsafe_allow_html=True)
            if st.form_submit_button("💾 Add Item",use_container_width=True):
                if m_std.strip() and m_price>0:
                    qrun("INSERT INTO expenses(date,time,category,amount,description,standard_name,quantity,unit_price) VALUES(?,?,?,?,?,?,?,?)",
                         (m_date.strftime('%Y-%m-%d'),datetime.datetime.now().strftime('%I:%M %p'),
                          m_cat,round(m_qty*m_price,2),m_desc,m_std.strip().title(),m_qty,m_price))
                    check_item_notifs([{"standard_name":m_std.strip().title(),"unit_price":m_price}])
                    st.toast(f"{m_std.title()} added Rs.{round(m_qty*m_price,2)}",icon="✅"); st.rerun()
                else: st.warning("Fill Item Name and Price.")

# ================================================================
# PRICE TRENDS
# ================================================================
def page_trends(df):
    ph("📈 Price Trends","Track how item prices change over time")
    if df.empty or df['standard_name'].dropna().nunique()==0: box("bx-info","No data yet."); return
    items_list=sorted(df[df['unit_price']>0]['standard_name'].dropna().unique())
    if not items_list: box("bx-info","No unit price data yet."); return
    mode=st.radio("View:",["🔍 Single Item","📊 Compare Items"],horizontal=True,key="trend_mode")
    POPTS=["3 months","6 months","1 year","2 years","All time"]
    PMAP={"3 months":3,"6 months":6,"1 year":12,"2 years":24,"All time":999}
    PAL=['#10B981','#6366F1','#F59E0B','#F87171','#A78BFA']
    if "Single" in mode:
        c1,c2=st.columns([2,1])
        with c1: sel=st.selectbox("Item:",items_list,key="t_sel")
        with c2: period=st.selectbox("Period:",POPTS,index=2,key="t_per")
        cutoff=(datetime.date.today()-datetime.timedelta(days=30*PMAP[period])).strftime('%Y-%m-%d')
        tdf=df[(df['standard_name']==sel)&(df['unit_price']>0)&(df['date']>=cutoff)].copy()
        if tdf.empty: box("bx-warn","No data for this period."); return
        tdf['date']=pd.to_datetime(tdf['date']); tdf=tdf.sort_values('date')
        pr=tdf['unit_price'].tolist(); dt=tdf['date'].tolist()
        fp=pr[0]; lp=pr[-1]; avgp=sum(pr)/len(pr); chg=(lp-fp)/fp*100 if fp>0 else 0
        vol=(max(pr)-min(pr))/avgp*100 if avgp>0 else 0
        m1,m2,m3,m4,m5=st.columns(5)
        with m1: kpi("First",f"Rs.{round(fp,2)}",dt[0].strftime('%d %b %y'),True)
        with m2: kpi("Latest",f"Rs.{round(lp,2)}",dt[-1].strftime('%d %b %y'),chg<=0)
        with m3: kpi("Lowest",f"Rs.{round(min(pr),2)}","best price",True)
        with m4: kpi("Highest",f"Rs.{round(max(pr),2)}","worst price",max(pr)==fp)
        with m5: kpi("Change",f"{round(chg,1)}%","Inflated" if chg>5 else("Cheaper" if chg<-5 else "Stable"),chg<=5)
        vc="#F87171" if vol>30 else("#FBBF24" if vol>15 else "#10B981")
        vl="High" if vol>30 else("Medium" if vol>15 else "Low")
        box("bx-info",f"Volatility: <span style='color:{vc};font-weight:700'>{vl} ({round(vol,1)}%)</span> | Avg: <b>Rs.{round(avgp,2)}</b> | <b>{len(tdf)}</b> purchases")
        with st.expander(f"📈 Price History: {sel}",expanded=True):
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=dt,y=pr,fill='tozeroy',fillcolor='rgba(16,185,129,.05)',line=dict(color='rgba(0,0,0,0)'),showlegend=False,hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=dt,y=pr,mode='lines+markers+text',name='Price',
                text=[f"Rs.{round(p)}" for p in pr],textposition='top center',
                line=dict(color='#10B981',width=2.5,shape='spline'),
                marker=dict(size=16,color='white',line=dict(width=3,color='#10B981')),
                textfont=dict(color='#94A3B8',size=10),
                hovertemplate="%{x|%d %b %Y}: Rs.%{y:.2f}<extra></extra>"))
            if len(tdf)>=3:
                ma=tdf['unit_price'].rolling(3,min_periods=1).mean().tolist()
                fig.add_trace(go.Scatter(x=dt,y=ma,mode='lines',name='3pt Moving Avg',line=dict(color='#FBBF24',width=1.5,dash='dash')))
            fig.add_hline(y=avgp,line_dash='dot',line_color='rgba(148,163,184,.35)',
                          annotation_text=f"Avg Rs.{round(avgp,1)}",annotation_font=dict(color='#64748B',size=10))
            style_fig(fig,h=380,xt="Date",yt="Unit Price (Rs.)")
            fig.update_xaxes(tickfont=dict(color="#FF6B8A",size=10))
            sch(fig,"price_hist")
        with st.expander("📋 All Records",expanded=False):
            s=tdf[['date','description','quantity','unit_price','amount','category']].copy()
            s['date']=s['date'].dt.strftime('%d/%m/%Y'); st.dataframe(s,use_container_width=True)
    else:
        c1,c2,c3=st.columns([3,1,1])
        with c1: sel=st.multiselect("Items (up to 5):",items_list,max_selections=5,default=items_list[:min(3,len(items_list))],key="c_sel")
        with c2: period=st.selectbox("Period:",POPTS,index=2,key="c_per")
        with c3: norm=st.toggle("Index to 100")
        if not sel: box("bx-info","Select items above."); return
        cutoff=(datetime.date.today()-datetime.timedelta(days=30*PMAP[period])).strftime('%Y-%m-%d')
        fig=go.Figure(); srows=[]
        for idx,item in enumerate(sel):
            idf=df[(df['standard_name']==item)&(df['unit_price']>0)&(df['date']>=cutoff)].copy()
            if idf.empty: continue
            idf['date']=pd.to_datetime(idf['date']); idf=idf.sort_values('date')
            di=idf['date'].tolist(); pi=idf['unit_price'].tolist(); ci=PAL[idx%len(PAL)]
            py=[p/pi[0]*100 for p in pi] if norm and pi[0]>0 else pi
            fig.add_trace(go.Scatter(x=di,y=py,mode='lines+markers',name=item,
                line=dict(color=ci,width=2.5,shape='spline'),
                marker=dict(size=14,color='white',line=dict(width=2.5,color=ci)),
                hovertemplate=f"<b>{item}</b><br>%{{x|%d %b %Y}}: %{{y:.1f}}<extra></extra>"))
            if len(pi)>=2:
                fp=pi[0]; lp=pi[-1]; chg=(lp-fp)/fp*100 if fp>0 else 0
                srows.append({"Item":item,"First":f"Rs.{round(fp,2)}","Latest":f"Rs.{round(lp,2)}",
                              "Change":f"{round(chg,1)}%","Purchases":len(idf),"Trend":"📈 Up" if chg>5 else("📉 Down" if chg<-5 else "➡️ Stable")})
        if norm: fig.add_hline(y=100,line_dash='dot',line_color='rgba(128,128,128,.4)',annotation_text="Baseline 100",annotation_font=dict(color='#64748B'))
        style_fig(fig,h=400,xt="Date",yt="Index (100=first)" if norm else "Unit Price (Rs.)")
        fig.update_xaxes(tickfont=dict(color="#FF6B8A",size=10))
        sch(fig,"compare")
        if srows: st.dataframe(pd.DataFrame(srows),use_container_width=True,hide_index=True)

    # ── Spending Analytics (moved from Dashboard) ─────────────────
    if not df.empty:
        st.divider()
        ph_sml="📊 Spending Analytics"
        st.markdown(f'<div class="ch-title">{ph_sml}</div><div class="ch-sub">Daily patterns, weekly comparison & top items</div>',unsafe_allow_html=True)
        today_a=datetime.date.today(); this_m_a=today_a.strftime('%Y-%m')
        db_v_a=float(get_s("daily_budget","500"))
        df_m_a=df[df['date'].str.startswith(this_m_a)].copy() if not df.empty else pd.DataFrame()
        # ── Daily bar ──────────────────────────────────────────────
        if not df_m_a.empty:
            with st.expander("📆 Daily Spending — This Month",expanded=True):
                daily=df_m_a.groupby('date',as_index=False)['amount'].sum()
                daily['over']=daily['amount']>db_v_a
                daily['lbl']=pd.to_datetime(daily['date']).dt.strftime('%d %b')
                fig_d=go.Figure()
                fig_d.add_hline(y=db_v_a,line_dash='dash',line_color='#FBBF24',line_width=1.5,
                               annotation_text=f"Limit Rs.{round(db_v_a)}",
                               annotation_font=dict(color='#FBBF24',size=10),annotation_position="top right")
                fig_d.add_trace(go.Bar(x=daily['lbl'],y=daily['amount'],
                    marker=dict(color=['rgba(248,113,113,.82)' if o else 'rgba(99,102,241,.82)' for o in daily['over']],cornerradius=4),
                    text=[f"Rs.{round(v)}" for v in daily['amount']],textposition='outside',textfont=dict(color='#94A3B8',size=9),
                    hovertemplate="<b>%{x}</b><br>Rs.%{y:,.0f}<extra></extra>"))
                style_fig(fig_d,h=340,xt="Date",yt="Amount (Rs.)",xa=-45,leg=False)
                fig_d.update_yaxes(range=[0,daily['amount'].max()*1.35])
                sch(fig_d,"daily_bar")
                box("bx-info","🟦 Blue = within limit &nbsp;|&nbsp; 🟥 Red = over daily limit &nbsp;|&nbsp; 🟡 Dashed = daily budget")
        # ── Week comparison ────────────────────────────────────────
        with st.expander("📅 This Week vs Last Week",expanded=True):
            mon_this=today_a-datetime.timedelta(days=today_a.weekday()); mon_last=mon_this-datetime.timedelta(days=7)
            wdays=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
            wdf2=df.copy(); wdf2['_dt']=pd.to_datetime(wdf2['date'])
            tw_df=wdf2[wdf2['_dt'].dt.date>=mon_this]; lw_df=wdf2[(wdf2['_dt'].dt.date>=mon_last)&(wdf2['_dt'].dt.date<mon_this)]
            tby=[tw_df[tw_df['_dt'].dt.dayofweek==i]['amount'].sum() for i in range(7)]
            lby=[lw_df[lw_df['_dt'].dt.dayofweek==i]['amount'].sum() for i in range(7)]
            fig_w=go.Figure()
            fig_w.add_trace(go.Bar(name='Last Week',x=wdays,y=lby,marker=dict(color='rgba(99,102,241,.25)',cornerradius=3),
                text=[f"Rs.{round(v)}" if v>0 else "" for v in lby],textposition='outside',textfont=dict(color='#64748B',size=9)))
            fig_w.add_trace(go.Bar(name='This Week',x=wdays,y=tby,marker=dict(color='rgba(99,102,241,.82)',cornerradius=3),
                text=[f"Rs.{round(v)}" if v>0 else "" for v in tby],textposition='outside',textfont=dict(color='#818CF8',size=9)))
            fig_w.update_layout(barmode='group',bargap=0.25,bargroupgap=0.06)
            style_fig(fig_w,h=300,xt="Day",yt="Amount (Rs.)")
            fig_w.update_yaxes(range=[0,max(max(tby),max(lby),1)*1.35])
            sch(fig_w,"week_bar")
            tw=sum(tby); lw=sum(lby); diff=tw-lw
            msg=f"Rs.{round(abs(diff))} {'more' if diff>0 else 'less'} than last week" if lw>0 else "First week of data"
            box("bx-info",f"This week: <b>Rs.{round(tw)}</b> | Last week: <b>Rs.{round(lw)}</b> | {msg}")
        # ── Top items ──────────────────────────────────────────────
        with st.expander("🏆 Top Items This Month",expanded=True):
            if not df_m_a.empty:
                tm_a=df_m_a['amount'].sum()
                top=df_m_a.groupby('standard_name',as_index=False)['amount'].sum().sort_values('amount',ascending=True).tail(8)
                if not top.empty:
                    top['pct']=top['amount']/tm_a*100
                    top['lbl2']=[f"  Rs.{round(a)} ({round(p,1)}%)" for a,p in zip(top['amount'],top['pct'])]
                    fig_t=go.Figure(go.Bar(x=top['amount'],y=top['standard_name'],orientation='h',
                        text=top['lbl2'],textposition='inside',insidetextanchor='start',textfont=dict(color='white',size=10),
                        marker=dict(color=top['amount'],colorscale=[[0,'#1E1B4B'],[0.3,'#4338CA'],[0.65,'#F59E0B'],[1,'#F87171']],cornerradius=4),
                        hovertemplate="<b>%{y}</b><br>Rs.%{x:,.0f}<extra></extra>"))
                    style_fig(fig_t,h=max(240,len(top)*36),xt="Amount (Rs.)",yt="",leg=False)
                    fig_t.update_xaxes(range=[0,top['amount'].max()*1.4])
                    sch(fig_t,"top_items")
            else:
                box("bx-info","No data this month yet.")

# ================================================================
# VAULT
# ================================================================
def page_vault():
    ph("📸 Vault","All scanned receipt images")
    files=sorted([f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.jpg','.jpeg','.png'))],reverse=True)
    if not files: box("bx-info","Vault is empty. Scan a receipt to save images."); return
    total_kb=sum(os.path.getsize(os.path.join(IMG_DIR,f)) for f in files)/1024
    box("bx-info",f"<b>{len(files)}</b> receipts | Storage: <b>{round(total_kb)} KB ({round(total_kb/1024,2)} MB)</b>")
    cols=st.columns(3)
    for i,fname in enumerate(files):
        fpath=os.path.join(IMG_DIR,fname)
        with cols[i%3]:
            st.image(fpath,use_container_width=True)
            st.caption(f"{fname} · {round(os.path.getsize(fpath)/1024)} KB")
            b1,b2,b3=st.columns(3)
            with b1:
                if st.button("🗑️ Del",key=f"d_{i}",use_container_width=True): os.remove(fpath); st.rerun()
            with b2:
                if st.button("🔄 Scan",key=f"r_{i}",use_container_width=True):
                    if GROQ_API_KEY.startswith("gsk_"):
                        with st.spinner("Scanning..."):
                            try:
                                items,_=groq_scan(fpath,datetime.date.today().strftime('%Y-%m-%d'),datetime.datetime.now().strftime('%I:%M %p'))
                                for it in items: it['receipt_file']=fname
                                st.session_state.scan_buffer.extend(items)
                                st.toast(f"{len(items)} items — go to Scan Receipt!",icon="🎉")
                            except Exception as e: st.toast(f"Error: {e}",icon="🚨")
                    else: st.toast("Set Groq key first.",icon="⚠️")
            with b3:
                with open(fpath,'rb') as fh:
                    st.download_button("⬇️",fh.read(),fname,"image/jpeg",key=f"dl_{i}",use_container_width=True)

# ================================================================
# SETTINGS
# ================================================================
def page_settings():
    ph("⚙️ Settings","Budget limits and data management")
    locked=get_s("budget_locked","0")=="1"
    c1,c2=st.columns([2,3])
    with c1:
        st.markdown("#### 💰 Budget")
        lk,_=st.columns([1,2])
        with lk: new_lock=st.toggle("🔒 Lock",value=locked,key="lock_toggle")
        if new_lock!=locked: save_s("budget_locked","1" if new_lock else "0"); st.rerun()
        box("bx-warn" if locked else "bx-good","🔒 Budgets locked." if locked else "🔓 Unlocked — edit below.")
        curr_m=float(get_s("monthly_budget","5000")); curr_d=float(get_s("daily_budget","500"))
        with st.form("sf"):
            nm=st.number_input("Monthly Budget (Rs.)",min_value=0.0,value=curr_m,step=500.0,format="%.0f",disabled=locked)
            nd=st.number_input("Daily Budget (Rs.)",min_value=0.0,value=curr_d,step=100.0,format="%.0f",disabled=locked)
            if not locked:
                imp=nm/30; match=abs(imp-nd)<nd*0.3
                box("bx-info",f"Rs.{round(nm)} / 30 = Rs.{round(imp)} implied daily | {'✅ aligned' if match else '⚠️ consider aligning'}")
            if st.form_submit_button("💾 Save",disabled=locked,use_container_width=True):
                save_s("monthly_budget",nm); save_s("daily_budget",nd); st.toast("Budget saved!",icon="✅"); st.rerun()
    with c2:
        st.markdown("#### 📊 Data Summary")
        with sqlite3.connect(DB_FILE) as c: adf=pd.read_sql("SELECT * FROM expenses",c)
        if not adf.empty:
            months=adf['date'].str[:7].nunique()
            s1,s2,s3,s4=st.columns(4)
            with s1: st.metric("Records",len(adf))
            with s2: st.metric("Total Spent",f"Rs.{round(adf['amount'].sum())}")
            with s3: st.metric("Unique Items",adf['standard_name'].nunique())
            with s4: st.metric("Avg/Month",f"Rs.{round(adf['amount'].sum()/max(months,1))}")
            img_kb=(sum(os.path.getsize(os.path.join(IMG_DIR,f)) for f in os.listdir(IMG_DIR) if f.lower().endswith(('.jpg','.jpeg','.png')))/1024 if os.path.exists(IMG_DIR) else 0)
            db_kb=os.path.getsize(DB_FILE)/1024 if os.path.exists(DB_FILE) else 0
            box("bx-info",f"DB: <b>{round(db_kb,1)} KB</b> | Images: <b>{round(img_kb)} KB</b> | Total: <b>{round((db_kb+img_kb)/1024,2)} MB</b>")
            st.markdown("#### Spending by Category")
            cat_s=adf.groupby('category')['amount'].sum().sort_values(ascending=False)
            for cat,amt in cat_s.items():
                p=amt/adf['amount'].sum()
                st.markdown(pill(cat)+f" <b>Rs.{round(amt)}</b> "+pbar(p,CAT_COLOR.get(cat,'#6366F1')),unsafe_allow_html=True)
            csv=adf.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Export All Data (CSV)",csv,"all_expenses.csv","text/csv",use_container_width=True)
        else: box("bx-info","No data yet.")
        st.divider()
        with st.expander("🔴 Danger Zone"):
            st.warning("This permanently deletes ALL expense records!")
            confirm=st.text_input("Type DELETE to confirm:")
            if st.button("Delete All Data",type="primary",use_container_width=True):
                if confirm.strip()=="DELETE": qrun("DELETE FROM expenses"); st.success("All cleared."); st.rerun()
                else: st.error("Type DELETE exactly.")


# ================================================================
# WELCOME / HOME
# ================================================================
def page_welcome():
    dark=st.session_state.theme=="dark"
    tc="#F8FAFC" if dark else "#1E293B"
    sc="#94A3B8" if dark else "#5B6B82"
    bg_card="rgba(22,32,52,.85)" if dark else "rgba(255,255,255,.92)"
    bdr="rgba(255,255,255,.07)" if dark else "rgba(0,0,0,.09)"
    shadow="0 4px 18px rgba(0,0,0,.25)" if dark else "0 4px 18px rgba(0,0,0,.08)"

    # ── Hero ────────────────────────────────────────────────────
    st.markdown(f"""
<div style="text-align:center;padding:44px 20px 24px;">
  <div style="font-size:3.4rem;line-height:1;margin-bottom:14px;">💰</div>
  <h1 style="font-size:2.6rem;font-weight:900;color:{tc};margin:0;letter-spacing:-.03em;line-height:1.15;">
    Welcome to<br>Expense Tracker Pro
  </h1>
  <p style="font-size:1.1rem;color:{sc};margin:14px auto 0;max-width:560px;line-height:1.65;">
    Scan any receipt in seconds. Track your spending. Spot price trends.<br>
    Your smart financial companion — built for real life.
  </p>
</div>
""",unsafe_allow_html=True)

    # ── Section guide cards ──────────────────────────────────────
    sections=[
        ("📊","Dashboard","#6366F1",
         "Your financial command centre.",
         "See how much you have spent this month and today versus your budget. Check remaining balance, daily average, and projected end-of-month spend. View all your transactions in one scrollable table and see spending broken down by category. Price change alerts show you when everyday items get more expensive or cheaper."),
        ("🧾","Scan Receipt","#10B981",
         "Point, scan, done — no typing needed.",
         "Upload a photo or use your phone camera. The AI reads every item on the bill word for word — printed receipts, thermal slips, or handwritten notes. Drag the red crop box to focus on just the receipt. Review extracted items, correct anything the AI missed, edit the final total, and save everything with one tap."),
        ("📈","Price Trends","#F59E0B",
         "Watch how prices move over time.",
         "Pick any item you have bought more than once and see a full price history chart. Compare multiple items side by side. Toggle to index mode to see percentage change from a baseline. Scroll down for spending analytics: daily bar chart for the current month, this-week vs last-week comparison, and your top spending items."),
        ("📸","Vault","#F87171",
         "Every receipt image, always safe.",
         "All scanned receipt photos are stored here automatically. Browse them, re-scan a saved image with the AI at any time, or download and delete as needed. Nothing gets lost between sessions."),
        ("⚙️","Settings","#A78BFA",
         "Budget limits and data control.",
         "Set your monthly and daily budget targets. Lock them with a password so you cannot accidentally change them. Export all your expense history as a CSV file. See how much storage your data and images are using. Use the Danger Zone to wipe all data if you ever need a fresh start."),
    ]

    for icon,name,color,tagline,desc in sections:
        st.markdown(f"""
<div style="background:{bg_card};border:1px solid {bdr};border-left:5px solid {color};
            border-radius:16px;padding:24px 26px;margin:12px 0;box-shadow:{shadow};">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:10px;">
    <span style="font-size:2.2rem;line-height:1;">{icon}</span>
    <div>
      <div style="font-size:1.55rem;font-weight:900;color:{color};line-height:1.1;">{name}</div>
      <div style="font-size:.95rem;font-weight:600;color:{tc};margin-top:2px;">{tagline}</div>
    </div>
  </div>
  <p style="font-size:1rem;color:{sc};margin:0;line-height:1.7;">{desc}</p>
</div>
""",unsafe_allow_html=True)

    # ── Footer nudge ─────────────────────────────────────────────
    st.markdown(f"""
<div style="text-align:center;padding:30px 0 10px;">
  <p style="font-size:1rem;color:{sc};">
    👆 Click any tab above to get started
  </p>
</div>
""",unsafe_allow_html=True)

# ================================================================
# MAIN
# ================================================================
inject_css()
inject_js()
df = load_df()
check_budget_notifs(df)
render_header(df)

# Navigation — always visible tabs on the front page
t0,t1,t2,t3,t4,t5 = st.tabs([
    "🏠 Home",
    "📊 Dashboard",
    "🧾 Scan Receipt",
    "📈 Price Trends",
    "📸 Vault",
    "⚙️ Settings"
])
with t0: page_welcome()
with t1: page_dashboard(df)
with t2: page_scanner()
with t3: page_trends(df)
with t4: page_vault()
with t5: page_settings()
