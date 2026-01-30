from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.memberships.schemas import MembershipRead, MembershipCreate, MembershipUpdate
from app.memberships.models import Membership
from app.core.database import SessionDep
from app.core.enums import RoleEnum, StatusEnum
from app.auth.dependencies import check_admin, get_current_user_optional
from app.auth.models import User



router = APIRouter(
    prefix="/memberships",
    tags=["memberships"]
)

@router.post("/", response_model=MembershipRead, status_code=status.HTTP_201_CREATED)
def create_membership(membership_data: MembershipCreate,
                      session: SessionDep,
                      admin: User = Depends(check_admin)):
    
    membership = Membership(**membership_data.model_dump())

    try: 
        session.add(membership)
        session.commit()
        session.refresh(membership)
        return membership
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Datos de membresía inválidos")
    
@router.get("/", response_model=list[MembershipRead])
def list_memberships(
    session: SessionDep,
    status: StatusEnum | None = None,
    search: str | None = None,
    current_user: User | None = Depends(get_current_user_optional),
):
    query = select(Membership)

    if current_user and current_user.role == RoleEnum.ADMIN:
        # admin: control total
        if status:
            query = query.where(Membership.status == status)
    else:
        query = query.where(Membership.status == StatusEnum.ACTIVE)

    if search:
        query = query.where(Membership.name.ilike(f"%{search}%"))

    return session.exec(query).all()


@router.get("/{membership_id}", response_model=MembershipRead)
def read_membership(
    membership_id: int,
    session: SessionDep,
    include_inactive: bool = False,
    current_user: User | None = Depends(get_current_user_optional),
):
    query = select(Membership).where(Membership.id == membership_id)

    if not (current_user and current_user.role == RoleEnum.ADMIN and include_inactive):
        query = query.where(Membership.status == StatusEnum.ACTIVE)

    membership = session.exec(query).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membresía no encontrada"
        )

    return membership



@router.patch("/{membership_id}", response_model=MembershipRead, status_code=status.HTTP_200_OK)
def update_membership(membership_id: int,
                      membership_data: MembershipUpdate,
                      session: SessionDep,
                      admin: User = Depends(check_admin)):
    
    membership = session.get(Membership, membership_id)

    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membresía no encontrada")
    
    update_data = membership_data.model_dump(exclude_unset=True)

    membership.sqlmodel_update(update_data)
    try:
        session.commit()
        session.refresh(membership)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos de membresía inválidos"
        )

    return membership

@router.delete("/{membership_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership(membership_id: int,
                      session: SessionDep,
                      admin: User = Depends(check_admin)):
    membership = session.get(Membership, membership_id)

    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Membresía no encontrada")
    
    membership.status = StatusEnum.INACTIVE
    session.commit()
