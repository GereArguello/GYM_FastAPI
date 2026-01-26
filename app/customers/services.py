from sqlmodel import Session
from app.customers.schemas import CustomerCreate
from app.customers.models import Customer
from app.auth.models import User
from app.core.security import get_password_hash
from app.core.enums import RoleEnum


def register_customer(session: Session, data: CustomerCreate) -> Customer:
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