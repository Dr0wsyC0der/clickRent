import pytest
from io import BytesIO
from app.models.property_images import PropertyImage
from PIL import Image


pytestmark = pytest.mark.asyncio


def image_file(
    filename: str = "test.jpg",
    content_type: str = "image/jpeg",
):
    image = Image.new("RGB", (100, 100), color="white")

    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    return {
        "file": (
            filename,
            buffer,
            content_type,
        )
    }


async def test_upload_property_image(
    client,
    owner,
    owner_property,
    owner_auth_headers,
):
    response = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(),
        headers=owner_auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["property_id"] == owner_property.id
    assert data["position"] == 1
    assert data["image_url"].startswith("/media/")
    assert data["id"] is not None


async def test_upload_property_image_without_auth(
    client,
    owner_property,
):
    response = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(),
    )

    assert response.status_code == 401


async def test_upload_property_image_property_not_found(
    client,
    owner_auth_headers,
):
    response = await client.post(
        "/api/v1/property-images/?property_id=999999",
        files=image_file(),
        headers=owner_auth_headers,
    )

    assert response.status_code == 404


async def test_upload_property_image_forbidden_for_other_user(
    client,
    owner_property,
    auth_headers,
):
    response = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(),
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_upload_invalid_property_image(
    client,
    owner_property,
    owner_auth_headers,
):
    response = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files={
            "file": (
                "test.txt",
                BytesIO(b"not an image"),
                "text/plain",
            )
        },
        headers=owner_auth_headers,
    )

    assert response.status_code == 415


async def test_get_property_images_empty(
    client,
    owner_property,
):
    response = await client.get(
        f"/api/v1/property-images/{owner_property.id}"
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_get_property_images(
    client,
    owner_property,
    owner_auth_headers,
):
    upload_response = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(),
        headers=owner_auth_headers,
    )

    assert upload_response.status_code == 201

    response = await client.get(
        f"/api/v1/property-images/{owner_property.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["property_id"] == owner_property.id
    assert data[0]["position"] == 1
    assert data[0]["image_url"].startswith("/media/")


async def test_get_property_images_property_not_found(
    client,
):
    response = await client.get(
        "/api/v1/property-images/999999"
    )

    assert response.status_code == 404


async def test_second_image_gets_position_two(
    client,
    owner_property,
    owner_auth_headers,
):
    response1 = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(filename="first.jpg"),
        headers=owner_auth_headers,
    )

    response2 = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(filename="second.jpg"),
        headers=owner_auth_headers,
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    data1 = response1.json()
    data2 = response2.json()

    assert data1["position"] == 1
    assert data2["position"] == 2


async def test_delete_property_image(
    client,
    owner_property,
    owner_auth_headers,
):
    upload_response = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(),
        headers=owner_auth_headers,
    )

    assert upload_response.status_code == 201

    image_id = upload_response.json()["id"]

    response = await client.delete(
        f"/api/v1/property-images/{image_id}",
        headers=owner_auth_headers,
    )

    assert response.status_code == 204


async def test_delete_property_image_without_auth(
    client,
    owner_property,
    owner_auth_headers,
):
    upload_response = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(),
        headers=owner_auth_headers,
    )

    assert upload_response.status_code == 201

    image_id = upload_response.json()["id"]

    response = await client.delete(
        f"/api/v1/property-images/{image_id}"
    )

    assert response.status_code == 401


async def test_delete_property_image_forbidden_for_other_user(
    client,
    owner_property,
    owner_auth_headers,
    auth_headers,
):
    upload_response = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(),
        headers=owner_auth_headers,
    )

    assert upload_response.status_code == 201

    image_id = upload_response.json()["id"]

    response = await client.delete(
        f"/api/v1/property-images/{image_id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


async def test_delete_property_image_not_found(
    client,
    owner_auth_headers,
):
    response = await client.delete(
        "/api/v1/property-images/999999",
        headers=owner_auth_headers,
    )

    assert response.status_code == 404


async def test_deleted_image_disappears_from_property_images(
    client,
    owner_property,
    owner_auth_headers,
):
    upload_response = await client.post(
        f"/api/v1/property-images/?property_id={owner_property.id}",
        files=image_file(),
        headers=owner_auth_headers,
    )

    assert upload_response.status_code == 201

    image_id = upload_response.json()["id"]

    delete_response = await client.delete(
        f"/api/v1/property-images/{image_id}",
        headers=owner_auth_headers,
    )

    assert delete_response.status_code == 204

    response = await client.get(
        f"/api/v1/property-images/{owner_property.id}"
    )

    assert response.status_code == 200
    assert response.json() == []