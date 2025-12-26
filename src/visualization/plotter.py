"""
경기 흐름 시각화 모듈
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List
from src.data.models import MatchData, MomentumScore, TurningPoint
from src.analysis.metrics import calculate_time_window_metrics, calculate_momentum_score


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

