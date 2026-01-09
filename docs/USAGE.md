# 사용 가이드

## 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 주피터 노트북 사용 시 (선택사항)
pip install jupyter ipykernel
```

### 2. 실행 방법

#### 방법 A: 주피터 노트북 사용 (권장)

```bash
# Jupyter 실행
jupyter notebook

# 또는 JupyterLab 사용
jupyter lab
```

주피터 노트북에서:
- `analysis_sample.ipynb`: 샘플 데이터로 테스트
- `analysis_real.ipynb`: 실제 K리그 데이터 분석
  - 경기 목록을 10개씩 페이지네이션하여 탐색 가능
  - 원하는 경기 ID 직접 입력 가능
  - 이미지가 노트북 셀에 인라인으로 자동 표시

#### 방법 B: Python 스크립트 실행

```bash
# 샘플 데이터 실행
python -m src.main

# 실제 K리그 데이터 실행
python -m src.main_real

# 특정 경기 ID로 실행
python -m src.main_real 126288
```

#### 방법 C: API 서버 실행

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

### GET /analyze/{game_id}

경기 ID로 변곡점을 분석합니다.

```python
import requests

url = "http://localhost:8000/analyze/126288"
response = requests.get(url)
result = response.json()
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

### GET /analyze/{game_id}/players/{turning_point_minute}

특정 변곡점 시점의 선수 분석 결과를 가져옵니다.

```python
import requests

url = "http://localhost:8000/analyze/126288/players/25"
response = requests.get(url, params={"top_n": 5})
result = response.json()

print(f"주요 선수: {len(result['key_players'])}명")
for player in result['key_players']:
    print(f"- {player['player_name']}: 영향도 {player['impact_score']:.1f}")
    print(f"  슈팅: {player['shots']}, 패스: {player['passes']}, xG: {player['xg_contribution']:.2f}")
```

### GET /visualize/{game_id}/heatmap/{turning_point_minute}

변곡점 시점의 선수 위치 히트맵을 생성합니다.

```python
import requests

url = "http://localhost:8000/visualize/126288/heatmap/25"
response = requests.get(url)
result = response.json()
print(f"히트맵 저장: {result['save_path']}")
```

### GET /visualize/{game_id}/movements/{turning_point_minute}

변곡점 시점의 주요 선수 움직임 그래프를 생성합니다.

```python
import requests

url = "http://localhost:8000/visualize/126288/movements/25"
response = requests.get(url, params={"top_n": 5})
result = response.json()
print(f"움직임 그래프 저장: {result['save_path']}")
```

## 실제 K리그 데이터 연동

### 주피터 노트북 사용 (권장)

`analysis_real.ipynb` 노트북을 사용하면 다음 기능을 제공합니다:

1. **경기 목록 페이지네이션**: 경기 목록을 10개씩 표시하고 `n`(다음), `p`(이전)로 탐색
2. **경기 ID 입력**: 원하는 경기 ID를 직접 입력하여 분석
3. **인라인 이미지 표시**: 생성된 그래프가 노트북 셀에 자동으로 표시

### 데이터 로더 사용 (Python 스크립트)

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

#### 모멘텀 곡선 그래프
- **파란색 영역**: 홈팀 우세 구간
- **빨간색 영역**: 원정팀 우세 구간
- **별표 마커**: 탐지된 변곡점
- **0선**: 경기 주도권이 균형인 상태

#### 히트맵 그래프
- **배경 히트맵**: 전체 선수 활동 빈도 (노란색 → 빨간색 = 높은 빈도)
- **개별 선수 히트맵**: 각 주요 선수별로 색상이 다른 히트맵으로 활동 영역 표시
  - 선수별 색상으로 구분 (파란색, 청록색 등 차가운색 계열)
  - 히트맵 색상이 진할수록 해당 선수가 그 위치에서 많이 활동
- **파란색 얇은 화살표**: 성공한 패스 연결 (앞쪽 10개는 더 진하게, 나머지는 투명하게)
- **회색 얇은 화살표**: 실패한 패스 또는 비중 낮은 패스 (투명도 낮게)
- **원형 마커 + 화살표**: 슈팅 위치 및 방향
  - xG에 따라 크기와 색상 조정 (xG ≥ 0.3: 진한 주황 큰 원, xG ≥ 0.15: 주황 중간 원, xG < 0.15: 노랑 작은 원)
  - 전반/후반 및 홈/원정팀에 따라 슈팅 방향 자동 결정
- **파란색 세로선**: 공격 라인 (공격 이벤트 평균 위치, 필드에 "공격 라인↑" 텍스트 표시)
- **청록색 세로선**: 수비 라인 (수비 이벤트 평균 위치, 필드에는 숫자 없이 색상과 두께로만 표시)
- **색상 원 마커**: 주요 선수 평균 위치 (원 안에 번호 표시, 상위 3명은 굵은 테두리와 halo 효과)
- **우측 패널**: 통일된 레이아웃으로 구성
  - **범례 박스**: 기호와 의미 설명 (변곡점, 선수, 패스, 슈팅 화살표 등)
  - **선수 통계 표**: 번호, 선수명, 슈팅, 패스, 수비, xG 기여, 영향도 점수 표시
    - 각 선수별 색상으로 행 구분 (채도 낮춤)
    - 주요 수치(영향도 1위, 슈팅 수 상위)는 굵게 표시
  - **변곡점 설명 박스**: 각 변곡점 이벤트에 대한 한 줄 요약 (가장 중요한 텍스트 카드)
  - **전체 설명 박스**: 경기 흐름 요약 및 공격/수비 라인 정보
- **좌표계 및 눈금**: X축(0-100, 10단위), Y축(0-100, 10단위) 눈금 표시
- **골대 팀 이름**: 각 골대 상단에 팀 이름 표시 (전반/후반에 따라 자동 결정)

#### 선수 움직임 그래프
- **히트맵**: 선수별 위치 분포 (활동 빈도)
- **빨간 별**: 슈팅 위치
- **청록 사각형**: 성공한 패스 위치
- **주황 X**: 실패한 패스 위치
- **초록 삼각형**: 수비 액션 위치

## 선수 분석 기능

### 선수 영향도 계산

변곡점 시점에 가장 큰 영향을 준 선수들을 식별합니다.

**영향도 점수 계산 공식:**
```
영향도 = xG 기여도 × 40% + 전진 패스 × 25% + 상대 진영 활동 × 20% + 수비 액션 × 15%
```

### 선수 활동 정보

각 선수에 대해 다음 정보를 제공합니다:
- 총 이벤트 수
- 슈팅 횟수 및 xG 기여도
- 패스 횟수 및 성공률
- 전진 패스 횟수
- 수비 액션 횟수
- 상대 진영 이벤트 횟수
- 평균 위치 좌표

### 패스 네트워크 분석

변곡점 시점의 선수 간 패스 연결 관계를 분석합니다.

**주요 기능:**
- 선수 간 패스 빈도 계산
- 주요 패스 경로 식별 (상위 5개)
- 패스 네트워크 시각화

**패스 연결 정보:**
- 각 패스 이벤트의 `metadata`에 `receiver_name` 필드 추가
- 패스를 한 선수와 받은 선수 정보 모두 포함
- 성공한 패스만 분석 대상

