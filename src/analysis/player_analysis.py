"""
변곡점 시점 선수 분석 모듈
"""
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import numpy as np
from src.data.models import MatchData, MatchEvent, TurningPoint


class PlayerActivity:
    """선수 활동 정보"""
    def __init__(self, player_name: str, team: str):
        self.player_name = player_name
        self.team = team
        self.events: List[MatchEvent] = []
        self.positions: List[Tuple[float, float]] = []  # (x, y) 좌표
        self.shots = 0
        self.passes = 0
        self.successful_passes = 0
        self.defense_actions = 0
        self.xg_contribution = 0.0
        self.forward_passes = 0
        self.opponent_half_events = 0


def extract_player_activities(
    match_data: MatchData,
    turning_point: TurningPoint,
    time_window: int = 5
) -> Dict[str, PlayerActivity]:
    """
    변곡점 시점 주변의 선수별 활동 추출
    
    Args:
        match_data: 경기 데이터
        turning_point: 변곡점 정보
        time_window: 분석할 시간 범위 (분) - 변곡점 전후 각각
    
    Returns:
        선수명을 키로 하는 PlayerActivity 딕셔너리
    """
    minute_start = max(0, turning_point.minute - time_window)
    minute_end = min(90, turning_point.minute + time_window)
    
    # 변곡점에 영향을 준 팀
    target_team = (
        match_data.home_team if turning_point.team_advantage == 'home'
        else match_data.away_team
    )
    
    # 해당 시간대의 이벤트 필터링
    window_events = [
        e for e in match_data.events
        if minute_start <= e.minute < minute_end
        and e.team == target_team
    ]
    
    # 선수별 활동 수집
    player_activities: Dict[str, PlayerActivity] = {}
    
    for event in window_events:
        player_name = event.metadata.get('player_name', '') if event.metadata else ''
        
        if not player_name or player_name == '':
            continue
        
        if player_name not in player_activities:
            player_activities[player_name] = PlayerActivity(player_name, target_team)
        
        activity = player_activities[player_name]
        activity.events.append(event)
        
        # 위치 정보 수집
        if event.x is not None and event.y is not None:
            activity.positions.append((event.x, event.y))
        
        # 이벤트 타입별 통계
        if event.event_type == 'shot':
            activity.shots += 1
            if event.xg:
                activity.xg_contribution += event.xg
        
        elif event.event_type == 'pass':
            activity.passes += 1
            if event.success:
                activity.successful_passes += 1
            
            # 전진 패스 확인
            if event.metadata and 'end_x' in event.metadata:
                end_x = event.metadata.get('end_x')
                if end_x is not None and event.x is not None and end_x > event.x:
                    activity.forward_passes += 1
        
        elif event.event_type == 'defense':
            activity.defense_actions += 1
        
        # 상대 진영 이벤트
        if event.x is not None and event.x > 50:
            activity.opponent_half_events += 1
    
    return player_activities


def calculate_player_impact_score(activity: PlayerActivity) -> float:
    """
    선수의 변곡점 기여도 점수 계산
    
    가중치:
    - 슈팅/xG: 40%
    - 전진 패스: 25%
    - 상대 진영 활동: 20%
    - 수비 액션: 15%
    """
    # 정규화된 점수
    xg_score = activity.xg_contribution * 40  # xG는 이미 0-1 범위
    forward_pass_score = min(activity.forward_passes / 5.0, 1.0) * 25
    opponent_half_score = min(activity.opponent_half_events / 10.0, 1.0) * 20
    defense_score = min(activity.defense_actions / 5.0, 1.0) * 15
    
    impact_score = xg_score + forward_pass_score + opponent_half_score + defense_score
    
    return round(impact_score, 2)


def get_key_players(
    player_activities: Dict[str, PlayerActivity],
    top_n: int = 5
) -> List[Tuple[str, PlayerActivity, float]]:
    """
    변곡점에 가장 큰 영향을 준 선수들 반환
    
    Returns:
        (선수명, PlayerActivity, 영향도 점수) 리스트 (내림차순)
    """
    player_scores = [
        (name, activity, calculate_player_impact_score(activity))
        for name, activity in player_activities.items()
    ]
    
    # 영향도 점수로 정렬
    player_scores.sort(key=lambda x: x[2], reverse=True)
    
    return player_scores[:top_n]


def get_player_event_summary(activity: PlayerActivity) -> Dict:
    """
    선수의 활동 요약 정보 반환
    """
    pass_success_rate = (
        activity.successful_passes / activity.passes * 100
        if activity.passes > 0 else 0.0
    )
    
    # 평균 위치 계산
    avg_x = sum([p[0] for p in activity.positions]) / len(activity.positions) if activity.positions else None
    avg_y = sum([p[1] for p in activity.positions]) / len(activity.positions) if activity.positions else None
    
    return {
        'player_name': activity.player_name,
        'team': activity.team,
        'total_events': len(activity.events),
        'shots': activity.shots,
        'xg_contribution': round(activity.xg_contribution, 2),
        'passes': activity.passes,
        'successful_passes': activity.successful_passes,
        'pass_success_rate': round(pass_success_rate, 1),
        'forward_passes': activity.forward_passes,
        'defense_actions': activity.defense_actions,
        'opponent_half_events': activity.opponent_half_events,
        'avg_position': {'x': round(avg_x, 1), 'y': round(avg_y, 1)} if avg_x and avg_y else None,
        'positions': activity.positions[:50]  # 최대 50개 위치만 반환
    }


def analyze_pass_network(
    match_data: MatchData,
    turning_point: TurningPoint,
    player_activities: Dict[str, PlayerActivity],
    time_window: int = 5
) -> Tuple[Dict[Tuple[str, str], int], List[Tuple[str, str, int]]]:
    """
    선수 간 패스 네트워크 분석
    
    Returns:
        - pass_connections: {(passer, receiver): count} 딕셔너리
        - top_pass_paths: [(passer, receiver, count)] 리스트 (정렬됨)
    """
    minute_start = max(0, turning_point.minute - time_window)
    minute_end = min(90, turning_point.minute + time_window)
    
    target_team = (
        match_data.home_team if turning_point.team_advantage == 'home'
        else match_data.away_team
    )
    
    # 해당 시간대의 성공한 패스만 필터링
    window_events = [
        e for e in match_data.events
        if minute_start <= e.minute < minute_end
        and e.team == target_team
        and e.event_type == 'pass'
        and e.success is True
    ]
    
    # 선수 간 패스 빈도 계산
    pass_connections = defaultdict(int)
    
    for event in window_events:
        if event.metadata:
            passer = event.metadata.get('player_name', '')
            receiver = event.metadata.get('receiver_name', '')
            
            if passer and receiver and passer != receiver:
                pass_connections[(passer, receiver)] += 1
    
    # 상위 패스 경로 정렬
    top_pass_paths = sorted(
        [(passer, receiver, count) for (passer, receiver), count in pass_connections.items()],
        key=lambda x: x[2],
        reverse=True
    )
    
    return dict(pass_connections), top_pass_paths


def get_player_average_positions(
    player_activities: Dict[str, PlayerActivity]
) -> Dict[str, Tuple[float, float]]:
    """
    선수별 평균 위치 계산
    
    Returns:
        {player_name: (avg_x, avg_y)} 딕셔너리
    """
    positions = {}
    
    for player_name, activity in player_activities.items():
        if activity.positions:
            positions_array = np.array(activity.positions)
            avg_x = float(np.mean(positions_array[:, 0]))
            avg_y = float(np.mean(positions_array[:, 1]))
            positions[player_name] = (avg_x, avg_y)
    
    return positions

