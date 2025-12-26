# 사용 가이드

## 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 샘플 실행

```bash
python -m src.main
```

이 명령은 샘플 경기 데이터를 생성하고 변곡점을 탐지한 후 그래프를 생성합니다.

### 3. API 서버 실행

```bash
uvicorn src.api.main:app --reload
```

API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## 데이터 입력 형식

### MatchData 구조

```python
from src.data.models import MatchData, MatchEvent
from datetime import datetime

match_data = MatchData(
    match_id="K2024_001",
    home_team="서울 FC",
    away_team="수원 삼성",
    match_date=datetime(2024, 3, 15, 19:00),
    events=[
        MatchEvent(
            minute=15,
            team="서울 FC",
            event_type="shot",
            x=75.0,
            y=50.0,
            success=True,
            xg=0.15
        ),
        MatchEvent(
            minute=15,
            team="서울 FC",
            event_type="pass",
            x=60.0,
            y=45.0,
            success=True
        ),
        # ... 더 많은 이벤트
    ],
    final_score={"home": 2, "away": 1}
)
```

### 이벤트 유형

- `shot`: 슈팅
- `pass`: 패스
- `defense`: 수비 이벤트 (태클, 인터셉트 등)
- `possession`: 점유 시작/종료

## API 사용 예시

### POST /analyze

경기 데이터를 분석하여 변곡점을 탐지합니다.

```python
import requests

url = "http://localhost:8000/analyze"
response = requests.post(url, json=match_data.dict())
result = response.json()

print(f"변곡점 개수: {result['turning_points_count']}")
for tp in result['turning_points']:
    print(f"{tp['minute']}분: {tp['explanation']}")
```

### POST /visualize

경기 흐름 그래프를 생성합니다.

```python
import requests

url = "http://localhost:8000/visualize"
response = requests.post(
    url,
    json=match_data.dict(),
    params={"save_path": "output.png"}
)
```

## 실제 K리그 데이터 연동

### 데이터 로더 사용

```python
from src.data.loader import load_match_by_id, list_available_matches

# 사용 가능한 경기 목록 확인
matches = list_available_matches("match_info.csv")
print(matches)

# 특정 경기 로드
match_data = load_match_by_id(
    "raw_data.csv",
    "match_info.csv",
    game_id=126288
)

# 분석 실행
from src.analysis.turning_point import detect_turning_points
turning_points = detect_turning_points(match_data)
```

### 데이터 구조 매핑

| 우리 모델 | K리그 데이터 컬럼 |
|----------|------------------|
| `minute` | `period_id` + `time_seconds` (변환) |
| `team` | `team_name_ko` |
| `event_type` | `type_name` (매핑) |
| `x`, `y` | `start_x`, `start_y` |
| `success` | `result_name` (변환) |
| `xg` | 추정 (슈팅 위치 기반) |

### 이벤트 타입 매핑

- `Shot` → `shot`
- `Pass`, `Carry` → `pass`
- `Block`, `Tackle`, `Interception` 등 → `defense`
- `Goal Kick`, `Throw-In` 등 → `possession`

## 결과 해석

### 변곡점 정보

각 변곡점은 다음 정보를 포함합니다:

- `minute`: 변곡점 발생 시각
- `team`: 유리해진 팀
- `change_type`: 변화 유형
  - `attack_surge`: 공격 급증
  - `defense_breakdown`: 수비 붕괴
  - `momentum_shift`: 일반적인 흐름 변화
- `indicators`: 변화를 나타낸 지표 목록
- `explanation`: 팬 친화형 설명
- `metrics_before/after`: 변곡점 전후 지표

### 그래프 해석

- **파란색 영역**: 홈팀 우세 구간
- **빨간색 영역**: 원정팀 우세 구간
- **별표 마커**: 탐지된 변곡점
- **0선**: 경기 주도권이 균형인 상태

