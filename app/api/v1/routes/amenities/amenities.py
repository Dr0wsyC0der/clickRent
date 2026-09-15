from fastapi import APIRouter, Depends, status
from app.services.amenity import AmenityService
from app.schemas.amenity import AmenityCreate, AmenityResponse, AmenityUpdate
from app.api.dependencies.amenity import get_amenity_service
from app.api.dependencies.auth import check_admin


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

@router.post("/", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_admin)])
async def create_amenity(
    amenity_data: AmenityCreate,
    amenity_service: AmenityService = Depends(get_amenity_service),
):
    return await amenity_service.create_amenity(amenity_data)

@router.patch("/{amenity_id}", response_model=AmenityResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(check_admin)])
async def update_amenity(
    amenity_id: int,
    amenity_data: AmenityUpdate,
    amenity_service: AmenityService = Depends(get_amenity_service)
):
    updated_amenity = await amenity_service.update_amenity(
        amenity_id=amenity_id,
        amenity_data=amenity_data
    )
    return updated_amenity

@router.delete("/{amenity_id}",status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(check_admin)])
async def delete_amenity(
    amenity_id: int,
    amenity_service: AmenityService = Depends(get_amenity_service),
):
    await amenity_service.delete_amenity(
        amenity_id=amenity_id
    )
