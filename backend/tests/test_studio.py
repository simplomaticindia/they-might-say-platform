"""Test Studio Mode endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json


class TestStudio:
    """Test Studio Mode functionality."""

    def test_create_episode(self, client: TestClient, auth_headers):
        """Test creating a new episode."""
        response = client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={
                "title": "Test Episode",
                "description": "A test conversation with Lincoln"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Episode"
        assert data["description"] == "A test conversation with Lincoln"
        assert data["status"] == "active"
        assert "id" in data

    def test_get_episodes(self, client: TestClient, auth_headers):
        """Test getting list of episodes."""
        # Create a test episode first
        client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={
                "title": "Episode 1",
                "description": "First episode"
            }
        )

        response = client.get("/api/studio/episodes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["title"] == "Episode 1"

    def test_get_episode_by_id(self, client: TestClient, auth_headers):
        """Test getting a specific episode by ID."""
        # Create an episode first
        create_response = client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={
                "title": "Specific Episode",
                "description": "Episode for testing"
            }
        )
        episode_id = create_response.json()["id"]

        response = client.get(f"/api/studio/episodes/{episode_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == episode_id
        assert data["title"] == "Specific Episode"

    def test_update_episode_status(self, client: TestClient, auth_headers):
        """Test updating episode status."""
        # Create an episode first
        create_response = client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={"title": "Status Test Episode"}
        )
        episode_id = create_response.json()["id"]

        # Update status to paused
        response = client.put(
            f"/api/studio/episodes/{episode_id}/status",
            headers=auth_headers,
            json={"status": "paused"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"

    def test_delete_episode(self, client: TestClient, auth_headers):
        """Test deleting an episode."""
        # Create an episode first
        create_response = client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={"title": "To Be Deleted"}
        )
        episode_id = create_response.json()["id"]

        # Delete the episode
        response = client.delete(f"/api/studio/episodes/{episode_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/studio/episodes/{episode_id}", headers=auth_headers)
        assert get_response.status_code == 404

    @patch('services.rag_pipeline.RAGPipeline.generate_response')
    def test_conversation_endpoint(self, mock_generate, client: TestClient, auth_headers):
        """Test the conversation endpoint."""
        # Create an episode first
        create_response = client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={"title": "Conversation Test"}
        )
        episode_id = create_response.json()["id"]

        # Mock RAG response
        mock_generate.return_value = {
            "response": "I appreciate your question about the Union. A house divided against itself cannot stand.",
            "citations": [
                {
                    "id": "citation-1",
                    "citation_text": "A house divided against itself cannot stand",
                    "source_title": "House Divided Speech",
                    "confidence_score": 0.95,
                    "context_snippet": "I believe this government cannot endure permanently half slave and half free."
                }
            ],
            "metadata": {
                "context_chunks_used": 3,
                "model": "gpt-4",
                "response_time_ms": 1500
            }
        }

        response = client.post(
            "/api/studio/conversation",
            headers=auth_headers,
            json={
                "message": "What are your thoughts on preserving the Union?",
                "episode_id": episode_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "citations" in data
        assert len(data["citations"]) > 0
        assert data["citations"][0]["confidence_score"] == 0.95

    @patch('services.rag_pipeline.StreamingRAGPipeline.generate_streaming_response')
    def test_streaming_conversation(self, mock_stream, client: TestClient, auth_headers):
        """Test streaming conversation endpoint."""
        # Create an episode first
        create_response = client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={"title": "Streaming Test"}
        )
        episode_id = create_response.json()["id"]

        # Mock streaming response
        async def mock_stream_generator():
            yield {"type": "content", "content": "I appreciate "}
            yield {"type": "content", "content": "your question "}
            yield {"type": "content", "content": "about the Union."}
            yield {
                "type": "complete",
                "citations": [
                    {
                        "id": "citation-1",
                        "citation_text": "Test citation",
                        "source_title": "Test Source",
                        "confidence_score": 0.9
                    }
                ]
            }

        mock_stream.return_value = mock_stream_generator()

        response = client.post(
            "/api/studio/conversation/stream",
            headers=auth_headers,
            json={
                "message": "Tell me about the Union",
                "episode_id": episode_id
            }
        )
        assert response.status_code == 200
        # Note: Testing streaming responses requires special handling
        # This is a basic test to ensure the endpoint exists and responds

    def test_get_episode_beats(self, client: TestClient, auth_headers):
        """Test getting conversation beats for an episode."""
        # Create an episode first
        create_response = client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={"title": "Beats Test Episode"}
        )
        episode_id = create_response.json()["id"]

        response = client.get(f"/api/studio/episodes/{episode_id}/beats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_export_episode(self, client: TestClient, auth_headers):
        """Test exporting an episode."""
        # Create an episode first
        create_response = client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={"title": "Export Test Episode"}
        )
        episode_id = create_response.json()["id"]

        # Test JSON export
        response = client.get(
            f"/api/studio/episodes/{episode_id}/export?format=json",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "episode" in data
        assert "beats" in data
        assert "citations" in data

        # Test Markdown export
        response = client.get(
            f"/api/studio/episodes/{episode_id}/export?format=markdown",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"

    def test_conversation_validation(self, client: TestClient, auth_headers):
        """Test conversation input validation."""
        # Test empty message
        response = client.post(
            "/api/studio/conversation",
            headers=auth_headers,
            json={"message": ""}
        )
        assert response.status_code == 422

        # Test message too long
        long_message = "x" * 5000  # Assuming there's a length limit
        response = client.post(
            "/api/studio/conversation",
            headers=auth_headers,
            json={"message": long_message}
        )
        # This might be 422 or 413 depending on implementation
        assert response.status_code in [413, 422]

    def test_conversation_without_episode(self, client: TestClient, auth_headers):
        """Test conversation without specifying an episode."""
        response = client.post(
            "/api/studio/conversation",
            headers=auth_headers,
            json={"message": "Hello Lincoln"}
        )
        # Should either create a default episode or require episode_id
        assert response.status_code in [200, 422]

    def test_conversation_with_source_selection(self, client: TestClient, auth_headers):
        """Test conversation with specific source selection."""
        # Create a source first
        source_response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Test Source for Conversation",
                "source_type": "book"
            }
        )
        source_id = source_response.json()["id"]

        # Create an episode
        episode_response = client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={"title": "Source Selection Test"}
        )
        episode_id = episode_response.json()["id"]

        # Mock RAG response
        with patch('services.rag_pipeline.RAGPipeline.generate_response') as mock_generate:
            mock_generate.return_value = {
                "response": "Based on the selected source...",
                "citations": [],
                "metadata": {}
            }

            response = client.post(
                "/api/studio/conversation",
                headers=auth_headers,
                json={
                    "message": "What can you tell me?",
                    "episode_id": episode_id,
                    "source_ids": [source_id]
                }
            )
            assert response.status_code == 200

    def test_episode_statistics(self, client: TestClient, auth_headers):
        """Test getting episode statistics."""
        # Create some test episodes
        for i in range(3):
            client.post(
                "/api/studio/episodes",
                headers=auth_headers,
                json={
                    "title": f"Stats Test Episode {i}",
                    "status": "active" if i < 2 else "completed"
                }
            )

        response = client.get("/api/studio/episodes/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_episodes" in data
        assert "by_status" in data
        assert "total_beats" in data
        assert data["total_episodes"] >= 3

    def test_unauthorized_access(self, client: TestClient):
        """Test unauthorized access to studio endpoints."""
        endpoints = [
            "/api/studio/episodes",
            "/api/studio/conversation",
            "/api/studio/episodes/stats"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_episode_pagination(self, client: TestClient, auth_headers):
        """Test episode list pagination."""
        # Create multiple episodes
        for i in range(15):
            client.post(
                "/api/studio/episodes",
                headers=auth_headers,
                json={"title": f"Pagination Test Episode {i}"}
            )

        # Test first page
        response = client.get("/api/studio/episodes?limit=10&offset=0", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

        # Test second page
        response = client.get("/api/studio/episodes?limit=10&offset=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5  # Should have at least 5 more episodes

    def test_episode_search(self, client: TestClient, auth_headers):
        """Test searching episodes."""
        # Create episodes with different titles
        client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={"title": "Lincoln's Leadership Lessons"}
        )
        
        client.post(
            "/api/studio/episodes",
            headers=auth_headers,
            json={"title": "Civil War Discussions"}
        )

        # Search by title
        response = client.get("/api/studio/episodes/search?q=Leadership", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("Leadership" in episode["title"] for episode in data)