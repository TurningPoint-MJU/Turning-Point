"""
경기 지표 계산 모듈
"""
import pandas as pd
from typing import List
from src.data.models import MatchEvent, TimeWindowMetrics


def calculate_time_window_metrics(
    events: List[MatchEvent],
    team: str,
    minute_start: int,
    minute_end: int
) -> TimeWindowMetrics:
    """
    5분 단위 지표 계산
    """
    window_events = [
        e for e in events
        if e.team == team and minute_start <= e.minute < minute_end
    ]
    
    if not window_events:
        return TimeWindowMetrics(
            minute_start=minute_start,
            minute_end=minute_end,
            team=team,
            possession=0,
            shots=0,
            xg=0.0,
            forward_passes=0,
            opponent_half_events=0,
            defense_avg_x=50.0,
            pass_success_rate=0.0
        )
    
    # 점유율 (이벤트 수 기반 근사치)
    total_events = len([e for e in events if minute_start <= e.minute < minute_end])
    possession = (len(window_events) / total_events * 100) if total_events > 0 else 0
    
    # 슈팅 및 xG
    shots = len([e for e in window_events if e.event_type == 'shot'])
    xg = sum([e.xg or 0.0 for e in window_events if e.event_type == 'shot'])
    
    # 전진 패스 (x 좌표가 증가하는 패스, 즉 상대 골대 방향)
    passes = [e for e in window_events if e.event_type == 'pass' and e.x is not None]
    forward_passes = 0
    for e in passes:
        if e.metadata and 'end_x' in e.metadata:
            end_x = e.metadata.get('end_x')
            if end_x is not None and end_x > e.x:  # x 좌표 증가 = 전진
                forward_passes += 1
        elif e.success:  # end_x가 없으면 성공한 패스로 간주
            forward_passes += 1
    
    # 상대 진영 이벤트 (x > 50)
    opponent_half_events = len([
        e for e in window_events
        if e.x is not None and e.x > 50
    ])
    
    # 수비 이벤트 평균 x 좌표
    defense_events = [e for e in window_events if e.event_type == 'defense' and e.x is not None]
    defense_avg_x = (
        sum([e.x for e in defense_events]) / len(defense_events)
        if defense_events else 50.0
    )
    
    # 패스 성공률
    all_passes = [e for e in window_events if e.event_type == 'pass']
    successful_passes = [e for e in all_passes if e.success is True]
    pass_success_rate = (
        len(successful_passes) / len(all_passes) * 100
        if all_passes else 0.0
    )
    
    return TimeWindowMetrics(
        minute_start=minute_start,
        minute_end=minute_end,
        team=team,
        possession=possession,
        shots=shots,
        xg=xg,
        forward_passes=forward_passes,
        opponent_half_events=opponent_half_events,
        defense_avg_x=defense_avg_x,
        pass_success_rate=pass_success_rate
    )


def calculate_momentum_score(
    home_metrics: TimeWindowMetrics,
    away_metrics: TimeWindowMetrics
) -> float:
    """
    모멘텀 점수 계산 (0-100)
    
    가중치:
    - 점유율: 20%
    - 슈팅/xG: 30%
    - 전진 패스: 15%
    - 상대 진영 이벤트: 20%
    - 패스 성공률: 15%
    """
    # 정규화된 점수 계산
    possession_score = (home_metrics.possession - away_metrics.possession) / 100 * 20
    xg_score = (home_metrics.xg - away_metrics.xg) * 10  # xG 차이를 점수로 변환
    forward_pass_score = (home_metrics.forward_passes - away_metrics.forward_passes) / 10 * 15
    opponent_half_score = (home_metrics.opponent_half_events - away_metrics.opponent_half_events) / 10 * 20
    pass_success_score = (home_metrics.pass_success_rate - away_metrics.pass_success_rate) / 100 * 15
    
    momentum = (
        possession_score +
        xg_score +
        forward_pass_score +
        opponent_half_score +
        pass_success_score
    )
    
    # -100 ~ 100 범위로 제한
    return max(-100, min(100, momentum))

