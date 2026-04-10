from sqlalchemy.orm import Session
from ...models import models
import time

def get_chat_record(ID: int, sessionid: int, db: Session):
    db_chat_session = db.query(models.ChatSession).filter(
        models.ChatSession.id == sessionid,
        models.ChatSession.user_id == ID
    ).first()

    if not db_chat_session:
        return 102  # No chat session found
    chat_records = db.query(models.ChatRecord).filter(
        models.ChatRecord.session_id == sessionid
    ).order_by(models.ChatRecord.created_at).all()

    if not chat_records:
        return 103  # No chat records found
    return chat_records

def get_all_chat_id(ID: int, db: Session):
    return db.query(models.ChatSession).filter(
        models.ChatSession.user_id == ID
    ).order_by(models.ChatSession.id).all()

def get_result(img_src: str, db: Session):
    result = db.query(models.TongueAnalysis).filter(models.TongueAnalysis.img_src == img_src).first()
    if result is None:
        return None
    db.refresh(result)
    return result

def create_new_session(db: Session,
                       ID: int,
                       tittle: str
                       ):
    new_message = models.ChatSession(
        title=tittle,
        user_id=ID
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

def create_new_chat_records(db: Session,
                            session_id: int,
                            content: str,
                            role: int
                       ):
    millis_timestamp = int(time.time() * 1000)
    new_message = models.ChatRecord(
        session_id=session_id,
        content=content,
        created_at=millis_timestamp,
        role=role
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

def delete_session(db: Session, session_id: int, user_id: int):
    # 检查会话是否存在且属于该用户
    db_session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == user_id
    ).first()
    
    if not db_session:
        return 102  # 会话不存在或不属于该用户
    
    try:
        # 删除该会话下的所有聊天记录
        db.query(models.ChatRecord).filter(
            models.ChatRecord.session_id == session_id
        ).delete()
        
        # 删除会话本身
        db.delete(db_session)
        db.commit()
        
        return 0  # 删除成功
    except Exception as e:
        db.rollback()
        print(f"删除会话失败: {e}")
        return 104  # 删除失败
