from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.reviews import Review as ReviewModel
from app.models.products import Product as ProductModel
from app.schemas import Review as ReviewSchema, ReviewCreate
from app.db_depends import get_async_db
from app.models.users import User as UserModel
from app.auth import get_current_seller, get_current_buyer, get_current_user

# Создаём маршрутизатор для отзывов
router = APIRouter(
    tags=["reviews"],
)


@router.get("/reviews/", response_model=list[ReviewSchema])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных отзывов
    """
    result = await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    reviews = result.all()
    return reviews


@router.get("/products/{product_id}/reviews/", response_model=list[ReviewSchema])
async def get_all_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных отзывов о конкретном товаре
    """
    product_result = await db.scalars(
        select(ProductModel).where(ProductModel.id == product_id,
                                    ProductModel.is_active == True)
    )
    product = product_result.first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found or inactive")

    result = await db.scalars(
        select(ReviewModel).where(ReviewModel.is_active == True, ReviewModel.product_id == product_id)
    )
    reviews = result.all()
    return reviews


@router.post("/reviews/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    review: ReviewCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_buyer)
):
    """
    Создаёт новый отзыв, привязанный к текущему пользователю (только для 'buyer') и продукту
    """
    product_result = await db.scalars(
        select(ProductModel).where(ProductModel.id == review.product_id,
                                   ProductModel.is_active == True)
    )
    product = product_result.first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found or inactive")

    db_review = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    await update_product_rating(db, review.product_id)
    return db_review


async def update_product_rating(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    product = await db.get(ProductModel, product_id)
    product.rating = avg_rating
    await db.commit()


@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Мягкое удаление отзыва, если он принадлежит текущему пользователю (только для 'buyer').
    """
    review_result = await db.scalars(
        select(ReviewModel).where(ReviewModel.id == review_id,
                                  ReviewModel.is_active == True)
    )
    review = review_result.first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or inactive")

    if current_user.role != "admin" and review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only administrators or reviewers can perform this action")

    await db.execute(
        update(ReviewModel).where(ReviewModel.id == review_id).values(is_active=False)
    )
    await db.commit()
    await update_product_rating(db, review.product_id)
    return {"message": "Review deleted"}
