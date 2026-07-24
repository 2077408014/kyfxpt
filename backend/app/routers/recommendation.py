from fastapi import APIRouter, Depends, HTTPException, Query, Body, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.recommendation_service import recommendation_service
from ..services.agent_log_service import agent_log_service
from ..schemas.recommendation import RecommendationCreate, RecommendationComplete, RecommendationReport
from ..routers.auth import get_current_user
import matplotlib.pyplot as plt
import io

router = APIRouter(prefix="/api/recommend", tags=["推荐系统"])


@router.get("/analysis", response_model=list)
def analyze_weak_points(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = recommendation_service.analyze_weak_points(db, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=list)
async def generate_recommendations(
    count: int = Query(5, ge=1, le=20),
    subject: str = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = await recommendation_service.generate_recommendations(db, current_user.id, count, subject)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=list)
def get_recommendations(
    completed: bool = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = recommendation_service.get_recommendations(db, current_user.id, completed)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/complete")
def complete_recommendation(
    id: int,
    data: RecommendationComplete,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = recommendation_service.complete_recommendation(db, current_user.id, id, data.result)
        if not result:
            raise HTTPException(status_code=404, detail="推荐题目不存在")
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report", response_model=RecommendationReport)
def get_recommendation_report(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = recommendation_service.get_recommendation_report(db, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
def get_agent_status(current_user = Depends(get_current_user)):
    try:
        return {"agents": recommendation_service.get_agent_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_name}/toggle")
def toggle_agent(
    agent_name: str,
    enabled: bool = Body(..., embed=True),
    current_user = Depends(get_current_user)
):
    try:
        recommendation_service.toggle_agent(agent_name, enabled)
        return {"success": True, "message": f"智能体 {agent_name} 已{'启用' if enabled else '禁用'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
def get_collaboration_logs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logs = agent_log_service.get_collaboration_logs(db, current_user.id, limit, offset)
        stats = agent_log_service.get_collaboration_stats(db, current_user.id)
        return {"logs": logs, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{request_id}")
def get_interaction_logs(
    request_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logs = agent_log_service.get_interaction_logs(db, request_id)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/render")
def render_question_image(
    id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    type: str = Query("question", description="渲染类型：question/answer/analysis")
):
    from ..models.recommendation import Recommendation
    
    rec = db.query(Recommendation).filter(
        Recommendation.id == id,
        Recommendation.user_id == current_user.id
    ).first()
    
    if not rec:
        raise HTTPException(status_code=404, detail="推荐题目不存在")
    
    content = ""
    if type == "question":
        content = rec.question_text
    elif type == "answer":
        content = f"答案：{rec.answer}"
    elif type == "analysis":
        content = f"解析：{rec.analysis}" if rec.analysis else "暂无解析"
    else:
        raise HTTPException(status_code=400, detail="无效的渲染类型")
    
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['text.usetex'] = False
    
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    ax.axis('off')
    
    wrapped_text = _wrap_text(content, 80)
    
    ax.text(0.02, 0.95, wrapped_text, transform=ax.transAxes, 
            fontsize=14, verticalalignment='top', 
            bbox=dict(facecolor='white', edgecolor='none', pad=10))
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.5, dpi=150)
    buf.seek(0)
    
    plt.close(fig)
    
    return Response(content=buf.read(), media_type="image/png")


def _wrap_text(text: str, max_width: int) -> str:
    lines = []
    current_line = ""
    
    for char in text:
        if char == '\n':
            lines.append(current_line)
            current_line = ""
        elif len(current_line) >= max_width:
            lines.append(current_line)
            current_line = char
        else:
            current_line += char
    
    if current_line:
        lines.append(current_line)
    
    return '\n'.join(lines)