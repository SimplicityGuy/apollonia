"""Test GraphQL API."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_neo4j_session() -> Generator[AsyncMock, None, None]:
    """Mock Neo4j session."""
    with patch("api.database.get_neo4j_session") as mock:
        session = AsyncMock()
        mock.return_value.__aenter__.return_value = session
        yield session


class TestGraphQLQueries:
    """Test GraphQL queries."""

    def test_query_media_files(self, client: TestClient, mock_neo4j_session: AsyncMock) -> None:
        """Test querying media files via GraphQL."""
        mock_neo4j_session.run.return_value = Mock(
            data=Mock(
                return_value=[
                    {
                        "file": {
                            "id": "1",
                            "filename": "test1.mp3",
                            "media_type": "audio",
                            "size": 1024,
                        }
                    }
                ]
            )
        )

        query = """
        query {
            mediaFiles(limit: 10) {
                items {
                    id
                    filename
                    mediaType
                    size
                }
                total
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "mediaFiles" in data["data"]
        assert len(data["data"]["mediaFiles"]["items"]) == 1

    def test_query_single_media_file(
        self, client: TestClient, mock_neo4j_session: AsyncMock
    ) -> None:
        """Test querying a single media file."""
        mock_neo4j_session.run.return_value = Mock(
            single=Mock(
                return_value={
                    "file": {
                        "id": "test-123",
                        "filename": "test.mp3",
                        "media_type": "audio",
                        "size": 2048,
                    }
                }
            )
        )

        query = """
        query($id: ID!) {
            mediaFile(id: $id) {
                id
                filename
                mediaType
                size
                createdAt
            }
        }
        """

        response = client.post("/graphql", json={"query": query, "variables": {"id": "test-123"}})

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["mediaFile"]["id"] == "test-123"

    def test_search_query(self, client: TestClient, mock_neo4j_session: AsyncMock) -> None:
        """Test search via GraphQL."""
        mock_neo4j_session.run.return_value = Mock(
            data=Mock(return_value=[{"file": {"id": "1", "filename": "result.mp3"}}])
        )

        query = """
        query($query: String!, $mediaType: String) {
            search(query: $query, mediaType: $mediaType) {
                results {
                    id
                    filename
                    score
                }
                totalCount
                facets {
                    mediaTypes {
                        value
                        count
                    }
                }
            }
        }
        """

        response = client.post(
            "/graphql", json={"query": query, "variables": {"query": "test", "mediaType": "audio"}}
        )

        assert response.status_code == 200
        data = response.json()
        assert "search" in data["data"]
        assert len(data["data"]["search"]["results"]) == 1


class TestGraphQLMutations:
    """Test GraphQL mutations."""

    def test_create_media_file_mutation(
        self, client: TestClient, mock_neo4j_session: AsyncMock
    ) -> None:
        """Test creating a media file via GraphQL."""
        mock_neo4j_session.run.return_value = Mock(
            single=Mock(
                return_value={
                    "file": {
                        "id": "new-123",
                        "filename": "new.mp3",
                        "media_type": "audio",
                        "size": 1024,
                    }
                }
            )
        )

        mutation = """
        mutation($input: MediaFileInput!) {
            createMediaFile(input: $input) {
                id
                filename
                mediaType
                size
            }
        }
        """

        response = client.post(
            "/graphql",
            json={
                "query": mutation,
                "variables": {
                    "input": {
                        "path": "/data/new.mp3",
                        "filename": "new.mp3",
                        "mediaType": "audio",
                        "size": 1024,
                    }
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["createMediaFile"]["filename"] == "new.mp3"

    def test_update_media_file_mutation(
        self, client: TestClient, mock_neo4j_session: AsyncMock
    ) -> None:
        """Test updating a media file via GraphQL."""
        mock_neo4j_session.run.return_value = Mock(
            single=Mock(
                return_value={"file": {"id": "test-123", "filename": "test.mp3", "size": 2048}}
            )
        )

        mutation = """
        mutation($id: ID!, $input: MediaFileUpdateInput!) {
            updateMediaFile(id: $id, input: $input) {
                id
                size
            }
        }
        """

        response = client.post(
            "/graphql",
            json={"query": mutation, "variables": {"id": "test-123", "input": {"size": 2048}}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["updateMediaFile"]["size"] == 2048

    def test_delete_media_file_mutation(
        self, client: TestClient, mock_neo4j_session: AsyncMock
    ) -> None:
        """Test deleting a media file via GraphQL."""
        mock_neo4j_session.run.return_value = Mock(single=Mock(return_value={"deleted": True}))

        mutation = """
        mutation($id: ID!) {
            deleteMediaFile(id: $id) {
                success
                message
            }
        }
        """

        response = client.post(
            "/graphql", json={"query": mutation, "variables": {"id": "test-123"}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["deleteMediaFile"]["success"] is True


class TestGraphQLSubscriptions:
    """Test GraphQL subscriptions."""

    def test_media_updates_subscription(self, client: TestClient) -> None:
        """Test subscription query parsing."""
        subscription = """
        subscription {
            mediaUpdates {
                id
                filename
                event
                timestamp
            }
        }
        """

        # Just test that the subscription is accepted
        response = client.post("/graphql", json={"query": subscription})
        assert response.status_code == 200


class TestGraphQLErrors:
    """Test GraphQL error handling."""

    def test_invalid_query_syntax(self, client: TestClient) -> None:
        """Test handling of invalid GraphQL syntax."""
        query = """
        query {
            mediaFiles {
                invalid syntax here
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 400
        data = response.json()
        assert "errors" in data

    def test_field_not_found(self, client: TestClient) -> None:
        """Test querying non-existent fields."""
        query = """
        query {
            mediaFiles {
                items {
                    nonExistentField
                }
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 400
        data = response.json()
        assert "errors" in data

    def test_type_mismatch(self, client: TestClient) -> None:
        """Test type validation in GraphQL."""
        query = """
        query {
            mediaFile(id: 123) {
                id
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 400
        data = response.json()
        assert "errors" in data

    def test_resolver_error(self, client: TestClient, mock_neo4j_session: AsyncMock) -> None:
        """Test handling of resolver errors."""
        mock_neo4j_session.run.side_effect = Exception("Database error")

        query = """
        query {
            mediaFiles {
                items {
                    id
                }
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200  # GraphQL returns 200 with errors
        data = response.json()
        assert "errors" in data
        assert "Database error" in str(data["errors"])
