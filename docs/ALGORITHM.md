# 변곡점 탐지 알고리즘 상세 설계

## 1. Momentum Score 계산 공식

### 기본 개념
경기 주도권을 수치화한 점수로, -100 ~ +100 범위의 값을 가집니다.
- 양수: 홈팀 우세
- 음수: 원정팀 우세

### 계산 공식

```
Momentum = w1 × P + w2 × X + w3 × F + w4 × O + w5 × S
```

여기서:
- **P (Possession Score)**: 점유율 차이 점수
  - `P = (home_possession - away_possession) / 100 × 20`
  - 범위: -20 ~ +20

- **X (xG Score)**: 기대득점 차이 점수
  - `X = (home_xg - away_xg) × 10`
  - 범위: 제한 없음 (실제로는 -30 ~ +30)

- **F (Forward Pass Score)**: 전진 패스 차이 점수
  - `F = (home_forward_passes - away_forward_passes) / 10 × 15`
  - 범위: -15 ~ +15

- **O (Opponent Half Score)**: 상대 진영 이벤트 차이 점수
  - `O = (home_opponent_half_events - away_opponent_half_events) / 10 × 20`
  - 범위: -20 ~ +20

- **S (Pass Success Score)**: 패스 성공률 차이 점수
  - `S = (home_pass_success_rate - away_pass_success_rate) / 100 × 15`
  - 범위: -15 ~ +15

### 가중치
| 지표 | 가중치 | 이유 |
|------|--------|------|
| 점유율 | 20% | 경기 주도권의 기본 지표 |
| xG/슈팅 | 30% | 실제 골 가능성과 직결 |
| 상대 진영 이벤트 | 20% | 공격 압박 강도 |
| 전진 패스 | 15% | 공격 의도 |
| 패스 성공률 | 15% | 공격 연결성 |

## 2. 변곡점 판단 기준

### 후보 선정 조건
5분 단위로 계산된 Momentum Score의 변화량이 **20 이상**인 경우 후보로 선정

```
|Momentum(t) - Momentum(t-5)| ≥ 20
```

### 변곡점 확정 조건
아래 4가지 지표 중 **2개 이상** 충족 시 변곡점으로 확정

#### 1. 슈팅/xG 급증 또는 급감
```
|shots(t) - shots(t-5)| ≥ 2
또는
|xg(t) - xg(t-5)| ≥ 0.3
```

#### 2. 공격 지역 점유 변화
```
|opponent_half_events(t) - opponent_half_events(t-5)| ≥ 3
```

#### 3. 수비 이벤트 평균 위치 변화
```
|defense_avg_x(t) - defense_avg_x(t-5)| ≥ 5
```

#### 4. 패스 성공/실패 패턴 변화
```
|pass_success_rate(t) - pass_success_rate(t-5)| ≥ 15%
```

## 3. 실제 K리그 데이터 컬럼 매핑

### 필수 데이터 컬럼

| 우리 모델 | K리그 데이터 컬럼 | 설명 |
|----------|------------------|------|
| `minute` | `event_minute` | 이벤트 발생 시간 |
| `team` | `team_name` | 팀명 |
| `event_type` | `event_type` | 이벤트 유형 (shot, pass, defense 등) |
| `x`, `y` | `field_x`, `field_y` | 필드 좌표 (0-100) |
| `success` | `pass_success` / `shot_on_target` | 성공 여부 |
| `xg` | `expected_goals` | 기대득점 |

### 이벤트 유형 분류

```python
EVENT_TYPES = {
    'shot': ['shot', 'shot_on_target', 'shot_off_target'],
    'pass': ['pass', 'forward_pass', 'backward_pass'],
    'defense': ['tackle', 'interception', 'clearance', 'block'],
    'possession': ['possession_start', 'possession_end']
}
```

### 좌표계 변환 (필요시)

일부 데이터는 다른 좌표계를 사용할 수 있으므로 변환이 필요할 수 있습니다:

```python
# 0-100 좌표계로 정규화
normalized_x = (raw_x / field_width) * 100
normalized_y = (raw_y / field_length) * 100
```

