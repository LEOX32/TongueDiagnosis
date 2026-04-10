from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, date, timedelta
from typing import List, Optional
from ..models import schemas
from ..models.database import get_db
from ..models.models import HealthReport, HealthProgress, HealthRecommendation, TongueAnalysis, User
from ..core.authentication import get_current_user
import random
import requests
import json

router = APIRouter(tags=["Health Tracking"])


def generate_ai_recommendations(user: User, db: Session) -> str:
    """基于3种报告生成AI个性化建议"""
    try:
        now = datetime.now()

        daily_reports = db.query(HealthReport).filter(
            HealthReport.user_id == user.id,
            HealthReport.report_type == "daily"
        ).order_by(desc(HealthReport.report_date)).limit(7).all()

        weekly_reports = db.query(HealthReport).filter(
            HealthReport.user_id == user.id,
            HealthReport.report_type == "weekly"
        ).order_by(desc(HealthReport.report_date)).limit(4).all()

        monthly_reports = db.query(HealthReport).filter(
            HealthReport.user_id == user.id,
            HealthReport.report_type == "monthly"
        ).order_by(desc(HealthReport.report_date)).limit(3).all()

        daily_summary = f"最近{len(daily_reports)}次日报分析，整体评分{sum(r.overall_score for r in daily_reports)/len(daily_reports):.1f}分。" if daily_reports else "暂无日报数据。"
        weekly_summary = f"最近{len(weekly_reports)}周周报分析，平均评分{sum(r.overall_score for r in weekly_reports)/len(weekly_reports):.1f}分。" if weekly_reports else "暂无周报数据。"
        monthly_summary = f"最近{len(monthly_reports)}月月报分析，平均评分{sum(r.overall_score for r in monthly_reports)/len(monthly_reports):.1f}分。" if monthly_reports else "暂无月报数据。"

        from ..config import settings
        language = user.language or 'zh'
        language_prompts = {
            'zh': {'system': '你是一位中医舌诊专家。根据提供的健康报告数据，给出3条简洁的健康建议。用中文回答。格式："1. ... 2. ... 3. ..."', 'data': '健康报告数据'},
            'en': {'system': 'You are an AI traditional Chinese medicine doctor. Based on the health report data provided, give 3 concise health recommendations. Answer in English only. Format: "1. ... 2. ... 3. ..."', 'data': 'Health Report Data'},
            'ja': {'system': 'あなたは中医舌診専門家です。提供された健康報告データに基づいて、3つの簡潔な健康提案を日本語で答えてください。形式："1. ... 2. ... 3. ..."', 'data': '健康報告データ'},
            'ko': {'system': '당신은 중의 혀진단 전문가입니다. 제공된 건강 보고서 데이터에 기반으로 3가지 간결한 건강 권장 사항을 한국어로 답변하세요. 형식: "1. ... 2. ... 3. ..."', 'data': '건강 보고서 데이터'},
            'de': {'system': 'Sie sind ein TCM-Zungendiagnose-Experte. Basierend auf den bereitgestellten Gesundheitsberichtsdaten geben Sie 3 kurze Gesundheitsempfehlungen auf Deutsch. Format: "1. ... 2. ... 3. ..."', 'data': 'Gesundheitsberichtsdaten'},
            'es': {'system': 'Eres un experto en diagnóstico de lengua de TCM. Basándose en los datos del informe de salud proporcionado, dé 3 recomendaciones breves de salud en español. Formato: "1. ... 2. ... 3. ..."', 'data': 'Datos del informe de salud'},
            'fr': {'system': 'Vous êtes un expert en diagnostic de langue TCM. Basé sur les données du rapport de santé fourni, donnez 3 recommandations de santé brèves en français. Format: "1. ... 2. ... 3. ..."', 'data': 'Données du rapport de santé'}
        }
        prompt_config = language_prompts.get(language, language_prompts['en'])
        system_prompt = prompt_config['system']
        user_prompt = f"{prompt_config['data']}：{daily_summary} {weekly_summary} {monthly_summary}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        data = {
            "model": settings.LLM_NAME,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": 300,
                "temperature": 0.7
            }
        }

        response = requests.post(settings.OLLAMA_PATH, headers={"Content-Type": "application/json"}, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('message', {}).get('content', '建议保持良好的作息习惯，注意饮食均衡。')
        else:
            return '建议保持良好的作息习惯，注意饮食均衡。'
    except Exception as e:
        print(f"AI建议生成失败: {e}")
        return '建议保持良好的作息习惯，注意饮食均衡。'


@router.get("/reports", response_model=schemas.BaseResponse)
async def get_health_reports(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    report_type: Optional[str] = "all",
    limit: int = 100
):
    """获取用户的健康报告列表"""
    query = db.query(HealthReport).filter(HealthReport.user_id == user.id)

    now = datetime.now()

    if report_type == "daily":
        start_time = now - timedelta(hours=24)
        query = query.filter(HealthReport.report_date >= start_time)
    elif report_type == "weekly":
        start_time = now - timedelta(weeks=1)
        query = query.filter(HealthReport.report_date >= start_time)
    elif report_type == "monthly":
        start_time = now - timedelta(days=30)
        query = query.filter(HealthReport.report_date >= start_time)

    if report_type != "all":
        query = query.filter(HealthReport.report_type == report_type)

    reports = query.order_by(desc(HealthReport.report_date)).limit(limit).all()

    return schemas.BaseResponse(
        code=200,
        message="success",
        data={
            "reports": [
                {
                    "id": r.id,
                    "report_date": str(r.report_date),
                    "report_type": r.report_type,
                    "overall_score": r.overall_score,
                    "tongue_health_score": r.tongue_health_score,
                    "trend": r.trend,
                    "summary": r.summary,
                    "recommendations": r.recommendations
                }
                for r in reports
            ]
        }
    )

@router.get("/progress", response_model=schemas.BaseResponse)
async def get_health_progress(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    """获取指定天数内的健康进度数据"""
    start_date = date.today() - timedelta(days=days)
    
    progress_data = db.query(HealthProgress).filter(
        HealthProgress.user_id == user.id,
        HealthProgress.record_date >= start_date
    ).order_by(HealthProgress.record_date).all()
    
    return schemas.BaseResponse(
        code=200,
        message="success",
        data={
            "progress": [
                {
                    "date": str(p.record_date),
                    "tongue_color_score": p.tongue_color_score,
                    "coating_color_score": p.coating_color_score,
                    "thickness_score": p.thickness_score,
                    "greasy_score": p.greasy_score,
                    "overall_score": p.overall_score
                }
                for p in progress_data
            ]
        }
    )

@router.get("/recommendations", response_model=schemas.BaseResponse)
async def get_recommendations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = "all"
):
    """获取个性化健康建议"""
    query = db.query(HealthRecommendation).filter(
        HealthRecommendation.user_id == user.id,
        HealthRecommendation.is_active == 1
    )

    if category != "all":
        query = query.filter(HealthRecommendation.category == category)

    recommendations = query.order_by(HealthRecommendation.priority).all()

    ai_recommendation = generate_ai_recommendations(user, db)

    return schemas.BaseResponse(
        code=200,
        message="success",
        data={
            "recommendations": [
                {
                    "id": r.id,
                    "category": r.category,
                    "priority": r.priority,
                    "content": r.content,
                    "created_at": str(r.created_at) if r.created_at else None
                }
                for r in recommendations
            ],
            "ai_recommendation": ai_recommendation
        }
    )

@router.post("/report/generate", response_model=schemas.BaseResponse)
async def generate_health_report(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    report_type: str = "daily"
):
    """生成健康报告"""
    # 根据报告类型获取不同时间范围的数据
    now = datetime.now()
    if report_type == "daily":
        # 日报：最近24小时的数据
        start_time = now - timedelta(hours=24)
        limit = 100
    elif report_type == "weekly":
        # 周报：最近7天的数据
        start_time = now - timedelta(weeks=1)
        limit = 100
    else:  # monthly
        # 月报：最近30天的数据
        start_time = now - timedelta(days=30)
        limit = 100

    recent_analyses = db.query(TongueAnalysis).filter(
        TongueAnalysis.user_id == user.id,
        TongueAnalysis.state == 1
    ).order_by(desc(TongueAnalysis.id)).limit(limit).all()

    if not recent_analyses:
        return schemas.BaseResponse(
            code=400,
            message="暂无足够的舌象分析数据来生成报告",
            data=None
        )

    first_analysis_time = recent_analyses[0].created_at if recent_analyses[0].created_at else datetime.now()

    # 计算各项指标的平均值
    valid_analyses = [a for a in recent_analyses if a.tongue_color is not None and a.coating_color is not None and a.tongue_thickness is not None and a.rot_greasy is not None]

    if not valid_analyses:
        return schemas.BaseResponse(
            code=400,
            message="暂无足够的舌象分析数据来生成报告",
            data=None
        )

    avg_tongue_color = sum(a.tongue_color for a in valid_analyses) / len(valid_analyses)
    avg_coating_color = sum(a.coating_color for a in valid_analyses) / len(valid_analyses)
    avg_thickness = sum(a.tongue_thickness for a in valid_analyses) / len(valid_analyses)
    avg_greasy = sum(a.rot_greasy for a in valid_analyses) / len(valid_analyses)

    # 计算健康评分（简化版本）
    tongue_score = max(0, min(100, 100 - abs(avg_tongue_color - 50)))
    coating_score = max(0, min(100, 100 - abs(avg_coating_color - 50)))
    thickness_score = max(0, min(100, 100 - abs(avg_thickness - 50)))
    greasy_score = max(0, min(100, 100 - abs(avg_greasy - 50)))

    overall_score = (tongue_score + coating_score + thickness_score + greasy_score) / 4

    # 判断趋势
    if len(recent_analyses) >= 2:
        first_half = recent_analyses[:len(recent_analyses)//2]
        second_half = recent_analyses[len(recent_analyses)//2:]

        first_avg = sum(a.overall_score if hasattr(a, 'overall_score') else 50 for a in first_half) / len(first_half)
        second_avg = sum(a.overall_score if hasattr(a, 'overall_score') else 50 for a in second_half) / len(second_half)

        if second_avg > first_avg + 5:
            trend = "improving"
        elif second_avg < first_avg - 5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # 生成报告摘要和建议 - 根据报告类型和语言
    language = user.language or 'zh'
    summary_templates = {
        'daily': {
            'zh': f"基于最近{len(recent_analyses)}次舌象分析，您的整体健康评分为{overall_score:.1f}分。",
            'en': f"Based on the latest {len(recent_analyses)} tongue analyses, your overall health score is {overall_score:.1f}.",
            'ja': f"最近の{len(recent_analyses)}回の舌分析に基づき、総合健康スコアは{overall_score:.1f}点です。",
            'ko': f"최근 {len(recent_analyses)}회 혀 분석 기반으로 종합 건강 점수는 {overall_score:.1f}점입니다.",
            'de': f"Basierend auf den neuesten {len(recent_analyses)} Zungenanalysen beträgt Ihr Gesamtd Gesundheitsscore {overall_score:.1f}.",
            'es': f"Basándose en los últimos {len(recent_analyses)} análisis de lengua, su puntuación general de salud es {overall_score:.1f}.",
            'fr': f"Basé sur les derniers {len(recent_analyses)} analyses de langue, votre score de santé général est {overall_score:.1f}."
        },
        'weekly': {
            'zh': f"基于最近7天舌象分析，您的整体健康评分为{overall_score:.1f}分。",
            'en': f"Based on 7 days of tongue analyses, your overall health score is {overall_score:.1f}.",
            'ja': f"7日間の舌分析に基づき、総合健康スコアは{overall_score:.1f}点です。",
            'ko': f"7일간의 혀 분석 기반으로 종합 건강 점수는 {overall_score:.1f}점입니다.",
            'de': f"Basierend auf 7 Tagen Zungenanalysen beträgt Ihr Gesamtd Gesundheitsscore {overall_score:.1f}.",
            'es': f"Basándose en 7 días de análisis de lengua, su puntuación general de salud es {overall_score:.1f}.",
            'fr': f"Basé sur 7 jours d'analyses de langue, votre score de santé général est {overall_score:.1f}."
        },
        'monthly': {
            'zh': f"基于最近4周舌象分析，您的整体健康评分为{overall_score:.1f}分。",
            'en': f"Based on 4 weeks of tongue analyses, your overall health score is {overall_score:.1f}.",
            'ja': f"4週間の舌分析に基づき、総合健康スコアは{overall_score:.1f}点です。",
            'ko': f"4주간의 혀 분석 기반으로 종합 건강 점수는 {overall_score:.1f}점입니다.",
            'de': f"Basierend auf 4 Wochen Zungenanalysen beträgt Ihr Gesamtd Gesundheitsscore {overall_score:.1f}.",
            'es': f"Basándose en 4 semanas de análisis de lengua, su puntuación general de salud es {overall_score:.1f}.",
            'fr': f"Basé sur 4 semaines d'analyses de langue, votre score de santé général est {overall_score:.1f}."
        }
    }
    summary = summary_templates[report_type].get(language, summary_templates[report_type]['zh'])

    recommendations = "建议保持良好的作息习惯，注意饮食均衡。"
    
    # 创建健康报告
    new_report = HealthReport(
        user_id=user.id,
        report_date=first_analysis_time,
        report_type=report_type,
        overall_score=overall_score,
        tongue_health_score=tongue_score,
        trend=trend,
        summary=summary,
        recommendations=recommendations,
        created_at=first_analysis_time
    )
    
    db.add(new_report)
    
    # 同时保存进度记录
    new_progress = HealthProgress(
        user_id=user.id,
        record_date=first_analysis_time.date() if isinstance(first_analysis_time, datetime) else first_analysis_time,
        tongue_color_score=tongue_score,
        coating_color_score=coating_score,
        thickness_score=thickness_score,
        greasy_score=greasy_score,
        overall_score=overall_score,
        analysis_id=recent_analyses[0].id if recent_analyses else None
    )
    db.add(new_progress)
    
    db.commit()
    db.refresh(new_report)
    
    return schemas.BaseResponse(
        code=200,
        message="报告生成成功",
        data={
            "report_id": new_report.id,
            "overall_score": overall_score,
            "trend": trend
        }
    )

@router.post("/recommendation/add", response_model=schemas.BaseResponse)
async def add_recommendation(
    category: str,
    content: str,
    priority: int = 2,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加个性化建议"""
    new_rec = HealthRecommendation(
        user_id=user.id,
        category=category,
        priority=priority,
        content=content,
        is_active=1,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30)
    )
    
    db.add(new_rec)
    db.commit()
    
    return schemas.BaseResponse(
        code=200,
        message="建议添加成功",
        data={"id": new_rec.id}
    )

@router.put("/recommendation/{rec_id}/toggle", response_model=schemas.BaseResponse)
async def toggle_recommendation(
    rec_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """激活/停用建议"""
    rec = db.query(HealthRecommendation).filter(
        HealthRecommendation.id == rec_id,
        HealthRecommendation.user_id == user.id
    ).first()
    
    if not rec:
        raise HTTPException(status_code=404, detail="建议不存在")
    
    rec.is_active = 0 if rec.is_active == 1 else 1
    db.commit()
    
    return schemas.BaseResponse(
        code=200,
        message="操作成功",
        data={"is_active": rec.is_active}
    )

@router.get("/summary", response_model=schemas.BaseResponse)
async def get_health_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取健康概览"""
    # 获取总分析次数
    total_analyses = db.query(func.count(TongueAnalysis.id)).filter(
        TongueAnalysis.user_id == user.id,
        TongueAnalysis.state == 1
    ).scalar()
    
    # 获取最新报告
    latest_report = db.query(HealthReport).filter(
        HealthReport.user_id == user.id
    ).order_by(desc(HealthReport.report_date)).first()
    
    # 获取活动建议数量
    active_recommendations = db.query(func.count(HealthRecommendation.id)).filter(
        HealthRecommendation.user_id == user.id,
        HealthRecommendation.is_active == 1
    ).scalar()
    
    return schemas.BaseResponse(
        code=200,
        message="success",
        data={
            "total_analyses": total_analyses,
            "latest_report": {
                "id": latest_report.id,
                "overall_score": latest_report.overall_score,
                "trend": latest_report.trend,
                "report_date": str(latest_report.report_date)
            } if latest_report else None,
            "active_recommendations": active_recommendations
        }
    )
