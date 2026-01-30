from sqlmodel import Session
from datetime import datetime, timedelta
from app.customers.schemas import CustomerCreate
from app.customers.models import Customer
from app.auth.models import User
from app.core.security import get_password_hash
from app.core.enums import RoleEnum


def register_customer(session: Session, data: CustomerCreate) -> Customer:
    """
    Registra un nuevo cliente en el sistema.

    Crea el usuario asociado con rol CUSTOMER y genera la entidad Customer
    vinculada dentro de la misma transacción.
    """
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role=RoleEnum.CUSTOMER,
        is_active=True
    )

    session.add(user)
    session.flush()  # genera user.id

    customer = Customer(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        birth_date=data.birth_date
    )

    session.add(customer)
    session.commit()
    session.refresh(customer)

    return customer


def obtener_ultimo_dia(fecha: datetime):
    """Devuelve el último día del mes y el primer día del mes siguiente."""
    
    # 1. Ir al primer día del mes siguiente
    if fecha.month == 12:
        primer_dia_siguiente = datetime(fecha.year + 1, 1, 1)
    else:
        primer_dia_siguiente = datetime(fecha.year, fecha.month + 1, 1)
    
    # 2. Restar un día
    ultimo_dia = primer_dia_siguiente - timedelta(days=1)

    return ultimo_dia.date(), primer_dia_siguiente.date()