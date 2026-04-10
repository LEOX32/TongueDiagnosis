import os
import time
import asyncio
import concurrent.futures
import json
from fastapi import APIRouter, Depends, UploadFile, Body, Form, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from tempfile import SpooledTemporaryFile
from .ollama_used import OllamaStreamChatter
from ..core import get_current_user
from ..models import schemas
from ..models.database import get_db
from ..orm import write_event, write_result, get_record_by_location, get_chat_record, get_all_chat_id, create_new_session, create_new_chat_records, delete_session
from ..config import Settings
from ..net.predict import TonguePredictor
from ..config import settings

router_tongue_analysis = APIRouter()

# 创建全局线程池，用于处理多会话请求
# max_workers 设置为 10，允许同时处理多个会话
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

# OllamaStreamChatter 实例缓存，按语言和系统提示缓存
chatter_cache = {}

def get_chatter(language='en', system_prompt=None):
    """获取或创建 OllamaStreamChatter 实例，使用缓存减少初始化时间"""
    cache_key = f"{language}_{system_prompt}"
    if cache_key not in chatter_cache:
        chatter_cache[cache_key] = OllamaStreamChatter(
            system_prompt=system_prompt,
            language=language
        )
    return chatter_cache[cache_key]

# 多语言特征映射
feature_map = {
    'en': {
        "Color of the tongue": {
            0: "Pale white tongue",
            1: "Light red tongue",
            2: "Red tongue",
            3: "Crimson tongue",
            4: "Bluish-purple tongue"
        },
        "Color of the tongue coating": {
            0: "White coating",
            1: "Yellow tongue coating",
            2: "Gray-black tongue coating"
        },
        "Thickness of the tongue": {
            0: "Thin",
            1: "Thick"
        },
        "Decay and putrefaction of the tongue": {
            0: "Putrefaction",
            1: "Decay"
        }
    },
    'zh': {
        "舌头颜色": {
            0: "淡白舌",
            1: "淡红舌",
            2: "红舌",
            3: "绛舌",
            4: "青紫舌"
        },
        "舌苔颜色": {
            0: "白苔",
            1: "黄苔",
            2: "灰黑苔"
        },
        "舌头厚度": {
            0: "薄",
            1: "厚"
        },
        "腻腐程度": {
            0: "腐苔",
            1: "腻苔"
        }
    }
}

def format_tongue_features(tongue_color,
                           coating_color,
                           tongue_thickness,
                           rot_greasy,
                           language='zh'):
    try:
        # 默认使用中文，如果语言不在映射中也使用中文
        lang_map = feature_map.get(language, feature_map['zh'])
        
        # 根据语言选择特征描述
        if language == 'en':
            features = [
                f"Color of the tongue: {lang_map['Color of the tongue'][tongue_color]}",
                f"Color of the tongue coating: {lang_map['Color of the tongue coating'][coating_color]}",
                f"Thickness of the tongue: {lang_map['Thickness of the tongue'][tongue_thickness]}",
                f"Decay and putrefaction of the tongue: {lang_map['Decay and putrefaction of the tongue'][rot_greasy]}"
            ]
            return ", ".join(features)
        else:
            features = [
                f"舌头颜色：{lang_map['舌头颜色'][tongue_color]}",
                f"舌苔颜色：{lang_map['舌苔颜色'][coating_color]}",
                f"舌头厚度：{lang_map['舌头厚度'][tongue_thickness]}",
                f"腻腐程度：{lang_map['腻腐程度'][rot_greasy]}"
            ]
            return "，".join(features)
    except KeyError as e:
        error_msg = f"检测到无效特征值 {str(e)}，请检查输入范围"
        if language == 'en':
            error_msg = f"Invalid feature value detected: {str(e)}, please check input range"
        return error_msg


def create_error_stream(error_message: str, session_id: int):
    """创建错误信息的流式响应"""
    async def generate():
        # 模拟流式输出，逐字发送错误消息
        for char in error_message:
            chunk = {"token": char, "session_id": session_id}
            yield json.dumps(chunk) + "\n"
            await asyncio.sleep(0.02)  # 模拟打字速度
    return generate()


