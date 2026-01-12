import atexit
import base64
import io
import json
import os
import tempfile
import threading
import time
import uuid
import zipfile
from pathlib import Path

import gradio as gr
import requests
from PIL import Image

# Get absolute path for static files
BASE_DIR = Path(__file__).parent.resolve()

API_URL = os.environ.get("API_URL", "http://localhost:8080/api/v1/ocr")

TOKEN = os.environ.get("API_TOKEN", "")

TITLE = "PP-OCRv5 Online Demo"
# DESCRIPTION = """
# - PP-OCRv5 is the latest generation of the PP-OCR series model, designed to handle a wide range of scene and text types.
# - It supports five major text types: Simplified Chinese, Traditional Chinese, Pinyin annotation, English, and Japanese.
# - PP-OCRv5 has enhanced recognition capabilities for challenging use cases, including complex handwritten Chinese and English, vertical text, and rare characters.
# - To use it, simply upload your image, or click one of the examples to load them. Read more at the links below.
# """

TEMP_DIR = tempfile.TemporaryDirectory()
atexit.register(TEMP_DIR.cleanup)

paddle_theme = gr.themes.Soft(
    font=(gr.themes.GoogleFont("Roboto"), "Open Sans", "Arial", "sans-serif"),
    font_mono=(gr.themes.GoogleFont("Fira Code"), "monospace"),
    primary_hue=gr.themes.Color(
        c50="#e8eafc",
        c100="#c5c9f7",
        c200="#a1a7f2",
        c300="#7d85ed",
        c400="#5963e8",
        c500="#2932e1",  # 메인 색상
        c600="#242bb4",
        c700="#1e2487",
        c800="#181d5a",
        c900="#12162d",
        c950="#0c0f1d",
    ),
)
MAX_NUM_PAGES = 10
TMP_DELETE_TIME = 900
THREAD_WAKEUP_TIME = 600
CSS = """
/* ===== Baidu AI Studio PaddleOCR Style CSS ===== */

/* ===== CSS Variables ===== */
:root {
    --primary-color: #2932E1;
    --primary-hover: #515eed;
    --primary-light: #e8eafc;
    --title-color: #140E35;
    --text-color: #565772;
    --text-light: #9498AC;
    --text-disabled: #C8CEDE;
    --bg-main: #F8F9FB;
    --bg-white: #ffffff;
    --bg-hover: #F7F7F9;
    --bg-disabled: #f5f5f5;
    --border-color: #E8EDF6;
    --border-input: #d9d9d9;
    --shadow-card: 0 2px 8px rgba(37, 38, 94, 0.08);
    --shadow-hover: 0 4px 12px rgba(37, 38, 94, 0.12);
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
}

/* ===== Global Styles ===== */
body, .gradio-container {
    background-color: var(--bg-main) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 10px !important;
}

/* Force all containers to use full width */
.gradio-container .app,
.gradio-container main,
.gradio-container .wrap,
.gradio-container .contain,
.row,
#results-column,
#sidebar-column,
.white-container,
.column {
    max-width: none !important;
    width: 100% !important;
}

/* Override any flex basis constraints */
.row > .column {
    flex-basis: 0 !important;
}

/* ===== Typography ===== */
#markdown-title {
    text-align: center;
    color: var(--title-color) !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
}

#markdown-title h1 {
    color: var(--primary-color) !important;
    font-size: 32px !important;
    font-weight: 700 !important;
}

label, .gr-label {
    color: rgba(0, 0, 0, 0.85) !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    margin-bottom: 4px !important;
}

/* Remove block-info background */
span[data-testid="block-info"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    color: inherit !important;
    font-weight: inherit !important;
}

/* Hide Examples default label */
.gallery.svelte-p5q82i {
    margin-top: 0 !important;
}

.block.svelte-1svsvh2 .label.svelte-p5q82i {
    display: none !important;
}

.custom-markdown h3 {
    font-size: 20px !important;
    color: var(--title-color) !important;
    font-weight: 600 !important;
    margin-bottom: 16px !important;
}

/* ===== Sidebar Toggle ===== */
#sidebar-toggle-btn {
    position: fixed !important;
    left: 0 !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    z-index: 1000 !important;
    background: linear-gradient(135deg, var(--primary-color) 0%, #4658FF 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 0 12px 12px 0 !important;
    padding: 18px 12px !important;
    cursor: pointer !important;
    box-shadow: 3px 0 12px rgba(41, 50, 225, 0.4) !important;
    transition: all 0.3s ease !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 8px !important;
    line-height: 1 !important;
    letter-spacing: 0.5px !important;
}

#sidebar-toggle-btn:hover {
    background: linear-gradient(135deg, #4658FF 0%, var(--primary-color) 100%) !important;
    box-shadow: 3px 0 16px rgba(41, 50, 225, 0.5) !important;
    padding-right: 16px !important;
}

#sidebar-toggle-btn .toggle-icon {
    font-size: 20px !important;
    display: block !important;
    color: #FFFFFF !important;
    font-weight: bold !important;
}

#sidebar-toggle-btn .toggle-text {
    font-size: 12px !important;
    display: block !important;
    white-space: nowrap !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    writing-mode: vertical-rl !important;
    text-orientation: mixed !important;
}

.sidebar-column {
    transition: all 0.3s ease !important;
    overflow: visible !important;
    position: relative !important;
}

.sidebar-hidden {
    transform: translateX(-90%) !important;
    opacity: 0.3 !important;
    pointer-events: none !important;
}

.sidebar-hidden:hover {
    opacity: 0.5 !important;
}

/* ===== Card & Panel ===== */
.gr-panel, .gr-box, .gr-group {
    background: var(--bg-white) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-card) !important;
}

.form { background: transparent !important; }

/* ===== Buttons ===== */
#analyze-btn, #unzip-btn {
    color: white !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    padding: 12px 32px !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

#analyze-btn {
    background: linear-gradient(135deg, var(--primary-color) 0%, #4658FF 100%) !important;
    box-shadow: 0 4px 12px rgba(41, 50, 225, 0.25) !important;
}

#analyze-btn:hover {
    background: linear-gradient(135deg, #4658FF 0%, var(--primary-color) 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(41, 50, 225, 0.35) !important;
}

#unzip-btn {
    background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%) !important;
    box-shadow: 0 4px 12px rgba(82, 196, 26, 0.25) !important;
}

#unzip-btn:hover {
    background: linear-gradient(135deg, #73d13d 0%, #52c41a 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(82, 196, 26, 0.35) !important;
}

/* Drag and Drop File Upload Area */
.upload-area {
    width: 100% !important;
}

.drag-drop-file {
    background: #FAFBFF !important;
    border: 1px dashed #D9D9D9 !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.3s ease !important;
    color: var(--text-color) !important;
    cursor: pointer !important;
    width: 100% !important;
    font-size: 14px !important;
    text-align: center !important;
}

.drag-drop-file:active {
    background: #E8EAFF !important;
}

.drag-drop-file:hover {
    border-color: var(--primary-color) !important;
    background: #F0F2FF !important;
}

.drag-drop-file-custom {
    background: #FAFBFF !important;
    border: 1px dashed #D9D9D9 !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.3s ease !important;
    color: var(--text-color) !important;
    cursor: pointer !important;
    width: 100% !important;
    font-size: 14px !important;
    text-align: center !important;
}

.drag-drop-file-custom button {
    min-height: 100px !important;
    height: 100px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: relative !important;
    flex-direction: column !important;
}

/* Hide original content */
.drag-drop-file-custom button .wrap {
    display: none !important;
}

/* Add custom content - only when no file */
.drag-drop-file-custom:not(:has(.file-preview-holder)) button::before {
    content: "📤" !important;
    display: block !important;
    font-size: 32px !important;
    margin-bottom: 8px !important;
}

.drag-drop-file-custom:not(:has(.file-preview-holder)) button::after {
    content: "Click or drag file to upload\\ASupport formats: PDF, JPG, PNG, JPEG" !important;
    white-space: pre-wrap !important;
    display: block !important;
    font-size: 13px !important;
    line-height: 1.6 !important;
    color: var(--text-color) !important;
    text-align: center !important;
}

/* When file is uploaded, show normal layout */
.drag-drop-file-custom:has(.file-preview-holder) {
    border-style: solid !important;
    min-height: auto !important;
}

/* Hide the upload button content when file is present, but keep button visible for delete functionality */
.drag-drop-file-custom:has(.file-preview-holder) button {
    min-height: auto !important;
    height: auto !important;
    padding: 0 !important;
}

.drag-drop-file-custom:has(.file-preview-holder) button::before,
.drag-drop-file-custom:has(.file-preview-holder) button::after {
    display: none !important;
}

/* Hover effect on custom content */
.drag-drop-file-custom:hover button::after {
    color: var(--primary-color) !important;
}

.drag-drop-file-custom:active {
    background: #E8EAFF !important;
}

.drag-drop-file-custom:hover {
    border-color: var(--primary-color) !important;
    background: #F0F2FF !important;
}

.drag-drop-file-custom label[data-testid="block-label"] {
    display: none !important;
}

.drag-drop-file-custom .upload-container {
    padding: 0 !important;
}

.drag-drop-file-custom .file-preview-holder {
    margin-top: 8px !important;
    background: #F0F2FF !important;
    border-radius: var(--radius-sm) !important;
    padding: 8px !important;
}

.file-status {
    margin-top: 8px !important;
    color: #52c41a !important;
    font-weight: 500 !important;
}

/* ===== Tabs ===== */
.tabs, .gr-tabs {
    background: var(--bg-white) !important;
    border-radius: var(--radius-lg) !important;
    padding: 16px !important;
    border: 1px solid var(--border-color) !important;
}

/* White Container (same style as Tabs) */
.white-container {
    background: var(--bg-white) !important;
    border-radius: var(--radius-lg) !important;
    padding: 16px !important;
    border: 1px solid var(--border-color) !important;
}

.tab-nav, .gr-tab-nav {
    background: var(--bg-hover) !important;
    border-radius: var(--radius-md) !important;
    padding: 4px !important;
    gap: 4px !important;
}

.tab-nav button, .gr-tab-nav button {
    background: transparent !important;
    color: var(--text-color) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 8px 16px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.tab-nav button.selected, .gr-tab-nav button.selected,
.tab-nav button[aria-selected="true"], .gr-tab-nav button[aria-selected="true"] {
    background: var(--bg-white) !important;
    color: var(--primary-color) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}

.tab-nav button:hover, .gr-tab-nav button:hover {
    color: var(--primary-color) !important;
}

/* ===== Common Form Item Base Style ===== */
#inference_device,
#use_doc_orientation_classify_cb,
#use_doc_unwarping_cb,
#use_textline_orientation_cb,
#text_det_thresh_nb,
#text_det_box_thresh_nb,
#text_det_unclip_ratio_nb,
#text_rec_score_thresh_nb,
#text_det_limit_side_len_nb,
#text_det_limit_type_rd,
#enable_perf_metrics_cb {
    padding: 8px 0 !important;
    background: transparent !important;
    border: none !important;
    border-width: 0 !important;
    border-radius: 0 !important;
    margin-bottom: 4px !important;
}

#inference_device:hover,
#use_doc_orientation_classify_cb:hover,
#use_doc_unwarping_cb:hover,
#use_textline_orientation_cb:hover,
#text_det_thresh_nb:hover,
#text_det_box_thresh_nb:hover,
#text_det_unclip_ratio_nb:hover,
#text_rec_score_thresh_nb:hover,
#text_det_limit_side_len_nb:hover,
#text_det_limit_type_rd:hover,
#enable_perf_metrics_cb:hover {
    border-color: transparent !important;
    box-shadow: none !important;
}

/* ===== Common Label Style ===== */
#inference_device > span[data-testid="block-info"],
#text_det_thresh_nb span[data-testid="block-info"],
#text_det_box_thresh_nb span[data-testid="block-info"],
#text_det_unclip_ratio_nb span[data-testid="block-info"],
#text_rec_score_thresh_nb span[data-testid="block-info"],
#text_det_limit_side_len_nb span[data-testid="block-info"] {
    font-size: 14px !important;
    font-weight: 400 !important;
    color: rgba(0, 0, 0, 0.85) !important;
}

/* ===== Radio Button Common Style ===== */
#inference_device .wrap,
#text_det_limit_type_rd .wrap {
    display: flex !important;
    gap: 8px !important;
}

#inference_device .wrap > label,
#text_det_limit_type_rd .wrap > label {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    padding: 4px 12px !important;
    border: 1px solid var(--border-input) !important;
    border-radius: var(--radius-sm) !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    font-weight: 400 !important;
    font-size: 12px !important;
    background: #fff !important;
    height: 24px !important;
}

#inference_device .wrap > label:hover,
#text_det_limit_type_rd .wrap > label:hover {
    border-color: var(--primary-color) !important;
}

#inference_device .wrap > label:has(input:checked),
#text_det_limit_type_rd .wrap > label:has(input:checked) {
    border-color: var(--primary-color) !important;
    background: var(--primary-light) !important;
    color: var(--primary-color) !important;
}

#inference_device .wrap > label input[type="radio"],
#text_det_limit_type_rd .wrap > label input[type="radio"] {
    width: 14px !important;
    height: 14px !important;
    accent-color: var(--primary-color) !important;
}

#text_det_limit_type_rd > label {
    font-size: 14px !important;
    font-weight: 400 !important;
    color: rgba(0, 0, 0, 0.85) !important;
    margin-bottom: 8px !important;
    display: block !important;
}

/* ===== Toggle Switch Style (Module Tab) ===== */
#use_doc_orientation_classify_cb > label,
#use_doc_unwarping_cb > label,
#use_textline_orientation_cb > label,
#enable_perf_metrics_cb > label {
    display: flex !important;
    flex-direction: row-reverse !important;
    align-items: center !important;
    justify-content: space-between !important;
    width: 100% !important;
    cursor: pointer !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    color: rgba(0, 0, 0, 0.85) !important;
}

#use_doc_orientation_classify_cb input[type="checkbox"],
#use_doc_unwarping_cb input[type="checkbox"],
#use_textline_orientation_cb input[type="checkbox"],
#enable_perf_metrics_cb input[type="checkbox"] {
    width: 36px !important;
    height: 20px !important;
    appearance: none !important;
    -webkit-appearance: none !important;
    background: #bfbfbf !important;
    border-radius: 10px !important;
    position: relative !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    flex-shrink: 0 !important;
    margin: 0 !important;
}

#use_doc_orientation_classify_cb input[type="checkbox"]::before,
#use_doc_unwarping_cb input[type="checkbox"]::before,
#use_textline_orientation_cb input[type="checkbox"]::before,
#enable_perf_metrics_cb input[type="checkbox"]::before {
    content: '' !important;
    position: absolute !important;
    width: 16px !important;
    height: 16px !important;
    background: white !important;
    border-radius: 50% !important;
    top: 2px !important;
    left: 2px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important;
}

#use_doc_orientation_classify_cb input[type="checkbox"]:checked,
#use_doc_unwarping_cb input[type="checkbox"]:checked,
#use_textline_orientation_cb input[type="checkbox"]:checked,
#enable_perf_metrics_cb input[type="checkbox"]:checked {
    background: var(--primary-color) !important;
}

#use_doc_orientation_classify_cb input[type="checkbox"]:checked::before,
#use_doc_unwarping_cb input[type="checkbox"]:checked::before,
#use_textline_orientation_cb input[type="checkbox"]:checked::before,
#enable_perf_metrics_cb input[type="checkbox"]:checked::before {
    left: 18px !important;
}

/* ===== Number Input Style ===== */
#text_det_thresh_nb > label,
#text_det_box_thresh_nb > label,
#text_det_unclip_ratio_nb > label,
#text_rec_score_thresh_nb > label,
#text_det_limit_side_len_nb > label {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 12px !important;
}

#text_det_thresh_nb span[data-testid="block-info"],
#text_det_box_thresh_nb span[data-testid="block-info"],
#text_det_unclip_ratio_nb span[data-testid="block-info"],
#text_rec_score_thresh_nb span[data-testid="block-info"],
#text_det_limit_side_len_nb span[data-testid="block-info"] {
    flex: 1 !important;
}

#text_det_thresh_nb input,
#text_det_box_thresh_nb input,
#text_det_unclip_ratio_nb input,
#text_rec_score_thresh_nb input,
#text_det_limit_side_len_nb input {
    border: 1px solid var(--border-input) !important;
    border-radius: var(--radius-sm) !important;
    padding: 4px 8px !important;
    font-size: 12px !important;
    width: 70px !important;
    height: 24px !important;
    text-align: center !important;
    transition: all 0.2s ease !important;
    background: #fff !important;
    flex-shrink: 0 !important;
}

#text_det_thresh_nb input:focus,
#text_det_box_thresh_nb input:focus,
#text_det_unclip_ratio_nb input:focus,
#text_rec_score_thresh_nb input:focus,
#text_det_limit_side_len_nb input:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(41, 50, 225, 0.1) !important;
    outline: none !important;
}

/* ===== Disabled States ===== */
#text_det_limit_type_rd:has(input:disabled),
#text_det_limit_side_len_nb:has(input:disabled) {
    opacity: 0.6 !important;
}

#text_det_limit_type_rd:has(input:disabled) label,
#text_det_limit_type_rd:has(input:disabled) .wrap > label {
    color: var(--text-disabled) !important;
    cursor: not-allowed !important;
    opacity: 0.7 !important;
}

#text_det_limit_side_len_nb input:disabled {
    background-color: var(--bg-disabled) !important;
    color: var(--text-disabled) !important;
    cursor: not-allowed !important;
    border-color: var(--border-color) !important;
}

/* ===== Loader ===== */
.loader {
    border: 4px solid var(--bg-hover);
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    width: 48px;
    height: 48px;
    animation: spin 1s linear infinite;
    margin: 24px auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loader-container {
    text-align: center;
    margin: 24px 0;
    color: var(--text-color);
}

.loader-container-prepare {
    text-align: left;
    margin: 16px 0;
}

.loader-container-prepare > div {
    background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 100%) !important;
    border: 1px solid var(--border-color) !important;
    border-left: 4px solid var(--primary-color) !important;
}

/* ===== Gallery ===== */
.gr-gallery, .gallery {
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
}

.gradio-gallery-item:hover {
    background-color: transparent !important;
    filter: none !important;
    transform: none !important;
}

/* ===== Spacing Classes ===== */
.tight-spacing { margin-bottom: -5px !important; }

.tight-spacing-as {
    margin-top: 8px !important;
    margin-bottom: 8px !important;
    padding: 12px 16px !important;
    background: var(--bg-white) !important;
    border-radius: var(--radius-md) !important;
    border-left: 3px solid var(--primary-color) !important;
    color: var(--text-color) !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}

.image-container img { display: inline-block !important; }

/* ===== Navigation Bar ===== */
.nav-bar {
    display: flex !important;
    justify-content: center !important;
    background-color: var(--bg-white) !important;
    padding: 16px 0 !important;
    box-shadow: var(--shadow-card) !important;
    margin-top: 24px !important;
    border-radius: var(--radius-lg) !important;
}

.nav-links {
    display: flex !important;
    gap: 32px !important;
    width: 100% !important;
    justify-content: center !important;
}

.nav-link {
    color: var(--title-color) !important;
    text-decoration: none !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    padding: 8px 24px !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

.nav-link:hover {
    color: var(--primary-color) !important;
    background: var(--primary-light) !important;
    text-decoration: none !important;
}

/* ===== File Download & JSON ===== */
.file-download { margin-top: 16px !important; }

.json-holder {
    background: var(--bg-white) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border-color) !important;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
    .gradio-container { padding: 12px !important; }
    
    #analyze-btn, #unzip-btn {
        padding: 10px 20px !important;
        font-size: 14px !important;
    }
    
    .nav-links {
        flex-direction: column !important;
        gap: 8px !important;
    }
}

/* ===== Banner ===== */
.banner-container {
    background: transparent !important;
    margin: -16px -16px 16px -16px !important;
    padding: 0 !important;
    width: calc(100% + 32px) !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
}

.banner-container .image-container {
    background: transparent !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

.banner-container .image-container button {
    cursor: default !important;
    background: transparent !important;
}

.banner-container .image-frame {
    background: transparent !important;
    display: flex !important;
    justify-content: center !important;
}

.banner-container img {
    max-width: 100% !important;
    width: auto !important;
    height: auto !important;
    display: block !important;
    margin: 0 auto !important;
    object-fit: contain !important;
}

.banner-container .icon-button-wrapper,
.banner-container .icon-buttons,
.banner-container .top-panel {
    display: none !important;
}
"""

