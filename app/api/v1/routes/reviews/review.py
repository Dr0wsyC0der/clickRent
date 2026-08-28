from fastapi import APIRouter, Depends, status
from app.models.users import User
from app.schemas.review import CreateReview, UpdateReview, ReviewResponse
from app.services.review import ReviewService
from app.api.dependencies.review import get_review_service
from app.api.dependencies.auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: CreateReview,
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service)
):
    new_review = await review_service.create_review(
        user_id=current_user.id,
        review_data=review_data
    )
    return new_review

@router.get("/property/{property_id}", response_model=list[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_property_reviews(
    property_id: int,
    review_service: ReviewService = Depends(get_review_service)
):
    reviews = await review_service.get_property_reviews(property_id=property_id)
    return reviews

@router.get("/{review_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def get_review_by_id(
    review_id: int,
    review_service: ReviewService = Depends(get_review_service)
):
    review = await review_service.get_review_by_id(review_id=review_id)
    return review

@router.patch("/{review_id}", response_model=ReviewResponse, status_code=status.HTTP_200_OK)
async def update_review(
    review_id: int,
    review_data: UpdateReview,
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service)
):
    updated_review = await review_service.update_review(
        user_id=current_user.id,
        review_id=review_id,
        review_data=review_data
    )
    return updated_review

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service)
):
    await review_service.delete_review(
        user_id=current_user.id,
        review_id=review_id
    )   
