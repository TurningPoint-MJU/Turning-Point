"""
변곡점 탐지 알고리즘
"""
from typing import List, Tuple
from src.data.models import (
    MatchData, TimeWindowMetrics, MomentumScore, TurningPoint
)
from src.analysis.metrics import calculate_time_window_metrics, calculate_momentum_score


def detect_turning_points(match_data: MatchData) -> List[TurningPoint]:
    """
    경기 전체에서 변곡점 탐지
    
    변곡점 판단 기준 (2개 이상 충족):
    1. 슈팅/xG 급증 또는 급감
    2. 공격 지역 점유 변화
    3. 수비 이벤트 평균 위치 변화
    4. 연속적인 패스 성공/실패 패턴 변화
    """
    events = match_data.events
    turning_points = []
    
    # 5분 단위로 지표 계산
    time_windows = []
    for minute in range(0, 90, 5):
        minute_end = min(minute + 5, 90)
        
        home_metrics = calculate_time_window_metrics(
            events, match_data.home_team, minute, minute_end
        )
        away_metrics = calculate_time_window_metrics(
            events, match_data.away_team, minute, minute_end
        )
        
        momentum = calculate_momentum_score(home_metrics, away_metrics)
        
        time_windows.append({
            'minute': minute,
            'home_metrics': home_metrics,
            'away_metrics': away_metrics,
            'momentum': momentum
        })
    
    # 변곡점 후보 탐지 (모멘텀 변화가 큰 지점)
    for i in range(1, len(time_windows)):
        prev_momentum = time_windows[i-1]['momentum']
        curr_momentum = time_windows[i]['momentum']
        momentum_change = abs(curr_momentum - prev_momentum)
        
        # 모멘텀 변화가 20 이상이면 후보
        if momentum_change >= 20:
            prev_home = time_windows[i-1]['home_metrics']
            prev_away = time_windows[i-1]['away_metrics']
            curr_home = time_windows[i]['home_metrics']
            curr_away = time_windows[i]['away_metrics']
            
            # 변곡점 지표 확인
            indicators = []
            
            # 1. 슈팅/xG 급증/급감
            home_xg_change = curr_home.xg - prev_home.xg
            away_xg_change = curr_away.xg - prev_away.xg
            if abs(home_xg_change) >= 0.3 or abs(away_xg_change) >= 0.3:
                indicators.append('xG_change')
            
            home_shots_change = curr_home.shots - prev_home.shots
            away_shots_change = curr_away.shots - prev_away.shots
            if abs(home_shots_change) >= 2 or abs(away_shots_change) >= 2:
                indicators.append('shots_surge')
            
            # 2. 공격 지역 점유 변화
            home_opp_half_change = curr_home.opponent_half_events - prev_home.opponent_half_events
            away_opp_half_change = curr_away.opponent_half_events - prev_away.opponent_half_events
            if abs(home_opp_half_change) >= 3 or abs(away_opp_half_change) >= 3:
                indicators.append('attack_zone_change')
            
            # 3. 수비 이벤트 평균 위치 변화
            home_defense_change = abs(curr_home.defense_avg_x - prev_home.defense_avg_x)
            away_defense_change = abs(curr_away.defense_avg_x - prev_away.defense_avg_x)
            if home_defense_change >= 5 or away_defense_change >= 5:
                indicators.append('defense_line_shift')
            
            # 4. 패스 성공률 변화
            home_pass_change = abs(curr_home.pass_success_rate - prev_home.pass_success_rate)
            away_pass_change = abs(curr_away.pass_success_rate - prev_away.pass_success_rate)
            if home_pass_change >= 15 or away_pass_change >= 15:
                indicators.append('pass_pattern_change')
            
            # 2개 이상 충족 시 변곡점 확정
            if len(indicators) >= 2:
                team_advantage = 'home' if curr_momentum > 0 else 'away'
                
                # 변화 유형 결정
                if 'xG_change' in indicators or 'shots_surge' in indicators:
                    change_type = 'attack_surge'
                elif 'defense_line_shift' in indicators:
                    change_type = 'defense_breakdown'
                else:
                    change_type = 'momentum_shift'
                
                # 설명 생성 (간단한 버전, 나중에 explanation 모듈로 이동)
                explanation = generate_simple_explanation(
                    minute=time_windows[i]['minute'],
                    team_advantage=team_advantage,
                    indicators=indicators,
                    prev_home=prev_home,
                    prev_away=prev_away,
                    curr_home=curr_home,
                    curr_away=curr_away,
                    home_team=match_data.home_team,
                    away_team=match_data.away_team
                )
                
                turning_point = TurningPoint(
                    minute=time_windows[i]['minute'],
                    team_advantage=team_advantage,
                    change_type=change_type,
                    indicators=indicators,
                    explanation=explanation,
                    metrics_before=prev_home if team_advantage == 'home' else prev_away,
                    metrics_after=curr_home if team_advantage == 'home' else curr_away
                )
                
                turning_points.append(turning_point)
    
    return turning_points


def generate_simple_explanation(
    minute: int,
    team_advantage: str,
    indicators: List[str],
    prev_home: TimeWindowMetrics,
    prev_away: TimeWindowMetrics,
    curr_home: TimeWindowMetrics,
    curr_away: TimeWindowMetrics,
    home_team: str,
    away_team: str
) -> str:
    """
    간단한 설명 생성 (나중에 explanation 모듈로 개선)
    """
    team_name = home_team if team_advantage == 'home' else away_team
    prev_metrics = prev_home if team_advantage == 'home' else prev_away
    curr_metrics = curr_home if team_advantage == 'home' else curr_away
    
    explanations = []
    
    if 'xG_change' in indicators or 'shots_surge' in indicators:
        shots_diff = curr_metrics.shots - prev_metrics.shots
        if shots_diff > 0:
            explanations.append(f"{team_name}의 슈팅 시도가 급격히 증가했습니다")
        else:
            explanations.append(f"{team_name}의 슈팅 시도가 크게 줄어들었습니다")
    
    if 'attack_zone_change' in indicators:
        opp_half_diff = curr_metrics.opponent_half_events - prev_metrics.opponent_half_events
        if opp_half_diff > 0:
            explanations.append(f"상대 진영에서의 활동이 활발해졌습니다")
        else:
            explanations.append(f"상대 진영에서의 활동이 크게 줄어들었습니다")
    
    if 'defense_line_shift' in indicators:
        defense_change = curr_metrics.defense_avg_x - prev_metrics.defense_avg_x
        if defense_change > 0:
            explanations.append(f"수비 라인이 전진하며 압박 강도가 높아졌습니다")
        else:
            explanations.append(f"수비 라인이 후퇴하며 수동적인 수비로 전환되었습니다")
    
    if 'pass_pattern_change' in indicators:
        pass_diff = curr_metrics.pass_success_rate - prev_metrics.pass_success_rate
        if pass_diff > 0:
            explanations.append(f"패스 성공률이 크게 향상되었습니다")
        else:
            explanations.append(f"패스 성공률이 급격히 하락하며 공격 흐름이 끊겼습니다")
    
    base = f"{minute}분 이후"
    if explanations:
        return base + ", " + ", ".join(explanations) + "."
    else:
        return base + " 경기 흐름에 변화가 있었습니다."

