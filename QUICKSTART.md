# 빠른 시작 가이드

## 📋 사전 준비사항

### 1. Python 설치 확인

터미널에서 다음 명령어로 Python 버전 확인:

```bash
python --version
# 또는
python3 --version
```

**필요 버전**: Python 3.8 이상

Python이 설치되어 있지 않다면:
- macOS: `brew install python3`
- 또는 [python.org](https://www.python.org/downloads/)에서 다운로드

### 2. 프로젝트 위치 확인

터미널에서 프로젝트 폴더로 이동:

```bash
cd "/Users/leejiho/Desktop/터닝포인트 프로젝트"
```

---

## 🚀 설치 단계

### 1단계: 가상환경 생성 (권장)

가상환경을 사용하면 프로젝트별로 패키지를 관리할 수 있습니다.

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

가상환경이 활성화되면 터미널 앞에 `(venv)`가 표시됩니다.

### 2단계: 패키지 설치

```bash
pip install -r requirements.txt
```

설치되는 패키지:
- `fastapi`: API 서버
- `uvicorn`: ASGI 서버
- `pandas`: 데이터 처리
- `numpy`: 수치 계산
- `matplotlib`: 그래프 생성
- `plotly`: 인터랙티브 그래프
- `pydantic`: 데이터 검증

### 3단계: 설치 확인

```bash
python -c "import pandas, fastapi; print('설치 완료!')"
```

오류가 없으면 설치가 완료된 것입니다.

---

## 🎯 실행 방법

### 방법 1: 샘플 데이터로 테스트 (가장 간단)

처음 실행할 때는 샘플 데이터로 테스트하는 것을 권장합니다.

```bash
python -m src.main
```

**예상 출력:**
```
============================================================
K리그 경기 변곡점 분석 MVP
============================================================

경기: 서울 FC vs 수원 삼성
이벤트 수: 180

변곡점 탐지 중...
탐지된 변곡점: 3개

[25분] 서울 FC
  유형: attack_surge
  지표: xG_change, shots_surge
  설명: 서울 FC의 공격이 25분 이후 급격히 살아났습니다...

전체 요약:
  이 경기의 가장 큰 변곡점은 25분이었습니다...

그래프 생성 중...
그래프가 'momentum_curve.png'로 저장되었습니다.
```

**생성되는 파일:**
- `momentum_curve.png`: 경기 흐름 그래프

---

### 방법 2: 실제 K리그 데이터로 분석

#### 2-1. 사용 가능한 경기 확인

먼저 어떤 경기를 분석할 수 있는지 확인:

```bash
python -c "from src.data.loader import list_available_matches; import pandas as pd; matches = list_available_matches('match_info.csv'); print(matches.head(10))"
```

또는 Python 스크립트로:

```python
from src.data.loader import list_available_matches
import pandas as pd

matches = list_available_matches("match_info.csv")
print(matches[['game_id', 'game_date', 'home_team_name_ko', 'away_team_name_ko', 'home_score', 'away_score']].head(10))
```

#### 2-2. 특정 경기 분석

```bash
# 기본 경기 (첫 번째 경기)
python -m src.main_real

# 특정 경기 ID로 분석 (예: 126288)
python -m src.main_real 126288
```

**예상 출력:**
```
============================================================
K리그 경기 변곡점 분석 MVP - 실제 데이터 테스트
============================================================

사용 가능한 경기 목록:
  game_id  game_date  home_team_name_ko  away_team_name_ko  home_score  away_score
  126283  2024-03-01  울산 HD FC         포항 스틸러스      1           0
  ...

경기 ID 126288 분석 중...

경기: 대구FC vs 김천 상무 프로축구단
경기 날짜: 2024-03-03 05:00:00
최종 스코어: 0 - 1
이벤트 수: 1234

변곡점 탐지 중...
탐지된 변곡점: 2개

[20분] 김천 상무 프로축구단
  유형: attack_surge
  ...
```

**생성되는 파일:**
- `momentum_curve_126288.png`: 해당 경기의 흐름 그래프

---

### 방법 3: API 서버 실행 (웹 인터페이스)

#### 3-1. 서버 시작

```bash
uvicorn src.api.main:app --reload
```

**예상 출력:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### 3-2. API 문서 확인

브라우저에서 다음 주소 열기:

```
http://localhost:8000/docs
```

Swagger UI가 열리며 모든 API 엔드포인트를 테스트할 수 있습니다.

#### 3-3. 주요 API 엔드포인트

**1. 경기 목록 조회**
```
GET http://localhost:8000/matches
```

**2. 경기 분석**
```
GET http://localhost:8000/analyze/126288
```

**3. 그래프 생성**
```
GET http://localhost:8000/visualize/126288
```

#### 3-4. curl로 테스트

터미널에서 직접 API 호출:

```bash
# 경기 목록
curl http://localhost:8000/matches

# 경기 분석
curl http://localhost:8000/analyze/126288

# JSON 형식으로 보기
curl http://localhost:8000/analyze/126288 | python -m json.tool
```

---

## 📊 결과 확인

### 1. 콘솔 출력

터미널에서 변곡점 정보와 설명이 출력됩니다:
- 변곡점 발생 시각
- 유리해진 팀
- 변화 유형
- 주요 지표
- 팬 친화형 설명

### 2. 그래프 파일

프로젝트 폴더에 PNG 파일이 생성됩니다:
- `momentum_curve.png` (샘플 데이터)
- `momentum_curve_{game_id}.png` (실제 데이터)

**그래프 해석:**
- 파란색 영역: 홈팀 우세 구간
- 빨간색 영역: 원정팀 우세 구간
- 별표 마커: 탐지된 변곡점
- 0선: 경기 주도권이 균형인 상태

### 3. API 응답 (JSON)

API를 사용한 경우 JSON 형식으로 결과를 받을 수 있습니다:

```json
{
  "match_id": "126288",
  "home_team": "대구FC",
  "away_team": "김천 상무 프로축구단",
  "summary": "이 경기의 가장 큰 변곡점은...",
  "turning_points_count": 2,
  "turning_points": [
    {
      "minute": 20,
      "team": "김천 상무 프로축구단",
      "change_type": "attack_surge",
      "explanation": "...",
      "metrics_before": {...},
      "metrics_after": {...}
    }
  ]
}
```

---

## 🔧 문제 해결

### 오류 1: "ModuleNotFoundError"

**원인**: 패키지가 설치되지 않음

**해결**:
```bash
pip install -r requirements.txt
```

### 오류 2: "FileNotFoundError: raw_data.csv"

**원인**: 데이터 파일이 프로젝트 루트에 없음

**해결**: 
- `raw_data.csv`와 `match_info.csv`가 프로젝트 폴더에 있는지 확인
- 파일 경로가 올바른지 확인

### 오류 3: "No such file or directory: venv"

**원인**: 가상환경이 생성되지 않음

**해결**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 오류 4: 포트 8000이 이미 사용 중

**원인**: 다른 프로그램이 포트 8000을 사용 중

**해결**: 다른 포트 사용
```bash
uvicorn src.api.main:app --reload --port 8001
```

---

## 📝 다음 단계

1. **다양한 경기 분석**: 다른 game_id로 여러 경기 분석
2. **알고리즘 튜닝**: `src/analysis/turning_point.py`에서 변곡점 판단 기준 조정
3. **설명 개선**: `src/explanation/generator.py`에서 템플릿 수정
4. **시각화 개선**: `src/visualization/plotter.py`에서 그래프 스타일 변경

---

## 💡 팁

- **첫 실행**: 샘플 데이터(`python -m src.main`)로 먼저 테스트
- **빠른 확인**: API 문서(`http://localhost:8000/docs`)에서 바로 테스트 가능
- **대량 분석**: Python 스크립트로 여러 경기를 반복 분석 가능
- **결과 저장**: API 응답을 JSON 파일로 저장하여 나중에 분석 가능

---

## 🆘 도움이 필요하신가요?

문제가 발생하면 다음을 확인하세요:
1. Python 버전 (3.8 이상)
2. 모든 패키지 설치 완료
3. 데이터 파일 위치 (프로젝트 루트)
4. 파일 경로 (한글 경로 문제 가능)

