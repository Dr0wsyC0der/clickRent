from fastapi import APIRouter, Depends, status
from app.services.amenity import AmenityService
from app.schemas.amenity import AmenityCreate, AmenityResponse
from app.api.dependencies.amenity import get_amenity_service


router = APIRouter(prefix="/amenities", tags=["amenities"])


@router.get("/", response_model=list[AmenityResponse], status_code=status.HTTP_200_OK)
async def get_all_amenities(
    amenity_service: AmenityService = Depends(get_amenity_service)
):
    return await amenity_service.get_all_amenities()

@router.get("/{amenity_id}", response_model=AmenityResponse, status_code=status.HTTP_200_OK)
async def get_amenity_by_id(
    amenity_id: int,
    ameity_service: AmenityService = Depends(get_amenity_service)
):
    return await ameity_service.get_amenity_by_id(amenity_id=amenity_id)

