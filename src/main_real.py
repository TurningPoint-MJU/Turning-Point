"""
실제 K리그 데이터로 테스트하는 메인 실행 파일
"""
import sys
from pathlib import Path
from src.data.loader import load_match_by_id, list_available_matches
from src.analysis.turning_point import detect_turning_points
from src.explanation.generator import ExplanationGenerator
from src.visualization.plotter import (
    plot_momentum_curve,
    plot_player_heatmap,
    plot_player_movements
)
from src.analysis.player_analysis import (
    extract_player_activities,
    get_key_players,
    get_player_event_summary
)

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "raw_data.csv"
MATCH_INFO_PATH = PROJECT_ROOT / "match_info.csv"


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("K리그 경기 변곡점 분석 MVP - 실제 데이터 테스트")
    print("=" * 60)
    
    # 사용 가능한 경기 목록 출력
    print("\n사용 가능한 경기 목록:")
    matches = list_available_matches(str(MATCH_INFO_PATH))
    print(matches.head(10).to_string(index=False))
    
    # 첫 번째 경기로 테스트 (또는 명령줄 인자로 game_id 받기)
    if len(sys.argv) > 1:
        game_id = int(sys.argv[1])
    else:
        game_id = matches.iloc[0]['game_id']
        print(f"\n기본 경기 선택: {game_id}")
    
    print(f"\n경기 ID {game_id} 분석 중...")
    
    try:
        # 경기 데이터 로드
        match_data = load_match_by_id(
            str(RAW_DATA_PATH),
            str(MATCH_INFO_PATH),
            game_id
        )
        
        print(f"\n경기: {match_data.home_team} vs {match_data.away_team}")
        print(f"경기 날짜: {match_data.match_date}")
        print(f"최종 스코어: {match_data.final_score['home']} - {match_data.final_score['away']}")
        print(f"이벤트 수: {len(match_data.events)}")
        
        # 변곡점 탐지
        print("\n변곡점 탐지 중...")
        turning_points = detect_turning_points(match_data)
        print(f"탐지된 변곡점: {len(turning_points)}개")
        
        # 설명 생성
        explanation_gen = ExplanationGenerator()
        for tp in turning_points:
            team_name = (
                match_data.home_team if tp.team_advantage == 'home'
                else match_data.away_team
            )
            tp.explanation = explanation_gen.generate_explanation(tp, team_name)
            print(f"\n[{tp.minute}분] {team_name}")
            print(f"  유형: {tp.change_type}")
            print(f"  지표: {', '.join(tp.indicators)}")
            print(f"  설명: {tp.explanation}")
        
        # 전체 요약
        summary = explanation_gen.generate_summary(
            turning_points,
            match_data.home_team,
            match_data.away_team
        )
        print(f"\n전체 요약:")
        print(f"  {summary}")
        
        # 시각화
        print("\n그래프 생성 중...")
        output_path = f"momentum_curve_{game_id}.png"
        plot_momentum_curve(match_data, turning_points, output_path)
        print(f"그래프가 '{output_path}'로 저장되었습니다.")
        
        # 변곡점별 선수 분석 및 히트맵 생성
        if turning_points:
            print("\n변곡점별 선수 분석 중...")
            for tp in turning_points:
                print(f"\n[{tp.minute}분] 변곡점 선수 분석...")
                
                # 선수 활동 추출
                player_activities = extract_player_activities(match_data, tp)
                
                if player_activities:
                    # 주요 선수 식별
                    key_players = get_key_players(player_activities, top_n=5)
                    
                    print(f"  분석된 선수 수: {len(player_activities)}")
                    print(f"  주요 선수 (상위 5명):")
                    for player_name, activity, impact_score in key_players:
                        print(f"    - {player_name}: 영향도 {impact_score:.1f} "
                              f"(슈팅: {activity.shots}, 패스: {activity.passes}, "
                              f"xG: {activity.xg_contribution:.2f})")
                    
                    # 히트맵 생성
                    heatmap_path = f"heatmap_{game_id}_{tp.minute}.png"
                    plot_player_heatmap(match_data, tp, player_activities, heatmap_path)
                    print(f"  히트맵 저장: {heatmap_path}")
                    
                    # 선수 움직임 시각화
                    movements_path = f"movements_{game_id}_{tp.minute}.png"
                    plot_player_movements(match_data, tp, player_activities, top_n=5, save_path=movements_path)
                    print(f"  선수 움직임 그래프 저장: {movements_path}")
                else:
                    print(f"  해당 시점의 선수 데이터를 찾을 수 없습니다.")
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

