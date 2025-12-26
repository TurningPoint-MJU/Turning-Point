# K리그 경기 변곡점 분석 MVP

> **"K리그 경기 데이터를 기반으로, 팬들이 '왜 이겼고 왜 졌는지'를 이해할 수 있도록 경기 흐름의 변곡점을 AI가 자동으로 탐지·설명하는 팬 친화형 분석 MVP"**

## 핵심 키워드
- **왜** - 경기 결과의 원인 분석
- **언제** - 변곡점 시점 탐지
- **무엇 때문에** - 구체적 지표 변화 설명

## MVP 기능 구조

### STEP 1. 경기 흐름 수치화 (Momentum Curve)
- 5분 단위 팀별 경기 주도권 점수 계산
- 타임라인 그래프 시각화

### STEP 2. 변곡점 자동 탐지
- 슈팅/xG 급증/급감
- 공격 지역 점유 변화
- 수비 이벤트 평균 위치 변화
- 패스 성공/실패 패턴 변화

### STEP 3. 팬 친화형 AI 설명 생성
- 전술 용어 최소화
- 팬 언어로 경기 흐름 설명

## 프로젝트 구조

```
├── src/
│   ├── data/              # 데이터 모델 (models.py)
│   ├── analysis/          # 지표 계산 및 변곡점 탐지
│   │   ├── metrics.py     # 지표 계산
│   │   └── turning_point.py  # 변곡점 탐지
│   ├── explanation/       # AI 설명 생성
│   │   └── generator.py    # 팬 친화형 설명 생성
│   ├── visualization/    # 시각화
│   │   └── plotter.py     # 모멘텀 곡선 그래프
│   ├── api/               # API 엔드포인트
│   │   └── main.py        # FastAPI 서버
│   └── main.py            # 메인 실행 파일
├── docs/                  # 문서
│   ├── ALGORITHM.md       # 알고리즘 상세 설계
│   ├── USAGE.md           # 사용 가이드
│   └── PROPOSAL.md        # 공모전 제출용 기획서
└── requirements.txt
```

## 🚀 빠른 시작

**처음 사용하시나요?** → [QUICKSTART.md](QUICKSTART.md)를 먼저 읽어주세요!

## 설치 및 실행

### 1단계: 패키지 설치

```bash
# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2단계: 실행 방법 선택

#### 방법 A: 샘플 데이터로 테스트 (가장 간단)

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

#### 방법 C: API 서버 실행 (웹 인터페이스)

```bash
uvicorn src.api.main:app --reload
```

브라우저에서 `http://localhost:8000/docs` 접속

### 상세한 실행 가이드

더 자세한 설명이 필요하시면 [QUICKSTART.md](QUICKSTART.md)를 참고하세요.

#### API 엔드포인트

- `GET /matches`: 사용 가능한 경기 목록
- `GET /analyze/{game_id}`: 경기 ID로 변곡점 분석
- `GET /visualize/{game_id}`: 경기 ID로 그래프 생성
- `POST /analyze`: 직접 제공된 경기 데이터 분석
- `POST /visualize`: 직접 제공된 경기 데이터로 그래프 생성