EXAMPLE_DIR = BASE_DIR / "examples"
EXAMPLE_PDF_DIR = BASE_DIR / "examples_pdf"

# Dynamically load example files from directories
def load_examples_from_dir(directory, extensions):
    """Load all files with specified extensions from directory"""
    examples = []
    if directory.exists() and directory.is_dir():
        for file_path in sorted(directory.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                examples.append([str(file_path)])
    return examples

# Load image examples (png, jpg, jpeg)
EXAMPLE_TEST = load_examples_from_dir(EXAMPLE_DIR, {'.png', '.jpg', '.jpeg'})

# Load PDF examples
EXAMPLE_PDF = load_examples_from_dir(EXAMPLE_PDF_DIR, {'.pdf'})

DESC_DICT = {
    "use_doc_orientation_classify": "Enable the document image orientation classification module. When enabled, you can correct distorted images, such as wrinkles, tilts, etc.",
    "use_doc_unwarping": "Enable the document unwarping module. When enabled, you can correct distorted images, such as wrinkles, tilts, etc.",
    "use_textline_orientation": "Enable the text line orientation classification module to support the distinction and correction of text lines of 0 degrees and 180 degrees.",
    "text_det_limit_type": "[Short side] means to ensure that the shortest side of the image is not less than [Image side length limit for text detection], and [Long side] means to ensure that the longest side of the image is not greater than [Image side length limit for text detection].",
    "text_det_limit_side_len_nb": "For the side length limit of the text detection input image, for large images with dense text, if you want more accurate recognition, you should choose a larger size. This parameter is used in conjunction with the [Image side length limit type for text detection]. Generally, the maximum [Long side] is suitable for scenes with large images and text, and the minimum [Short side] is suitable for document scenes with small and dense images.",
    "text_det_thresh_nb": "In the output probability map, only pixels with scores greater than the threshold are considered text pixels, and the value range is 0~1.",
    "text_det_box_thresh_nb": "When the average score of all pixels in the detection result border is greater than the threshold, the result will be considered as a text area, and the value range is 0 to 1. If missed detection occurs, this value can be appropriately lowered.",
    "text_det_unclip_ratio_nb": "Use this method to expand the text area. The larger the value, the larger the expanded area.",
    "text_rec_score_thresh_nb": "After text detection, the text box performs text recognition, and the text results with scores greater than the threshold will be retained. The value range is 0~1.",
}
tmp_time = {}
lock = threading.Lock()


def gen_tooltip_radio(desc_dict):
    tooltip = {}
    for key, desc in desc_dict.items():
        suffixes = ["_cb", "_rb", "_md"]
        if key.endswith("_nb"):
            suffix = "_nb"
            suffixes = ["_nb", "_md"]
            key = key[: -len(suffix)]
        for suffix in suffixes:
            tooltip[f"{key}{suffix}"] = desc
    return tooltip


TOOLTIP_RADIO = gen_tooltip_radio(DESC_DICT)


def url_to_bytes(url, *, timeout=10):
    """Download image from URL"""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def base64_to_bytes(base64_str):
    """Decode base64 string to bytes"""
    return base64.b64decode(base64_str)


def get_image_bytes(image_data):
    """Get image bytes from either URL or base64 string"""
    if image_data is None:
        return None
    
    # Check if it's a URL (starts with http:// or https://)
    if isinstance(image_data, str) and (image_data.startswith('http://') or image_data.startswith('https://')):
        return url_to_bytes(image_data)
    # Otherwise assume it's base64
    elif isinstance(image_data, str):
        return base64_to_bytes(image_data)
    else:
        return None


def bytes_to_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes))


