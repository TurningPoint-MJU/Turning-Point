"""
경기 흐름 시각화 모듈
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
from matplotlib.table import Table
import numpy as np
import seaborn as sns
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
    모멘텀 곡선 및 변곡점 시각화 (개선된 버전)
    """
    # seaborn 스타일 설정
    sns.set_style("whitegrid")
    sns.set_palette("husl")
    plt.rcParams['font.size'] = 12
    plt.rcParams['font.weight'] = 'bold'
    
    # 한글 폰트 설정 (기존 함수 활용)
    setup_korean_font()
    
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
    
    # 그래프 생성 (개선된 크기)
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 모멘텀 곡선 (부드럽게 개선)
    ax.plot(minutes, momentum_scores, color='blue', lw=2.5, marker='o', 
            markersize=6, alpha=0.9, label='경기 흐름', zorder=3)
    
    # 영역 채우기 (더 세련되게)
    ax.fill_between(minutes, momentum_scores, 0, alpha=0.4, 
                    where=[m > 0 for m in momentum_scores], color='blue', zorder=1)
    ax.fill_between(minutes, momentum_scores, 0, alpha=0.4, 
                    where=[m < 0 for m in momentum_scores], color='red', zorder=1)
    
    # 0선 (더 명확하게)
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1.5, alpha=0.6, zorder=2)
    
    # 변곡점 마커 (노란색으로 강조)
    turning_x = []
    turning_y = []
    for tp in turning_points:
        # 해당 구간의 모멘텀 점수 찾기
        tp_minute_idx = tp.minute // 5
        if tp_minute_idx < len(momentum_scores):
            tp_momentum = momentum_scores[tp_minute_idx]
            turning_x.append(tp.minute)
            turning_y.append(tp_momentum)
            
            # 변곡점 주석 (화살표 포함)
            ax.annotate(
                f'{tp.minute}분',
                xy=(tp.minute, tp_momentum),
                xytext=(10, 20),
                textcoords='offset points',
                arrowprops=dict(arrowstyle='->', color='gold', lw=2),
                fontsize=12,
                ha='left',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='gold', alpha=0.9, edgecolor='black', linewidth=1.5),
                zorder=10
            )
    
    # 변곡점 scatter (노란색, 큰 마커)
    if turning_x:
        ax.scatter(turning_x, turning_y, c='gold', s=200, zorder=10, 
                  edgecolors='black', lw=2, marker='*', label='변곡점')
    
    # 레이블 및 제목 (최적화)
    ax.set_xlabel('시간(분)', fontsize=14, fontweight='bold')
    ax.set_ylabel('상대값', fontsize=14, fontweight='bold')
    ax.set_title(
        f'{match_data.home_team} vs {match_data.away_team} - 경기 흐름 분석',
        fontsize=16,
        fontweight='bold',
        pad=20
    )
    
    # 축 범위 및 틱 설정
    ax.set_xlim(-2, 92)
    ax.set_ylim(-110, 110)
    ax.set_xticks(np.arange(0, 91, 10))  # 10단위 간격
    
    # 그리드 (seaborn whitegrid가 자동으로 처리하지만 추가 조정)
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    
    # 범례 (최적화)
    home_patch = mpatches.Patch(color='blue', alpha=0.4, label=match_data.home_team)
    away_patch = mpatches.Patch(color='red', alpha=0.4, label=match_data.away_team)
    turning_patch = mpatches.Patch(color='gold', label='변곡점')
    ax.legend(handles=[home_patch, away_patch, turning_patch], 
             loc='upper left', frameon=True, fancybox=True, shadow=True, fontsize=11)
    
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
    - 실제 축구장 형태로 시각화
    - 패스 연결선, 슈팅 방향, 공격/수비 라인 표시
    - 주요 선수 위치 및 활동 영역 표시
    - 선수 간 패스 네트워크 분석
    
    Args:
        match_data: 경기 데이터
        turning_point: 변곡점 정보
        player_activities: 선수별 활동 정보
        save_path: 저장 경로
    """
    # 기본 히트맵 함수 호출 (matplotlib 사용)
    return plot_player_heatmap_basic(match_data, turning_point, player_activities, save_path)


def plot_player_heatmap_basic(
    match_data: MatchData,
    turning_point: TurningPoint,
    player_activities: Dict[str, PlayerActivity],
    save_path: Optional[str] = None
):
    """
    개선된 히트맵 시각화
    - 변곡점과 주요 선수 위치를 최우선으로 강조
    - 단순화된 색상 팔레트
    - 좌측 70% 필드, 우측 30% 통계/설명
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
    
    # 변곡점 관련 이벤트 추출 (변곡점 번호 표시용)
    turning_point_events = [
        e for e in window_events
        if abs(e.minute - turning_point.minute) <= 2
        and e.event_type in ['shot', 'pass', 'defense']
        and e.x is not None and e.y is not None
    ]
    # 중요도 순으로 정렬 (슈팅 > 패스 > 수비)
    event_priority = {'shot': 3, 'pass': 2, 'defense': 1}
    turning_point_events.sort(key=lambda e: (event_priority.get(e.event_type, 0), -abs(e.minute - turning_point.minute)), reverse=True)
    turning_point_events = turning_point_events[:5]  # 최대 5개만 표시
    
    # 그래프 생성 - GridSpec으로 레이아웃 구성 (70:30), 높이 증가 (모든 카드가 들어오도록)
    fig = plt.figure(figsize=(18, 13))
    fig.patch.set_facecolor('#f5f5f5')
    gs = gridspec.GridSpec(1, 2, width_ratios=[7, 3], hspace=0.1, wspace=0.08)
    
    # 히트맵 영역 (왼쪽 70%)
    ax = fig.add_subplot(gs[0])
    ax.set_facecolor('#22312b')  # 축구장 초록색 배경
    
    # 통계/설명 영역 (오른쪽 30%)
    ax_side = fig.add_subplot(gs[1])
    ax_side.set_facecolor('#ffffff')
    ax_side.axis('off')
    
    # 축구장 필드 그리기 (단순화)
    field_rect = mpatches.Rectangle((0, 0), 100, 100, linewidth=2, 
                                   edgecolor='white', facecolor='#22312b', zorder=0)
    ax.add_patch(field_rect)
    ax.plot([50, 50], [0, 100], 'w-', linewidth=1.5, alpha=0.6, zorder=1)
    center_circle = plt.Circle((50, 50), 10, fill=False, edgecolor='white', 
                              linewidth=1.5, alpha=0.6, zorder=1)
    ax.add_patch(center_circle)
    penalty_left = mpatches.Rectangle((0, 20), 20, 60, fill=False, 
                                     edgecolor='white', linewidth=1.5, alpha=0.6, zorder=1)
    ax.add_patch(penalty_left)
    penalty_right = mpatches.Rectangle((80, 20), 20, 60, fill=False, 
                                      edgecolor='white', linewidth=1.5, alpha=0.6, zorder=1)
    ax.add_patch(penalty_right)
    
    # 전체 히트맵 생성 (단색 그라디언트: 연한 노랑 → 진한 빨강)
    all_x, all_y = [], []
    for player_name, activity in player_activities.items():
        for x, y in activity.positions:
            if 0 <= x <= 100 and 0 <= y <= 100:
                all_x.append(x)
                all_y.append(y)
    
    if all_x and all_y:
        heatmap, xedges, yedges = np.histogram2d(all_x, all_y, bins=20, range=[[0, 100], [0, 100]])
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
        # 단색 그라디언트: YlOrRd (연한 노랑 → 진한 빨강)
        im = ax.imshow(heatmap.T, origin='lower', extent=extent, cmap='YlOrRd', 
                      alpha=0.25, interpolation='gaussian', zorder=2)
        cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
        cbar.set_label('활동량/위험도', fontsize=9, color='white')
        cbar.ax.tick_params(colors='white', labelsize=8)
    
    # 공격/수비 라인 계산 및 표시 (단순화)
    attack_events = [e for e in window_events if e.event_type in ['shot', 'pass'] and e.x is not None]
    defense_events = [e for e in window_events if e.event_type == 'defense' and e.x is not None]
    attack_line_x = np.mean([e.x for e in attack_events]) if attack_events else None
    defense_line_x = np.mean([e.x for e in defense_events]) if defense_events else None
    
    # 공격 라인 (차가운색: 파랑) - 한쪽만 텍스트 표시
    if attack_line_x:
        ax.plot([attack_line_x, attack_line_x], [0, 100], color='#4A90E2', 
               linestyle='-', linewidth=2.5, alpha=0.7, zorder=3)
        ax.text(attack_line_x, 3, '공격 라인↑', ha='center', va='bottom', 
                fontsize=8, color='#4A90E2', weight='bold', zorder=10)
    
    # 수비 라인 (차가운색: 청록) - 텍스트 제거, 전체 설명에 포함
    if defense_line_x:
        ax.plot([defense_line_x, defense_line_x], [0, 100], color='#50C878', 
               linestyle='-', linewidth=2.5, alpha=0.7, zorder=3)
    
    # 패스 표시 (단순화된 색상)
    passes = [e for e in window_events if e.event_type == 'pass' and e.x is not None and e.y is not None]
    successful_passes = [p for p in passes if p.success is True]
    failed_passes = [p for p in passes if p.success is False]
    
    # 성공한 패스: 얇은 파란 실선 화살표 (투명도 더 낮춤)
    for i, pass_event in enumerate(successful_passes[:20]):
        if pass_event.metadata and 'end_x' in pass_event.metadata and 'end_y' in pass_event.metadata:
            end_x = pass_event.metadata.get('end_x')
            end_y = pass_event.metadata.get('end_y')
            if end_x is not None and end_y is not None:
                # 앞쪽 10개는 조금 더 진하게, 나머지는 더 투명하게
                alpha = 0.35 if i < 10 else 0.2
                ax.annotate('', xy=(end_x, end_y), xytext=(pass_event.x, pass_event.y),
                           arrowprops=dict(arrowstyle='->', color='#4A90E2', alpha=alpha, 
                                         lw=0.7, mutation_scale=8), zorder=4)
    
    # 실패한 패스: 얇은 회색 실선 화살표 (투명도 더 낮춤)
    for pass_event in failed_passes[:10]:
        if pass_event.metadata and 'end_x' in pass_event.metadata and 'end_y' in pass_event.metadata:
            end_x = pass_event.metadata.get('end_x')
            end_y = pass_event.metadata.get('end_y')
            if end_x is not None and end_y is not None:
                ax.annotate('', xy=(end_x, end_y), xytext=(pass_event.x, pass_event.y),
                           arrowprops=dict(arrowstyle='->', color='#808080', alpha=0.25, 
                                         lw=0.7, mutation_scale=8), zorder=3)
    
    # 슈팅 표시 (따뜻한색: 주황/노랑, xG에 따라 굵기/크기 조정)
    # 전후반 및 홈/원정팀에 따라 슈팅 방향 결정
    shots = [e for e in window_events if e.event_type == 'shot' and e.x is not None and e.y is not None]
    for shot_event in shots:
        # 전반/후반 판단 (minute 기준)
        is_first_half = shot_event.minute < 45
        is_home_team = shot_event.team == match_data.home_team
        
        # 슈팅 방향 결정 (데이터는 항상 왼쪽→오른쪽으로 통일되어 있음)
        # 전반: 홈팀은 오른쪽(x=100), 원정팀은 왼쪽(x=0)
        # 후반: 홈팀은 왼쪽(x=0), 원정팀은 오른쪽(x=100)
        if is_first_half:
            goal_x = 100 if is_home_team else 0
        else:
            goal_x = 0 if is_home_team else 100
        goal_y = 50
        
        # xG에 따라 색상과 크기 결정 (따뜻한색 계열)
        if shot_event.xg:
            if shot_event.xg >= 0.3:
                color = '#FF6B35'  # 진한 주황
                line_width = 2.5
                circle_size = 120
            elif shot_event.xg >= 0.15:
                color = '#FFA500'  # 주황
                line_width = 2.0
                circle_size = 90
            else:
                color = '#FFD700'  # 노랑
                line_width = 1.5
                circle_size = 70
        else:
            color = '#FFA500'
            line_width = 2.0
            circle_size = 90
        
        # 슈팅 위치: 작은 원 또는 별 아이콘
        ax.scatter(shot_event.x, shot_event.y, s=circle_size, c=color, marker='o', 
                  edgecolors='white', linewidths=2, alpha=0.9, zorder=8)
        
        # 슈팅 방향: 두께 한 단계 줄임
        dx = goal_x - shot_event.x
        dy = goal_y - shot_event.y
        if np.sqrt(dx**2 + dy**2) > 2:
            ax.arrow(shot_event.x, shot_event.y, dx * 0.25, dy * 0.25,
                    head_width=2.0, head_length=2.0, fc=color, ec='white', 
                    alpha=0.7, zorder=7, linewidth=line_width)
    
    # 주요 선수 위치 표시 (작은 원 + 번호, 주요 선수만 강조)
    from src.analysis.player_analysis import get_key_players
    key_players = get_key_players(player_activities, top_n=5)
    
    # 색상 팔레트 단순화 (차가운색 계열)
    player_colors = ['#4A90E2', '#50C878', '#5B9BD5', '#6BB6FF', '#7EC8E3']
    player_data_for_table = []
    
    for idx, (player_name, activity, impact_score) in enumerate(key_players):
        if activity.positions and len(activity.positions) > 0:
            positions = np.array(activity.positions)
            avg_x = np.mean(positions[:, 0])
            avg_y = np.mean(positions[:, 1])
            
            color = player_colors[idx % len(player_colors)]
            
            # 선수별 히트맵 (보조 정보, 약하게)
            player_x = positions[:, 0]
            player_y = positions[:, 1]
            valid_mask = (player_x >= 0) & (player_x <= 100) & (player_y >= 0) & (player_y <= 100)
            player_x_valid = player_x[valid_mask]
            player_y_valid = player_y[valid_mask]
            
            if len(player_x_valid) > 0:
                player_heatmap, xedges, yedges = np.histogram2d(
                    player_x_valid, player_y_valid, 
                    bins=15, range=[[0, 100], [0, 100]]
                )
                from matplotlib.colors import LinearSegmentedColormap
                cmap_colors = ['#00000000', color]
                player_cmap = LinearSegmentedColormap.from_list(f'player_{idx}', cmap_colors, N=256)
                extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
                ax.imshow(player_heatmap.T, origin='lower', extent=extent, 
                         cmap=player_cmap, alpha=0.3, interpolation='gaussian', zorder=4)
            
            # 선수 위치 마커: 작은 원 + 번호 (주요 선수는 강조)
            is_key_player = idx < 3  # 상위 3명만 주요 선수로 간주
            if is_key_player:
                # 주요 선수: 굵은 테두리 + halo 효과
                halo_circle = plt.Circle((avg_x, avg_y), 4, fill=True, 
                                        color=color, alpha=0.2, zorder=8)
                ax.add_patch(halo_circle)
                marker_size = 180
                edge_width = 3
            else:
                marker_size = 120
                edge_width = 2
            
            ax.scatter(avg_x, avg_y, s=marker_size, c=color, edgecolors='white', 
                      linewidths=edge_width, alpha=0.95, zorder=9, marker='o')
            ax.text(avg_x, avg_y, str(idx + 1), ha='center', va='center',
                   fontsize=10 if is_key_player else 8, color='white', weight='bold', zorder=10)
            
            player_data_for_table.append({
                'num': idx + 1,
                'name': player_name,
                'shots': activity.shots,
                'passes': activity.passes,
                'defense': activity.defense_actions,
                'xg': activity.xg_contribution,
                'impact': impact_score,
                'color': color,
                'is_key': is_key_player
            })
    
    # 변곡점 이벤트 번호 표시 (①, ②, ③...)
    turning_point_numbers = ['①', '②', '③', '④', '⑤']
    turning_point_explanations = []
    event_icons = {'shot': '⚽', 'pass': '→', 'defense': '🛡️'}  # 미니 아이콘
    
    for idx, event in enumerate(turning_point_events[:5]):
        if event.x is not None and event.y is not None:
            # 변곡점 번호 마커 (강조색: 선홍 또는 보라)
            marker_color = '#FF1493'  # 선홍색
            ax.scatter(event.x, event.y, s=400, c=marker_color, marker='*', 
                      edgecolors='white', linewidths=2.5, alpha=0.95, zorder=11)
            ax.text(event.x, event.y, turning_point_numbers[idx], ha='center', va='center',
                   fontsize=16, color='white', weight='bold', zorder=12)
            
            # 설명 텍스트 생성 (미니 아이콘 포함)
            event_type_kr = {'shot': '슈팅', 'pass': '패스', 'defense': '수비'}[event.event_type]
            icon = event_icons.get(event.event_type, '•')
            player_name = event.metadata.get('player_name', '') if event.metadata else ''
            if player_name:
                explanation = f"{turning_point_numbers[idx]} {icon} {player_name}의 {event_type_kr}"
                if event.event_type == 'shot' and event.xg:
                    explanation += f" (xG: {event.xg:.2f})"
            else:
                explanation = f"{turning_point_numbers[idx]} {icon} {event_type_kr} 이벤트"
            turning_point_explanations.append({
                'text': explanation,
                'event_type': event.event_type
            })
    
    # 우측 영역 구성: 통일된 레이아웃 (범례, 표, 변곡점 설명, 전체 설명)
    # 통일된 카드 설정
    card_left = 0.05  # 좌측 정렬 기준선
    card_width = 0.9  # 가로 폭
    card_margin = 0.02  # 카드 간 세로 간격 (약 16-24px)
    
    y_pos = 0.96  # 상단 여백 조정
    
    # 제목 (상단, 여백 줄임, 카드와 정렬)
    situation_text = ""
    if turning_point.change_type == 'attack_surge':
        situation_text = "공격 급증"
    elif turning_point.change_type == 'defense_breakdown':
        situation_text = "수비 붕괴"
    else:
        situation_text = "모멘텀 변화"
    
    ax_side.text(card_left, y_pos, f'{target_team}', ha='left', va='top',
                fontsize=13, fontweight='bold', color='#333333', transform=ax_side.transAxes)
    y_pos -= 0.035
    ax_side.text(card_left, y_pos, f'{turning_point.minute}분 변곡점 ({situation_text})', 
                ha='left', va='top', fontsize=11, fontweight='bold', color='#666666',
                transform=ax_side.transAxes)
    y_pos -= 0.04
    
    # ① 범례 박스 (통일된 폭과 정렬, 여백 최소화)
    legend_items = [
        ('★', '변곡점 이벤트(슈팅/결정적 패스)'),
        ('●', '파란 원: 분석 대상 수비수'),
        ('●', '연두색 원: 분석 대상 공격수'),
        ('→', '파란 실선 화살표: 성공 패스'),
        ('→', '회색 점선 화살표: 비중 낮은/예상 패스'),
        ('→', '노란/주황 화살표: 슈팅 방향(xG에 따라 색상)'),
    ]
    
    # 여백 줄임: 높이 계산 (줄 간격과 상하 패딩 감소)
    legend_box_height = len(legend_items) * 0.020 + 0.05  # 0.025 -> 0.020, 0.08 -> 0.05
    legend_box = mpatches.FancyBboxPatch(
        (card_left, y_pos - legend_box_height), card_width, legend_box_height,
        boxstyle='round,pad=0.01', edgecolor='#cccccc', facecolor='white',  # pad 0.02 -> 0.01
        alpha=0.85, linewidth=1, transform=ax_side.transAxes, zorder=1
    )
    ax_side.add_patch(legend_box)
    
    # 범례 제목 (왼쪽 정렬, 여백 줄임, 폰트 크기 증가)
    ax_side.text(card_left + 0.02, y_pos - 0.005, '범례', ha='left', va='top',  # 0.01 -> 0.005
                fontsize=10, fontweight='bold', color='#333333', transform=ax_side.transAxes)
    
    # 범례 항목들 (줄 간격 줄임, 폰트 크기 증가, 핵심 키워드 볼드)
    for idx, (symbol, text) in enumerate(legend_items):
        # 심볼 색상 설정
        if '파란 원' in text:
            symbol_color = '#4A90E2'
        elif '연두색 원' in text:
            symbol_color = '#50C878'
        elif '파란 실선' in text:
            symbol_color = '#4A90E2'
        elif '회색 점선' in text:
            symbol_color = '#808080'
        elif '노란/주황' in text or '슈팅' in text:
            symbol_color = '#FFD700'  # 노란색
        else:
            symbol_color = '#FF1493'
        
        y_item = y_pos - 0.025 - idx * 0.020  # 0.04 -> 0.025, 0.025 -> 0.020
        ax_side.text(card_left + 0.05, y_item, symbol, ha='left', va='top',
                    fontsize=9, color=symbol_color, weight='bold', transform=ax_side.transAxes)
        
        # 핵심 키워드 볼드 처리 (간단한 방법: 키워드가 포함된 경우 전체를 볼드)
        has_keyword = any(kw in text for kw in ['변곡점', '성공', '슈팅', 'xG'])
        ax_side.text(card_left + 0.13, y_item, text, ha='left', va='top',
                    fontsize=8, color='#555555', weight='bold' if has_keyword else 'normal',
                    transform=ax_side.transAxes)
    
    y_pos -= legend_box_height + card_margin
    
    # ② 선수 통계 표 (통일된 폭과 정렬)
    if player_data_for_table:
        table_data = [['번호', '선수명', '슈팅', '패스', '수비', 'xG', '영향도']]
        for player in player_data_for_table:
            table_data.append([
                str(player['num']),
                player['name'][:8] + ('...' if len(player['name']) > 8 else ''),
                str(player['shots']),
                str(player['passes']),
                str(player['defense']),
                f"{player['xg']:.2f}",
                f"{player['impact']:.1f}"
            ])
        
        table_height = 0.28  # 높이 약간 조정
        # table의 bbox는 정확히 card_left와 card_width를 사용하여 정렬
        table = ax_side.table(cellText=table_data[1:], colLabels=table_data[0],
                            cellLoc='center', loc='center',
                            colWidths=[0.08, 0.22, 0.10, 0.10, 0.10, 0.15, 0.15],
                            bbox=[card_left, y_pos - table_height, card_width, table_height])
        
        table.auto_set_font_size(False)
        table.set_fontsize(8.5)  # 7.5 -> 8.5
        table.scale(1, 2.0)
        
        # 헤더 스타일 (채도 낮춤, 폰트 크기 증가)
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#e0e0e0')
            table[(0, i)].set_text_props(weight='bold', color='#333333', size=9)  # 크기 증가
            table[(0, i)].set_edgecolor('#cccccc')
            table[(0, i)].set_linewidth(1)
        
        # 데이터 행 스타일 (채도 낮춤, 핵심 수치 볼드, 폰트 크기 증가)
        for row_idx, player in enumerate(player_data_for_table, start=1):
            for col_idx in range(len(table_data[0])):
                cell = table[(row_idx, col_idx)]
                # 색상 채도 낮춤 (pastel 톤)
                from matplotlib.colors import to_rgb
                rgb = to_rgb(player['color'])
                pastel_color = tuple(0.7 * c + 0.3 for c in rgb)  # 밝게
                cell.set_facecolor(pastel_color)
                cell.set_alpha(0.6)
                cell.set_edgecolor('#dddddd')
                cell.set_linewidth(0.5)
                
                # 핵심 수치: 선수명(1), 영향도(6), xG(5), 슈팅(2)는 볼드
                is_key_metric = col_idx in [1, 5, 6]  # 선수명, xG, 영향도
                is_top_value = (col_idx == 6 and player['impact'] == max(p['impact'] for p in player_data_for_table)) or \
                              (col_idx == 2 and player['shots'] == max(p['shots'] for p in player_data_for_table)) or \
                              (col_idx == 5 and player['xg'] == max(p['xg'] for p in player_data_for_table))
                cell.set_text_props(weight='bold' if (is_key_metric or is_top_value) else 'normal', 
                                  color='#333333', size=9)  # 8 -> 9
        
        y_pos -= table_height + card_margin
    
    # ③ 변곡점 설명 카드 (통일된 폭과 정렬, 가장 중요한 텍스트 카드, 여백 최소화)
    if turning_point_explanations:
        # 제목 (왼쪽 정렬, 진한 색, 굵게, 카드와 정렬, 폰트 크기 증가)
        ax_side.text(card_left + 0.02, y_pos, '변곡점 설명', ha='left', va='top',
                    fontsize=12, fontweight='bold', color='#222222', transform=ax_side.transAxes)
        y_pos -= 0.02  # 여백 더 줄임
        
        # 카드 높이 계산 (여백 최소화 - 더 줄임)
        line_spacing = 0.025  # 줄 간격 더 줄임 (0.030 -> 0.025)
        padding = 0.04  # 상하 패딩 더 줄임 (0.06 -> 0.04)
        explanation_box_height = len(turning_point_explanations) * line_spacing + padding
        explanation_box = mpatches.FancyBboxPatch(
            (card_left, y_pos - explanation_box_height), card_width, explanation_box_height,
            boxstyle='round,pad=0.005', edgecolor='#CC0066', facecolor='#fff5f5',  # pad 더 줄임
            linewidth=2.5, transform=ax_side.transAxes, zorder=1  # 더 두꺼운 테두리
        )
        ax_side.add_patch(explanation_box)
        
        # 각 번호 설명을 한 줄로 요약 (폰트 크기 증가, 핵심 키워드 볼드)
        for idx, explanation_data in enumerate(turning_point_explanations):
            if idx >= len(turning_point_events):
                break
                
            event = turning_point_events[idx]
            event_type = explanation_data.get('event_type', event.event_type) if isinstance(explanation_data, dict) else event.event_type
            player_name = event.metadata.get('player_name', '') if event.metadata else ''
            
            # 핵심 정보만 추출하여 한 줄 요약 (예: "① 김진규 전진 패스로 슈팅 유도(xG 0.15)")
            event_type_kr = {'shot': '슈팅', 'pass': '패스', 'defense': '수비'}.get(event_type, '이벤트')
            
            if player_name:
                if event_type == 'shot' and event.xg:
                    summary = f"{player_name} {event_type_kr} (xG {event.xg:.2f})"
                elif event_type == 'pass':
                    summary = f"{player_name} {event_type_kr}"
                else:
                    summary = f"{player_name} {event_type_kr}"
            else:
                summary = f"{event_type_kr} 이벤트"
            
            # 번호와 함께 표시 (줄 간격 더 줄임, 폰트 크기 증가, 핵심 내용 볼드)
            final_text = f"{turning_point_numbers[idx]} {summary}"
            ax_side.text(card_left + 0.04, y_pos - 0.02 - idx * line_spacing, final_text, 
                       ha='left', va='top', fontsize=9, color='#333333', weight='bold',
                       transform=ax_side.transAxes)
        
        y_pos -= explanation_box_height + card_margin
    
    # ④ 전체 설명 카드 (통일된 폭과 정렬, 변곡점 설명보다 낮은 위계, 독립적으로 배치)
    if turning_point.explanation:
        # 제목 (왼쪽 정렬, 연한 색, 작은 폰트, 카드와 정렬, 폰트 크기 증가)
        ax_side.text(card_left + 0.02, y_pos, '전체 설명', ha='left', va='top',
                    fontsize=10, fontweight='bold', color='#666666', transform=ax_side.transAxes)
        y_pos -= 0.02  # 여백 더 줄임 (0.025 -> 0.02)
        
        # 수비/공격 라인 정보와 설명을 통합 (생략 없이 모두 출력)
        explanation_lines = []
        
        # 공격/수비 라인 정보와 설명을 한 문장으로 통합
        if attack_line_x and defense_line_x:
            # 라인 변화 방향 판단
            if attack_line_x > 50:
                line_text = f"공격 라인 {attack_line_x:.0f}, 수비 라인 {defense_line_x:.0f}으로 전진하며"
            else:
                line_text = f"공격 라인 {attack_line_x:.0f}, 수비 라인 {defense_line_x:.0f}으로 후퇴하며"
            
            # 기존 설명 텍스트 요약과 통합 (생략 없이)
            explanation_text = turning_point.explanation
            sentences = explanation_text.replace('。', '。\n').replace('. ', '.\n').split('\n')
            summary_text = ""
            for line in sentences[:1]:
                if line.strip():
                    summary_text = line.strip()
                    break
            
            if summary_text:
                combined_text = f"{line_text} {target_team}의 {summary_text}"
            else:
                combined_text = f"{line_text} {target_team}의 경기 흐름 변화"
            
            explanation_lines.append(combined_text)
        elif attack_line_x:
            explanation_lines.append(f"공격 라인 {attack_line_x:.0f}으로 전진")
        elif defense_line_x:
            explanation_lines.append(f"수비 라인 {defense_line_x:.0f}으로 후퇴")
        
        # 라인 정보가 없으면 설명만 (생략 없이)
        if not explanation_lines:
            explanation_text = turning_point.explanation
            sentences = explanation_text.replace('。', '。\n').replace('. ', '.\n').split('\n')
            for line in sentences[:1]:
                if line.strip():
                    explanation_lines.append(line.strip())
                    break
        
        # 텍스트 줄바꿈 처리 및 실제 표시될 줄 수 계산 (줄바꿈 기준 완화)
        line_height = 0.045  # 줄 간격
        padding = 0.03  # 상하 패딩 (0.05 -> 0.03, 여백 줄임)
        max_chars_per_line = 35  # 한 줄당 최대 문자 수 증가 (28 -> 35, 줄바꿈 덜 일찍)
        
        # 모든 텍스트를 줄바꿈 처리하여 실제 표시될 줄 리스트 생성 (생략 없이)
        display_lines = []
        for line in explanation_lines:
            if len(line) <= max_chars_per_line:
                display_lines.append(line)
            else:
                # 긴 텍스트를 여러 줄로 분할 (생략 없이)
                words = line.split()
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if len(test_line) <= max_chars_per_line:
                        current_line = test_line
                    else:
                        if current_line:
                            display_lines.append(current_line)
                        current_line = word
                        # 단어 자체가 너무 길어도 생략하지 않고 그대로 표시
                        if len(current_line) > max_chars_per_line:
                            display_lines.append(current_line)  # 생략 없이
                            current_line = ""
                if current_line:
                    display_lines.append(current_line)
        
        # 줄 수 제한 없음 (모든 내용 표시)
        
        # 카드 높이 계산 (실제 표시될 줄 수 기준)
        total_explanation_height = len(display_lines) * line_height + padding
        
        # 박스 생성 (패딩 줄임)
        explanation_box = mpatches.FancyBboxPatch(
            (card_left, y_pos - total_explanation_height), card_width, total_explanation_height,
            boxstyle='round,pad=0.01', edgecolor='#FFB6C1', facecolor='#f9f9f9',  # pad 0.02 -> 0.01
            linewidth=1.5, transform=ax_side.transAxes, zorder=1  # 얇은 테두리
        )
        ax_side.add_patch(explanation_box)
        
        # 내용 표시 (텍스트가 박스 안에 들어가도록 좌우 여백 확보, 생략 없이)
        text_left_margin = card_left + 0.04  # 좌측 여백
        
        for idx, line in enumerate(display_lines):
            # 생략 없이 모두 표시 (위 여백 줄임, 폰트 크기 증가, 핵심 키워드 볼드)
            # 핵심 키워드가 포함된 경우 전체 줄을 볼드 처리
            has_keyword = any(kw in line for kw in ['라인', '전진', '후퇴', '공격', '수비', target_team]) or \
                         any(char.isdigit() for char in line)
            ax_side.text(text_left_margin, y_pos - 0.02 - idx * line_height, line, 
                       ha='left', va='top', fontsize=8.5, 
                       color='#666666', weight='bold' if has_keyword else 'normal',
                       transform=ax_side.transAxes)
        
        y_pos -= total_explanation_height
    
    # 하단 여백 확인 및 조정 (모든 카드가 화면에 들어오도록)
    # y_pos가 0보다 작으면 상단 여백을 더 줄이거나 캔버스 높이를 늘려야 함
    if y_pos < 0.01:
        # 경고: 카드가 화면을 벗어날 수 있음
        pass
    
    # 필드 설정
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect('equal')
    
    # 골대에 팀 이름 표시 (전반/후반에 따라)
    is_first_half = turning_point.minute < 45
    home_team = match_data.home_team
    away_team = match_data.away_team
    
    # 전반: 왼쪽(x=0) = 홈팀, 오른쪽(x=100) = 원정팀
    # 후반: 왼쪽(x=0) = 원정팀, 오른쪽(x=100) = 홈팀
    if is_first_half:
        left_goal_team = home_team
        right_goal_team = away_team
    else:
        left_goal_team = away_team
        right_goal_team = home_team
    
    # 왼쪽 골대 상단에 팀 이름 표시 (필드 상단)
    ax.text(0, 99, left_goal_team, ha='left', va='top', 
           fontsize=10, color='white', weight='bold', alpha=0.9,
           bbox=dict(boxstyle='round,pad=0.4', facecolor='#333333', alpha=0.7, 
                    edgecolor='white', linewidth=1.5),
           zorder=22, transform=ax.transData)
    
    # 오른쪽 골대 상단에 팀 이름 표시 (필드 상단)
    ax.text(100, 99, right_goal_team, ha='right', va='top', 
           fontsize=10, color='white', weight='bold', alpha=0.9,
           bbox=dict(boxstyle='round,pad=0.4', facecolor='#333333', alpha=0.7, 
                    edgecolor='white', linewidth=1.5),
           zorder=22, transform=ax.transData)
    
    # x축 눈금 추가 (0부터 100까지 10단위로, 필드 하단에 표시)
    tick_interval = 10  # 10단위로 눈금 표시
    tick_positions = list(range(0, 101, tick_interval))
    
    # 필드 하단에 눈금선과 숫자 표시 (기존 레이아웃 유지)
    tick_y_position = 2  # 필드 하단에서 약간 위에 표시
    tick_length = 1.5  # 눈금선 길이
    
    for tick_x in tick_positions:
        # 눈금선 그리기
        ax.plot([tick_x, tick_x], [0, tick_length], 'w-', linewidth=1, alpha=0.6, zorder=20)
        # 숫자 표시
        ax.text(tick_x, tick_y_position + 1, str(tick_x), ha='center', va='bottom', 
               fontsize=7, color='white', alpha=0.8, weight='bold', zorder=21)
    
    # y축 눈금 추가 (0부터 100까지 10단위로, 필드 좌측에 표시)
    tick_x_position = 2  # 필드 좌측에서 약간 오른쪽에 표시
    
    for tick_y in tick_positions:
        # 눈금선 그리기
        ax.plot([0, tick_length], [tick_y, tick_y], 'w-', linewidth=1, alpha=0.6, zorder=20)
        # 숫자 표시
        ax.text(tick_x_position + 1, tick_y, str(tick_y), ha='left', va='center', 
               fontsize=7, color='white', alpha=0.8, weight='bold', zorder=21)
    
    # x, y축 설명 추가 (기존 규격 유지하며 필드 상단에 작게 표시)
    ax.text(50, 98, 'X축: 필드 너비 (0=왼쪽 골대, 100=오른쪽 골대)', 
           ha='center', va='top', fontsize=8, color='white', alpha=0.7, 
           bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.5, edgecolor='white', linewidth=1),
           zorder=20, transform=ax.transData)
    ax.text(50, 95, 'Y축: 필드 높이 (0=하단, 100=상단)', 
           ha='center', va='top', fontsize=8, color='white', alpha=0.7,
           bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.5, edgecolor='white', linewidth=1),
           zorder=20, transform=ax.transData)
    
    ax.axis('off')
    
    # tight_layout 대신 subplots_adjust 사용 (table과 호환성 문제 해결)
    # 우측 패널이 잘리지 않도록 여백 조정
    plt.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.02, wspace=0.08)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.15, facecolor='#f5f5f5')
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


