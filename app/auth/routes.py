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


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="""
    Autentica a un usuario y devuelve un token de acceso JWT.

    Características:
    - Endpoint público.
    - Valida credenciales mediante email y contraseña.
    - Devuelve un token JWT para autenticación Bearer.
    - El token incluye el ID del usuario y su rol.
    - El token tiene una expiración configurable.

    Seguridad:
    - Contraseñas verificadas mediante hashing.
    - No expone información sensible en errores de autenticación.

    Requiere:
    - Credenciales válidas (email y contraseña).
    """,
    responses={
        200: {"description": "Autenticación exitosa"},
        401: {"description": "Usuario o contraseña incorrectos"},
    },
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(
        session=session,
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/admin")
async def admin_route(current_user: User = Depends(check_admin)):
    return {"msg": f"Hola {current_user.email}, bienvenido al panel de administrador"}