from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from datetime import timedelta

from app.auth.service import authenticate_user
from app.core.security import create_access_token
from app.core.database import get_session
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.schemas import Token
from app.auth.dependencies import check_admin
from app.auth.models import User



router = APIRouter(
    prefix="/auth",
    tags=["auth"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                session: Session = Depends(get_session)):
    user = authenticate_user(session=session,
                             email=form_data.username,
                             password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )

    access_token = create_access_token(
        data={"sub": user.id,"role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/admin")
async def admin_route(current_user: User = Depends(check_admin)):
    return {"msg": f"Hola {current_user.email}, bienvenido al panel de administrador"}