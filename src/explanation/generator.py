"""
팬 친화형 AI 설명 생성 모듈
"""
from typing import List
from src.data.models import TurningPoint, TimeWindowMetrics


class ExplanationGenerator:
    """팬 친화형 설명 생성기"""
    
    def __init__(self):
        self.templates = {
            'attack_surge': {
                'positive': [
                    "{team}의 공격이 {minute}분 이후 급격히 살아났습니다. "
                    "슈팅 시도가 {shots_before}회에서 {shots_after}회로 증가했고, "
                    "상대 진영에서의 활동도 활발해지며 경기 주도권을 잡았습니다.",
                    
                    "{minute}분을 기점으로 {team}의 공격이 폭발했습니다. "
                    "기대득점(xG)이 {xg_before:.2f}에서 {xg_after:.2f}로 상승하며 "
                    "실제 골로 이어질 가능성이 높아진 상황이었습니다.",
                ],
                'negative': [
                    "{team}의 공격이 {minute}분 이후 크게 주춤했습니다. "
                    "슈팅 시도가 줄어들고 상대 진영에서의 활동이 위축되며 "
                    "경기 주도권을 내주기 시작했습니다.",
                ]
            },
            'defense_breakdown': {
                'positive': [
                    "{minute}분 이후 {team}의 수비가 더욱 공격적으로 변했습니다. "
                    "수비 라인이 전진하며 상대를 압박하는 강도가 높아졌고, "
                    "이로 인해 공격 기회가 늘어났습니다.",
                ],
                'negative': [
                    "{minute}분을 기점으로 {team}의 수비가 후퇴하기 시작했습니다. "
                    "수비 라인이 낮아지며 수동적인 수비로 전환되었고, "
                    "상대의 공격을 막기 어려운 상황이 되었습니다.",
                ]
            },
            'momentum_shift': {
                'positive': [
                    "{minute}분 이후 경기 흐름이 {team} 쪽으로 기울었습니다. "
                    "패스 성공률이 {pass_before:.1f}%에서 {pass_after:.1f}%로 향상되며 "
                    "공격 연결이 부드러워졌고, 점유율도 상승했습니다.",
                ],
                'negative': [
                    "{minute}분을 기점으로 {team}의 경기력이 급격히 하락했습니다. "
                    "패스 성공률이 {pass_before:.1f}%에서 {pass_after:.1f}%로 떨어지며 "
                    "공격 흐름이 끊기고, 상대에게 주도권을 내주게 되었습니다.",
                ]
            }
        }
    
    def generate_explanation(
        self,
        turning_point: TurningPoint,
        team_name: str
    ) -> str:
        """
        변곡점에 대한 팬 친화형 설명 생성
        """
        change_type = turning_point.change_type
        metrics_before = turning_point.metrics_before
        metrics_after = turning_point.metrics_after
        
        # 변화 방향 판단
        momentum_improved = (
            metrics_after.possession > metrics_before.possession or
            metrics_after.xg > metrics_before.xg or
            metrics_after.shots > metrics_before.shots
        )
        direction = 'positive' if momentum_improved else 'negative'
        
        # 템플릿 선택
        templates = self.templates.get(change_type, {}).get(direction, [])
        if not templates:
            templates = self.templates.get('momentum_shift', {}).get(direction, [])
        
        if not templates:
            return f"{turning_point.minute}분 이후 {team_name}의 경기 흐름에 변화가 있었습니다."
        
        # 템플릿 채우기
        import random
        template = random.choice(templates)
        
        explanation = template.format(
            team=team_name,
            minute=turning_point.minute,
            shots_before=metrics_before.shots,
            shots_after=metrics_after.shots,
            xg_before=metrics_before.xg,
            xg_after=metrics_after.xg,
            pass_before=metrics_before.pass_success_rate,
            pass_after=metrics_after.pass_success_rate,
        )
        
        return explanation
    
    def generate_summary(
        self,
        turning_points: List[TurningPoint],
        home_team: str,
        away_team: str
    ) -> str:
        """
        경기 전체 요약 설명
        """
        if not turning_points:
            return "이 경기는 비교적 안정적인 흐름으로 진행되었습니다."
        
        key_turning_point = max(
            turning_points,
            key=lambda tp: abs(tp.metrics_after.possession - tp.metrics_before.possession)
        )
        
        team_name = home_team if key_turning_point.team_advantage == 'home' else away_team
        
        return (
            f"이 경기의 가장 큰 변곡점은 {key_turning_point.minute}분이었습니다. "
            f"{self.generate_explanation(key_turning_point, team_name)} "
            f"이 시점 이후 경기 흐름이 결정적으로 바뀌었습니다."
        )

