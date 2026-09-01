from fastapi import APIRouter, Depends, status
from app.models.users import User
from app.schemas.property import PropertyCreate, PropertyResponse, PropertyUpdate, PropertySearchParams, PropertyShortResponse
from app.services.property import PropertyService
from app.api.dependencies.property import get_property_service
from app.api.dependencies.auth import get_current_user, check_host

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("/", response_model=PropertyResponse, dependencies=[Depends(check_host)], status_code=status.HTTP_201_CREATED)
async def create_property(
    property_data: PropertyCreate,
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(get_property_service)
):
    new_property = await property_service.create_property(
        user_id=current_user.id,
        property_data=property_data
    )
    return new_property

@router.get("/search", response_model=list[PropertyShortResponse], status_code=status.HTTP_200_OK)
async def search_properties(
    search_params: PropertySearchParams = Depends(),
    property_service: PropertyService = Depends(get_property_service)
):
    return await property_service.search_properties(search_params)

@router.patch("/{property_id}", response_model=PropertyResponse, dependencies=[Depends(check_host)], status_code=status.HTTP_200_OK)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(get_property_service)
):
    updated_property = await property_service.update_property(
        owner_id=current_user.id,
        property_id=property_id,
        property_data=property_data
    )
    return updated_property

@router.delete("/{property_id}", dependencies=[Depends(check_host)], status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: int,
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(get_property_service)
):
    await property_service.delete_property(
        owner_id=current_user.id,
        property_id=property_id
    )

@router.get("/host", response_model=list[PropertyResponse],dependencies=[Depends(check_host)], status_code=status.HTTP_200_OK)
async def get_my_properties(
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(get_property_service)
):
    properties = await property_service.get_host_properties(current_user.id)
    return properties

@router.get("/", response_model=list[PropertyResponse], status_code=status.HTTP_200_OK)
async def get_all_properties(
    property_service: PropertyService = Depends(get_property_service)
):
    #ПОТОМ БУДЕТ ПАГИНАЦИЯ
    properties = await property_service.get_all_properties()
    return properties

@router.get("/{property_id}", response_model=PropertyResponse, status_code=status.HTTP_200_OK)
async def get_property_by_id(
    property_id: int,
    property_service: PropertyService = Depends(get_property_service)
):
    property = await property_service.get_property_by_id(property_id)
    return property