## 4. 시간 윈도우 집계 방법

### 5분 단위 집계
- 0-5분, 5-10분, ..., 85-90분
- 각 윈도우 내의 모든 이벤트를 집계하여 지표 계산

### 경계 처리
- 경기 시작/종료 시점의 불완전한 윈도우도 포함
- 예: 88-90분 윈도우는 2분만 포함

## 5. 설명 생성 로직

### 템플릿 기반 생성
1. 변곡점 유형 분류 (`attack_surge`, `defense_breakdown`, `momentum_shift`)
2. 변화 방향 판단 (positive/negative)
3. 해당 템플릿 선택
4. 지표 값으로 템플릿 채우기

### 향후 개선 방향
- LLM API 연동 (GPT-4, Claude 등)
- 더 자연스러운 문장 생성
- 팀별 특성 반영

## 6. 선수 분석 알고리즘

### 선수 활동 추출

변곡점 시점 전후 5분(총 10분) 동안의 선수별 이벤트를 추출합니다.

```python
time_window = 5분
분석 범위 = [변곡점 시점 - 5분, 변곡점 시점 + 5분]
```

### 선수 영향도 점수 계산

변곡점에 기여한 선수의 영향도를 다음 공식으로 계산합니다:

```
영향도 점수 = xG_score + forward_pass_score + opponent_half_score + defense_score
```

여기서:
- **xG_score**: `xg_contribution × 40`
  - 선수가 기여한 총 xG 값 (0-1 범위)
  - 슈팅의 xG를 누적하여 계산
  
- **forward_pass_score**: `min(forward_passes / 5.0, 1.0) × 25`
  - 전진 패스 횟수를 정규화 (최대 5개 기준)
  - 상대 골대 방향으로 향한 패스만 카운트
  
- **opponent_half_score**: `min(opponent_half_events / 10.0, 1.0) × 20`
  - 상대 진영(x > 50)에서의 이벤트 횟수
  - 최대 10개 기준으로 정규화
  
- **defense_score**: `min(defense_actions / 5.0, 1.0) × 15`
  - 수비 액션(태클, 인터셉트 등) 횟수
  - 최대 5개 기준으로 정규화

### 주요 선수 식별

영향도 점수가 높은 순서로 상위 N명의 선수를 선정합니다.

### 가중치 설정 이유

| 지표 | 가중치 | 이유 |
|------|--------|------|
| xG 기여도 | 40% | 골 가능성과 직접 연결되는 가장 중요한 지표 |
| 전진 패스 | 25% | 공격 의도와 연결성을 나타냄 |
| 상대 진영 활동 | 20% | 공격 압박 강도를 나타냄 |
| 수비 액션 | 15% | 수비 기여도 (공격 중심 변곡점에서는 낮은 가중치) |

## 7. 히트맵 생성 알고리즘

### 위치 히트맵

선수들의 위치를 20×20 그리드로 나누어 활동 빈도를 계산합니다.

```python
grid_size = 20
heatmap_data[y_grid, x_grid] = 해당 위치의 이벤트 수
```

### 공격/수비 라인 계산

- **공격 라인**: 공격 이벤트(슈팅, 패스)의 평균 x 좌표
- **수비 라인**: 수비 이벤트의 평균 x 좌표

```python
attack_line_x = mean([event.x for event in attack_events])
defense_line_x = mean([event.x for event in defense_events])
```

### 패스 연결선 표시

- 성공한 패스: 시작점 → 종료점을 청록색 실선 화살표로 표시
- 실패한 패스: 시작점 → 종료점을 주황색 점선 화살표로 표시
- 최대 25개(성공) + 15개(실패) 패스만 표시하여 가독성 유지

### 슈팅 표시

xG 값에 따라 색상과 크기를 구분:
- xG ≥ 0.3: 진한 빨강, 큰 별 (500px)
- xG ≥ 0.15: 토마토색, 중간 별 (350px)
- xG < 0.15: 금색, 작은 별 (250px)

