"""System tests for Group API endpoints."""

import logging
import uuid

import pytest
from fastapi import status
from httpx import AsyncClient, Response

from app.models import GroupModel
from app.schemas.group_schema import (
    GroupCreateRequest,
    GroupMemberAddRequest,
    GroupMemberRoleUpdateRequest,
    GroupUpdateRequest,
)

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("reset_user_data_function")
class TestGroupAPI:
    """System tests for group creation, listing, detail, update, and member management."""

    async def _create_group(self, client: AsyncClient, auth_headers: dict, group_data: GroupModel) -> Response:
        """Create a group using the API."""
        return await client.post(
            "/groups",
            headers=auth_headers,
            json=GroupCreateRequest(
                name=group_data.name,
                description=group_data.description,
            ).model_dump(),
        )

    async def _update_group(
        self,
        client: AsyncClient,
        auth_headers: dict,
        group_id: str,
        group_data: GroupModel,
    ) -> Response:
        """Update a group using the API."""
        return await client.put(
            f"/groups/{group_id}",
            headers=auth_headers,
            json=GroupUpdateRequest(
                name=group_data.name,
                description=group_data.description,
            ).model_dump(),
        )

    @pytest.mark.asyncio
    async def test_create_group_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
        sample_group_data: GroupModel,
    ) -> None:
        """Test successful group creation."""
        response = await self._create_group(client, auth_token_header, sample_group_data)

        assert response.status_code == status.HTTP_200_OK, response.json()
        json_data = response.json()
        assert "data" in json_data
        assert "group" in json_data["data"]
        group = json_data["data"]["group"]
        assert group["name"] == sample_group_data.name
        assert group["description"] == sample_group_data.description
        assert "id" in group
        assert "created_by" in group
        assert "created_at" in group
        assert "updated_at" in group
        assert group["member_count"] == 1
        assert group["user_role"] == "Admin"

    @pytest.mark.asyncio
    async def test_create_group_unauthorized(self, client: AsyncClient, sample_group_data: GroupModel) -> None:
        """Test group creation without authentication."""
        response = await client.post(
            "/groups",
            json=GroupCreateRequest(
                name=sample_group_data.name,
                description=sample_group_data.description,
            ).model_dump(),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_list_groups_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
        sample_group_data: GroupModel,
    ) -> None:
        """Test successful group listing."""
        # Create a group first
        await self._create_group(client, auth_token_header, sample_group_data)

        response = await client.get("/groups", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "groups" in json_data["data"]
        assert "pagination" in json_data["data"]
        groups = json_data["data"]["groups"]
        assert len(groups) == 1
        assert groups[0]["name"] == sample_group_data.name
        assert groups[0]["description"] == sample_group_data.description

    @pytest.mark.asyncio
    async def test_list_groups_empty(self, client: AsyncClient, auth_token_header: dict) -> None:
        """Test listing groups when no groups exist."""
        response = await client.get("/groups", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "groups" in json_data["data"]
        assert "pagination" in json_data["data"]
        groups = json_data["data"]["groups"]
        assert len(groups) == 0

    @pytest.mark.asyncio
    async def test_list_groups_unauthorized(self, client: AsyncClient) -> None:
        """Test group listing without authentication."""
        response = await client.get("/groups")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_group_detail_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
        sample_group_data: GroupModel,
    ) -> None:
        """Test successful group detail retrieval."""
        # Create a group first
        create_response = await self._create_group(client, auth_token_header, sample_group_data)
        group_id = create_response.json()["data"]["group"]["id"]

        response = await client.get(f"/groups/{group_id}", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "group" in json_data["data"]
        group = json_data["data"]["group"]
        assert group["id"] == group_id
        assert group["name"] == sample_group_data.name
        assert group["description"] == sample_group_data.description

    @pytest.mark.asyncio
    async def test_get_group_detail_not_found(self, client: AsyncClient, auth_token_header: dict) -> None:
        """Test group detail retrieval for non-existent group."""
        fake_group_id = str(uuid.uuid4())
        response = await client.get(f"/groups/{fake_group_id}", headers=auth_token_header)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]["message"]

    @pytest.mark.asyncio
    async def test_get_group_detail_unauthorized(self, client: AsyncClient) -> None:
        """Test group detail retrieval without authentication."""
        fake_group_id = str(uuid.uuid4())
        response = await client.get(f"/groups/{fake_group_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_update_group_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
        sample_group_data: GroupModel,
    ) -> None:
        """Test successful group update."""
        # Create a group first
        create_response = await self._create_group(client, auth_token_header, sample_group_data)
        group_id = create_response.json()["data"]["group"]["id"]

        # Update the group data
        updated_group_data = GroupModel(
            id=uuid.uuid4(),
            name="Updated Test Group",
            description="Updated description for the test group",
            created_by=uuid.uuid4(),
        )

        response = await self._update_group(client, auth_token_header, group_id, updated_group_data)

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "group" in json_data["data"]
        group = json_data["data"]["group"]
        assert group["id"] == group_id
        assert group["name"] == updated_group_data.name
        assert group["description"] == updated_group_data.description

    @pytest.mark.asyncio
    async def test_update_group_not_found(
        self,
        client: AsyncClient,
        auth_token_header: dict,
        sample_group_data: GroupModel,
    ) -> None:
        """Test group update for non-existent group."""
        fake_group_id = str(uuid.uuid4())
        response = await self._update_group(client, auth_token_header, fake_group_id, sample_group_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]["message"]

    @pytest.mark.asyncio
    async def test_update_group_unauthorized(self, client: AsyncClient, sample_group_data: GroupModel) -> None:
        """Test group update without authentication."""
        fake_group_id = str(uuid.uuid4())
        response = await client.put(
            f"/groups/{fake_group_id}",
            json=GroupUpdateRequest(
                name=sample_group_data.name,
                description=sample_group_data.description,
            ).model_dump(),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_group_members_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
        sample_group_data: GroupModel,
    ) -> None:
        """Test successful group members listing."""
        # Create a group first
        create_response = await self._create_group(client, auth_token_header, sample_group_data)
        group_id = create_response.json()["data"]["group"]["id"]

        response = await client.get(f"/groups/{group_id}/members", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "members" in json_data["data"]
        assert "pagination" in json_data["data"]
        members = json_data["data"]["members"]
        assert len(members) == 1  # Creator is automatically added as admin
        assert members[0]["role"] == "Admin"

    @pytest.mark.asyncio
    async def test_get_group_members_not_found(self, client: AsyncClient, auth_token_header: dict) -> None:
        """Test group members listing for non-existent group."""
        fake_group_id = str(uuid.uuid4())
        response = await client.get(f"/groups/{fake_group_id}/members", headers=auth_token_header)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_group_members_unauthorized(self, client: AsyncClient) -> None:
        """Test group members listing without authentication."""
        fake_group_id = str(uuid.uuid4())
        response = await client.get(f"/groups/{fake_group_id}/members")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_delete_group_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
        sample_group_data: GroupModel,
    ) -> None:
        """Test successful group deletion."""
        # Create a group first
        create_response = await self._create_group(client, auth_token_header, sample_group_data)
        group_id = create_response.json()["data"]["group"]["id"]

        response = await client.delete(f"/groups/{group_id}", headers=auth_token_header)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify the group is deleted
        get_response = await client.get(f"/groups/{group_id}", headers=auth_token_header)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_group_not_found(self, client: AsyncClient, auth_token_header: dict) -> None:
        """Test group deletion for non-existent group."""
        fake_group_id = str(uuid.uuid4())
        response = await client.delete(f"/groups/{fake_group_id}", headers=auth_token_header)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]["message"]

    @pytest.mark.asyncio
    async def test_delete_group_unauthorized(self, client: AsyncClient) -> None:
        """Test group deletion without authentication."""
        fake_group_id = str(uuid.uuid4())
        response = await client.delete(f"/groups/{fake_group_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_add_group_member_invalid_email(
        self,
        client: AsyncClient,
        auth_token_header: dict,
        sample_group_data: GroupModel,
    ) -> None:
        """Test adding a group member with invalid email."""
        # Create a group first
        create_response = await self._create_group(client, auth_token_header, sample_group_data)
        group_id = create_response.json()["data"]["group"]["id"]

        response = await client.post(
            f"/groups/{group_id}/members",
            headers=auth_token_header,
            json=GroupMemberAddRequest(
                email="nonexistent@example.com",
                role="Member",
            ).model_dump(),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]["message"]

    @pytest.mark.asyncio
    async def test_update_member_role_not_found(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test updating member role for non-existent group."""
        fake_group_id = str(uuid.uuid4())
        fake_user_id = str(uuid.uuid4())

        response = await client.put(
            f"/groups/{fake_group_id}/members/{fake_user_id}/role",
            headers=auth_token_header,
            json=GroupMemberRoleUpdateRequest(role="Admin").model_dump(),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]["message"]

    @pytest.mark.asyncio
    async def test_remove_group_member_not_found(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test removing member from non-existent group."""
        fake_group_id = str(uuid.uuid4())
        fake_user_id = str(uuid.uuid4())

        response = await client.delete(
            f"/groups/{fake_group_id}/members/{fake_user_id}",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]["message"]

    @pytest.mark.asyncio
    async def test_group_pagination(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test group listing pagination."""
        # Create multiple groups
        for i in range(5):
            group_data = GroupModel(
                id=uuid.uuid4(),
                name=f"Test Group {i}",
                description=f"Description for test group {i}",
                created_by=uuid.uuid4(),
            )
            await self._create_group(client, auth_token_header, group_data)

        # Test pagination
        response = await client.get("/groups?page=1&limit=3", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "groups" in json_data["data"]
        assert "pagination" in json_data["data"]
        groups = json_data["data"]["groups"]
        pagination = json_data["data"]["pagination"]

        assert len(groups) == 3
        assert pagination["page"] == 1
        assert pagination["limit"] == 3
        assert pagination["total"] == 5
        assert pagination["pages"] == 2

    @pytest.mark.asyncio
    async def test_group_members_pagination(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test group members listing pagination."""
        # Create a group first
        group_data = GroupModel(
            id=uuid.uuid4(),
            name="Test Group for Members",
            description="A test group for member pagination",
            created_by=uuid.uuid4(),
        )
        create_response = await self._create_group(client, auth_token_header, group_data)
        group_id = create_response.json()["data"]["group"]["id"]

        # Test pagination (will have 1 member - the creator)
        response = await client.get(f"/groups/{group_id}/members?page=1&limit=10", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "members" in json_data["data"]
        assert "pagination" in json_data["data"]
        pagination = json_data["data"]["pagination"]

        assert pagination["page"] == 1
        assert pagination["limit"] == 10
        assert pagination["total"] == 1
        assert pagination["pages"] == 1
