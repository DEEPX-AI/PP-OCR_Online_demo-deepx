---
title: PP-OCRv5 Online Demo
emoji: 🌍
colorFrom: purple
colorTo: green
sdk: gradio
sdk_version: 5.30.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Universal-Scene Text Recognition Model with High-Accuracy
tags:
  - ocr
  - paddleocr
  - computer-vision
  - image-to-text
  - gradio
  - DEEPX
  - NPU
---

This project is reconstructed based on [https://huggingface.co/docs/hub/spaces-config-reference](https://huggingface.co/docs/hub/spaces-config-reference) by integrating the DEEPX DX-M1 NPU SDK.

---

# PP-OCRv5 Online Demo - DEEPX Edition

A web-based OCR demo application utilizing PaddleOCR's PP-OCRv5 model. Supports DEEPX NPU hardware acceleration.

## 📋 Table of Contents

- [Introduction](#-introduction)
- [Prerequisites](#-prerequisites)
- [Installation and Setup](#-installation-and-setup)
- [How to Run](#-how-to-run)
- [Key Features](#-key-features)
- [Environment Variable Configuration](#-environment-variable-configuration)
- [Troubleshooting](#-troubleshooting)

## 🌟 Introduction

This project is a Gradio-based web demo using PaddleOCR's latest PP-OCRv5 model. It provides text recognition functionality for images and PDF files through a user-friendly UI.

### Key Features

- **Support for Various Text Types**: Simplified/Traditional Chinese, Pinyin annotation, English, Japanese
- **Complex Text Recognition**: Handwriting, vertical text, rare character recognition
- **DEEPX NPU Support**: High-speed processing through hardware acceleration
- **Responsive UI**: Sidebar toggle, full-screen results view

## 🔧 Prerequisites

### 1. Running OCR Server

This web demo operates by communicating with a backend OCR server. You must first run the OCR server.

#### OCR Server Setup and Execution

The OCR server uses the FastAPI server from the [PaddleOCR-deepx](https://github.com/DEEPX-AI/PaddleOCR-deepx) repository.

```bash
# 1. Clone PaddleOCR-deepx repository
git clone https://github.com/DEEPX-AI/PaddleOCR-deepx.git
cd PaddleOCR-deepx/deploy/fastapi

# 2. Environment setup (CPU version)
./local_setup.sh

# Or GPU version
./local_setup.sh --gpu

# Or DEEPX NPU version (Hardware acceleration)
./local_deepx_setup.sh --dx_rt /path/to/dx_rt

# 3. Start server (default port: 8080)
./run.sh
```

**Note**: For detailed OCR server setup instructions, refer to [PaddleOCR FastAPI README](https://github.com/DEEPX-AI/PaddleOCR-deepx/blob/deepx/deploy/fastapi/README.md).

**Note**: To use larger (higher accuracy) models, specify the `--use-server` option with `./local_setup.sh --use-server` or `./local_deepx_setup.sh --use-server` to use server-oriented (higher accuracy) models. (Caution: In low-spec edge environments, this may result in slower speeds or insufficient memory.)

#### Verify Server is Running

```bash
# Health check
curl http://localhost:8080/health

# Response: {"status": "healthy"}
```

### 2. System Requirements

- **Python**: 3.10 or higher
- **Memory**: Minimum 2GB RAM
- **Disk Space**: Approximately 500MB (including example files)
- **Git LFS**: For large file management (optional)

### 3. Git LFS Setup (Optional)

This repository uses Git LFS for managing large image files.

```bash
# Install Git LFS (Ubuntu/Debian)
sudo apt-get install git-lfs

# Initialize Git LFS
git lfs install

# Automatically download LFS files when cloning repository
git clone https://github.com/DongHyun-Yang/PP-OCRv5_Online_demo.git
cd PP-OCRv5_Online_demo

# Or if already cloned, download LFS files
git lfs pull
```

**Without Git LFS**: Pointer files will be downloaded, but the application will still work. However, some example images may not display.

## 📦 Installation and Setup

### 1. Clone Repository

```bash
git clone https://github.com/DEEPX-AI/PP-OCRv5_Online_demo-deepx.git
cd PP-OCRv5_Online_demo

# Install Git LFS
sudo apt-get install git-lfs
git lfs install

# Download LFS files
git lfs pull
```

### 2. Create Python Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Activate virtual environment (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install packages from requirements.txt
pip install --upgrade pip
pip install -r requirements.txt
```

**Main Dependencies**:
- `gradio==5.30.0`: Web UI framework
- `pillow==9.5.0`: Image processing
- `requests==2.31.0`: HTTP communication

## 🚀 How to Run

### 1. Basic Execution (Localhost OCR Server)

When OCR server is running at `localhost:8080`:

```bash
# Activate virtual environment
source venv/bin/activate

# Run application
python app.py
```

### 2. Specify Custom OCR Server URL

When OCR server is running on a different host or port:

```bash
# Specify API URL via environment variable
export API_URL="http://192.168.1.100:9000/api/v1/ocr"
python app.py
```

### 3. VS Code Debug Mode

You can run in debug mode by pressing F5 in VS Code.

### 4. Access Web Browser

After server starts, a browser will automatically open, and you can access the following URL:

```
http://localhost:7860
```

## 🎯 Key Features

### 1. File Upload

- **Supported Formats**: PDF, JPG, JPEG, PNG
- **Drag and Drop**: Upload by dragging files to the upload area
- **Click Upload**: Click upload area and select file

### 2. Example Selection

- **Image Examples**: 8 predefined image examples
- **PDF Examples**: 10 PDF document examples
- **One-Click Selection**: Load instantly by clicking examples

### 3. OCR Settings

#### Inference Device
- **DEEPX NPU**: Hardware acceleration (high-speed processing)
- **CPU**: CPU-based processing

#### Module Selection
- **Document Orientation Correction**: Automatically correct rotated images
- **Document Distortion Correction**: Flatten crumpled documents
- **Text Line Orientation Correction**: Correct 180-degree rotated text

#### OCR Parameters
- **Text Detection Threshold**: Pixel score threshold (0~1)
- **Box Threshold**: Text area judgment threshold (0~1)
- **Unclip Ratio**: Text area expansion ratio
- **Recognition Score Threshold**: Text recognition result filtering (0~1)

### 4. View Results

- **Visualization Results**: Images with text boxes displayed
- **JSON Output**: Structured OCR results (coordinates, text, confidence)
- **Download Full Results**: Download all results as ZIP file

### 5. UI Optimization

- **Sidebar Toggle**: Full-screen results view with hide/show left menu button
- **Responsive Layout**: Automatically adjusts to screen size

## 🔑 Environment Variable Configuration

### API_URL

Specifies the endpoint URL of the OCR server.

```python
# Default value in app.py file
API_URL = os.environ.get("API_URL", "http://localhost:8080/api/v1/ocr")
```

#### Configuration Methods

**Method 1: Shell Environment Variable**

```bash
export API_URL="http://your-ocr-server:8080/api/v1/ocr"
python app.py
```

**Method 2: .env File (Recommended)**

Create `.env` file in project root:

```bash
# .env
API_URL=http://192.168.1.100:8080/api/v1/ocr
API_TOKEN=your_optional_token_here
```

**Method 3: Direct Modification of app.py (Not Recommended)**

```python
# Modify line 20 of app.py
API_URL = "http://your-ocr-server:8080/api/v1/ocr"
```

## 🐛 Troubleshooting

### 1. OCR Server Connection Failure

**Symptom**: `API request failed` error message

**Solution**:
```bash
# Check OCR server status
curl http://localhost:8080/health

# If server is not running
cd PaddleOCR-deepx/deploy/fastapi
./run.sh

# If using a different port
export API_URL="http://localhost:9000/api/v1/ocr"
```

### 2. Virtual Environment Activation Issue

**Symptom**: `python` command points to system Python

**Solution**:
```bash
# Check if virtual environment is activated
which python  # Output: /path/to/venv/bin/python

# If not activated
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Git LFS File Download Failure

**Symptom**: Example images not displayed

**Solution**:
```bash
# Install Git LFS
sudo apt-get install git-lfs
git lfs install

# Download LFS files
git lfs pull
```

### 4. Port Conflict

**Symptom**: `Address already in use` error

**Solution**:
```bash
# Check process using port 7860
lsof -i :7860

# Change port in app.py
# Modify at end of file:
demo.launch(
    server_name="0.0.0.0",
    server_port=7861,  # Change to different port
    ...
)
```

### 5. Memory Shortage

**Symptom**: Server is slow or unresponsive

**Solution**:

When using `./local_setup.sh` with the --use-server option, server-oriented models are used.
If speed is slow or memory shortage occurs in edge environments, specify the --use-mobile option or remove the --use-server option and run with default options to use mobile-oriented models.

```bash
# Change OCR server to Mobile model (uses less memory)
cd PaddleOCR-deepx/deploy/fastapi
./local_setup.sh --use-mobile # default: --use-mobile on
./run.sh

# Or, when using DEEPX NPU

# Change OCR server to Mobile model (uses less memory)
cd PaddleOCR-deepx/deploy/fastapi
./local_deepx_setup.sh --use-mobile # default: --use-mobile on
./run.sh

```

## 📚 Additional Resources

- **PaddleOCR Official Documentation**: https://github.com/PaddlePaddle/PaddleOCR
- **PaddleOCR-deepx (DEEPX NPU Version)**: https://github.com/DEEPX-AI/PaddleOCR-deepx
- **OCR Server Setup Guide**: https://github.com/DEEPX-AI/PaddleOCR-deepx/blob/deepx/deploy/fastapi/README.md
- **DEEPX NPU Guide**: https://github.com/DEEPX-AI/PaddleOCR-deepx/blob/deepx/deploy/fastapi/docs/DEEPX_NPU_GUIDE.md
- **Gradio Official Documentation**: https://gradio.app/docs

## 📄 License

Apache License 2.0

## 🙏 Acknowledgments

- PaddlePaddle Team: PP-OCRv5 model development
- DEEPX: NPU hardware acceleration support
- Gradio Team: Web UI framework
