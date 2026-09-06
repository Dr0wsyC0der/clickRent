from fastapi import APIRouter, Depends, File, UploadFile, status
from app.schemas.property_image import PropertyImageResponse
from app.models.users import User
from app.services.property_image import PropertyImageService
from app.api.dependencies.property_image import get_property_image_service
from app.api.dependencies.auth import get_current_user


router = APIRouter(prefix="/property-images", tags=["property-images"])


@router.post("/", response_model=PropertyImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_property_image(
    property_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    property_image_service: PropertyImageService = Depends(
        get_property_image_service
    ),
):
    new_image = await property_image_service.add_image(
        property_id=property_id,
        user=current_user,
        file=file,
    )

    return new_image


@router.get( "/{property_id}", response_model=list[PropertyImageResponse], status_code=status.HTTP_200_OK)
async def get_property_images(
    property_id: int,
    property_image_service: PropertyImageService = Depends(
        get_property_image_service
    ),
):
    images = await property_image_service.get_images_by_property_id(
        property_id
    )

    return images


@router.delete( "/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    property_image_service: PropertyImageService = Depends(
        get_property_image_service
    ),
):
    await property_image_service.delete_image(
        image_id=image_id,
        user=current_user,
    )