def process_file(
    file_path,
    image_input,
    enable_deepx_npu,
    use_doc_orientation_classify,
    use_doc_unwarping,
    use_textline_orientation,
    text_det_limit_type,
    text_det_limit_side_len,
    text_det_thresh,
    text_det_box_thresh,
    text_det_unclip_ratio,
    text_rec_score_thresh,
    enable_perf_metrics=True,
):
    """Process uploaded file with API"""
    try:
        if not file_path and not image_input:
            # 파일이 없으면 조용히 None 반환 (validate_file_input에서 이미 경고 표시함)
            return None
        if file_path:
            if Path(file_path).suffix == ".pdf":
                file_type = "pdf"
            else:
                file_type = "image"
        else:
            file_path = image_input
            file_type = "image"
        # Read file content
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Call API for processing

        file_data = base64.b64encode(file_bytes).decode("ascii")
        headers = {
            "Authorization": f"token {TOKEN}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            API_URL,
            json={
                "file": file_data,
                "fileType": 0 if file_type == "pdf" else 1,
                "visualize": True,  # Enable visualization to get images
                "deepx": enable_deepx_npu,
                "inflight": enable_perf_metrics,  # Enable performance metrics
                "useDocOrientationClassify": use_doc_orientation_classify,
                "useDocUnwarping": use_doc_unwarping,
                "useTextlineOrientation": use_textline_orientation,
                "textDetLimitType": text_det_limit_type,
                "textDetLimitSideLen": text_det_limit_side_len,
                "textDetThresh": text_det_thresh,
                "textDetBoxThresh": text_det_box_thresh,
                "textDetUnclipRatio": text_det_unclip_ratio,
                "textRecScoreThresh": text_rec_score_thresh,
            },
            headers=headers,
            timeout=1000,
        )
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError("API request failed") from e
        # Parse API response
        result = response.json()
        layout_results = result.get("result", {}).get("ocrResults", [])
        overall_ocr_res_images = []
        output_json = result.get("result", {})
        input_images = []
        
        for res in layout_results:
            # Handle both URL and base64 encoded images
            ocr_image_bytes = get_image_bytes(res.get("ocrImage"))
            input_image_bytes = get_image_bytes(res.get("inputImage"))
            
            if ocr_image_bytes:
                overall_ocr_res_images.append(ocr_image_bytes)
            if input_image_bytes:
                input_images.append(input_image_bytes)

        return {
            "original_file": file_path,
            "file_type": file_type,
            "overall_ocr_res_images": overall_ocr_res_images,
            "output_json": output_json,
            "input_images": input_images,
            "api_response": result,
            "performance_metrics": output_json.get("performanceMetrics"),
        }

    except requests.exceptions.RequestException as e:
        raise gr.Error(f"API request failed: {str(e)}")
    except Exception as e:
        raise gr.Error(f"Error processing file: {str(e)}")


