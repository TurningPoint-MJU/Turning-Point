"""
경기 데이터 모델 정의
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MatchEvent(BaseModel):
    """경기 이벤트 (슈팅, 패스, 수비 등)"""
    minute: int
    team: str
    event_type: str  # 'shot', 'pass', 'defense', 'possession'
    x: Optional[float] = None  # 필드 x 좌표 (0-100)
    y: Optional[float] = None  # 필드 y 좌표 (0-100)
    success: Optional[bool] = None
    xg: Optional[float] = None  # 기대득점 (슈팅의 경우)
    metadata: Optional[dict] = None


class MatchData(BaseModel):
    """경기 전체 데이터"""
    match_id: str
    home_team: str
    away_team: str
    match_date: datetime
    events: List[MatchEvent]
    final_score: Optional[dict] = None  # {'home': 2, 'away': 1}


class TimeWindowMetrics(BaseModel):
    """5분 단위 지표"""
    minute_start: int
    minute_end: int
    team: str
    possession: float  # 점유율 (0-100)
    shots: int
    xg: float
    forward_passes: int
    opponent_half_events: int
    defense_avg_x: float  # 수비 이벤트 평균 x 좌표
    pass_success_rate: float  # 패스 성공률


class MomentumScore(BaseModel):
    """팀별 모멘텀 점수"""
    minute: int
    home_score: float
    away_score: float
    difference: float  # home - away


class TurningPoint(BaseModel):
    """변곡점"""
    minute: int
    team_advantage: str  # 'home' or 'away'
    change_type: str  # 'momentum_shift', 'attack_surge', 'defense_breakdown'
    indicators: List[str]  # 변화 지표 목록
    explanation: str  # 팬 친화형 설명
    metrics_before: TimeWindowMetrics
    metrics_after: TimeWindowMetrics

