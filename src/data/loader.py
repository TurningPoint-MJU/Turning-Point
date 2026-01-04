"""
K리그 실제 데이터 로더 및 변환 모듈
"""
import pandas as pd
from datetime import datetime
from typing import Optional, List
from src.data.models import MatchData, MatchEvent


def load_match_info(match_info_path: str) -> pd.DataFrame:
    """경기 메타 정보 로드"""
    return pd.read_csv(match_info_path)


def load_raw_data(raw_data_path: str, game_id: Optional[int] = None) -> pd.DataFrame:
    """원본 경기 데이터 로드"""
    df = pd.read_csv(raw_data_path)
    if game_id:
        df = df[df['game_id'] == game_id]
    return df


def convert_time_to_minute(period_id: int, time_seconds: float) -> int:
    """
    period_id와 time_seconds를 경기 시간(분)으로 변환
    - period_id 1: 전반 (0-45분)
    - period_id 2: 후반 (45-90분)
    """
    if period_id == 1:
        return int(time_seconds / 60)
    elif period_id == 2:
        return 45 + int(time_seconds / 60)
    else:
        return int(time_seconds / 60)


def map_event_type(type_name: str) -> str:
    """
    K리그 이벤트 타입을 우리 모델의 event_type으로 매핑
    """
    type_mapping = {
        'Shot': 'shot',
        'Pass': 'pass',
        'Carry': 'pass',  # Carry도 패스로 간주
        'Block': 'defense',
        'Tackle': 'defense',
        'Interception': 'defense',
        'Intervention': 'defense',
        'Clearance': 'defense',
        'Recovery': 'defense',
        'Duel': 'defense',
        'Goal Kick': 'possession',
        'Throw-In': 'possession',
        'Pass Received': 'possession',
        'Offside': 'possession',
        'Out': 'possession',
    }
    return type_mapping.get(type_name, 'possession')


def estimate_xg_from_shot(shot_data: pd.Series) -> float:
    """
    슈팅 데이터로부터 xG 추정
    실제 xG 데이터가 없으므로 위치와 결과로 추정
    """
    x = shot_data.get('start_x', 50.0)
    y = shot_data.get('start_y', 50.0)
    result = shot_data.get('result_name', '')
    
    # 골대까지의 거리 계산 (x 좌표가 클수록 골대에 가까움)
    distance_to_goal = 100 - x
    
    # 기본 xG (거리 기반)
    base_xg = max(0.01, (100 - distance_to_goal) / 100 * 0.5)
    
    # 결과에 따른 조정
    if result == 'Goal':
        return 1.0
    elif result == 'On Target':
        return base_xg * 0.8
    elif result == 'Off Target':
        return base_xg * 0.3
    else:
        return base_xg * 0.1


def is_forward_pass(start_x: float, end_x: float) -> bool:
    """전진 패스 여부 판단 (x 좌표 증가)"""
    if pd.isna(start_x) or pd.isna(end_x):
        return False
    return end_x > start_x


def convert_kleague_to_match_data(
    raw_data: pd.DataFrame,
    match_info: pd.DataFrame,
    game_id: int
) -> MatchData:
    """
    K리그 원본 데이터를 MatchData로 변환
    """
    # 경기 정보 추출
    match_row = match_info[match_info['game_id'] == game_id].iloc[0]
    
    home_team = match_row['home_team_name_ko']
    away_team = match_row['away_team_name_ko']
    home_score = int(match_row['home_score'])
    away_score = int(match_row['away_score'])
    game_date = pd.to_datetime(match_row['game_date'])
    
    # 해당 경기 데이터만 필터링
    game_data = raw_data[raw_data['game_id'] == game_id].copy()
    
    # 이벤트 변환
    events: List[MatchEvent] = []
    
    # 패스 연결 정보를 추출하기 위해 Pass Received 이벤트를 미리 수집
    pass_received_events = {}
    for idx, row in game_data.iterrows():
        if row['type_name'] == 'Pass Received':
            time_key = (row['period_id'], row['time_seconds'])
            pass_received_events[time_key] = {
                'player_name': row.get('player_name_ko', ''),
                'x': row.get('start_x'),
                'y': row.get('start_y'),
            }
    
    for idx, row in game_data.iterrows():
        # 시간 변환
        minute = convert_time_to_minute(row['period_id'], row['time_seconds'])
        
        # 팀명
        team = row['team_name_ko']
        
        # 이벤트 타입 매핑
        event_type = map_event_type(row['type_name'])
        
        # Pass Received는 건너뛰기 (패스 이벤트에 통합)
        if row['type_name'] == 'Pass Received':
            continue
        
        # 성공 여부
        result = row.get('result_name', '')
        success = None
        if result == 'Successful':
            success = True
        elif result == 'Unsuccessful':
            success = False
        elif result in ['On Target', 'Goal']:
            success = True
        elif result == 'Off Target':
            success = False
        
        # 좌표 (0-100 범위로 정규화되어 있음)
        x = row.get('start_x')
        y = row.get('start_y')
        
        # xG 계산 (슈팅인 경우)
        xg = None
        if event_type == 'shot':
            xg = estimate_xg_from_shot(row)
        
        # 패스인 경우: 패스를 받은 선수 정보 찾기
        receiver_name = None
        if event_type == 'pass':
            # Pass Received 이벤트 찾기 (시간이 약간 뒤에 있음, 0.5초 이내)
            time_key = (row['period_id'], row['time_seconds'])
            # 정확한 시간 또는 약간 뒤의 시간 찾기
            for offset in [0.0, 0.5, 1.0, 1.5, 2.0]:
                check_time = (row['period_id'], row['time_seconds'] + offset)
                if check_time in pass_received_events:
                    received_info = pass_received_events[check_time]
                    # 같은 팀이고 좌표가 비슷한지 확인
                    if received_info['player_name']:
                        receiver_name = received_info['player_name']
                        break
        
        # 전진 패스 여부 (패스인 경우)
        if event_type == 'pass' and x is not None:
            end_x = row.get('end_x')
            if end_x is not None:
                # 전진 패스는 별도로 표시하지 않고, metrics 계산 시 사용
                pass
        
        event = MatchEvent(
            minute=minute,
            team=team,
            event_type=event_type,
            x=x if not pd.isna(x) else None,
            y=y if not pd.isna(y) else None,
            success=success,
            xg=xg,
            metadata={
                'type_name': row['type_name'],
                'result_name': result,
                'player_name': row.get('player_name_ko', ''),
                'end_x': row.get('end_x'),
                'end_y': row.get('end_y'),
                'receiver_name': receiver_name,  # 패스를 받은 선수 이름 추가
            }
        )
        
        events.append(event)
    
    # 시간순 정렬
    events.sort(key=lambda e: e.minute)
    
    return MatchData(
        match_id=str(game_id),
        home_team=home_team,
        away_team=away_team,
        match_date=game_date,
        events=events,
        final_score={'home': home_score, 'away': away_score}
    )


def load_match_by_id(
    raw_data_path: str,
    match_info_path: str,
    game_id: int
) -> MatchData:
    """
    경기 ID로 경기 데이터 로드 및 변환
    """
    raw_data = load_raw_data(raw_data_path, game_id)
    match_info = load_match_info(match_info_path)
    
    return convert_kleague_to_match_data(raw_data, match_info, game_id)


def list_available_matches(match_info_path: str) -> pd.DataFrame:
    """
    사용 가능한 경기 목록 반환
    """
    match_info = load_match_info(match_info_path)
    return match_info[['game_id', 'game_date', 'home_team_name_ko', 'away_team_name_ko', 
                       'home_score', 'away_score']].copy()

