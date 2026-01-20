from fastapi import APIRouter, status, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from app.core.database import SessionDep
from app.shop.models import Product
from app.shop.schemas import ProductRead, ProductCreate, ProductUpdate

router = APIRouter(prefix="/shop",
                   tags=["shop"])

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(product_data: ProductCreate, session: SessionDep):
    product = Product(**product_data.model_dump())

    if product_data.price < 0: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="El precio no puede ser negativo")
        
    if product.stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El stock no puede ser negativo"
        )
    
    try:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un producto con ese nombre"
        )

@router.get("/", response_model=list[ProductRead], status_code=status.HTTP_200_OK)
def list_products(session: SessionDep, include_inactive: bool = False):
    query = select(Product)

    if not include_inactive:
        query= query.where(Product.is_active == True)

    return session.exec(query).all()

@router.get("/{product_id}", response_model=ProductRead)
def read_product(product_id: int, session: SessionDep):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Producto no encontrado")
    return product
    
@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    session: SessionDep
):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    # Solo validar si el nombre cambia
    if (
        product_data.name is not None
        and product_data.name != product.name
    ):
        product.name = product_data.name

    if product_data.description is not None:
        product.description = product_data.description

    if product_data.price is not None:
        if product_data.price < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="El precio no puede ser negativo")
        product.price = product_data.price

    if product_data.stock is not None:
        if product_data.stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El stock no puede ser negativo"
            )
        product.stock = product_data.stock

    try:
        session.commit()
        session.refresh(product)
        return product

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un producto con ese nombre"
        )
    
@router.patch("/{product_id}/activate", response_model=ProductRead)
def activate_product(product_id: int,session: SessionDep):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    product.is_active = True
    session.commit()
    session.refresh(product)
    return product
    
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, session: SessionDep):
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )

    product.is_active = False
    session.commit()
    session.refresh(product)