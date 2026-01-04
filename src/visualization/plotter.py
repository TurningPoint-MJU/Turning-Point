"""
경기 흐름 시각화 모듈
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
from matplotlib.table import Table
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
    기본 matplotlib를 사용한 히트맵
    실제 축구장 형태로 개선된 버전
    - 선수 활동 히트맵
    - 패스 네트워크 분석 (주요 패스 경로 표시)
    - 슈팅 방향 및 xG 표시
    - 공격/수비 라인 표시
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
    
    # 그래프 생성 - GridSpec으로 히트맵과 선수 정보 표 분리
    fig = plt.figure(figsize=(20, 11))
    fig.patch.set_facecolor('#22312b')
    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1], hspace=0.1, wspace=0.05)
    
    # 히트맵 영역 (왼쪽)
    ax = fig.add_subplot(gs[0])
    ax.set_facecolor('#22312b')  # 축구장 초록색 배경
    
    # 선수 정보 표 영역 (오른쪽)
    ax_table = fig.add_subplot(gs[1])
    ax_table.set_facecolor('#2d3a35')
    ax_table.axis('off')
    
    # 축구장 필드 그리기
    # 외곽선
    field_rect = mpatches.Rectangle((0, 0), 100, 100, linewidth=3, 
                                   edgecolor='white', facecolor='#22312b', zorder=0)
    ax.add_patch(field_rect)
    
    # 중앙선
    ax.plot([50, 50], [0, 100], 'w-', linewidth=2, alpha=0.8, zorder=1)
    # 중앙 서클
    center_circle = plt.Circle((50, 50), 10, fill=False, edgecolor='white', 
                              linewidth=2, alpha=0.8, zorder=1)
    ax.add_patch(center_circle)
    
    # 페널티 박스 (왼쪽)
    penalty_left = mpatches.Rectangle((0, 20), 20, 60, fill=False, 
                                     edgecolor='white', linewidth=2, alpha=0.8, zorder=1)
    ax.add_patch(penalty_left)
    # 골 에어리어 (왼쪽)
    goal_area_left = mpatches.Rectangle((0, 35), 8, 30, fill=False, 
                                       edgecolor='white', linewidth=2, alpha=0.8, zorder=1)
    ax.add_patch(goal_area_left)
    
    # 페널티 박스 (오른쪽)
    penalty_right = mpatches.Rectangle((80, 20), 20, 60, fill=False, 
                                      edgecolor='white', linewidth=2, alpha=0.8, zorder=1)
    ax.add_patch(penalty_right)
    # 골 에어리어 (오른쪽)
    goal_area_right = mpatches.Rectangle((92, 35), 8, 30, fill=False, 
                                        edgecolor='white', linewidth=2, alpha=0.8, zorder=1)
    ax.add_patch(goal_area_right)
    
    # 모든 선수의 위치 데이터 수집 (전체 히트맵용)
    all_x = []
    all_y = []
    for player_name, activity in player_activities.items():
        for x, y in activity.positions:
            if 0 <= x <= 100 and 0 <= y <= 100:
                all_x.append(x)
                all_y.append(y)
    
    # 전체 히트맵 생성 (배경용, 약하게)
    if all_x and all_y:
        # 2D 히스토그램으로 히트맵 생성
        heatmap, xedges, yedges = np.histogram2d(all_x, all_y, bins=25, range=[[0, 100], [0, 100]])
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
        im = ax.imshow(heatmap.T, origin='lower', extent=extent, cmap='YlOrRd', 
                      alpha=0.3, interpolation='gaussian', zorder=2)
        
        # 색상바
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('전체 활동 빈도', fontsize=11, color='white')
        cbar.ax.tick_params(colors='white')
    
    # 공격 라인 및 수비 라인 계산
    attack_events = [e for e in window_events if e.event_type in ['shot', 'pass'] and e.x is not None]
    defense_events = [e for e in window_events if e.event_type == 'defense' and e.x is not None]
    
    attack_line_x = np.mean([e.x for e in attack_events]) if attack_events else None
    defense_line_x = np.mean([e.x for e in defense_events]) if defense_events else None
    
    # 공격 라인 표시
    if attack_line_x:
        ax.plot([attack_line_x, attack_line_x], [0, 100], color='green', 
               linestyle='-', linewidth=4, alpha=0.8, zorder=3)
        ax.text(attack_line_x, 5, f'공격 라인\n{attack_line_x:.1f}', 
                ha='center', va='bottom', fontsize=10, color='green', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.95, 
                         edgecolor='green', linewidth=2), zorder=10)
    
    # 수비 라인 표시
    if defense_line_x:
        ax.plot([defense_line_x, defense_line_x], [0, 100], color='red', 
               linestyle='-', linewidth=4, alpha=0.8, zorder=3)
        ax.text(defense_line_x, 95, f'수비 라인\n{defense_line_x:.1f}', 
                ha='center', va='top', fontsize=10, color='red', weight='bold',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.95, 
                         edgecolor='red', linewidth=2), zorder=10)
    
    # 패스 네트워크 분석
    from src.analysis.player_analysis import analyze_pass_network, get_player_average_positions
    pass_connections, top_pass_paths = analyze_pass_network(
        match_data, turning_point, player_activities, time_window
    )
    player_positions = get_player_average_positions(player_activities)
    
    # 패스 연결선 그리기
    passes = [e for e in window_events if e.event_type == 'pass' and e.x is not None and e.y is not None]
    successful_passes = [p for p in passes if p.success is True]
    failed_passes = [p for p in passes if p.success is False]
    
    # 주요 패스 경로 (상위 5개) - 두꺼운 선으로 표시
    if top_pass_paths and player_positions:
        for passer, receiver, count in top_pass_paths[:5]:
            if passer in player_positions and receiver in player_positions:
                passer_pos = player_positions[passer]
                receiver_pos = player_positions[receiver]
                
                # 패스 빈도에 따라 선 두께 조정
                line_width = min(5 + count * 0.5, 8)
                alpha = min(0.9, 0.5 + count * 0.1)
                
                # 주요 패스 경로는 노란색으로 표시
                ax.plot([passer_pos[0], receiver_pos[0]], [passer_pos[1], receiver_pos[1]],
                       color='yellow', linewidth=line_width, alpha=alpha, zorder=5,
                       linestyle='-', label='주요 패스 경로' if (passer, receiver) == top_pass_paths[0][:2] else '')
                
                # 화살표 추가
                dx = receiver_pos[0] - passer_pos[0]
                dy = receiver_pos[1] - passer_pos[1]
                length = np.sqrt(dx**2 + dy**2)
                if length > 0:
                    ax.arrow(passer_pos[0] + dx * 0.7, passer_pos[1] + dy * 0.7,
                            dx * 0.2, dy * 0.2,
                            head_width=2, head_length=2, fc='yellow', ec='yellow',
                            alpha=alpha, zorder=5, linewidth=line_width * 0.8)
                
                # 패스 횟수 표시
                mid_x = (passer_pos[0] + receiver_pos[0]) / 2
                mid_y = (passer_pos[1] + receiver_pos[1]) / 2
                ax.text(mid_x, mid_y, str(count), ha='center', va='center',
                       fontsize=8, color='white', weight='bold',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', 
                               alpha=0.8, edgecolor='black', linewidth=1), zorder=12)
    
    # 일반 성공한 패스 (주요 경로가 아닌 것들)
    for pass_event in successful_passes[:25]:
        if pass_event.metadata and 'end_x' in pass_event.metadata and 'end_y' in pass_event.metadata:
            end_x = pass_event.metadata.get('end_x')
            end_y = pass_event.metadata.get('end_y')
            passer = pass_event.metadata.get('player_name', '')
            receiver = pass_event.metadata.get('receiver_name', '')
            
            # 주요 패스 경로가 아닌 경우만 표시
            if end_x is not None and end_y is not None:
                is_major_path = False
                if passer and receiver and (passer, receiver) in pass_connections:
                    if (passer, receiver, pass_connections[(passer, receiver)]) in top_pass_paths[:5]:
                        is_major_path = True
                
                if not is_major_path:
                    ax.annotate('', xy=(end_x, end_y), xytext=(pass_event.x, pass_event.y),
                               arrowprops=dict(arrowstyle='->', color='#00CED1', alpha=0.6, 
                                             lw=1.5, mutation_scale=15))
                    ax.scatter(pass_event.x, pass_event.y, s=60, c='#00CED1', 
                              marker='o', edgecolors='white', linewidths=1, alpha=0.7, zorder=6)
    
    # 실패한 패스
    for pass_event in failed_passes[:15]:
        if pass_event.metadata and 'end_x' in pass_event.metadata and 'end_y' in pass_event.metadata:
            end_x = pass_event.metadata.get('end_x')
            end_y = pass_event.metadata.get('end_y')
            if end_x is not None and end_y is not None:
                ax.plot([pass_event.x, end_x], [pass_event.y, end_y], 
                       color='#FF8C00', linestyle='--', linewidth=1.5, alpha=0.5, zorder=4)
                ax.scatter(pass_event.x, pass_event.y, s=80, c='#FF8C00', 
                          marker='x', linewidths=2, alpha=0.7, zorder=5)
    
    # 슈팅 표시
    shots = [e for e in window_events if e.event_type == 'shot' and e.x is not None and e.y is not None]
    for shot_event in shots:
        goal_x = 100
        goal_y = 50
        
        if shot_event.xg:
            if shot_event.xg >= 0.3:
                color = '#DC143C'
                size = 600
            elif shot_event.xg >= 0.15:
                color = '#FF6347'
                size = 400
            else:
                color = '#FFD700'
                size = 300
        else:
            color = '#FF6347'
            size = 400
        
        ax.scatter(shot_event.x, shot_event.y, s=size, c=color, marker='*', 
                  edgecolors='black', linewidths=2.5, alpha=0.9, zorder=8)
        
        # 슈팅 방향 화살표
        dx = goal_x - shot_event.x
        dy = goal_y - shot_event.y
        if np.sqrt(dx**2 + dy**2) > 2:
            ax.arrow(shot_event.x, shot_event.y, dx * 0.3, dy * 0.3,
                    head_width=3, head_length=3, fc=color, ec='black', 
                    alpha=0.8, zorder=7, linewidth=2.5)
        
        # xG 표시는 작게 (필드 가림 최소화)
        if shot_event.xg:
            ax.text(shot_event.x, shot_event.y - 4, f'{shot_event.xg:.2f}',
                   ha='center', va='top', fontsize=7, color='white', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor=color, alpha=0.9, 
                           edgecolor='black', linewidth=1), zorder=10)
    
    # 주요 선수 위치 및 활동 영역 표시 (개별 히트맵)
    from src.analysis.player_analysis import get_key_players
    key_players = get_key_players(player_activities, top_n=5)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    player_data_for_table = []
    
    for idx, (player_name, activity, impact_score) in enumerate(key_players):
        if activity.positions and len(activity.positions) > 0:
            positions = np.array(activity.positions)
            avg_x = np.mean(positions[:, 0])
            avg_y = np.mean(positions[:, 1])
            
            color = colors[idx % len(colors)]
            
            # 각 선수별 개별 히트맵 생성
            player_x = positions[:, 0]
            player_y = positions[:, 1]
            
            # 유효한 위치만 필터링
            valid_mask = (player_x >= 0) & (player_x <= 100) & (player_y >= 0) & (player_y <= 100)
            player_x_valid = player_x[valid_mask]
            player_y_valid = player_y[valid_mask]
            
            if len(player_x_valid) > 0:
                # 선수별 히트맵 데이터 생성
                player_heatmap, xedges, yedges = np.histogram2d(
                    player_x_valid, player_y_valid, 
                    bins=20, range=[[0, 100], [0, 100]]
                )
                
                # 히트맵 표시 (선수별 색상으로)
                # 색상 맵을 선수 색상에 맞게 조정
                from matplotlib.colors import LinearSegmentedColormap
                cmap_colors = ['#00000000', color]  # 투명 -> 선수 색상
                player_cmap = LinearSegmentedColormap.from_list(f'player_{idx}', cmap_colors, N=256)
                
                extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
                ax.imshow(player_heatmap.T, origin='lower', extent=extent, 
                         cmap=player_cmap, alpha=0.6, interpolation='gaussian', zorder=4)
            
            # 선수 위치 마커 (숫자로 표시)
            size = 300 + (impact_score * 5)
            ax.scatter(avg_x, avg_y, s=size, c=color, edgecolors='white', 
                      linewidths=3, alpha=0.95, zorder=9, marker='o')
            
            # 선수 번호 표시 (필드 위에는 번호만)
            ax.text(avg_x, avg_y, str(idx + 1), ha='center', va='center',
                   fontsize=12, color='white', weight='bold', zorder=10)
            
            # 표 데이터 수집
            player_data_for_table.append({
                'num': idx + 1,
                'name': player_name,
                'shots': activity.shots,
                'passes': activity.passes,
                'defense': activity.defense_actions,
                'xg': activity.xg_contribution,
                'impact': impact_score,
                'color': color
            })
    
    # 범례 (히트맵 영역)
    legend_elements = [
        mpatches.Patch(color='green', alpha=0.8, label='공격 라인'),
        mpatches.Patch(color='red', alpha=0.8, label='수비 라인'),
        plt.Line2D([0], [0], color='yellow', linewidth=5, label='주요 패스 경로 (상위 5개)'),
        plt.Line2D([0], [0], color='#00CED1', linewidth=2, label='일반 성공한 패스'),
        plt.Line2D([0], [0], color='#FF8C00', linewidth=2, linestyle='--', label='실패한 패스'),
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#DC143C', 
                  markersize=15, markeredgecolor='black', markeredgewidth=2, label='슈팅 (xG 높음)'),
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#FF6347', 
                  markersize=12, markeredgecolor='black', markeredgewidth=2, label='슈팅 (xG 중간)'),
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#FFD700', 
                  markersize=10, markeredgecolor='black', markeredgewidth=2, label='슈팅 (xG 낮음)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, framealpha=0.95, 
             edgecolor='black', fancybox=True, shadow=True, facecolor='white')
    
    # 선수 정보 표 생성 (오른쪽 사이드)
    if player_data_for_table:
        # 표 데이터 준비
        table_data = [['번호', '선수명', '슈팅', '패스', '수비', 'xG', '영향도']]
        
        for player in player_data_for_table:
            table_data.append([
                str(player['num']),
                player['name'][:10] + ('...' if len(player['name']) > 10 else ''),
                str(player['shots']),
                str(player['passes']),
                str(player['defense']),
                f"{player['xg']:.2f}",
                f"{player['impact']:.1f}"
            ])
        
        # 표 생성
        table = ax_table.table(cellText=table_data[1:], colLabels=table_data[0],
                              cellLoc='center', loc='center',
                              colWidths=[0.08, 0.25, 0.12, 0.12, 0.12, 0.15, 0.15])
        
        # 표 스타일링
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2.5)
        
        # 헤더 스타일
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#1a1a1a')
            table[(0, i)].set_text_props(weight='bold', color='white')
            table[(0, i)].set_edgecolor('white')
            table[(0, i)].set_linewidth(1.5)
        
        # 데이터 행 스타일 (색상별)
        for row_idx, player in enumerate(player_data_for_table, start=1):
            for col_idx in range(len(table_data[0])):
                cell = table[(row_idx, col_idx)]
                cell.set_facecolor(player['color'])
                cell.set_alpha(0.7)
                cell.set_text_props(weight='bold', color='white')
                cell.set_edgecolor('white')
                cell.set_linewidth(1)
        
        # 표 제목
        ax_table.text(0.5, 0.95, '주요 선수 통계', ha='center', va='top',
                     fontsize=14, fontweight='bold', color='white',
                     transform=ax_table.transAxes)
        
        # 범례 설명 (표 아래)
        legend_text = "※ 필드 위 숫자는 선수 번호를 나타냅니다"
        ax_table.text(0.5, 0.02, legend_text, ha='center', va='bottom',
                     fontsize=8, color='#cccccc', style='italic',
                     transform=ax_table.transAxes)
    
    # 제목
    situation_text = ""
    if turning_point.change_type == 'attack_surge':
        situation_text = "공격 급증"
    elif turning_point.change_type == 'defense_breakdown':
        situation_text = "수비 붕괴"
    else:
        situation_text = "모멘텀 변화"
    
    fig.suptitle(
        f'{target_team} - {turning_point.minute}분 변곡점 ({situation_text})\n'
        f'주요 선수 활동 히트맵 및 패스/슈팅 분석',
        fontsize=16,
        fontweight='bold',
        y=0.98,
        color='white'
    )
    
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect('equal')
    ax.axis('off')  # 축 숨기기
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.2, facecolor='#22312b')
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


