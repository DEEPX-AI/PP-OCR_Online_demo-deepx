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

본 프로젝트는  [https://huggingface.co/docs/hub/spaces-config-reference](https://huggingface.co/docs/hub/spaces-config-reference)를 베이스로 DEEPX DX-M1 NPU SDK를 통합하여 재구성하였습니다.

---

# PP-OCRv5 Online Demo - DEEPX Edition

PaddleOCR의 PP-OCRv5 모델을 활용한 웹 기반 OCR 데모 애플리케이션입니다. DEEPX NPU 하드웨어 가속을 지원합니다.

## 📋 목차

- [소개](#-소개)
- [사전 요구사항](#-사전-요구사항)
- [설치 및 설정](#-설치-및-설정)
- [실행 방법](#-실행-방법)
- [주요 기능](#-주요-기능)
- [환경 변수 설정](#-환경-변수-설정)
- [문제 해결](#-문제-해결)

## 🌟 소개

이 프로젝트는 PaddleOCR의 PP-OCRv5 모델을 위한 Gradio 기반 웹 데모입니다. 사용자 친화적인 UI를 통해 이미지 및 PDF 파일의 텍스트 인식 기능을 제공합니다.

이 데모는 OCR을 직접 수행하지 않습니다. PaddleOCR-deepx FastAPI 서버의 얇은
클라이언트이며, DX-M1 NPU 가속은 전적으로 그 서버가 담당합니다. 따라서 어떤
OCR pipeline이 동작할지는 서버를 기동할 때 결정됩니다. PP-OCRv6로 기동한
서버를 가리키면 데모는 코드 변경 없이 PP-OCRv6 결과를 그대로 렌더링합니다.
[어떤 브랜치를 checkout할 것인가](#어떤-브랜치를-checkout할-것인가)를 참고하세요.

### 주요 특징

- **다양한 텍스트 유형 지원**: 간체/번체 중국어, 병음 주석, 영어, 일본어
- **복잡한 텍스트 인식**: 필기체, 세로쓰기, 희귀 문자 인식
- **DEEPX NPU 지원**: 하드웨어 가속을 통한 고속 처리
- **성능 메트릭**: 실시간 OCR 파이프라인 타이밍 분석 (NPU: 단계별, CPU: 전체 시간)
- **PP-OCRv5 / PP-OCRv6 모두 지원**: 동일한 backend 브랜치가 둘 다 서비스
- **반응형 UI**: 사이드바 토글, 전체 화면 결과 보기

## 🔧 사전 요구사항

### 1. OCR 서버 실행

이 웹 데모는 백엔드 OCR 서버와 통신하여 동작합니다. 먼저 OCR 서버를 실행해야 합니다.

#### OCR 서버 설정 및 실행

OCR 서버는 [PaddleOCR-deepx](https://github.com/DEEPX-AI/PaddleOCR-deepx) 레포지토리의 FastAPI 서버를 사용합니다.

```bash
# 1. PaddleOCR-deepx 클론 후 브랜치를 명시적으로 checkout
git clone https://github.com/DEEPX-AI/PaddleOCR-deepx.git
cd PaddleOCR-deepx
git checkout deepx-v6          # PP-OCRv5와 PP-OCRv6를 모두 서비스
cd deploy/fastapi

# 2. 환경 설정 (CPU 버전)
./local_setup.sh

# 또는 GPU 버전
./local_setup.sh --gpu

# 또는 DEEPX NPU 버전 (하드웨어 가속)
./local_deepx_setup.sh --dx_rt /path/to/dx_rt

# 3. 서버 실행 (기본 포트: 8080) - 모델을 반드시 지정
./run.sh --ocr-version v6 --model-size medium
```

#### 어떤 브랜치를 checkout할 것인가

레포지토리의 default 브랜치가 `deepx`이므로, `git checkout` 없이 클론하면
그 브랜치에 머무릅니다. default에 의존하지 말고 브랜치를 이름으로 지정하세요.

| 브랜치 | 서비스 범위 | 선택 기준 |
|---|---|---|
| **`deepx-v6`** (권장) | PP-OCRv5 **및** PP-OCRv6 | 과거 결과를 재현할 목적이 아니라면 항상 |
| `deepx-v5` | PP-OCRv5 전용 | v5 시점 서버에 고정할 때. `deepx`와 동일 커밋 |

이 데모는 `deepx-v6`에서 어느 pipeline을 선택하든 동작합니다. 두 브랜치 사이에
request/response 계약이 바뀌지 않았고, `deepx-v6`는 필드를 추가만 했기
때문입니다. 모든 모델 조합에서 검증했습니다.

| 서버 기동 옵션 | NPU (이미지) | CPU (이미지) | NPU (PDF) |
|---|---|---|---|
| `--ocr-version v5 --model-size server` | 1.94s | 11.95s | 0.98s |
| `--ocr-version v5 --model-size mobile` | 0.94s | 3.75s | 0.59s |
| `--ocr-version v6 --model-size medium` | 1.51s | 9.84s | 0.86s |
| `--ocr-version v6 --model-size small` | 0.96s | 4.00s | 0.62s |
| `--ocr-version v6 --model-size tiny` | 0.81s | 1.78s | 0.54s |

(1 page, `visualize=true`, `inflight=true`, DX-M1 NPU. base64 전송과 시각화
시간이 포함된 end-to-end 데모 지연이며, 순수 inference 시간이 아닙니다.)

#### 모델 선택

`--ocr-version`과 `--model-size`는 둘 다 필수이며, 파일명이 아니라 배포 대상을
가리킵니다.

```bash
./run.sh --ocr-version v6 --model-size medium   # v6: medium | small | tiny
./run.sh --ocr-version v5 --model-size server   # v5: server | mobile
```

둘 다 생략하면 `run.sh`가 대화형으로 물어봅니다. 비대화형 shell(Docker, CI)
에서는 조용히 기본값으로 뜨지 않고 에러를 냅니다. 아무도 선택하지 않은 모델이
서비스되는 일을 막기 위해서입니다. 이 옵션들이 과거 setup script에 주던
`--use-server` / `--use-mobile`을 대체합니다.

두 버전의 이름은 서로 다른 것을 가리킵니다. v5의 `server` / `mobile`은 배포
대상이고, v6의 `medium` / `small` / `tiny`는 모델 규모입니다. 한 글자 축약형이
겹치는데 - v6의 `s`는 *small*이지 *server*가 아니고, `m`은 *medium*이지
*mobile*이 아닙니다 - 이 옵션이 전체 단어를 받는 이유가 그것입니다.

**참고**: 자세한 OCR 서버 설정 방법은 [PaddleOCR FastAPI README](https://github.com/DEEPX-AI/PaddleOCR-deepx/blob/deepx-v6/deploy/fastapi/README.md)를 참조하세요.

**참고**: `local_deepx_setup.sh`는 DX-M1 NPU 모델 세트를 한 번에 모두
받습니다(v5 server, v5 mobile, v6). CPU용 PP-OCRv6 가중치는 미리 받지 않으며,
해당 모델이 처음 필요해지는 요청에서 PaddleOCR이 자동으로 다운로드합니다.

#### 서버 실행 확인

```bash
# Health check
curl http://localhost:8080/health

# 응답: {"status": "healthy"}
```

### 2. 시스템 요구사항

- **Python**: 3.10 이상
- **메모리**: 최소 2GB RAM
- **디스크 공간**: 약 500MB (예제 파일 포함)
- **Git LFS**: 대용량 파일 관리용 (선택사항)

### 3. Git LFS 설정 (선택사항)

이 레포지토리는 대용량 이미지 파일 관리를 위해 Git LFS를 사용합니다.

```bash
# Git LFS 설치 (Ubuntu/Debian)
sudo apt-get install git-lfs

# Git LFS 초기화
git lfs install

# 레포지토리 클론 시 자동으로 LFS 파일 다운로드
git clone https://github.com/DongHyun-Yang/PP-OCRv5_Online_demo.git
cd PP-OCRv5_Online_demo

# 또는 이미 클론한 경우, LFS 파일 다운로드
git lfs pull
```

**Git LFS가 없는 경우**: 포인터 파일이 다운로드되지만, 애플리케이션은 여전히 동작합니다. 단, 일부 예제 이미지가 표시되지 않을 수 있습니다.

## 📦 설치 및 설정

### 1. 레포지토리 클론

```bash
git clone https://github.com/DEEPX-AI/PP-OCRv5_Online_demo-deepx.git
cd PP-OCRv5_Online_demo

# Install Git LFS
sudo apt-get install git-lfs
git lfs install

# Download LFS files
git lfs pull
```

### 2. Python 가상 환경 생성

```bash
# venv 생성
python3 -m venv venv

# 가상 환경 활성화 (Linux/macOS)
source venv/bin/activate

# 가상 환경 활성화 (Windows)
venv\Scripts\activate
```

### 3. 의존성 설치

```bash
# requirements.txt에서 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt
```

**주요 의존성**:
- `gradio==5.30.0`: 웹 UI 프레임워크
- `pillow==9.5.0`: 이미지 처리
- `requests==2.31.0`: HTTP 통신

## 🚀 실행 방법

### 1. 기본 실행 (로컬호스트 OCR 서버)

OCR 서버가 `localhost:8080`에서 실행 중인 경우:

```bash
# 가상 환경 활성화
source venv/bin/activate

# 애플리케이션 실행
python app.py
```

### 2. 커스텀 OCR 서버 URL 지정

OCR 서버가 다른 호스트나 포트에서 실행 중인 경우:

```bash
# 환경 변수로 API URL 지정
export API_URL="http://192.168.1.100:9000/api/v1/ocr"
python app.py
```

### 3. VS Code 디버그 모드

VS Code에서 F5 키를 눌러 디버그 모드로 실행할 수 있습니다.

### 4. 웹 브라우저 접속

서버 시작 후 자동으로 브라우저가 열리며, 다음 URL로 접속할 수 있습니다:

```
http://localhost:7860
```

## 🎯 주요 기능

### 1. 파일 업로드

- **지원 형식**: PDF, JPG, JPEG, PNG
- **드래그 앤 드롭**: 파일을 업로드 영역에 드래그하여 업로드
- **클릭 업로드**: 업로드 영역 클릭 후 파일 선택

### 2. 예제 선택

- **이미지 예제**: 8개의 사전 정의된 이미지 예제
- **PDF 예제**: 10개의 PDF 문서 예제
- **원클릭 선택**: 예제 클릭으로 즉시 로드

### 3. OCR 설정

#### 인퍼런스 디바이스
- **DEEPX NPU**: 하드웨어 가속 (고속 처리)
- **CPU**: CPU 기반 처리

이 선택은 요청마다 전달되므로 장치를 바꿀 때 서버를 재시작할 필요가 없습니다.
backend가 실제로 사용할 장치를 지정하며, NPU가 장착된 서버라도 CPU 요청은 CPU로
처리합니다. 성능 탭의 두 값을 비교할 수 있는 이유가 이것입니다.

#### 모듈 선택
- **문서 방향 보정**: 회전된 이미지 자동 보정
- **문서 왜곡 보정**: 구겨진 문서 펼치기
- **텍스트 라인 방향 보정**: 180도 회전 텍스트 보정

#### OCR 파라미터
- **텍스트 검출 임계값**: 픽셀 점수 임계값 (0~1)
- **박스 임계값**: 텍스트 영역 판단 임계값 (0~1)
- **언클립 비율**: 텍스트 영역 확장 비율
- **인식 점수 임계값**: 텍스트 인식 결과 필터링 (0~1)

### 4. 결과 보기

- **시각화 결과**: 텍스트 박스가 표시된 이미지
- **JSON 출력**: 구조화된 OCR 결과 (좌표, 텍스트, 신뢰도)
- **성능 메트릭**: OCR 처리에 대한 상세 시간 분석
- **전체 결과 다운로드**: ZIP 파일로 모든 결과 다운로드

### 5. 성능 메트릭 (Performance Metrics)

실시간 성능 분석 정보를 제공합니다:

- **요약 카드**: 총 처리 시간, OCR 추론 시간, 처리된 페이지 수, 백엔드 정보
- **시간 분석**: PDF 변환, OCR 추론, 결과 포맷팅 시간 비율을 시각적 프로그레스 바로 표시
- **OCR 파이프라인 단계** (NPU 전용): 각 OCR 단계별 상세 타이밍
  - 문서 방향 분류 (Document Orientation Classification)
  - 문서 왜곡 보정 (Document Unwarping)
  - 텍스트 검출 (Text Detection)
  - 텍스트 라인 방향 분류 (Textline Orientation Classification)
  - 텍스트 인식 (Text Recognition)
- **페이지별 통계**: 페이지당 평균 처리 시간

> **참고**: 단계별 타이밍은 NPU 백엔드 사용 시에만 제공됩니다. CPU 백엔드는 전체 OCR 시간만 표시됩니다.

### 6. UI 최적화

- **사이드바 토글**: 왼쪽 메뉴 숨김/표시 버튼으로 전체 화면 결과 보기
- **반응형 레이아웃**: 화면 크기에 맞춰 자동 조정

## 🔑 환경 변수 설정

### API_URL

OCR 서버의 엔드포인트 URL을 지정합니다.

```python
# app.py 파일 내 기본값
API_URL = os.environ.get("API_URL", "http://localhost:8080/api/v1/ocr")
```

#### 설정 방법

**방법 1: 쉘 환경 변수**

```bash
export API_URL="http://your-ocr-server:8080/api/v1/ocr"
python app.py
```

**방법 2: .env 파일 (권장)**

프로젝트 루트에 `.env` 파일 생성:

```bash
# .env
API_URL=http://192.168.1.100:8080/api/v1/ocr
API_TOKEN=your_optional_token_here
```

**방법 3: app.py 직접 수정 (권장하지 않음)**

```python
# app.py의 20번째 줄 수정
API_URL = "http://your-ocr-server:8080/api/v1/ocr"
```

## 🐛 문제 해결

### 1. OCR 서버 연결 실패

**증상**: `API request failed` 에러 메시지

**해결 방법**:
```bash
# OCR 서버 상태 확인
curl http://localhost:8080/health

# 서버가 실행 중이 아닌 경우
cd PaddleOCR-deepx/deploy/fastapi
./run.sh --ocr-version v6 --model-size medium

# 다른 포트를 사용하는 경우
export API_URL="http://localhost:9000/api/v1/ocr"
```

### 2. 가상 환경 활성화 문제

**증상**: `python` 명령이 시스템 Python을 가리킴

**해결 방법**:
```bash
# 가상 환경이 활성화되었는지 확인
which python  # 출력: /path/to/venv/bin/python

# 활성화되지 않은 경우
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Git LFS 파일 다운로드 실패

**증상**: 예제 이미지가 표시되지 않음

**해결 방법**:
```bash
# Git LFS 설치
sudo apt-get install git-lfs
git lfs install

# LFS 파일 다운로드
git lfs pull
```

### 4. 포트 충돌

**증상**: `Address already in use` 에러

**해결 방법**:
```bash
# 7860 포트를 사용 중인 프로세스 확인
lsof -i :7860

# app.py의 포트 변경
# 파일 끝부분 수정:
demo.launch(
    server_name="0.0.0.0",
    server_port=7861,  # 다른 포트로 변경
    ...
)
```

### 5. 메모리 부족

**증상**: 서버가 느리거나 응답 없음

**해결 방법**:

더 작은 모델로 서버를 재시작하세요. 모델 크기는 기동 시 `--model-size`로
결정되므로 setup script를 다시 실행할 필요가 없습니다. 과거 setup script의
`--use-server` / `--use-mobile` 플래그는 더 이상 이것을 결정하지 않습니다.

```bash
cd PaddleOCR-deepx/deploy/fastapi

# PP-OCRv6, 가장 작고 빠름
./run.sh --ocr-version v6 --model-size tiny

# PP-OCRv6, 중간 단계
./run.sh --ocr-version v6 --model-size small

# PP-OCRv5, 두 대상 중 가벼운 쪽
./run.sh --ocr-version v5 --model-size mobile
```

NPU에서는 더 작은 모델이 inference engine을 더 적게 로드하므로, 기동 시
메모리 부족 실패는 대개 이것으로 해소됩니다.

### 6. OCR 서버가 모델 다운로드에 실패

**증상**: OCR 서버가 기동 중 다음 메시지로 중단됩니다.
`FATAL ERROR: Failed to load CPU models: No available model hosting platforms
detected. Please check your network connection.`

**원인**: PaddleOCR은 CPU 가중치를 최초 사용 시 HuggingFace / AI Studio / BOS
에서 받아옵니다. TLS를 재서명하는 사내 proxy 환경에서는 이 호스트들이 모두
인증서 검증에 실패하는데, PaddleOCR은 이를 TLS 오류가 아니라 "사용 가능한
플랫폼 없음"으로 보고합니다.

**해결 방법**: Python의 HTTP stack이 시스템 신뢰 저장소를 보도록 지정한 뒤
서버를 다시 기동합니다.

```bash
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
cd PaddleOCR-deepx/deploy/fastapi
./run.sh --ocr-version v6 --model-size medium
```

모델은 `~/.paddlex/official_models` 아래에 캐시되므로, 각 모델을 한 번 받고
나면 더 이상 필요하지 않습니다. DX-M1 NPU 모델은 이 문제와 무관합니다.
`local_deepx_setup.sh`가 별도로 받습니다.

## 📚 추가 리소스

- **PaddleOCR 공식 문서**: https://github.com/PaddlePaddle/PaddleOCR
- **PaddleOCR-deepx (DEEPX NPU 버전)**: https://github.com/DEEPX-AI/PaddleOCR-deepx
- **OCR 서버 설정 가이드**: https://github.com/DEEPX-AI/PaddleOCR-deepx/blob/deepx-v6/deploy/fastapi/README.md
- **DEEPX NPU 가이드**: https://github.com/DEEPX-AI/PaddleOCR-deepx/blob/deepx-v6/deploy/fastapi/docs/DEEPX_NPU_GUIDE.md
- **Gradio 공식 문서**: https://gradio.app/docs

## 📄 라이선스

Apache License 2.0

## 🙏 감사의 말

- PaddlePaddle Team: PP-OCRv5 모델 개발
- DEEPX: NPU 하드웨어 가속 지원
- Gradio Team: 웹 UI 프레임워크
