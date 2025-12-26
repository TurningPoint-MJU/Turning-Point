"""
메인 실행 파일
"""
from datetime import datetime
from src.data.models import MatchData, MatchEvent
from src.analysis.turning_point import detect_turning_points
from src.explanation.generator import ExplanationGenerator
from src.visualization.plotter import plot_momentum_curve

# 샘플 데이터 생성 (실제로는 API나 데이터베이스에서 가져옴)
def create_sample_match_data() -> MatchData:
    """테스트용 샘플 경기 데이터 - 변곡점이 명확한 시나리오"""
    import random
    events = []
    random.seed(42)  # 재현 가능한 결과
    
    # 전반 초반 (0-20분): 홈팀 우세 - 높은 점유율, 슈팅, 상대 진영 활동
    for minute in range(0, 20):
        # 홈팀 공격 이벤트
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="shot",
            x=75.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-10, 10),
            success=True,
            xg=0.15 + random.uniform(-0.05, 0.05)
        ))
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="pass",
            x=60.0 + random.uniform(-5, 5),
            y=45.0 + random.uniform(-5, 5),
            success=True
        ))
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="pass",
            x=65.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-5, 5),
            success=True
        ))
        # 원정팀은 수비 위주
        events.append(MatchEvent(
            minute=minute,
            team="원정팀",
            event_type="defense",
            x=30.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-5, 5),
            success=True
        ))
        events.append(MatchEvent(
            minute=minute,
            team="원정팀",
            event_type="pass",
            x=35.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-5, 5),
            success=random.choice([True, False])  # 패스 실패도 포함
        ))
    
    # 전반 중반 (20-45분): 원정팀 반격 - 변곡점 1
    for minute in range(20, 45):
        # 원정팀 공격 증가
        events.append(MatchEvent(
            minute=minute,
            team="원정팀",
            event_type="shot",
            x=25.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-10, 10),
            success=True,
            xg=0.12 + random.uniform(-0.05, 0.05)
        ))
        events.append(MatchEvent(
            minute=minute,
            team="원정팀",
            event_type="pass",
            x=40.0 + random.uniform(-5, 5),
            y=55.0 + random.uniform(-5, 5),
            success=True
        ))
        events.append(MatchEvent(
            minute=minute,
            team="원정팀",
            event_type="pass",
            x=45.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-5, 5),
            success=True
        ))
        # 홈팀 공격 감소
        if minute % 3 == 0:  # 가끔만 슈팅
            events.append(MatchEvent(
                minute=minute,
                team="홈팀",
                event_type="shot",
                x=70.0 + random.uniform(-5, 5),
                y=50.0 + random.uniform(-10, 10),
                success=True,
                xg=0.10 + random.uniform(-0.03, 0.03)
            ))
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="pass",
            x=50.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-5, 5),
            success=random.choice([True, False])  # 패스 실패 증가
        ))
    
    # 후반 초반 (45-70분): 홈팀 재반격 - 변곡점 2
    for minute in range(45, 70):
        # 홈팀 공격 급증
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="shot",
            x=80.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-10, 10),
            success=True,
            xg=0.20 + random.uniform(-0.05, 0.05)
        ))
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="pass",
            x=65.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-5, 5),
            success=True
        ))
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="pass",
            x=70.0 + random.uniform(-5, 5),
            y=45.0 + random.uniform(-5, 5),
            success=True
        ))
        # 수비 라인 전진
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="defense",
            x=45.0 + random.uniform(-5, 5),  # 수비 라인 전진
            y=50.0 + random.uniform(-5, 5),
            success=True
        ))
        # 원정팀은 수비 위주
        events.append(MatchEvent(
            minute=minute,
            team="원정팀",
            event_type="defense",
            x=25.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-5, 5),
            success=True
        ))
        if minute % 4 == 0:  # 가끔만 공격
            events.append(MatchEvent(
                minute=minute,
                team="원정팀",
                event_type="shot",
                x=20.0 + random.uniform(-5, 5),
                y=50.0 + random.uniform(-10, 10),
                success=True,
                xg=0.08 + random.uniform(-0.03, 0.03)
            ))
    
    # 후반 후반 (70-90분): 원정팀 최종 공격 - 변곡점 3
    for minute in range(70, 90):
        # 원정팀 공격 급증
        events.append(MatchEvent(
            minute=minute,
            team="원정팀",
            event_type="shot",
            x=20.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-10, 10),
            success=True,
            xg=0.18 + random.uniform(-0.05, 0.05)
        ))
        events.append(MatchEvent(
            minute=minute,
            team="원정팀",
            event_type="pass",
            x=35.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-5, 5),
            success=True
        ))
        events.append(MatchEvent(
            minute=minute,
            team="원정팀",
            event_type="pass",
            x=40.0 + random.uniform(-5, 5),
            y=55.0 + random.uniform(-5, 5),
            success=True
        ))
        # 홈팀 패스 실패 증가
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="pass",
            x=55.0 + random.uniform(-5, 5),
            y=50.0 + random.uniform(-5, 5),
            success=random.choice([True, False, False])  # 실패율 증가
        ))
        # 홈팀 수비 라인 후퇴
        events.append(MatchEvent(
            minute=minute,
            team="홈팀",
            event_type="defense",
            x=35.0 + random.uniform(-5, 5),  # 수비 라인 후퇴
            y=50.0 + random.uniform(-5, 5),
            success=True
        ))
    
    return MatchData(
        match_id="sample_001",
        home_team="서울 FC",
        away_team="수원 삼성",
        match_date=datetime.now(),
        events=events,
        final_score={"home": 2, "away": 1}
    )


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("K리그 경기 변곡점 분석 MVP")
    print("=" * 60)
    
    # 샘플 데이터 생성
    match_data = create_sample_match_data()
    print(f"\n경기: {match_data.home_team} vs {match_data.away_team}")
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
    plot_momentum_curve(match_data, turning_points, "momentum_curve.png")
    print("그래프가 'momentum_curve.png'로 저장되었습니다.")


if __name__ == "__main__":
    main()

