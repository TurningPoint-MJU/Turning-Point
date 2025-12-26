# K리그 데이터 매핑 가이드

## 데이터 파일 구조

### raw_data.csv
경기 이벤트 데이터 (약 57만 행)

**주요 컬럼:**
- `game_id`: 경기 ID
- `period_id`: 전반(1)/후반(2)
- `time_seconds`: 경기 시간 (초)
- `team_id`: 팀 ID
- `team_name_ko`: 팀명 (한글)
- `type_name`: 이벤트 유형
- `result_name`: 결과 (Successful, Unsuccessful, On Target, Off Target, Goal)
- `start_x`, `start_y`: 시작 좌표 (0-100)
- `end_x`, `end_y`: 종료 좌표
- `player_name_ko`: 선수명 (한글)

### match_info.csv
경기 메타 정보

**주요 컬럼:**
- `game_id`: 경기 ID
- `game_date`: 경기 날짜
- `home_team_id`, `away_team_id`: 홈/원정 팀 ID
- `home_team_name_ko`, `away_team_name_ko`: 팀명 (한글)
- `home_score`, `away_score`: 최종 스코어

## 이벤트 타입 매핑

| K리그 type_name | 우리 모델 event_type | 설명 |
|----------------|---------------------|------|
| Shot | shot | 슈팅 |
| Pass | pass | 패스 |
| Carry | pass | 드리블 (패스로 간주) |
| Block | defense | 블록 |
| Tackle | defense | 태클 |
| Interception | defense | 인터셉트 |
| Intervention | defense | 개입 |
| Clearance | defense | 클리어런스 |
| Recovery | defense | 볼 회수 |
| Duel | defense | 듀얼 |
| Goal Kick | possession | 골킥 |
| Throw-In | possession | 스로인 |
| Pass Received | possession | 패스 수신 |
| Offside | possession | 오프사이드 |
| Out | possession | 아웃 |

## 시간 변환

```python
def convert_time_to_minute(period_id: int, time_seconds: float) -> int:
    if period_id == 1:  # 전반
        return int(time_seconds / 60)  # 0-45분
    elif period_id == 2:  # 후반
        return 45 + int(time_seconds / 60)  # 45-90분
```

## xG 추정

실제 xG 데이터가 없으므로 슈팅 위치와 결과로 추정:

```python
def estimate_xg_from_shot(shot_data):
    x = shot_data['start_x']  # 골대까지 거리
    distance_to_goal = 100 - x
    
    base_xg = (100 - distance_to_goal) / 100 * 0.5
    
    # 결과에 따른 조정
    if result == 'Goal':
        return 1.0
    elif result == 'On Target':
        return base_xg * 0.8
    elif result == 'Off Target':
        return base_xg * 0.3
```

## 좌표계

- **x 좌표**: 0 (자신의 골대) ~ 100 (상대 골대)
- **y 좌표**: 0 (왼쪽 사이드) ~ 100 (오른쪽 사이드)
- **상대 진영**: x > 50
- **전진 패스**: end_x > start_x

## 성공 여부 판단

| result_name | success |
|------------|---------|
| Successful | True |
| Unsuccessful | False |
| On Target | True |
| Off Target | False |
| Goal | True |