class UserInput(BaseModel):
    input: str
    language: str = 'zh'


@router_tongue_analysis.post('/session/{sessionId}')
async def continue_chat(sessionId: int,
                        user_input: UserInput,
                        user: schemas.UserBase = Depends(get_current_user),
                        db: Session = Depends(get_db),
                        ):
    bot = get_chatter(language=user_input.language, system_prompt=settings.SYSTEM_PROMPT)
    create_new_chat_records(db=db, content=user_input.input, session_id=sessionId, role=1)
    db.commit()
    return bot.chat_stream_add(user.id, db, sessionId)


@router_tongue_analysis.post('/session')
async def upload(file_data: UploadFile = File(...),
                user_input: str = Form(...),
                name: str = Form(...),
                 user: schemas.UserBase = Depends(get_current_user),
                 db: Session = Depends(get_db)
                 ):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(file_data.filename)[1]
    filename = f"{timestamp}{file_extension}"
    file_location = f"{Settings.IMG_PATH}/{filename}"
    with open(file_location, "wb") as f:
        contents = await file_data.read()
        f.write(contents)

    img_db_path = f"{Settings.IMG_DB_PATH}/{filename}"
    code = write_event(user_id=user.id, img_src=img_db_path, state=0, db=db)

    if code == 0:
        record = get_record_by_location(img_db_path, db=db)

        if record.state == 1:
            tongue_color = record.tongue_color
            coating_color = record.coating_color
            tongue_thickness = record.tongue_thickness
            rot_greasy = record.rot_greasy
            feature = format_tongue_features(tongue_color, coating_color, tongue_thickness, rot_greasy, user.language)
            bot = get_chatter(language=user.language, system_prompt=settings.SYSTEM_PROMPT)
            new_message = create_new_session(ID=user.id, db=db, tittle=name)
            session_new_id = new_message.id
            create_new_chat_records(db=db, content=user_input, session_id=session_new_id, role=1)
            return bot.chat_stream_first(user_input, feature, user.id, db, session_new_id)

        from tempfile import SpooledTemporaryFile
        file_data.file.seek(0)
        temp_file = SpooledTemporaryFile()
        temp_file.write(file_data.file.read())
        temp_file.seek(0)

        predictor = TonguePredictor(use_sparse_attention=False, use_improved_resnet=True, use_multi_output=True, use_yolo_sam_joint=True)
        predictor.predict(img=temp_file, record_id=record.id, fun=write_result, db=db)

        temp_file.close()
        
        # 获取分析结果
        result = get_record_by_location(img_db_path, db=db)
        if result is None or result.state != 1:
            # 分析失败，检查是否是因为没有检测到舌头
            if result and result.state == 201:
                # 没有检测到舌头，创建会话并让 AI 输出提示
                new_message = create_new_session(ID=user.id, db=db, tittle=name)
                session_new_id = new_message.id
                create_new_chat_records(db=db, content=user_input, session_id=session_new_id, role=1)
                
                # 根据用户语言生成提示信息
                error_messages = {
                    'zh': '抱歉，我没有在图片中检测到舌头。请确保上传的是清晰的舌头正面照片，光线充足，舌头自然伸出。',
                    'en': "Sorry, I couldn't detect a tongue in the image. Please make sure to upload a clear frontal photo of your tongue with good lighting and your tongue naturally extended.",
                    'es': 'Lo siento, no pude detectar una lengua en la imagen. Por favor, asegúrese de subir una foto frontal clara de su lengua con buena iluminación y la lengua naturalmente extendida.',
                    'fr': "Désolé, je n'ai pas pu détecter de langue dans l'image. Veuillez vous assurer de télécharger une photo frontale claire de votre langue avec un bon éclairage et votre langue naturellement étendue.",
                    'de': 'Entschuldigung, ich konnte keine Zunge im Bild erkennen. Bitte stellen Sie sicher, dass Sie ein klares Frontalfoto Ihrer Zunge mit guter Beleuchtung und natürlich ausgestreckter Zunge hochladen.',
                    'ja': '申し訳ありませんが、画像に舌が検出されませんでした。明るい照明の下で、舌を自然に突き出した明確な正面写真を撮影してアップロードしてください。',
                    'ko': '죄송합니다. 이미지에서 혀가 감지되지 않았습니다. 충분한 조명 아래에서 혀를 자연스럽게 내민 명확한 정면 사진을 업로드해 주세요.'
                }
                error_message = error_messages.get(user.language, error_messages['en'])
                
                # 创建 AI 回复记录
                create_new_chat_records(db=db, content=error_message, session_id=session_new_id, role=0)
                db.commit()
                
                # 返回流式响应
                return StreamingResponse(
                    create_error_stream(error_message, session_new_id),
                    media_type="application/x-ndjson"
                )
            else:
                # 其他错误情况
                new_message = create_new_session(ID=user.id, db=db, tittle=name)
                session_new_id = new_message.id
                create_new_chat_records(db=db, content=user_input, session_id=session_new_id, role=1)
                
                error_message = f"图片分析失败，错误码：{result.state if result else 500}"
                create_new_chat_records(db=db, content=error_message, session_id=session_new_id, role=0)
                db.commit()
                
                # 返回流式响应
                return StreamingResponse(
                    create_error_stream(error_message, session_new_id),
                    media_type="application/x-ndjson"
                )
        
        tongue_color = result.tongue_color
        coating_color = result.coating_color
        tongue_thickness = result.tongue_thickness
        rot_greasy = result.rot_greasy
        feature = format_tongue_features(tongue_color, coating_color, tongue_thickness, rot_greasy, user.language)
        bot = get_chatter(language=user.language, system_prompt=settings.SYSTEM_PROMPT)
        new_message = create_new_session(ID=user.id, db=db, tittle=name)
        session_new_id = new_message.id
        create_new_chat_records(db=db, content=user_input, session_id=session_new_id, role=1)
        return bot.chat_stream_first(user_input, feature, user.id, db, session_new_id)
    else:
        return schemas.UploadResponse(
            code=201,
            message="operation failed",
            data=None
        )

