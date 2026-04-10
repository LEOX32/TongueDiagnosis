from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from typing_extensions import Annotated
from ..core import create_access_token, get_current_user
from ..models import schemas
from ..models import models
from ..orm import register_user, login_user, get_user
from ..models.database import get_db

router_user = APIRouter()

@router_user.post('/register', response_model=schemas.RegisterResponse)
def register(schema: schemas.UserRegister, db: Session = Depends(get_db)):
    password = schema.password
    email = schema.email
    code = register_user(email=email, password=password, db=db)
    if code == 0:
        response = schemas.RegisterResponse(code=code, message='operation success')
    elif code == 101:
        response = schemas.RegisterResponse(code=code, message='has been registered')
    else:
        response = schemas.RegisterResponse(code=code, message='operation failed')
    return response

@router_user.put('/login', response_model=schemas.LoginResponse)
def login(
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    code = login_user(email=email, password=password, db=db)
    if code == 0:
        user = get_user(email=email, db=db)
        token = create_access_token(data={"ID": user.id, "email": email})
        access_token = token
        response = schemas.LoginResponse(
            code=code,
            message='operation success',
            data=schemas.Token(token=access_token)
        )
    elif code == 101:
        response = schemas.LoginResponse(
            code=code,
            message='operation failed',
            data=None
        )
    else:
        response = schemas.LoginResponse(
            code=code,
            message='wrong password',
            data=None
        )
    return response

@router_user.get('/info', response_model=schemas.InfoResponse)
def info_get(user: schemas.UserBase = Depends(get_current_user)):
    user_data_temp = schemas.UserBase(
        ID=user.id,
        email=user.email,
        language=user.language
    )
    return schemas.InfoResponse(
        code=0,
        message="operation success",
        data=user_data_temp
    )

@router_user.get('/record', response_model=schemas.RecordResponse)
def record_get(user: schemas.UserBase = Depends(get_current_user), db: Session = Depends(get_db)):
    user_record = db.query(models.TongueAnalysis).filter(
        models.TongueAnalysis.user_id == user.id
    ).all()
    data_temp = []
    for record in user_record:
        data_temp.append(schemas.Record(
            ID=record.id,
            user_ID=record.user_id,
            img_src=record.img_src,
            state=record.state,
            result=schemas.Result(
                tongue_color=record.tongue_color,
                coating_color=record.coating_color,
                tongue_thickness=record.tongue_thickness,
                rot_greasy=record.rot_greasy
            )
        ))
    return schemas.RecordResponse(
        code=0,
        message="operation success",
        data=data_temp
    )

@router_user.put('/language', response_model=schemas.LanguageResponse)
def update_language(
    language_request: schemas.LanguageRequest,
    user: schemas.UserBase = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    language = language_request.language
    if language not in ["en", "zh", "es", "fr", "de", "ja", "ko"]:
        return schemas.LanguageResponse(
            code=102,
            message="unsupported language",
            data=None
        )
    
    user.language = language
    try:
        db.commit()
        return schemas.LanguageResponse(
            code=0,
            message="language updated successfully",
            data={"language": language}
        )
    except Exception as e:
        db.rollback()
        return schemas.LanguageResponse(
            code=1,
            message=f"operation failed: {str(e)}",
            data=None
        )

@router_user.get('/language', response_model=schemas.LanguageResponse)
def get_language(
    user: schemas.UserBase = Depends(get_current_user)
):
    return schemas.LanguageResponse(
        code=0,
        message="operation success",
        data={"language": user.language if user.language else "en"}
    )