def export_full_results(results):
    """Create ZIP file with all analysis results"""
    try:
        global tmp_time
        if not results:
            raise ValueError("No results to export")

        filename = Path(results["original_file"]).stem + f"_{uuid.uuid4().hex}.zip"
        zip_path = Path(TEMP_DIR.name, filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for i, img_bytes in enumerate(results["overall_ocr_res_images"]):
                zipf.writestr(f"overall_ocr_res_images/page_{i+1}.jpg", img_bytes)

            zipf.writestr(
                "output.json",
                json.dumps(results["output_json"], indent=2, ensure_ascii=False),
            )

            # Add API response
            api_response = results.get("api_response", {})
            zipf.writestr(
                "api_response.json",
                json.dumps(api_response, indent=2, ensure_ascii=False),
            )

            for i, img_bytes in enumerate(results["input_images"]):
                zipf.writestr(f"input_images/page_{i+1}.jpg", img_bytes)
        with lock:
            tmp_time[zip_path] = time.time()
        return str(zip_path)

    except Exception as e:
        raise gr.Error(f"Error creating ZIP file: {str(e)}")

def on_file_change_from_examples_image(file):
    return on_common_change(file, "examples_image")

def on_file_change_from_examples_pdf(file):
    return on_common_change(file, "examples_pdf")

def on_file_change_from_input_impl(file_select, self_input, ref_input, called_from):
    if file_select != '':
        # file_select가 이미 설정되어 있음, X버튼을 눌렸는지 파악하고 X 버튼 누른경우면 file_select 초기화
        if ref_input is not None:
            # img인 경우 file이 이미 설정된게 있음
            # file인 경우 img가 이미 설정된게 있음
            if self_input is not  None:
                # 자신이 비지 않은 경우
                if self_input != ref_input:
                    # 자신과 ref가 다른경우 정상 변경된 경우
                    return on_common_change(self_input, called_from)
                else: 
                    # 자신과 ref가 같은경우 X버튼 눌려서 초기화된 경우
                    return gr.Textbox(value=None, visible=False), gr.File(value=None), gr.Image(value=None)
            else:
                # 자신이 빈경우 skip
                return gr.skip(), gr.skip(), gr.skip()
        else:
            # img인 경우 file이 설정된게 없음
            # file인 경우 img가 설정된게 없음
            if self_input is not  None:
                # 자신이 비지 않은 경우
                if (file_select in os.path.basename(self_input)):
                    # 자신과 file_select가 같은경우 X버튼 눌려서 초기화된 경우
                    return gr.Textbox(value=None, visible=False), gr.File(value=None), gr.Image(value=None)
                else:
                    # 자신과 file_select가 다른경우 정상 변경된 경우
                    return on_common_change(self_input, called_from)
            else:
                # file_select는 존재하는데 self와 ref가 비어있는경우는 초기화
                if self_input is None:
                    return gr.Textbox(value=None, visible=False), gr.File(value=None), gr.Image(value=None)
                else:
                    # file_select가 존재 self는 존재하나 ref는 비어있는 경우 skip
                    return gr.skip(), gr.skip(), gr.skip()
    else:
        # file_select가 빈경우 skip
        return gr.skip(), gr.skip(), gr.skip()

def on_file_change_from_file_input(file_select, self_input, ref_input):
    return on_file_change_from_input_impl(file_select, self_input, ref_input, "file_input")

def on_file_change_from_image_input(file_select, self_input, ref_input):
    return on_file_change_from_input_impl(file_select, self_input, ref_input, "image_input")

def on_common_change_impl(file):
    """Handle file input change and return status textbox"""
    if file is not None:
        try:
            filename = os.path.basename(file.name) if hasattr(file, 'name') else os.path.basename(str(file))
            return gr.Textbox(value=f"✅ Chosen file: {filename}", visible=True)
        except Exception:
            return gr.Textbox(value="✅ File selected", visible=True)
    return gr.Textbox(value=None, visible=False)

def on_common_change(file, called_from):
    """Handle file input change and return status textbox"""
    input_select = on_common_change_impl(file)

    if called_from == 'examples_image':
        file_input = gr.File(value=None)
        image_input = gr.skip()
    elif called_from == 'examples_pdf':
        file_input = gr.skip()
        image_input = gr.Image(value=None)
    elif called_from == 'file_input':
        file_input = gr.skip()
        image_input = gr.Image(value=None)
    elif called_from == 'image_input':
        file_input = gr.File(value=None)
        image_input = gr.skip()
    else:
        raise ValueError("Invalid called_from value")
    
    return input_select, file_input, image_input

def clear_file_selection():
    return gr.File(value=None), gr.Textbox(value=None, visible=False)


def clear_file_selection_from_examples_image(image_input):
    """Examples 선택시 호출 - 상태 텍스트만 업데이트"""
    if image_input is None:
        return gr.Textbox(value=None, visible=False)
    try:
        text_name = "✅ Chosen file: " + os.path.basename(image_input)
        return gr.Textbox(value=text_name, visible=True)
    except Exception:
        return gr.Textbox(value="✅ Example selected", visible=True)


def clear_file_on_image_change(image_input):
    """image_input이 변경되면 file_input 초기화"""
    if image_input is not None:
        return gr.File(value=None)
    return gr.skip()

# def clear_image_on_file_change(file_input):
#     """file_input이 변경되면 image_input 초기화"""
#     if file_input is not None:
#         return gr.Image(value=None)
#     return gr.skip()


def toggle_device_options(inference_device):
    """Toggle interactive state of text detection limit options based on device type"""
    is_cpu = not inference_device  # CPU = False, NPU = True
    if is_cpu:
        info_html = """<div style="
            padding: 12px 16px;
            background: #F6FFED;
            border-left: 3px solid #52C41A;
            border-radius: 6px;
            margin-bottom: 12px;
            font-size: 13px;
            color: #389E0D;
            line-height: 1.5;
        ">
            <strong style="color: #237804;">ℹ️ CPU Mode:</strong> 
            You can configure image size limits. The image will be resized according to your settings (e.g., 736px).
        </div>"""
    else:
        info_html = """<div style="
            padding: 12px 16px;
            background: #FFF7E6;
            border-left: 3px solid #FAAD14;
            border-radius: 6px;
            margin-bottom: 12px;
            font-size: 13px;
            color: #8C6D1F;
            line-height: 1.5;
        ">
            <strong style="color: #D48806;">ℹ️ DEEPX NPU Mode:</strong> 
            Uses fixed resolution models (640×640 or 960×960) for hardware acceleration. 
            Image size limit parameters are automatically determined.
        </div>"""
    return {
        text_det_limit_type_rd: gr.Radio(interactive=is_cpu),
        text_det_limit_side_len_nb: gr.Number(interactive=is_cpu),
        device_info_md: gr.HTML(value=info_html),
    }

# Interaction logic
def validate_file_input(file_path, image_input):
    """파일이 선택되었는지 확인하고, 없으면 경고 표시"""
    if not file_path and not image_input:
        gr.Warning("📁 Please select a file first before parsing.")

def toggle_spinner(file_path, image_input):
    """파일이 있을 때만 스피너 표시"""
    if not file_path and not image_input:
        # 파일이 없으면 현재 상태 유지
        return (
            gr.skip(),
            gr.skip(),
            gr.skip(),
            gr.skip(),
            gr.skip(),
        )
    return (
        gr.Column(visible=True),
        gr.Column(visible=False),
        gr.File(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def hide_spinner(results):
    """스피너 숨기고, 결과가 있을 때만 탭 표시"""
    if results:
        return gr.Column(visible=False), gr.update(visible=True)
    else:
        # 결과가 없으면 스피너만 숨기고 탭은 숨김 유지
        return gr.Column(visible=False), gr.skip()


def update_display(results):
    if not results:
        return [gr.skip()] * (MAX_NUM_PAGES + 1 + len(gallery_list) + 1)  # +1 for perf_metrics_html
    
    # Validate results
    assert len(results["overall_ocr_res_images"]) <= MAX_NUM_PAGES, len(
        results["overall_ocr_res_images"]
    )
    
    # Prepare OCR images
    ocr_imgs = []
    for img in results["overall_ocr_res_images"]:
        ocr_imgs.append(gr.Image(value=bytes_to_image(img), visible=True))
    for _ in range(len(results["overall_ocr_res_images"]), MAX_NUM_PAGES):
        ocr_imgs.append(gr.Image(visible=False))
    
    # Prepare JSON output
    output_json = [gr.JSON(value=results["output_json"], visible=True)]
    
    # Prepare gallery images - convert bytes to PIL Image for gallery
    gallery_images = []
    for img_data in results["input_images"]:
        if isinstance(img_data, bytes):
            gallery_images.append(bytes_to_image(img_data))
        else:
            gallery_images.append(img_data)
    
    # Update all galleries with the same images
    gallery_list_imgs = []
    for i in range(len(gallery_list)):
        gallery_list_imgs.append(
            gr.Gallery(
                value=gallery_images,
                rows=len(gallery_images) if len(gallery_images) > 0 else 1,
            )
        )
    
    # Prepare performance metrics HTML
    perf_metrics = results.get("performance_metrics")
    if perf_metrics:
        perf_html = format_performance_metrics_html(perf_metrics)
    else:
        perf_html = "<div style='padding: 20px; text-align: center; color: #888;'>Performance metrics not available. Enable 'Performance Metrics' option to see timing information.</div>"
    
    perf_metrics_output = [gr.HTML(value=perf_html)]
    
    return ocr_imgs + output_json + gallery_list_imgs + perf_metrics_output


def format_performance_metrics_html(metrics):
    """Format performance metrics as HTML for display"""
    if not metrics:
        return "<div style='padding: 20px; text-align: center; color: #888;'>No performance metrics available.</div>"
    
    breakdown = metrics.get("breakdown", {})
    per_page = metrics.get("perPage", {})
    ocr_stages = metrics.get("ocrStages", {})
    
    # Build HTML
    html = """
    <div style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <h3 style="color: #2932E1; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 24px;">📊</span> Performance Metrics
        </h3>
        
        <!-- Summary Cards -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 4px;">Total Time</div>
                <div style="font-size: 28px; font-weight: 700;">{total_time:.2f}s</div>
                <div style="font-size: 12px; opacity: 0.8;">{total_time_ms:.0f} ms</div>
            </div>
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 4px;">OCR Inference</div>
                <div style="font-size: 28px; font-weight: 700;">{ocr_time:.2f}s</div>
                <div style="font-size: 12px; opacity: 0.8;">{ocr_pct:.1f}% of total</div>
            </div>
            <div style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(235, 51, 73, 0.4);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 4px;">Pages Processed</div>
                <div style="font-size: 28px; font-weight: 700;">{page_count}</div>
                <div style="font-size: 12px; opacity: 0.8;">{per_page_time:.2f}s per page</div>
            </div>
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 4px;">Backend</div>
                <div style="font-size: 28px; font-weight: 700;">{backend}</div>
                <div style="font-size: 12px; opacity: 0.8;">{mode} mode</div>
            </div>
        </div>
        
        <!-- Detailed Breakdown -->
        <div style="background: white; border: 1px solid #e8edf6; border-radius: 12px; padding: 20px; margin-bottom: 16px;">
            <h4 style="color: #140E35; margin-bottom: 16px;">Time Breakdown</h4>
            <div style="display: flex; flex-direction: column; gap: 12px;">
    """
    
    total_time = metrics.get("totalTimeSec", 0)
    ocr_time = breakdown.get("ocrInferenceSec", 0)
    formatting_time = breakdown.get("formattingSec", 0)
    pdf_time = breakdown.get("pdfConversionSec", 0) or 0
    
    # Calculate percentages
    ocr_pct = (ocr_time / total_time * 100) if total_time > 0 else 0
    formatting_pct = (formatting_time / total_time * 100) if total_time > 0 else 0
    pdf_pct = (pdf_time / total_time * 100) if total_time > 0 else 0
    
    # Add PDF conversion if present
    if pdf_time > 0:
        html += f"""
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #565772;">PDF Conversion</span>
                        <span style="font-weight: 600; color: #140E35;">{pdf_time:.3f}s ({pdf_pct:.1f}%)</span>
                    </div>
                    <div style="background: #e8edf6; border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #f5af19, #f12711); height: 100%; width: {pdf_pct}%; border-radius: 4px;"></div>
                    </div>
                </div>
        """
    
    html += f"""
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #565772;">OCR Inference</span>
                        <span style="font-weight: 600; color: #140E35;">{ocr_time:.3f}s ({ocr_pct:.1f}%)</span>
                    </div>
                    <div style="background: #e8edf6; border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #11998e, #38ef7d); height: 100%; width: {ocr_pct}%; border-radius: 4px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #565772;">Result Formatting</span>
                        <span style="font-weight: 600; color: #140E35;">{formatting_time:.3f}s ({formatting_pct:.1f}%)</span>
                    </div>
                    <div style="background: #e8edf6; border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; width: {formatting_pct}%; border-radius: 4px;"></div>
                    </div>
                </div>
            </div>
        </div>
    """
    
    # OCR Stages Breakdown (new section)
    doc_ori_ms = ocr_stages.get("docOrientationMs")
    doc_uv_ms = ocr_stages.get("docUnwarpingMs")
    det_ms = ocr_stages.get("detectionMs", 0)
    cls_ms = ocr_stages.get("textlineOrientationMs")
    rec_ms = ocr_stages.get("recognitionMs", 0)
    
    # Check if backend is CPU
    backend = metrics.get("backend", "CPU")
    is_cpu = backend == "CPU"
    
    # Calculate total OCR stages time for percentage
    total_stages_ms = (doc_ori_ms or 0) + (doc_uv_ms or 0) + det_ms + (cls_ms or 0) + rec_ms
    
    # Show CPU notice or stages breakdown
    if is_cpu:
        html += """
        <!-- CPU Notice for OCR Stages -->
        <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 12px; padding: 20px; margin-bottom: 16px;">
            <h4 style="color: #92400e; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 18px;">ℹ️</span> OCR Pipeline Stages
            </h4>
            <p style="color: #78350f; margin: 0; font-size: 14px; line-height: 1.6;">
            <strong>Note:</strong> CPU backend doesn't support per-stage timing for OCR inference. Only total time is provided.
            <br><span style="opacity: 0.8;">Use NPU backend to see detailed timing for each stage.</span>
            </p>
        </div>
        """
    elif total_stages_ms > 0:
        html += f"""
        <!-- OCR Stages Breakdown -->
        <div style="background: white; border: 1px solid #e8edf6; border-radius: 12px; padding: 20px; margin-bottom: 16px;">
            <h4 style="color: #140E35; margin-bottom: 16px;">🔬 OCR Pipeline Stages</h4>
            <div style="display: flex; flex-direction: column; gap: 12px;">
        """
        
        # Define stages with colors
        stages = [
            ("Doc Orientation", doc_ori_ms, "#f093fb", "#f5576c"),
            ("Doc Unwarping", doc_uv_ms, "#4facfe", "#00f2fe"),
            ("Text Detection", det_ms, "#43e97b", "#38f9d7"),
            ("Textline Orientation", cls_ms, "#fa709a", "#fee140"),
            ("Text Recognition", rec_ms, "#a18cd1", "#fbc2eb"),
        ]
        
        for stage_name, stage_ms, color1, color2 in stages:
            if stage_ms is not None and stage_ms > 0:
                stage_pct = (stage_ms / total_stages_ms * 100) if total_stages_ms > 0 else 0
                html += f"""
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="color: #565772;">{stage_name}</span>
                        <span style="font-weight: 600; color: #140E35;">{stage_ms:.1f}ms ({stage_pct:.1f}%)</span>
                    </div>
                    <div style="background: #e8edf6; border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, {color1}, {color2}); height: 100%; width: {stage_pct}%; border-radius: 4px;"></div>
                    </div>
                </div>
                """
        
        html += """
            </div>
        </div>
        """
    
    # Per-page stats
    per_page_ocr = per_page.get("ocrInferenceSec", 0)
    per_page_format = per_page.get("formattingSec", 0)
    per_page_doc_ori = per_page.get("docOrientationMs")
    per_page_doc_uv = per_page.get("docUnwarpingMs")
    per_page_det = per_page.get("detectionMs")
    per_page_cls = per_page.get("textlineOrientationMs")
    per_page_rec = per_page.get("recognitionMs")
    
    html += f"""
        <!-- Per-Page Stats -->
        <div style="background: white; border: 1px solid #e8edf6; border-radius: 12px; padding: 20px;">
            <h4 style="color: #140E35; margin-bottom: 16px;">Per-Page Statistics</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px;">
                <div style="text-align: center; padding: 12px; background: #f8f9fb; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 700; color: #2932E1;">{per_page_ocr:.3f}s</div>
                    <div style="font-size: 12px; color: #565772;">OCR Total</div>
                </div>
                <div style="text-align: center; padding: 12px; background: #f8f9fb; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 700; color: #2932E1;">{per_page_format:.3f}s</div>
                    <div style="font-size: 12px; color: #565772;">Formatting</div>
                </div>
    """
    
    # Add per-page OCR stage stats if available (only for NPU, CPU returns 0)
    # CPU doesn't support per-stage timing, so we hide these when backend is CPU
    if not is_cpu:
        if per_page_doc_ori is not None and per_page_doc_ori > 0:
            html += f"""
                <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #fff5f5, #fff); border-radius: 8px; border: 1px solid #ffe0e0;">
                    <div style="font-size: 20px; font-weight: 700; color: #f5576c;">{per_page_doc_ori:.1f}ms</div>
                    <div style="font-size: 12px; color: #565772;">Doc Orient.</div>
                </div>
            """
        
        if per_page_doc_uv is not None and per_page_doc_uv > 0:
            html += f"""
                <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #f0f9ff, #fff); border-radius: 8px; border: 1px solid #bae6fd;">
                    <div style="font-size: 20px; font-weight: 700; color: #0284c7;">{per_page_doc_uv:.1f}ms</div>
                    <div style="font-size: 12px; color: #565772;">Unwarping</div>
                </div>
            """
        
        if per_page_det is not None and per_page_det > 0:
            html += f"""
                <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #f0fdf4, #fff); border-radius: 8px; border: 1px solid #bbf7d0;">
                    <div style="font-size: 20px; font-weight: 700; color: #16a34a;">{per_page_det:.1f}ms</div>
                    <div style="font-size: 12px; color: #565772;">Detection</div>
                </div>
            """
        
        if per_page_cls is not None and per_page_cls > 0:
            html += f"""
                <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #fffbeb, #fff); border-radius: 8px; border: 1px solid #fde68a;">
                    <div style="font-size: 20px; font-weight: 700; color: #d97706;">{per_page_cls:.1f}ms</div>
                    <div style="font-size: 12px; color: #565772;">Textline Ori.</div>
                </div>
            """
        
        if per_page_rec is not None and per_page_rec > 0:
            html += f"""
                <div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #faf5ff, #fff); border-radius: 8px; border: 1px solid #e9d5ff;">
                    <div style="font-size: 20px; font-weight: 700; color: #9333ea;">{per_page_rec:.1f}ms</div>
                    <div style="font-size: 12px; color: #565772;">Recognition</div>
                </div>
            """
    
    # Add PDF-specific info if available
    pdf_dpi = metrics.get("pdfDpi")
    pdf_threads = metrics.get("pdfThreadCount")
    if pdf_dpi:
        html += f"""
                <div style="text-align: center; padding: 12px; background: #f8f9fb; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 700; color: #2932E1;">{pdf_dpi}</div>
                    <div style="font-size: 12px; color: #565772;">PDF DPI</div>
                </div>
                <div style="text-align: center; padding: 12px; background: #f8f9fb; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 700; color: #2932E1;">{pdf_threads}</div>
                    <div style="font-size: 12px; color: #565772;">PDF Threads</div>
                </div>
        """
    
    html += """
            </div>
        </div>
    </div>
    """
    
    # Format the HTML with values
    return html.format(
        total_time=total_time,
        total_time_ms=metrics.get("totalTimeMs", 0),
        ocr_time=ocr_time,
        ocr_pct=ocr_pct,
        page_count=metrics.get("pageCount", 1),
        per_page_time=per_page_ocr,
        backend=metrics.get("backend", "N/A"),
        mode=metrics.get("mode", "N/A"),
    )


def update_image(evt: gr.SelectData):
    update_images = []
    for index in range(MAX_NUM_PAGES):
        update_images.append(
            gr.Image(visible=False) if index != evt.index else gr.Image(visible=True)
        )
    return update_images


def delete_file_periodically():
    global tmp_time
    while True:
        current_time = time.time()
        delete_tmp = []
        for filename, strat_time in list(tmp_time.items()):
            if (current_time - strat_time) >= TMP_DELETE_TIME:
                if os.path.exists(filename):
                    os.remove(filename)
                    delete_tmp.append(filename)
        for filename in delete_tmp:
            with lock:
                del tmp_time[filename]
        time.sleep(THREAD_WAKEUP_TIME)

BANNER_PATH = str(BASE_DIR / "res" / "img" / "deepx-baidu-pp-banner.png")
BANNER_CES_PATH = str(BASE_DIR / "res" / "img" / "DEEPX-Banner-CES-2026-01.png")

# 브라우저의 언어 설정을 'en-US'로 속이는 스크립트
FORCE_EN_SCRIPT = """
<script>
    try {
        Object.defineProperty(navigator, 'language', {
            get: function() { return 'en-US'; }
        });
        Object.defineProperty(navigator, 'languages', {
            get: function() { return ['en-US', 'en']; }
        });
    } catch (e) {
        console.log("Language override failed");
    }
</script>
"""

with gr.Blocks(css=CSS, title=TITLE, theme=paddle_theme, head=FORCE_EN_SCRIPT) as demo:
    results_state = gr.State()

    gr.Image(
        value=BANNER_PATH,
        show_label=False,
        show_download_button=False,
        show_fullscreen_button=False,
        container=False,
        elem_classes=["banner-container"],
    )

    # gr.Markdown(
    #     value=f"## PP-OCRv5 Online Demo",
    #     elem_id="markdown-title",
    # )
    # gr.Markdown(value=DESCRIPTION)
    # gr.Markdown(
    #     """
    #     Since our inference server is deployed in mainland China, cross-border
    #     network transmission may be slow, which could result in a suboptimal experience on Hugging Face.
    #     We recommend visiting the [PaddlePaddle AI Studio Community](https://aistudio.baidu.com/community/app/91660/webUI?source=appCenter) to try the demo for a smoother experience.
    #     """,
    #     elem_classes=["tight-spacing-as"],
    #     visible=True,
    # )
    
    with gr.Row():
        with gr.Column(scale=3, elem_classes=["sidebar-column"], elem_id="sidebar-column"):

            # Inference device section
            gr.Markdown("#### ⚡ Inference Device")    
            with gr.Column(elem_classes=["white-container"]):
                inference_device = gr.Radio(
                    choices=[("DEEPX NPU", True), ("CPU", False)],
                    value=True,
                    show_label=False,
                    elem_id="inference_device",
            )
        
            # Upload section
            gr.Markdown("#### 📁 Input File")
            with gr.Column(elem_classes=["white-container"]):
                with gr.Column(elem_classes=["upload-area"]):
                    file_input = gr.File(
                        # label="📤 Click or drag file to upload",
                        file_types=[".pdf", ".jpg", ".jpeg", ".png"],
                        type="filepath",
                        visible=True,
                        show_label=False,
                        elem_classes=["drag-drop-file-custom"],
                    )

                    file_select = gr.Textbox(
                        show_label=False, 
                        visible=False,
                        interactive=False,
                        elem_classes=["file-status"],
                    )

                process_btn = gr.Button(
                    "🚀 Parse Document", elem_id="analyze-btn", variant="primary"
                )

                gr.Markdown("##### 📷 Image Examples")

                image_input = gr.Image(
                    label="Image",
                    sources="upload",
                    type="filepath",
                    visible=False,
                    interactive=True,
                    placeholder="Click to upload file",
                )

                examples_image = gr.Examples(
                    fn=on_file_change_from_examples_image,
                    inputs=image_input,
                    outputs=[file_select, file_input, image_input],
                    examples_per_page=8,
                    examples=EXAMPLE_TEST,
                    run_on_click=True,
                )
                
                gr.Markdown("##### 📄 PDF Examples")
                examples_pdf = gr.Examples(
                    fn=on_file_change_from_examples_pdf,
                    inputs=file_input,
                    outputs=[file_select, file_input, image_input],
                    examples_per_page=5,
                    examples=EXAMPLE_PDF,
                    run_on_click=True,
                )

                image_input.change(
                    fn=on_file_change_from_image_input,
                    inputs=[file_select, image_input, file_input],
                    outputs=[file_select, file_input, image_input],
                )

                file_input.change(
                    fn=on_file_change_from_file_input, 
                    inputs=[file_select, file_input, image_input],
                    outputs=[file_select, file_input, image_input]
                )
            
            # Settings section
            gr.Markdown("#### ⚙️ Settings")
            with gr.Tabs() as advance_options_tabs:
                with gr.Tab("Module Selection") as Module_Options:
                    use_doc_orientation_classify_cb = gr.Checkbox(
                        value=False,
                        interactive=True,
                        label="Image Orientation Correction",
                        show_label=True,
                        elem_id="use_doc_orientation_classify_cb",
                    )
                    use_doc_unwarping_cb = gr.Checkbox(
                        value=False,
                        interactive=True,
                        label="Image Distortion Correction",
                        show_label=True,
                        elem_id="use_doc_unwarping_cb",
                    )
                    use_textline_orientation_cb = gr.Checkbox(
                        value=False,
                        interactive=True,
                        label="Text Line Orientation Correction",
                        show_label=True,
                        elem_id="use_textline_orientation_cb",
                    )
                
                with gr.Tab("OCR Settings") as Text_detection_Options:
                    text_det_thresh_nb = gr.Number(
                        value=0.30,
                        step=0.01,
                        minimum=0.00,
                        maximum=1.00,
                        interactive=True,
                        label="Text Detection Pixel Threshold",
                        show_label=True,
                        elem_id="text_det_thresh_nb",
                    )
                    text_det_box_thresh_nb = gr.Number(
                        value=0.60,
                        step=0.01,
                        minimum=0.00,
                        maximum=1.00,
                        interactive=True,
                        label="Text Detection Box Threshold",
                        show_label=True,    
                        elem_id="text_det_box_thresh_nb",
                    )
                    text_det_unclip_ratio_nb = gr.Number(
                        value=1.5,
                        step=0.1,
                        minimum=0,
                        maximum=10.0,
                        interactive=True,
                        label="Expansion Coefficient",
                        show_label=True,
                        elem_id="text_det_unclip_ratio_nb",
                    )
                    text_rec_score_thresh_nb = gr.Number(
                        value=0.00,
                        step=0.01,
                        minimum=0,
                        maximum=1.00,
                        interactive=True,
                        label="Text Recognition Score Threshold",
                        show_label=True,
                        elem_id="text_rec_score_thresh_nb",
                    )

                    gr.Markdown("---")
        
                    device_info_md = gr.HTML(
                        """<div style="
                            padding: 12px 16px;
                            background: #FFF7E6;
                            border-left: 3px solid #FAAD14;
                            border-radius: 6px;
                            margin-bottom: 12px;
                            font-size: 13px;
                            color: #8C6D1F;
                            line-height: 1.5;
                        ">
                            <strong style="color: #D48806;">ℹ️ DEEPX NPU Mode:</strong> 
                            Uses fixed resolution models (640×640 or 960×960) for hardware acceleration. 
                            Image size limit parameters are automatically determined.
                        </div>""",
                        visible=True,
                    )
                    text_det_limit_type_rd = gr.Radio(
                        choices=[("Long side", "max"), ("Short side", "min")],
                        value="min",
                        interactive=False,
                        label="Image Side Length Limit Type",
                        show_label=True,
                        elem_id="text_det_limit_type_rd",
                    )
                    text_det_limit_side_len_nb = gr.Number(
                        value=736,
                        step=1,
                        minimum=0,
                        maximum=10000,
                        interactive=False,
                        label="Image Side Length Limit",
                        show_label=True,
                        elem_id="text_det_limit_side_len_nb",
                    )

        # Results display section
        with gr.Column(scale=7, elem_classes=["white-container"], elem_id="results-column"):
            
            # Performance Metrics section
            # gr.Markdown("#### 📊 Performance Metrics")
            gr.Markdown("### 📋 Results", elem_classes="custom-markdown")
            
            with gr.Column(elem_classes=["white-container"]):
                enable_perf_metrics_cb = gr.Checkbox(
                    label="📊 Enable Performance Metrics",
                    value=True,
                    show_label=False,
                    # info="Show detailed timing information (inflight mode)",
                    elem_id="enable_perf_metrics_cb",
                )

            loading_spinner = gr.Column(
                visible=False, elem_classes=["loader-container"]
            )
            with loading_spinner:
                gr.HTML(
                    """
                    <div class="loader"></div>
                    <p style="color: #565772; font-size: 14px;">Processing, please wait...</p>
                    """
                )
            prepare_spinner = gr.Column(
                visible=True, elem_classes=["loader-container-prepare"]
            )
            with prepare_spinner:
                gr.HTML(
                    """
                    <div style="font-size: 18px; font-weight: 600; color: #140E35; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                        <span style="background: #2932E1; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px;">GUIDE</span>
                        User Guide
                    </div>
                    <div style="display: grid; gap: 12px;">
                        <div style="display: flex; align-items: flex-start; gap: 12px;">
                            <span style="background: #2932E1; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; flex-shrink: 0;">1</span>
                            <div><b style="color: #140E35;">Upload Your File</b><br><span style="font-size: 13px;">Upload directly or select from Image/PDF Examples below<br>Supported formats: JPG, PNG, PDF, JPEG</span></div>
                        </div>
                        <div style="display: flex; align-items: flex-start; gap: 12px;">
                            <span style="background: #2932E1; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; flex-shrink: 0;">2</span>
                            <div><b style="color: #140E35;">Click Parse Document Button</b><br><span style="font-size: 13px;">System will process automatically</span></div>
                        </div>
                        <div style="display: flex; align-items: flex-start; gap: 12px;">
                            <span style="background: #2932E1; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; flex-shrink: 0;">3</span>
                            <div><b style="color: #140E35;">View & Download Results</b><br><span style="font-size: 13px;">Results will be displayed after processing</span></div>
                        </div>
                        <div style="display: flex; align-items: flex-start; gap: 12px;">
                            <span style="background: #2932E1; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; flex-shrink: 0;">4</span>
                            <div><b style="color: #140E35;">Expand Results View</b><br><span style="font-size: 13px;">Click <b>HIDE LEFT MENU</b> button on the left to view results in full screen</span></div>
                        </div>
                    </div>
                    <div style="margin-top: 16px; padding: 12px 16px; background: #FFF7E6; border-radius: 6px; border-left: 3px solid #FAAD14;">
                        <span style="font-weight: 600; color: #D48806;">⚠️ Notice:</span>
                        <span style="color: #8C6D1F;">Only the first 3 pages will be processed. Please ensure uploaded files do not contain personal information.</span>
                    </div>
                    """
                )

            overall_ocr_res_images = []
            output_json_list = []
            gallery_list = []
            with gr.Tabs(visible=False) as tabs:
                with gr.Tab("OCR"):
                    with gr.Row():
                        with gr.Column(scale=2, min_width=1):
                            gallery_ocr_det = gr.Gallery(
                                show_label=False,
                                allow_preview=False,
                                preview=False,
                                columns=1,
                                min_width=10,
                                object_fit="contain",
                            )
                            gallery_list.append(gallery_ocr_det)
                        with gr.Column(scale=10):
                            for i in range(MAX_NUM_PAGES):
                                overall_ocr_res_images.append(
                                    gr.Image(
                                        label=f"OCR Image {i}",
                                        show_label=True,
                                        visible=False,
                                    )
                                )
                with gr.Tab("Performance"):
                    perf_metrics_html = gr.HTML(
                        value="<div style='padding: 20px; text-align: center; color: #888;'>Enable 'Performance Metrics' option and run analysis to see timing information.</div>",
                        visible=True,
                    )
                with gr.Tab("JSON"):
                    with gr.Row():
                        with gr.Column(scale=2, min_width=1):
                            gallery_json = gr.Gallery(
                                show_label=False,
                                allow_preview=False,
                                preview=False,
                                columns=1,
                                min_width=10,
                                object_fit="contain",
                            )
                            gallery_list.append(gallery_json)
                        with gr.Column(scale=10):
                            gr.HTML(
                                """
                            <style>
                            .line.svelte-19ir0ev svg {
                                width: 30px !important;
                                height: 30px !important;
                                min-width: 30px !important;
                                min-height: 30px !important;
                                padding: 0 !important;
                                font-size: 18px !important;
                            }
                            .line.svelte-19ir0ev span:contains('Object(') {
                                font-size: 12px;
                                }
                            </style>
                            """
                            )
                            output_json_list.append(
                                gr.JSON(
                                    visible=False,
                                )
                            )
            download_all_btn = gr.Button(
                "📦 Download Full Results (ZIP)",
                elem_id="unzip-btn",
                variant="primary",
                visible=False,
            )

            download_file = gr.File(visible=False, label="Download File")

            gr.Markdown("")

            gr.Image(
                value=BANNER_CES_PATH,
                show_label=False,
                show_download_button=False,
                show_fullscreen_button=False,
                container=False,
                elem_classes=["banner-container"],
            )

    # Sidebar toggle button
    gr.HTML(
        """
        <button id="sidebar-toggle-btn">
            <span class="toggle-icon">◀</span>
            <span class="toggle-text">HIDE LEFT MENU</span>
        </button>
        """
    )        

    # # Navigation bar - Baidu AI Studio Style
    # with gr.Column(elem_classes=["nav-bar"]):
    #     gr.HTML(
    #         """
    #     <div class="nav-links">
    #         <a href="https://github.com/PaddlePaddle/PaddleOCR" class="nav-link" target="_blank" style="display: flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #24292e 0%, #1a1e22 100%); color: white !important; padding: 8px 20px; border-radius: 6px;">
    #             <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    #                 <path d="M10 0C4.475 0 0 4.542 0 10.15a10.248 10.248 0 001.886 5.937 10.005 10.005 0 004.952 3.695c.5.088.687-.217.687-.484 0-.24-.013-1.039-.013-1.89-2.512.47-3.162-.62-3.362-1.192-.113-.293-.6-1.193-1.025-1.435-.35-.19-.85-.66-.013-.672.788-.013 1.35.736 1.538 1.04.9 1.536 2.338 1.104 2.912.838.088-.66.35-1.103.638-1.357-2.225-.254-4.55-1.13-4.55-5.012 0-1.105.387-2.017 1.025-2.729-.1-.254-.45-1.294.1-2.69 0 0 .837-.266 2.75 1.042a9.151 9.151 0 012.5-.343c.85 0 1.7.113 2.5.342 1.912-1.32 2.75-1.04 2.75-1.04.55 1.396.2 2.436.1 2.69.637.71 1.025 1.611 1.025 2.728 0 3.896-2.337 4.758-4.562 5.012.362.317.675.926.675 1.878 0 1.357-.013 2.448-.013 2.791 0 .266.188.583.688.482a10.029 10.029 0 004.932-3.703A10.272 10.272 0 0020 10.15C20 4.542 15.525 0 10 0z"></path>
    #             </svg>
    #             <span style="font-weight: 600;">GitHub</span>
    #             <span style="background: #2932E1; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 4px;">⭐ 67.5k+</span>
    #         </a>
    #         <a href="https://aistudio.baidu.com/community/app/91660/webUI" class="nav-link" target="_blank" style="display: flex; align-items: center; gap: 8px;">
    #             <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    #                 <path d="M8 0L0 4v8l8 4 8-4V4L8 0zm5.6 10.4L8 13.2 2.4 10.4V5.6L8 2.8l5.6 2.8v4.8z"/>
    #             </svg>
    #             <span>PaddleOCR Demo (Baidu)</span>
    #         </a>
    #         <a href="https://paddlepaddle.github.io/PaddleOCR/" class="nav-link" target="_blank" style="display: flex; align-items: center; gap: 8px;">
    #             <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    #                 <path d="M1 2.5A1.5 1.5 0 012.5 1h11A1.5 1.5 0 0115 2.5v11a1.5 1.5 0 01-1.5 1.5h-11A1.5 1.5 0 011 13.5v-11zM3 4h10v1H3V4zm0 3h10v1H3V7zm0 3h7v1H3v-1z"/>
    #             </svg>
    #             <span>Documentation</span>
    #         </a>
    #     </div>
    #     """
    #     )

    
    gr.Markdown("")
    gr.Image(
        value=BANNER_PATH,
        show_label=False,
        show_download_button=False,
        show_fullscreen_button=False,
        container=False,
        elem_classes=["banner-container"],
    )

    inference_device.change(
        fn=toggle_device_options,
        inputs=inference_device,
        outputs=[
            text_det_limit_type_rd,
            text_det_limit_side_len_nb,
            device_info_md,
        ],
    )
    
    process_btn.click(
        validate_file_input,
        inputs=[file_input, image_input],
        outputs=[],
    ).then(
        toggle_spinner,
        inputs=[file_input, image_input],
        outputs=[
            loading_spinner,
            prepare_spinner,
            download_file,
            tabs,
            download_all_btn,
        ],
    ).then(
        process_file,
        inputs=[
            file_input,
            image_input,
            inference_device,
            use_doc_orientation_classify_cb,
            use_doc_unwarping_cb,
            use_textline_orientation_cb,
            text_det_limit_type_rd,
            text_det_limit_side_len_nb,
            text_det_thresh_nb,
            text_det_box_thresh_nb,
            text_det_unclip_ratio_nb,
            text_rec_score_thresh_nb,
            enable_perf_metrics_cb,
        ],
        outputs=[results_state],
    ).then(
        hide_spinner, inputs=[results_state], outputs=[loading_spinner, tabs]
    ).then(
        update_display,
        inputs=[results_state],
        outputs=overall_ocr_res_images + output_json_list + gallery_list + [perf_metrics_html],
    ).then(
        lambda results: gr.update(visible=True) if results else gr.skip(),
        inputs=[results_state],
        outputs=download_all_btn,
    )

    gallery_ocr_det.select(update_image, outputs=overall_ocr_res_images)

    download_all_btn.click(
        export_full_results, inputs=[results_state], outputs=[download_file]
    ).success(lambda: gr.update(visible=True), outputs=[download_file])

    demo.load(
        fn=lambda: None,
        inputs=[],
        outputs=[],
        js=f"""
        () => {{
            // Sidebar toggle functionality
            let sidebarVisible = true;
            const toggleBtn = document.getElementById('sidebar-toggle-btn');
            const sidebar = document.getElementById('sidebar-column');
            const resultsColumn = document.getElementById('results-column');
            
            if (toggleBtn && sidebar) {{
                toggleBtn.addEventListener('click', () => {{
                    sidebarVisible = !sidebarVisible;
                    const icon = toggleBtn.querySelector('.toggle-icon');
                    const text = toggleBtn.querySelector('.toggle-text');
                    
                    if (sidebarVisible) {{
                        // Show: restore display first, then animate
                        sidebar.style.display = '';
                        sidebar.classList.remove('sidebar-hidden');
                        setTimeout(() => {{
                            sidebar.style.transform = 'translateX(0)';
                            sidebar.style.opacity = '1';
                        }}, 10);
                        if (resultsColumn) {{
                            resultsColumn.style.flexGrow = '8';
                        }}
                        if (icon) icon.textContent = '◀';
                        if (text) text.textContent = 'HIDE LEFT MENU';
                    }} else {{
                        // Hide: animate to 90%, then apply display:none
                        sidebar.classList.add('sidebar-hidden');
                        sidebar.style.transform = 'translateX(-90%)';
                        sidebar.style.opacity = '0.3';
                        setTimeout(() => {{
                            if (!sidebarVisible) {{
                                sidebar.style.display = 'none';
                            }}
                        }}, 300);
                        if (resultsColumn) {{
                            resultsColumn.style.flexGrow = '12';
                        }}
                        if (icon) icon.textContent = '▶';
                        if (text) text.textContent = 'SHOW LEFT MENU';
                    }}
                }});
            }}
            
            const tooltipTexts = {TOOLTIP_RADIO};
            let tooltip = document.getElementById("custom-tooltip");
            if (!tooltip) {{
                tooltip = document.createElement("div");
                tooltip.id = "custom-tooltip";
                tooltip.style.position = "fixed";
                tooltip.style.background = "rgba(0, 0, 0, 0.75)";
                tooltip.style.color = "white";
                tooltip.style.padding = "6px 10px";
                tooltip.style.borderRadius = "4px";
                tooltip.style.fontSize = "13px";
                tooltip.style.maxWidth = "300px";
                tooltip.style.zIndex = "10000";
                tooltip.style.pointerEvents = "none";
                tooltip.style.transition = "opacity 0.2s";
                tooltip.style.opacity = "0";
                tooltip.style.whiteSpace = "normal";
                document.body.appendChild(tooltip);
            }}
            Object.keys(tooltipTexts).forEach(id => {{
                const elem = document.getElementById(id);
                if (!elem) return;
                function showTooltip(e) {{
                    tooltip.style.opacity = "1";
                    tooltip.innerText = tooltipTexts[id];
                    let x = e.clientX + 10;
                    let y = e.clientY + 10;
                    if (x + tooltip.offsetWidth > window.innerWidth) {{
                        x = e.clientX - tooltip.offsetWidth - 10;
                    }}
                    if (y + tooltip.offsetHeight > window.innerHeight) {{
                        y = e.clientY - tooltip.offsetHeight - 10;
                    }}
                    tooltip.style.left = x + "px";
                    tooltip.style.top = y + "px";
                }}
                function hideTooltip() {{
                    tooltip.style.opacity = "0";
                }}
                elem.addEventListener("mousemove", showTooltip);
                elem.addEventListener("mouseleave", hideTooltip);
            }});
        }}
        """,
    )

if __name__ == "__main__":
    t = threading.Thread(target=delete_file_periodically, daemon=True)
    t.start()

    allowed_dirs = [
        str(BASE_DIR / "res"), 
        str(BASE_DIR / "icon"), 
        str(BASE_DIR / "examples")
    ]

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        inbrowser=False,
        allowed_paths=allowed_dirs,
    )