@router_tongue_analysis.get("/record/{sessionid}", response_model=schemas.ChatSessionRecordsResponse)
async def get_chat_records_by_session(sessionid: int,
                                      db: Session = Depends(get_db),
                                      user: schemas.UserBase = Depends(get_current_user)
                                      ):
    chat_record = get_chat_record(ID=user.id, sessionid=sessionid, db=db)
    if chat_record == 102 or chat_record == 103:
        return schemas.ChatSessionRecordsResponse(
            code=chat_record,
            message="operation failed",
            data={"records": []}
        )
    records = []
    for record in chat_record:
        records.append(schemas.ChatRecordResponse(
            content=record.content,
            create_at=record.created_at,
            role=record.role
        ))
    data_temp = {
        "records": records
    }
    return schemas.ChatSessionRecordsResponse(
        code=0,
        message="operation success",
        data=data_temp,
    )

@router_tongue_analysis.get("/session", response_model=schemas.SessionIdResponse)
async def get_chat_records_id(db: Session = Depends(get_db),
                              user: schemas.UserBase = Depends(get_current_user)):
    chat_id_records = get_all_chat_id(ID=user.id, db=db)
    data_temp = []
    for record in chat_id_records:
        data_temp.append(schemas.SessionId(
            session_id=record.id,
            name=record.title
        ))
    return schemas.SessionIdResponse(
        code=0,
        message="operation success",
        data=data_temp
    )


@router_tongue_analysis.delete("/record/{sessionid}", response_model=schemas.BaseResponse)
async def delete_chat_record(sessionid: int,
                            user: schemas.UserBase = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    result = delete_session(db=db, session_id=sessionid, user_id=user.id)
    if result == 0:
        return schemas.BaseResponse(
            code=0,
            message="operation success",
            data=None
        )
    else:
        return schemas.BaseResponse(
            code=result,
            message="operation failed",
            data=None
        )
