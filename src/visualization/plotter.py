"""
경기 흐름 시각화 모듈
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import numpy as np
from typing import List, Dict, Optional
from src.data.models import MatchData, MomentumScore, TurningPoint
from src.analysis.metrics import calculate_time_window_metrics, calculate_momentum_score
from src.analysis.player_analysis import PlayerActivity

# 한글 폰트 설정
def setup_korean_font():
    """한글 폰트 설정"""
    # macOS에서 사용 가능한 한글 폰트 목록
    korean_fonts = ['AppleGothic', 'NanumGothic', 'Malgun Gothic', 'NanumBarunGothic']
    
    # 시스템에 설치된 폰트 확인
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 사용 가능한 한글 폰트 찾기
    for font in korean_fonts:
        if font in available_fonts:
            plt.rcParams['font.family'] = font
            plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
            return font
    
    # 한글 폰트를 찾지 못한 경우 경고
    print("경고: 한글 폰트를 찾을 수 없습니다. 한글이 깨질 수 있습니다.")
    plt.rcParams['axes.unicode_minus'] = False
    return None

# 모듈 로드 시 한글 폰트 설정
setup_korean_font()


def plot_momentum_curve(
    match_data: MatchData,
    turning_points: List[TurningPoint],
    save_path: str = None
):
    """
    모멘텀 곡선 및 변곡점 시각화
    """
    events = match_data.events
    
    # 5분 단위 모멘텀 점수 계산
    minutes = []
    momentum_scores = []
    
    for minute in range(0, 90, 5):
        minute_end = min(minute + 5, 90)
        
        home_metrics = calculate_time_window_metrics(
            events, match_data.home_team, minute, minute_end
        )
        away_metrics = calculate_time_window_metrics(
            events, match_data.away_team, minute, minute_end
        )
        
        momentum = calculate_momentum_score(home_metrics, away_metrics)
        
        minutes.append(minute)
        momentum_scores.append(momentum)
    
    # 그래프 생성
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # 모멘텀 곡선
    ax.plot(minutes, momentum_scores, 'b-', linewidth=2, label='경기 흐름')
    ax.fill_between(minutes, momentum_scores, 0, alpha=0.3, where=[m > 0 for m in momentum_scores], color='blue')
    ax.fill_between(minutes, momentum_scores, 0, alpha=0.3, where=[m < 0 for m in momentum_scores], color='red')
    
    # 0선
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    
    # 변곡점 마커
    for tp in turning_points:
        # 해당 구간의 모멘텀 점수 찾기
        tp_minute_idx = tp.minute // 5
        if tp_minute_idx < len(momentum_scores):
            tp_momentum = momentum_scores[tp_minute_idx]
            color = 'green' if tp.team_advantage == 'home' else 'orange'
            ax.scatter(tp.minute, tp_momentum, s=200, color=color, 
                      marker='*', zorder=5, edgecolors='black', linewidths=1)
            ax.annotate(
                f'{tp.minute}분',
                xy=(tp.minute, tp_momentum),
                xytext=(tp.minute, tp_momentum + 15),
                fontsize=9,
                ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7)
            )
    
    # 레이블 및 제목
    ax.set_xlabel('경기 시간 (분)', fontsize=12)
    ax.set_ylabel('경기 흐름 점수', fontsize=12)
    ax.set_title(
        f'{match_data.home_team} vs {match_data.away_team} - 경기 흐름 분석',
        fontsize=14,
        fontweight='bold'
    )
    ax.set_xlim(-2, 92)
    ax.set_ylim(-110, 110)
    ax.grid(True, alpha=0.3)
    
    # 범례
    home_patch = mpatches.Patch(color='blue', alpha=0.3, label=match_data.home_team)
    away_patch = mpatches.Patch(color='red', alpha=0.3, label=match_data.away_team)
    turning_patch = mpatches.Patch(color='yellow', label='변곡점')
    ax.legend(handles=[home_patch, away_patch, turning_patch], loc='upper right')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
    plt.close()


def create_turning_point_details(
    turning_point: TurningPoint,
    team_name: str
) -> dict:
    """
    변곡점 상세 정보 딕셔너리 생성
    """
    return {
        'minute': turning_point.minute,
        'team': team_name,
        'change_type': turning_point.change_type,
        'indicators': turning_point.indicators,
        'explanation': turning_point.explanation,
        'metrics_before': {
            'possession': turning_point.metrics_before.possession,
            'shots': turning_point.metrics_before.shots,
            'xg': turning_point.metrics_before.xg,
            'pass_success_rate': turning_point.metrics_before.pass_success_rate,
        },
        'metrics_after': {
            'possession': turning_point.metrics_after.possession,
            'shots': turning_point.metrics_after.shots,
            'xg': turning_point.metrics_after.xg,
            'pass_success_rate': turning_point.metrics_after.pass_success_rate,
        }
    }


def plot_player_heatmap(
    match_data: MatchData,
    turning_point: TurningPoint,
    player_activities: Dict[str, PlayerActivity],
    save_path: Optional[str] = None
):
    """
    변곡점 시점의 상세한 선수 활동 히트맵 생성
    - 패스 연결선, 슈팅 방향, 공격/수비 라인 표시
    
    Args:
        match_data: 경기 데이터
        turning_point: 변곡점 정보
        player_activities: 선수별 활동 정보
        save_path: 저장 경로
    """
    if not player_activities:
        print("히트맵을 생성할 선수 데이터가 없습니다.")
        return
    
    # 변곡점 시점 주변 이벤트 추출
    time_window = 5
    minute_start = max(0, turning_point.minute - time_window)
    minute_end = min(90, turning_point.minute + time_window)
    
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
    
    # 필드 크기 설정
    field_width = 100
    field_height = 100
    
    # 히트맵 그리드 생성
    grid_size = 20
    heatmap_data = np.zeros((grid_size, grid_size))
    
    # 모든 선수의 위치를 히트맵에 누적
    for player_name, activity in player_activities.items():
        for x, y in activity.positions:
            if 0 <= x <= 100 and 0 <= y <= 100:
                grid_x = int(x / field_width * grid_size)
                grid_y = int(y / field_height * grid_size)
                grid_x = min(grid_x, grid_size - 1)
                grid_y = min(grid_y, grid_size - 1)
                heatmap_data[grid_y, grid_x] += 1
    
    # 그래프 생성
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 히트맵 플롯 (배경)
    im = ax.imshow(heatmap_data, cmap='YlOrRd', interpolation='gaussian', 
                   extent=[0, field_width, 0, field_height], aspect='auto', alpha=0.4)
    
    # 필드 라인 그리기
    ax.axvline(x=50, color='white', linestyle='--', linewidth=2, alpha=0.6)
    ax.add_patch(mpatches.Rectangle((0, 20), 20, 60, fill=False, edgecolor='white', linewidth=2, alpha=0.6))
    ax.add_patch(mpatches.Rectangle((80, 20), 20, 60, fill=False, edgecolor='white', linewidth=2, alpha=0.6))
    
    # 공격 라인 및 수비 라인 계산
    attack_events = [e for e in window_events if e.event_type in ['shot', 'pass'] and e.x is not None]
    defense_events = [e for e in window_events if e.event_type == 'defense' and e.x is not None]
    
    attack_line_x = np.mean([e.x for e in attack_events]) if attack_events else None
    defense_line_x = np.mean([e.x for e in defense_events]) if defense_events else None
    
    # 공격 라인 표시
    if attack_line_x:
        ax.axvline(x=attack_line_x, color='green', linestyle='-', linewidth=3, alpha=0.7, label='공격 라인')
        # 텍스트가 필드 안에 들어오도록 조정
        text_y = max(8, min(attack_line_x < 50 and 5 or 95, 92))
        ax.text(attack_line_x, text_y, f'공격 라인\n({attack_line_x:.1f})', 
                ha='center', va='bottom' if text_y < 50 else 'top', fontsize=9, color='green', weight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor='green', linewidth=1.5))
    
    # 수비 라인 표시
    if defense_line_x:
        ax.axvline(x=defense_line_x, color='red', linestyle='-', linewidth=3, alpha=0.7, label='수비 라인')
        # 텍스트가 필드 안에 들어오도록 조정
        text_y = max(8, min(defense_line_x < 50 and 5 or 95, 92))
        ax.text(defense_line_x, text_y, f'수비 라인\n({defense_line_x:.1f})', 
                ha='center', va='bottom' if text_y < 50 else 'top', fontsize=9, color='red', weight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor='red', linewidth=1.5))
    
    # 패스 연결선 그리기 (더 직관적으로)
    passes = [e for e in window_events if e.event_type == 'pass' and e.x is not None and e.y is not None]
    successful_passes = [p for p in passes if p.success is True]
    failed_passes = [p for p in passes if p.success is False]
    
    # 성공한 패스 (더 두껍고 진한 색상)
    for pass_event in successful_passes[:25]:  # 최대 25개
        if pass_event.metadata and 'end_x' in pass_event.metadata and 'end_y' in pass_event.metadata:
            end_x = pass_event.metadata.get('end_x')
            end_y = pass_event.metadata.get('end_y')
            if end_x is not None and end_y is not None:
                # 성공한 패스는 진한 청록색, 두꺼운 선
                ax.annotate('', xy=(end_x, end_y), xytext=(pass_event.x, pass_event.y),
                           arrowprops=dict(arrowstyle='->', color='#00CED1', alpha=0.8, lw=2.5, 
                                         mutation_scale=20, connectionstyle='arc3,rad=0.1'))
                # 시작점에 작은 원 표시
                ax.scatter(pass_event.x, pass_event.y, s=80, c='#00CED1', 
                          marker='o', edgecolors='white', linewidths=1, alpha=0.9, zorder=7)
    
    # 실패한 패스 (더 얇고 연한 색상)
    for pass_event in failed_passes[:15]:  # 최대 15개
        if pass_event.metadata and 'end_x' in pass_event.metadata and 'end_y' in pass_event.metadata:
            end_x = pass_event.metadata.get('end_x')
            end_y = pass_event.metadata.get('end_y')
            if end_x is not None and end_y is not None:
                # 실패한 패스는 주황색, 얇은 점선
                ax.annotate('', xy=(end_x, end_y), xytext=(pass_event.x, pass_event.y),
                           arrowprops=dict(arrowstyle='->', color='#FF8C00', alpha=0.5, lw=1.5,
                                         linestyle='--', mutation_scale=15))
                # 시작점에 작은 X 표시
                ax.scatter(pass_event.x, pass_event.y, s=60, c='#FF8C00', 
                          marker='x', linewidths=2, alpha=0.7, zorder=6)
    
    # 슈팅 방향 표시 (더 직관적으로)
    shots = [e for e in window_events if e.event_type == 'shot' and e.x is not None and e.y is not None]
    for shot_event in shots:
        # 슈팅은 골대 방향으로 (x 좌표가 증가하는 방향)
        goal_x = 100  # 골대 위치
        goal_y = 50   # 골대 중앙
        
        # xG에 따라 색상 및 크기 구분 (더 명확하게)
        if shot_event.xg:
            if shot_event.xg >= 0.3:
                color = '#DC143C'  # 진한 빨강
                size = 500
                edge_color = 'black'
                edge_width = 3
            elif shot_event.xg >= 0.15:
                color = '#FF6347'  # 토마토색
                size = 350
                edge_color = 'black'
                edge_width = 2.5
            else:
                color = '#FFD700'  # 금색
                size = 250
                edge_color = 'black'
                edge_width = 2
        else:
            color = '#FF6347'
            size = 350
            edge_color = 'black'
            edge_width = 2.5
        
        # 슈팅 위치 (더 큰 별 모양)
        ax.scatter(shot_event.x, shot_event.y, s=size, c=color, 
                  marker='*', edgecolors=edge_color, linewidths=edge_width, zorder=10, alpha=0.9)
        
        # 슈팅 방향 화살표 (더 두껍고 명확하게)
        dx = goal_x - shot_event.x
        dy = goal_y - shot_event.y
        arrow_length = min(15, np.sqrt(dx**2 + dy**2) * 0.4)
        if arrow_length > 2:
            ax.arrow(shot_event.x, shot_event.y, dx * 0.4, dy * 0.4,
                    head_width=3, head_length=3, fc=color, ec='black', 
                    alpha=0.8, zorder=9, linewidth=2.5)
        
        # xG 표시 (더 명확하게)
        if shot_event.xg:
            # 배경이 있는 텍스트 박스
            ax.text(shot_event.x, shot_event.y - 5, f'xG\n{shot_event.xg:.2f}',
                   ha='center', va='top', fontsize=8, color='black', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.95, 
                           edgecolor=color, linewidth=2))
    
    # 주요 선수 위치 및 활동 영역 표시
    from src.analysis.player_analysis import get_key_players
    key_players = get_key_players(player_activities, top_n=5)
    
    colors = ['blue', 'purple', 'brown', 'pink', 'olive']
    for idx, (player_name, activity, impact_score) in enumerate(key_players):
        if activity.positions and len(activity.positions) > 0:
            # 평균 위치
            positions = np.array(activity.positions)
            avg_x = np.mean(positions[:, 0])
            avg_y = np.mean(positions[:, 1])
            
            # 위치 분산 계산 (활동 영역 반경)
            if len(positions) > 1:
                std_x = np.std(positions[:, 0])
                std_y = np.std(positions[:, 1])
                # 활동 반경 (표준편차의 1.5배)
                radius = max(std_x, std_y) * 1.5
            else:
                radius = 3  # 기본 반경
            
            color = colors[idx % len(colors)]
            
            # 활동 영역을 반투명 원으로 표시
            circle = plt.Circle((avg_x, avg_y), radius, color=color, 
                              alpha=0.15, zorder=6, edgecolor=color, linewidth=1.5)
            ax.add_patch(circle)
            
            # 선수 위치 마커 (더 크게)
            ax.scatter(avg_x, avg_y, s=400, c=color, edgecolors='white', 
                      linewidths=3, zorder=8, alpha=0.95, marker='o')
            
            # 선수 이름 및 통계 (필드 안에 들어오도록 조정)
            stats = f"{activity.shots}슈팅/{activity.passes}패스"
            # 텍스트 위치를 필드 안으로 조정
            text_offset_y = -(radius + 3)
            text_y = avg_y + text_offset_y
            # 필드 밖으로 나가지 않도록 조정
            if text_y < 5:
                text_y = avg_y + radius + 3  # 위쪽으로
            if text_y > 95:
                text_y = avg_y - (radius + 3)  # 아래쪽으로
            
            ax.annotate(
                f'{player_name[:8]}\n{stats}',
                xy=(avg_x, avg_y),
                xytext=(avg_x, text_y),
                fontsize=8,
                ha='center',
                va='top' if text_y > avg_y else 'bottom',
                color='white',
                weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=color, alpha=0.9, 
                        edgecolor='white', linewidth=1.5)
            )
    
    # 범례 (더 명확하게)
    legend_elements = [
        mpatches.Patch(color='green', alpha=0.7, label='공격 라인'),
        mpatches.Patch(color='red', alpha=0.7, label='수비 라인'),
        plt.Line2D([0], [0], color='#00CED1', linewidth=2.5, label='성공한 패스 (→)'),
        plt.Line2D([0], [0], color='#FF8C00', linewidth=1.5, linestyle='--', label='실패한 패스 (→)'),
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#DC143C', 
                  markersize=12, markeredgecolor='black', markeredgewidth=2, label='슈팅 (xG 높음 ≥0.3)'),
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#FF6347', 
                  markersize=10, markeredgecolor='black', markeredgewidth=2, label='슈팅 (xG 중간 ≥0.15)'),
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#FFD700', 
                  markersize=8, markeredgecolor='black', markeredgewidth=1.5, label='슈팅 (xG 낮음 <0.15)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.95, 
             edgecolor='black', fancybox=True, shadow=True)
    
    # 색상바
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('선수 활동 빈도', fontsize=10)
    
    # 레이블 및 제목
    situation_text = ""
    if turning_point.change_type == 'attack_surge':
        situation_text = "공격 급증"
    elif turning_point.change_type == 'defense_breakdown':
        situation_text = "수비 붕괴"
    else:
        situation_text = "모멘텀 변화"
    
    ax.set_xlabel('필드 너비 (0-100) → 골대 방향', fontsize=12)
    ax.set_ylabel('필드 높이 (0-100)', fontsize=12)
    ax.set_title(
        f'{target_team} - {turning_point.minute}분 변곡점 ({situation_text})\n'
        f'패스 연결, 슈팅 방향, 공격/수비 라인 분석',
        fontsize=14,
        fontweight='bold'
    )
    # 필드 범위를 약간 확장하여 텍스트가 잘리지 않도록
    ax.set_xlim(-2, field_width + 2)
    ax.set_ylim(-2, field_height + 2)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.2, linestyle='--')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.2)
    else:
        plt.show()
    
    plt.close()


def plot_player_movements(
    match_data: MatchData,
    turning_point: TurningPoint,
    player_activities: Dict[str, PlayerActivity],
    top_n: int = 5,
    save_path: Optional[str] = None
):
    """
    주요 선수들의 움직임 패턴 시각화
    
    Args:
        match_data: 경기 데이터
        turning_point: 변곡점 정보
        player_activities: 선수별 활동 정보
        top_n: 표시할 상위 선수 수
        save_path: 저장 경로
    """
    if not player_activities:
        print("시각화할 선수 데이터가 없습니다.")
        return
    
    # 영향도가 높은 선수 선택
    from src.analysis.player_analysis import get_key_players
    key_players = get_key_players(player_activities, top_n)
    
    if not key_players:
        print("주요 선수를 찾을 수 없습니다.")
        return
    
    # 서브플롯 생성
    n_players = len(key_players)
    cols = min(3, n_players)
    rows = (n_players + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
    if n_players == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    target_team = (
        match_data.home_team if turning_point.team_advantage == 'home'
        else match_data.away_team
    )
    
    for idx, (player_name, activity, impact_score) in enumerate(key_players):
        ax = axes[idx]
        
        # 선수 위치 히트맵 (단순하게)
        if activity.positions:
            positions = np.array(activity.positions)
            x_positions = positions[:, 0]
            y_positions = positions[:, 1]
            
            # 히트맵 그리드 생성
            grid_size = 20
            heatmap_data = np.zeros((grid_size, grid_size))
            
            for x, y in zip(x_positions, y_positions):
                if 0 <= x <= 100 and 0 <= y <= 100:
                    grid_x = int(x / 100 * grid_size)
                    grid_y = int(y / 100 * grid_size)
                    grid_x = min(grid_x, grid_size - 1)
                    grid_y = min(grid_y, grid_size - 1)
                    heatmap_data[grid_y, grid_x] += 1
            
            # 히트맵 플롯
            im = ax.imshow(heatmap_data, cmap='YlOrRd', interpolation='gaussian',
                          extent=[0, 100, 0, 100], aspect='auto', alpha=0.6)
            
            # 이벤트 타입별 마커 (더 명확하게)
            shots = [e for e in activity.events if e.event_type == 'shot' and e.x is not None and e.y is not None]
            successful_passes = [e for e in activity.events if e.event_type == 'pass' and e.success is True and e.x is not None and e.y is not None]
            failed_passes = [e for e in activity.events if e.event_type == 'pass' and e.success is False and e.x is not None and e.y is not None]
            defense_actions = [e for e in activity.events if e.event_type == 'defense' and e.x is not None and e.y is not None]
            
            # 슈팅 (별 모양, 빨강)
            if shots:
                shot_x = [e.x for e in shots]
                shot_y = [e.y for e in shots]
                ax.scatter(shot_x, shot_y, c='red', marker='*', s=200, 
                          edgecolors='black', linewidths=1.5, alpha=0.9, zorder=10, label='슈팅')
            
            # 성공한 패스 (파란 사각형)
            if successful_passes:
                pass_x = [e.x for e in successful_passes]
                pass_y = [e.y for e in successful_passes]
                ax.scatter(pass_x, pass_y, c='#00CED1', marker='s', s=80, 
                          edgecolors='white', linewidths=1, alpha=0.8, zorder=9, label='성공한 패스')
            
            # 실패한 패스 (주황 X)
            if failed_passes:
                fail_x = [e.x for e in failed_passes]
                fail_y = [e.y for e in failed_passes]
                ax.scatter(fail_x, fail_y, c='#FF8C00', marker='x', s=100, 
                          linewidths=2, alpha=0.7, zorder=8, label='실패한 패스')
            
            # 수비 액션 (초록 삼각형)
            if defense_actions:
                def_x = [e.x for e in defense_actions]
                def_y = [e.y for e in defense_actions]
                ax.scatter(def_x, def_y, c='green', marker='^', s=80, 
                          edgecolors='white', linewidths=1, alpha=0.8, zorder=8, label='수비')
        
        # 필드 라인
        ax.axvline(x=50, color='white', linestyle='--', linewidth=1.5, alpha=0.6)
        ax.add_patch(mpatches.Rectangle((0, 20), 20, 60, fill=False, 
                                       edgecolor='white', linewidth=1.5, alpha=0.6))
        ax.add_patch(mpatches.Rectangle((80, 20), 20, 60, fill=False, 
                                       edgecolor='white', linewidth=1.5, alpha=0.6))
        
        # 제목
        stats_text = (
            f"슈팅: {activity.shots} | "
            f"패스: {activity.passes} | "
            f"수비: {activity.defense_actions}\n"
            f"xG 기여: {activity.xg_contribution:.2f} | "
            f"영향도: {impact_score:.1f}"
        )
        ax.set_title(f'{player_name}\n{stats_text}', fontsize=10, fontweight='bold')
        ax.set_xlabel('필드 너비', fontsize=9)
        ax.set_ylabel('필드 높이', fontsize=9)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.invert_yaxis()
        ax.grid(True, alpha=0.2, linestyle='--')
        
        # 범례 추가 (첫 번째 서브플롯에만)
        if idx == 0:
            legend_elements = [
                plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='red', 
                          markersize=10, markeredgecolor='black', markeredgewidth=1, label='슈팅'),
                plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='#00CED1', 
                          markersize=8, markeredgecolor='white', label='성공한 패스'),
                plt.Line2D([0], [0], marker='x', color='#FF8C00', linewidth=2, 
                          markersize=8, label='실패한 패스'),
                plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='green', 
                          markersize=8, markeredgecolor='white', label='수비'),
            ]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=8, 
                    framealpha=0.9, edgecolor='black')
    
    # 빈 서브플롯 제거
    for idx in range(n_players, len(axes)):
        fig.delaxes(axes[idx])
    
    fig.suptitle(
        f'{target_team} - {turning_point.minute}분 변곡점 주요 선수 움직임',
        fontsize=14,
        fontweight='bold',
        y=0.995
    )
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
    plt.close()


