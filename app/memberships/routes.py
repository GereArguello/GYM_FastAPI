from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.memberships.schemas import MembershipRead, MembershipCreate, MembershipUpdate
from app.memberships.models import Membership
from app.core.database import SessionDep


router = APIRouter(
    prefix="/memberships",
    tags=["memberships"]
)

@router.post("/", response_model=MembershipRead, status_code=status.HTTP_201_CREATED)
def create_membership(membership_data: MembershipCreate, session: SessionDep):
    if membership_data.points_multiplier < 1:
        raise HTTPException(
            status_code=400,
            detail="El multiplicador de puntos debe ser mayor o igual a 1"
        )
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
    include_inactive: bool = False, 
    search: str | None = None
):
    
    query = select(Membership)

    #--- A futuro los no activos solo serán visibles para el staff ---#
    
    if not include_inactive:
        query = query.where(Membership.is_active == True)

    if search:
        query = query.where(Membership.name.ilike(f"%{search}%"))
    
    return session.exec(query).all()

@router.get("/{membership_id}", response_model=MembershipRead)
def read_membership(membership_id: int, session: SessionDep):
    membership = session.get(Membership, membership_id)
    if not membership or not membership.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membresía no encontrada")
    return membership

@router.patch("/{membership_id}", response_model=MembershipRead, status_code=status.HTTP_200_OK)
def update_membership(membership_id: int, membership_data: MembershipUpdate, session: SessionDep):

    if membership_data.points_multiplier is not None and membership_data.points_multiplier < 1:
        raise HTTPException(
            status_code=400,
            detail="El multiplicador de puntos debe ser mayor o igual a 1"
        )
    
    membership = session.get(Membership, membership_id)

    if not membership or not membership.is_active:
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

@router.delete("/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership(membership_id: int, session: SessionDep):
    membership = session.get(Membership, membership_id)

    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Membresía no encontrada")
    
    session.delete(membership)
    session.commit()
