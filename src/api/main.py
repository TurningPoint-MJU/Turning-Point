"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path
from src.data.models import MatchData
from src.data.loader import load_match_by_id, list_available_matches
from src.analysis.turning_point import detect_turning_points
from src.explanation.generator import ExplanationGenerator
from src.visualization.plotter import (
    plot_momentum_curve, 
    create_turning_point_details,
    plot_player_heatmap,
    plot_player_movements
)
from src.analysis.player_analysis import (
    extract_player_activities,
    get_key_players,
    get_player_event_summary
)

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "raw_data.csv"
MATCH_INFO_PATH = PROJECT_ROOT / "match_info.csv"

app = FastAPI(
    title="K리그 경기 변곡점 분석 API",
    description="경기 흐름의 변곡점을 탐지하고 팬 친화적으로 설명하는 API"
)


@app.get("/")
async def root():
    return {
        "message": "K리그 경기 변곡점 분석 MVP API",
        "version": "1.0.0"
    }


@app.get("/matches")
async def get_matches():
    """
    사용 가능한 경기 목록 반환
    """
    try:
        matches = list_available_matches(str(MATCH_INFO_PATH))
        return {
            "matches": matches.to_dict('records'),
            "total": len(matches)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/{game_id}")
async def analyze_match_by_id(game_id: int):
    """
    경기 ID로 경기 데이터를 분석하여 변곡점 탐지 및 설명 생성
    """
    try:
        # 경기 데이터 로드
        match_data = load_match_by_id(
            str(RAW_DATA_PATH),
            str(MATCH_INFO_PATH),
            game_id
        )
        
        # 변곡점 탐지
        turning_points = detect_turning_points(match_data)
        
        # 설명 생성
        explanation_gen = ExplanationGenerator()
        
        # 각 변곡점에 대한 설명 개선
        for tp in turning_points:
            team_name = (
                match_data.home_team if tp.team_advantage == 'home'
                else match_data.away_team
            )
            tp.explanation = explanation_gen.generate_explanation(tp, team_name)
        
        # 전체 요약
        summary = explanation_gen.generate_summary(
            turning_points,
            match_data.home_team,
            match_data.away_team
        )
        
        # 변곡점 상세 정보
        turning_point_details = [
            create_turning_point_details(
                tp,
                match_data.home_team if tp.team_advantage == 'home' else match_data.away_team
            )
            for tp in turning_points
        ]
        
        return {
            "match_id": match_data.match_id,
            "home_team": match_data.home_team,
            "away_team": match_data.away_team,
            "match_date": match_data.match_date.isoformat(),
            "final_score": match_data.final_score,
            "summary": summary,
            "turning_points_count": len(turning_points),
            "turning_points": turning_point_details
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"경기 ID {game_id}를 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_match(match_data: MatchData):
    """
    경기 데이터를 분석하여 변곡점 탐지 및 설명 생성
    """
    try:
        # 변곡점 탐지
        turning_points = detect_turning_points(match_data)
        
        # 설명 생성
        explanation_gen = ExplanationGenerator()
        
        # 각 변곡점에 대한 설명 개선
        for tp in turning_points:
            team_name = (
                match_data.home_team if tp.team_advantage == 'home'
                else match_data.away_team
            )
            tp.explanation = explanation_gen.generate_explanation(tp, team_name)
        
        # 전체 요약
        summary = explanation_gen.generate_summary(
            turning_points,
            match_data.home_team,
            match_data.away_team
        )
        
        # 변곡점 상세 정보
        turning_point_details = [
            create_turning_point_details(
                tp,
                match_data.home_team if tp.team_advantage == 'home' else match_data.away_team
            )
            for tp in turning_points
        ]
        
        return {
            "match_id": match_data.match_id,
            "home_team": match_data.home_team,
            "away_team": match_data.away_team,
            "summary": summary,
            "turning_points_count": len(turning_points),
            "turning_points": turning_point_details
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualize/{game_id}")
async def visualize_match_by_id(
    game_id: int,
    save_path: Optional[str] = Query(None, description="저장 경로 (기본값: momentum_curve_{game_id}.png)")
):
    """
    경기 ID로 경기 흐름 그래프 생성
    """
    try:
        # 경기 데이터 로드
        match_data = load_match_by_id(
            str(RAW_DATA_PATH),
            str(MATCH_INFO_PATH),
            game_id
        )
        
        turning_points = detect_turning_points(match_data)
        
        if save_path is None:
            save_path = f"momentum_curve_{game_id}.png"
        
        plot_momentum_curve(match_data, turning_points, save_path)
        
        return {
            "message": "그래프가 생성되었습니다.",
            "save_path": save_path,
            "turning_points_count": len(turning_points)
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"경기 ID {game_id}를 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_match(match_data: MatchData):
    """
    직접 제공된 경기 데이터를 분석하여 변곡점 탐지 및 설명 생성
    (기존 API 호환성 유지)
    """
    try:
        # 변곡점 탐지
        turning_points = detect_turning_points(match_data)
        
        # 설명 생성
        explanation_gen = ExplanationGenerator()
        
        # 각 변곡점에 대한 설명 개선
        for tp in turning_points:
            team_name = (
                match_data.home_team if tp.team_advantage == 'home'
                else match_data.away_team
            )
            tp.explanation = explanation_gen.generate_explanation(tp, team_name)
        
        # 전체 요약
        summary = explanation_gen.generate_summary(
            turning_points,
            match_data.home_team,
            match_data.away_team
        )
        
        # 변곡점 상세 정보
        turning_point_details = [
            create_turning_point_details(
                tp,
                match_data.home_team if tp.team_advantage == 'home' else match_data.away_team
            )
            for tp in turning_points
        ]
        
        return {
            "match_id": match_data.match_id,
            "home_team": match_data.home_team,
            "away_team": match_data.away_team,
            "summary": summary,
            "turning_points_count": len(turning_points),
            "turning_points": turning_point_details
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/visualize")
async def visualize_match(match_data: MatchData, save_path: str = "momentum_curve.png"):
    """
    직접 제공된 경기 데이터로 경기 흐름 그래프 생성
    (기존 API 호환성 유지)
    """
    try:
        turning_points = detect_turning_points(match_data)
        plot_momentum_curve(match_data, turning_points, save_path)
        
        return {
            "message": "그래프가 생성되었습니다.",
            "save_path": save_path,
            "turning_points_count": len(turning_points)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/{game_id}/players/{turning_point_minute}")
async def analyze_turning_point_players(
    game_id: int,
    turning_point_minute: int,
    top_n: int = Query(5, description="상위 선수 수")
):
    """
    특정 변곡점 시점의 선수 분석
    
    Args:
        game_id: 경기 ID
        turning_point_minute: 변곡점 시점 (분)
        top_n: 반환할 상위 선수 수
    """
    try:
        # 경기 데이터 로드
        match_data = load_match_by_id(
            str(RAW_DATA_PATH),
            str(MATCH_INFO_PATH),
            game_id
        )
        
        # 변곡점 탐지
        turning_points = detect_turning_points(match_data)
        
        # 해당 시점의 변곡점 찾기
        target_tp = None
        for tp in turning_points:
            if abs(tp.minute - turning_point_minute) <= 5:  # 5분 이내 허용
                target_tp = tp
                break
        
        if not target_tp:
            raise HTTPException(
                status_code=404, 
                detail=f"{turning_point_minute}분 시점의 변곡점을 찾을 수 없습니다."
            )
        
        # 선수 활동 추출
        player_activities = extract_player_activities(match_data, target_tp)
        
        # 주요 선수 식별
        key_players = get_key_players(player_activities, top_n)
        
        # 선수별 상세 정보
        player_details = []
        for player_name, activity, impact_score in key_players:
            summary = get_player_event_summary(activity)
            summary['impact_score'] = impact_score
            player_details.append(summary)
        
        return {
            "turning_point": {
                "minute": target_tp.minute,
                "team_advantage": target_tp.team_advantage,
                "change_type": target_tp.change_type,
                "explanation": target_tp.explanation
            },
            "key_players": player_details,
            "total_players_analyzed": len(player_activities)
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"경기 ID {game_id}를 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualize/{game_id}/heatmap/{turning_point_minute}")
async def visualize_turning_point_heatmap(
    game_id: int,
    turning_point_minute: int,
    save_path: Optional[str] = Query(None, description="저장 경로")
):
    """
    변곡점 시점의 선수 위치 히트맵 생성
    
    Args:
        game_id: 경기 ID
        turning_point_minute: 변곡점 시점 (분)
        save_path: 저장 경로 (기본값: heatmap_{game_id}_{minute}.png)
    """
    try:
        # 경기 데이터 로드
        match_data = load_match_by_id(
            str(RAW_DATA_PATH),
            str(MATCH_INFO_PATH),
            game_id
        )
        
        # 변곡점 탐지
        turning_points = detect_turning_points(match_data)
        
        # 해당 시점의 변곡점 찾기
        target_tp = None
        for tp in turning_points:
            if abs(tp.minute - turning_point_minute) <= 5:
                target_tp = tp
                break
        
        if not target_tp:
            raise HTTPException(
                status_code=404,
                detail=f"{turning_point_minute}분 시점의 변곡점을 찾을 수 없습니다."
            )
        
        # 선수 활동 추출
        player_activities = extract_player_activities(match_data, target_tp)
        
        if not player_activities:
            raise HTTPException(
                status_code=404,
                detail="해당 시점의 선수 데이터를 찾을 수 없습니다."
            )
        
        # 저장 경로 설정
        if save_path is None:
            save_path = f"heatmap_{game_id}_{turning_point_minute}.png"
        
        # 히트맵 생성
        plot_player_heatmap(match_data, target_tp, player_activities, save_path)
        
        return {
            "message": "히트맵이 생성되었습니다.",
            "save_path": save_path,
            "turning_point": {
                "minute": target_tp.minute,
                "team_advantage": target_tp.team_advantage
            }
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"경기 ID {game_id}를 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/visualize/{game_id}/movements/{turning_point_minute}")
async def visualize_player_movements(
    game_id: int,
    turning_point_minute: int,
    top_n: int = Query(5, description="표시할 상위 선수 수"),
    save_path: Optional[str] = Query(None, description="저장 경로")
):
    """
    변곡점 시점의 주요 선수 움직임 시각화
    
    Args:
        game_id: 경기 ID
        turning_point_minute: 변곡점 시점 (분)
        top_n: 표시할 상위 선수 수
        save_path: 저장 경로 (기본값: movements_{game_id}_{minute}.png)
    """
    try:
        # 경기 데이터 로드
        match_data = load_match_by_id(
            str(RAW_DATA_PATH),
            str(MATCH_INFO_PATH),
            game_id
        )
        
        # 변곡점 탐지
        turning_points = detect_turning_points(match_data)
        
        # 해당 시점의 변곡점 찾기
        target_tp = None
        for tp in turning_points:
            if abs(tp.minute - turning_point_minute) <= 5:
                target_tp = tp
                break
        
        if not target_tp:
            raise HTTPException(
                status_code=404,
                detail=f"{turning_point_minute}분 시점의 변곡점을 찾을 수 없습니다."
            )
        
        # 선수 활동 추출
        player_activities = extract_player_activities(match_data, target_tp)
        
        if not player_activities:
            raise HTTPException(
                status_code=404,
                detail="해당 시점의 선수 데이터를 찾을 수 없습니다."
            )
        
        # 저장 경로 설정
        if save_path is None:
            save_path = f"movements_{game_id}_{turning_point_minute}.png"
        
        # 움직임 시각화
        plot_player_movements(match_data, target_tp, player_activities, top_n, save_path)
        
        return {
            "message": "선수 움직임 그래프가 생성되었습니다.",
            "save_path": save_path,
            "turning_point": {
                "minute": target_tp.minute,
                "team_advantage": target_tp.team_advantage
            }
        }
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"경기 ID {game_id}를 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

