from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text, Date
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)  # 自增主键
    email = Column(String(255))
    password = Column(String(255))
    language = Column(String(10), default='en')  # 用户语言偏好（默认英语）


class TongueAnalysis(Base):
    __tablename__ = 'TongueAnalysis'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    img_src = Column(String(255))
    state = Column(Integer)
    tongue_color = Column(Integer)
    coating_color = Column(Integer)
    tongue_thickness = Column(Integer)
    rot_greasy = Column(Integer)
    created_at = Column(DateTime)
    user = relationship('User')


class ChatSession(Base):
    __tablename__ = "chatSession"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.id"))
    title = Column(String)
    user = relationship("User")
    chat_records = relationship("ChatRecord")


class ChatRecord(Base):
    __tablename__ = "chatRecord"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chatSession.id"))
    content = Column(String)
    created_at = Column(Integer, nullable=False)
    role = Column(Integer)
    session = relationship("ChatSession")


# 健康跟踪相关模型
class HealthReport(Base):
    """健康报告表 - 存储定期生成的健康分析报告"""
    __tablename__ = 'HealthReport'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    report_date = Column(DateTime)  # 报告日期时间
    report_type = Column(String(50))  # 报告类型：daily, weekly, monthly
    overall_score = Column(Float)  # 整体健康评分 (0-100)
    tongue_health_score = Column(Float)  # 舌象健康评分
    trend = Column(String(20))  # 趋势：improving, stable, declining
    summary = Column(Text)  # 报告摘要
    recommendations = Column(Text)  # 主要建议
    created_at = Column(DateTime)  # 创建时间
    user = relationship('User')


class HealthProgress(Base):
    """健康进度表 - 存储每日/每周的健康指标"""
    __tablename__ = 'HealthProgress'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    record_date = Column(Date)  # 记录日期
    tongue_color_score = Column(Float)  # 舌色评分
    coating_color_score = Column(Float)  # 苔色评分
    thickness_score = Column(Float)  # 厚度评分
    greasy_score = Column(Float)  # 腻腐苔评分
    overall_score = Column(Float)  # 综合评分
    notes = Column(Text)  # 备注
    analysis_id = Column(Integer, ForeignKey('TongueAnalysis.id'))  # 关联的舌象分析
    user = relationship('User')
    tongue_analysis = relationship('TongueAnalysis')


class HealthRecommendation(Base):
    """个性化建议表 - 存储针对不同健康问题的建议"""
    __tablename__ = 'HealthRecommendation'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('User.id'))
    category = Column(String(50))  # 建议类别：diet, lifestyle, exercise, sleep
    priority = Column(Integer, default=1)  # 优先级：1-高，2-中，3-低
    content = Column(Text)  # 建议内容
    is_active = Column(Integer, default=1)  # 是否激活：1-是，0-否
    created_at = Column(DateTime)
    expires_at = Column(DateTime)  # 过期时间
    user = relationship('User')
