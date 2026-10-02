from typing import Annotated
from fastapi import APIRouter, Depends, Query, status, Request, Response, WebSocket, WebSocketDisconnect
from uuid import UUID, uuid4
from app.models.users import User
from app.schemas.property import PropertyCreate, PropertyResponse, PropertyUpdate, PropertySearchParams, PropertySearchResponse, PropertyListParams
from app.services.property import PropertyService
from app.api.dependencies.property import get_property_service
from app.api.dependencies.property_view import get_property_view_service
from app.services.property_view import PropertyViewService
from app.schemas.amenity import AmenityResponse
from app.schemas.property_signal import PropertySignalsResponse
from app.services.property_signal import PropertySignalService
from app.api.dependencies.property_signal import get_property_signal_service
from app.api.dependencies.repositories import get_user_repository
from app.repositories.user import UserRepository
from app.exceptions.property import PropertyNotFoundException
from app.websocket.codes import WS_NOT_FOUND
from app.websocket.manager import property_viewers_manager
from app.api.dependencies.auth import (
    get_current_user,
    get_optional_current_user,
    check_host,
)

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

@router.get("/search", response_model=PropertySearchResponse, status_code=status.HTTP_200_OK)
async def search_properties(
    search_params: Annotated[PropertySearchParams, Query()],
    property_service: PropertyService = Depends(get_property_service)
):
    properties, total = await property_service.search_properties(search_params)
    pages = (total + search_params.size - 1) // search_params.size
    return PropertySearchResponse(
        properties=properties,
        total=total,
        page=search_params.page,
        size=search_params.size,
        pages=pages
    )

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

@router.get("/", response_model=PropertySearchResponse, status_code=status.HTTP_200_OK)
async def get_all_properties(
    property_service: PropertyService = Depends(get_property_service),
    params: PropertyListParams = Depends()
):
    properties, total = await property_service.get_all_properties(params)
    pages = (total + params.size - 1) // params.size
    return PropertySearchResponse(
        properties=properties,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages
    )

@router.get("/{property_id}",response_model=PropertyResponse,status_code=status.HTTP_200_OK)
async def get_property_by_id(
    property_id: int,
    request: Request,
    response: Response,
    current_user: User | None = Depends(get_optional_current_user),
    property_service: PropertyService = Depends(get_property_service),
    property_view_service: PropertyViewService = Depends(get_property_view_service),
):
    property = await property_service.get_property_by_id(property_id)

    if current_user:
        await property_view_service.create_view(
            property_id=property_id,
            user_id=current_user.id,
        )

    else:
        visitor_id = request.cookies.get("visitor_id")

        if visitor_id:
            try:
                visitor_uuid = UUID(visitor_id)
            except ValueError:
                visitor_uuid = uuid4()
        else:
            visitor_uuid = uuid4()

        response.set_cookie(
            key="visitor_id",
            value=str(visitor_uuid),
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 365,
        )

        await property_view_service.create_view(
            property_id=property_id,
            visitor_id=visitor_uuid,
        )

    return property

@router.post("/{property_id}/amenities/{amenity_id}", dependencies=[Depends(check_host)], status_code=status.HTTP_204_NO_CONTENT)
async def add_amenity_to_property(
    property_id: int,
    amenity_id: int,
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(get_property_service),
):
    await property_service.add_amenity_to_property(
        owner_id=current_user.id,
        property_id=property_id,
        amenity_id=amenity_id,
    )

@router.get("/{property_id}/amenities",response_model=list[AmenityResponse],status_code=status.HTTP_200_OK)
async def get_property_amenities(
    property_id: int,
    property_service: PropertyService = Depends(get_property_service),
):
    return await property_service.get_property_amenities(property_id)

@router.delete("/{property_id}/amenities/{amenity_id}", dependencies=[Depends(check_host)], status_code=status.HTTP_204_NO_CONTENT)
async def remove_amenity_from_property(
    property_id: int,
    amenity_id: int,
    current_user: User = Depends(get_current_user),
    property_service: PropertyService = Depends(get_property_service),
):
    await property_service.remove_amenity_from_property(
        owner_id=current_user.id,
        property_id=property_id,
        amenity_id=amenity_id,
    )

@router.get("/{property_id}/signals", response_model=PropertySignalsResponse, status_code=status.HTTP_200_OK)
async def get_property_signals(
    property_id: int,
    signal_service: PropertySignalService = Depends(get_property_signal_service),
):
    return await signal_service.get_signals(property_id)

@router.websocket("/{property_id}/viewers/ws")
async def property_viewers_websocket(
    websocket: WebSocket,
    property_id: int,
    token: str | None = Query(None, description="Необязательный access-токен: пользователь с несколькими вкладками считается один раз"),
    user_repository: UserRepository = Depends(get_user_repository),
    signal_service: PropertySignalService = Depends(get_property_signal_service),
):
    await websocket.accept()

    current_user = await get_optional_current_user(token=token, user_repository=user_repository) if token else None

    try:
        await signal_service.authorize_watching(property_id)
    except PropertyNotFoundException as exc:
        await websocket.close(code=WS_NOT_FOUND, reason=str(exc))
        return

    property_viewers_manager.connect(property_id, websocket, current_user.id if current_user else None)
    try:
        await signal_service.broadcast_viewers_count(property_id)
        # Клиент только слушает обновления; входящие сообщения (например, ping) игнорируются
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        property_viewers_manager.disconnect(property_id, websocket)
        await signal_service.broadcast_viewers_count(property_id)
