from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
import pytest_asyncio
from sqlalchemy import insert

from app.models.amenities import Amenity
from app.models.bookings import Booking
from app.models.properties import Property
from app.models.property_views import PropertyView
from app.models.association_tables import property_amenities
from app.db.enums import BookingStatus

pytestmark = pytest.mark.asyncio

SEARCH_URL = "/api/v1/properties/search"


def make_property(owner_id, title, **overrides):
    values = dict(
        owner_id=owner_id,
        title=title,
        price_per_night=Decimal("100.00"),
        country="Russia",
        city="Moscow",
        address=f"{title} street",
        rooms=2,
        beds=2,
        bathrooms=1,
        guest_capacity=4,
    )
    values.update(overrides)
    return Property(**values)


@pytest_asyncio.fixture
async def catalog(db_session, owner):
    cheap = make_property(owner.id, "Cheap", price_per_night=Decimal("50.00"), rating=Decimal("3.50"), review_count=2)
    middle = make_property(owner.id, "Middle", price_per_night=Decimal("120.00"), rooms=3, guest_capacity=6, rating=Decimal("4.90"), review_count=10)
    luxury = make_property(owner.id, "Luxury", price_per_night=Decimal("500.00"), rooms=5, guest_capacity=10, city="Sochi")
    db_session.add_all([cheap, middle, luxury])
    await db_session.flush()

    wifi = Amenity(name="Wi-Fi")
    parking = Amenity(name="Парковка")
    db_session.add_all([wifi, parking])
    await db_session.flush()

    await db_session.execute(insert(property_amenities).values([
        {"property_id": cheap.id, "amenity_id": wifi.id},
        {"property_id": middle.id, "amenity_id": wifi.id},
        {"property_id": middle.id, "amenity_id": parking.id},
    ]))

    today = date.today()
    views = [PropertyView(visitor_id=uuid4(), property_id=cheap.id, view_date=today) for _ in range(3)]
    views.append(PropertyView(visitor_id=uuid4(), property_id=luxury.id, view_date=today))
    # Старые просмотры не учитываются в популярности
    views += [PropertyView(visitor_id=uuid4(), property_id=luxury.id, view_date=today - timedelta(days=60)) for _ in range(5)]
    db_session.add_all(views)
    await db_session.flush()

    return {"cheap": cheap, "middle": middle, "luxury": luxury, "wifi": wifi, "parking": parking}


def titles(response):
    assert response.status_code == 200, response.text
    return [item["title"] for item in response.json()["properties"]]


async def test_search_by_city_case_insensitive(client, catalog):
    response = await client.get(SEARCH_URL, params={"city": "sochi"})

    assert titles(response) == ["Luxury"]


async def test_search_by_guests_and_rooms(client, catalog):
    response = await client.get(SEARCH_URL, params={"guest_capacity": 5, "rooms": 3, "sort_by": "price_asc"})

    assert titles(response) == ["Middle", "Luxury"]


async def test_search_by_price_range(client, catalog):
    response = await client.get(SEARCH_URL, params={"min_price": 60, "max_price": 200})

    assert titles(response) == ["Middle"]


async def test_search_by_amenities_requires_all(client, catalog):
    one = await client.get(SEARCH_URL, params={"amenity_ids": [catalog["wifi"].id], "sort_by": "price_asc"})
    both = await client.get(SEARCH_URL, params={"amenity_ids": [catalog["wifi"].id, catalog["parking"].id]})

    assert titles(one) == ["Cheap", "Middle"]
    assert titles(both) == ["Middle"]


async def test_search_excludes_booked_properties(client, db_session, api_user, catalog):
    check_in = datetime(2031, 1, 10, tzinfo=timezone.utc)
    db_session.add(Booking(
        property_id=catalog["cheap"].id,
        guest_id=api_user.id,
        check_in=check_in,
        check_out=check_in + timedelta(days=3),
        total_price=Decimal("150.00"),
        status=BookingStatus.CONFIRMED,
    ))
    # Истекшая pending-бронь не должна блокировать даты
    db_session.add(Booking(
        property_id=catalog["middle"].id,
        guest_id=api_user.id,
        check_in=check_in,
        check_out=check_in + timedelta(days=3),
        total_price=Decimal("360.00"),
        status=BookingStatus.PENDING,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    ))
    await db_session.flush()

    response = await client.get(SEARCH_URL, params={
        "check_in": "2031-01-11T00:00:00Z",
        "check_out": "2031-01-12T00:00:00Z",
        "sort_by": "price_asc",
    })

    assert titles(response) == ["Middle", "Luxury"]


async def test_sort_by_price(client, catalog):
    asc = await client.get(SEARCH_URL, params={"sort_by": "price_asc"})
    desc = await client.get(SEARCH_URL, params={"sort_by": "price_desc"})

    assert titles(asc) == ["Cheap", "Middle", "Luxury"]
    assert titles(desc) == ["Luxury", "Middle", "Cheap"]


async def test_sort_by_rating_puts_unrated_last(client, catalog):
    response = await client.get(SEARCH_URL, params={"sort_by": "rating"})

    assert titles(response) == ["Middle", "Cheap", "Luxury"]


async def test_sort_by_popularity(client, catalog):
    response = await client.get(SEARCH_URL, params={"sort_by": "popularity"})

    assert titles(response)[:2] == ["Cheap", "Luxury"]


async def test_search_pagination(client, catalog):
    response = await client.get(SEARCH_URL, params={"sort_by": "price_asc", "page": 2, "size": 2})

    data = response.json()
    assert titles(response) == ["Luxury"]
    assert data["total"] == 3
    assert data["pages"] == 2


@pytest.mark.parametrize("params", [
    {"sort_by": "unknown"},
    {"min_price": 300, "max_price": 100},
    {"check_in": "2031-01-11T00:00:00Z"},
    {"check_in": "2031-01-12T00:00:00Z", "check_out": "2031-01-11T00:00:00Z"},
    {"size": 0},
])
async def test_search_invalid_params(client, params):
    response = await client.get(SEARCH_URL, params=params)

    assert response.status_code == 422
