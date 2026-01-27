from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.security import decode_token
from app.core.enums import RoleEnum
from app.auth.models import User
from app.customers.models import Customer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)

async def get_current_user(token: str = Depends(oauth2_scheme),session: Session = Depends(get_session)) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Token inválido")
    
    user = session.get(User, int(user_id))

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Credenciales inválidas")

    return user

def get_current_customer(user: User = Depends(get_current_user), session: Session = Depends(get_session)) -> Customer:
    if user.role != RoleEnum.CUSTOMER:
        raise HTTPException(status.HTTP_403_FORBIDDEN,detail="Solo customers")

    customer = session.exec(
        select(Customer).where(Customer.user_id == user.id)
    ).first()

    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Customer no encontrado")

    return customer

def check_admin(user: User = Depends(get_current_user)):
    if user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos suficientes")
    return user

def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    session: Session = Depends(get_session),
) -> User | None:
    if not token:
        return None

    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        return None

    user = session.get(User, int(user_id))
    if not user or not user.is_active:
        return None

    return user
