from datetime import date
from app.models.property_views import PropertyView as PropertyViewModel
from app.repositories.property_view import PropertyViewRepository


class PropertyViewService:
    def __init__(self,property_view_repository: PropertyViewRepository,):
        self.property_view_repository = property_view_repository

    async def create_view(self,property_id: int,user_id: int | None = None,visitor_id=None,) -> PropertyViewModel | None:
        view = PropertyViewModel(
            user_id=user_id,
            visitor_id=visitor_id,
            property_id=property_id,
            view_date=date.today(),
        )

        try:
            await self.property_view_repository.create_view(view)
            await self.property_view_repository.commit()
        except Exception:
            await self.property_view_repository.rollback()
            raise