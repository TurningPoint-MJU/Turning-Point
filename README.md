# K리그 경기 변곡점 분석 MVP

> **"K리그 경기 데이터를 기반으로, 팬들이 '왜 이겼고 왜 졌는지'를 이해할 수 있도록 경기 흐름의 변곡점을 AI가 자동으로 탐지·설명하는 팬 친화형 분석 MVP"**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 프로젝트 소개

이 프로젝트는 K리그 경기 데이터를 분석하여 **경기 흐름의 변곡점을 자동으로 탐지**하고, **팬 친화적인 언어로 설명**하는 AI 분석 도구입니다.

### 왜 필요한가?

현재 K리그 팬들은 경기 결과를 이해하는 데 어려움을 겪고 있습니다:
- **"점유율은 높은데 왜 졌지?"** - 단순 통계만으로는 경기 흐름을 파악하기 어려움
- **"후반에 갑자기 밀린 이유가 뭐지?"** - 골이 없어도 경기가 기울어지는 순간을 설명할 수 없음
- **"골 말고 뭐가 결정적이었지?"** - 골 중심의 하이라이트만으로는 경기 전체 흐름을 이해할 수 없음

### 해결 방법

이 프로젝트는 다음과 같은 방식으로 문제를 해결합니다:

1. **경기 흐름 수치화**: 5분 단위로 경기 주도권을 점수화하여 시각화
2. **변곡점 자동 탐지**: 슈팅, 패스, 수비 라인 등 다양한 지표를 종합하여 경기 흐름이 바뀌는 순간을 탐지
3. **선수 분석**: 변곡점에 가장 큰 영향을 준 선수들을 식별하고 시각화
4. **팬 친화형 설명**: 전술 용어를 최소화하고 일반 팬이 이해하기 쉬운 언어로 설명

## ✨ 주요 기능

### 1. 경기 흐름 분석
- 5분 단위 모멘텀 점수 계산 및 시각화
- 변곡점 자동 탐지 (4가지 지표 종합 분석)
- 팬 친화형 설명 생성

### 2. 선수 분석
- 변곡점 시점 선수 영향도 계산
- 주요 선수 식별 및 활동 통계 제공
- 선수별 위치 히트맵 및 움직임 패턴 시각화

### 3. 시각화
- **모멘텀 곡선 그래프**: 경기 전체 흐름 시각화
- **히트맵**: 선수 위치 분포, 패스 연결, 슈팅 방향, 공격/수비 라인 표시
- **선수 움직임 그래프**: 주요 선수별 개별 활동 패턴

### 4. REST API
- FastAPI 기반 RESTful API 제공
- 경기 분석, 시각화, 선수 분석 엔드포인트

## 🚀 빠른 시작

### 설치

```bash
# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 실행

#### 방법 A: 샘플 데이터로 테스트

```bash
python -m src.main
```

#### 방법 B: 실제 K리그 데이터로 분석

```bash
# 기본 경기 분석
python -m src.main_real

# 특정 경기 ID로 분석
python -m src.main_real 126288
```

#### 방법 C: API 서버 실행

```bash
uvicorn src.api.main:app --reload
```

브라우저에서 `http://localhost:8000/docs` 접속하여 API 문서 확인

## 📚 문서

더 자세한 정보는 다음 문서를 참고하세요:

- **[사용 가이드](docs/USAGE.md)**: API 사용법, 데이터 입력 형식, 결과 해석 방법
- **[알고리즘 상세 설계](docs/ALGORITHM.md)**: 모멘텀 점수 계산 공식, 변곡점 탐지 알고리즘, 선수 분석 알고리즘, 패스 네트워크 분석
- **[시각화 가이드](docs/VISUALIZATION.md)**: 각 그래프의 요소 설명 및 해석 방법
- **[데이터 매핑 가이드](docs/DATA_MAPPING.md)**: K리그 데이터 형식 및 매핑 방법
- **[프로젝트 기획서](docs/PROPOSAL.md)**: 프로젝트 배경, 목표, 차별성
- **[변경 이력](docs/CHANGELOG.md)**: 주요 변경사항 및 업데이트 내역

## 🏗️ 프로젝트 구조

```
├── src/
│   ├── data/              # 데이터 모델 및 로더
│   │   ├── models.py      # 데이터 모델 정의
│   │   └── loader.py      # K리그 데이터 로더
│   ├── analysis/          # 지표 계산 및 변곡점 탐지
│   │   ├── metrics.py      # 지표 계산
│   │   ├── turning_point.py  # 변곡점 탐지
│   │   └── player_analysis.py  # 선수 분석
│   ├── explanation/       # AI 설명 생성
│   │   └── generator.py    # 팬 친화형 설명 생성
│   ├── visualization/     # 시각화
│   │   └── plotter.py     # 그래프 생성
│   ├── api/               # API 엔드포인트
│   │   └── main.py        # FastAPI 서버
│   ├── main.py            # 샘플 데이터 실행 파일
│   └── main_real.py       # 실제 K리그 데이터 실행 파일
├── docs/                  # 문서
│   ├── ALGORITHM.md       # 알고리즘 상세 설계
│   ├── USAGE.md           # 사용 가이드
│   ├── PROPOSAL.md        # 공모전 제출용 기획서
│   ├── DATA_MAPPING.md    # 데이터 매핑 가이드
│   └── VISUALIZATION.md   # 시각화 기능 상세 가이드
└── requirements.txt
```

## 🔌 API 엔드포인트

### 기본 분석
- `GET /matches`: 사용 가능한 경기 목록
- `GET /analyze/{game_id}`: 경기 ID로 변곡점 분석
- `GET /visualize/{game_id}`: 경기 ID로 모멘텀 곡선 그래프 생성
- `POST /analyze`: 직접 제공된 경기 데이터 분석
- `POST /visualize`: 직접 제공된 경기 데이터로 그래프 생성

### 선수 분석
- `GET /analyze/{game_id}/players/{turning_point_minute}`: 변곡점 시점 선수 분석
- `GET /visualize/{game_id}/heatmap/{turning_point_minute}`: 선수 위치 히트맵 생성
- `GET /visualize/{game_id}/movements/{turning_point_minute}`: 선수 움직임 그래프 생성

자세한 API 사용법은 [사용 가이드](docs/USAGE.md)를 참고하세요.

## 🛠️ 기술 스택

- **Backend**: Python 3.9+, FastAPI
- **Data Analysis**: Pandas, NumPy
- **Visualization**: Matplotlib
- **Data Validation**: Pydantic
- **API Server**: Uvicorn

**참고**: 
- 프로젝트는 Python 3.9 이상에서 작동합니다.
- 시각화는 matplotlib를 사용하며, 실제 축구장 형태의 히트맵을 제공합니다.

## 📊 생성되는 파일

- `momentum_curve_{game_id}.png`: 경기 흐름 그래프
- `heatmap_{game_id}_{minute}.png`: 변곡점 시점 선수 위치 히트맵
- `movements_{game_id}_{minute}.png`: 주요 선수 움직임 패턴 그래프

## 👥 팀원 소개

이 프로젝트를 함께 만든 팀원들:

| 역할 | 이름 | GitHub | 기여 내용 |
|------|------|--------|----------|
| 팀장 | [이지호] | [@username] | 프로젝트 총괄 및 관리 |
| 기획 | [민창기] | [@username] | 프로젝트 기획 및 요구사항 정의 |
| 데이터 분석 | [배성현] | [@username] | 데이터 분석 및 알고리즘 설계 |

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.

## 🙏 감사의 말

- K리그 데이터 제공에 감사드립니다.
