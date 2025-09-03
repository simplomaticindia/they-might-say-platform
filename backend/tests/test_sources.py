"""Test source management endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io


class TestSources:
    """Test source management functionality."""

    def test_create_source(self, client: TestClient, auth_headers):
        """Test creating a new source."""
        response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "The Gettysburg Address",
                "description": "Lincoln's famous speech at Gettysburg",
                "source_type": "speech",
                "author": "Abraham Lincoln",
                "publication_date": "1863-11-19",
                "reliability_score": 0.95,
                "tags": ["speech", "civil war", "gettysburg"]
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "The Gettysburg Address"
        assert data["source_type"] == "speech"
        assert data["author"] == "Abraham Lincoln"
        assert data["reliability_score"] == 0.95
        assert "id" in data

    def test_create_source_unauthorized(self, client: TestClient):
        """Test creating source without authentication."""
        response = client.post(
            "/api/sources",
            json={
                "title": "Test Source",
                "source_type": "book"
            }
        )
        assert response.status_code == 401

    def test_get_sources(self, client: TestClient, auth_headers, db_session):
        """Test getting list of sources."""
        # Create a test source first
        client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Test Source",
                "source_type": "book",
                "reliability_score": 0.8
            }
        )

        response = client.get("/api/sources", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["title"] == "Test Source"

    def test_get_source_by_id(self, client: TestClient, auth_headers):
        """Test getting a specific source by ID."""
        # Create a source first
        create_response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Specific Source",
                "source_type": "document",
                "reliability_score": 0.9
            }
        )
        source_id = create_response.json()["id"]

        response = client.get(f"/api/sources/{source_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == source_id
        assert data["title"] == "Specific Source"

    def test_get_nonexistent_source(self, client: TestClient, auth_headers):
        """Test getting a nonexistent source."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/sources/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_source(self, client: TestClient, auth_headers):
        """Test updating a source."""
        # Create a source first
        create_response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Original Title",
                "source_type": "book",
                "reliability_score": 0.7
            }
        )
        source_id = create_response.json()["id"]

        # Update the source
        response = client.put(
            f"/api/sources/{source_id}",
            headers=auth_headers,
            json={
                "title": "Updated Title",
                "description": "Updated description",
                "reliability_score": 0.85
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"
        assert data["reliability_score"] == 0.85

    def test_delete_source(self, client: TestClient, auth_headers):
        """Test deleting a source."""
        # Create a source first
        create_response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "To Be Deleted",
                "source_type": "article"
            }
        )
        source_id = create_response.json()["id"]

        # Delete the source
        response = client.delete(f"/api/sources/{source_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/sources/{source_id}", headers=auth_headers)
        assert get_response.status_code == 404

    @patch('services.file_processor.FileProcessor.process_file')
    def test_upload_document(self, mock_process, client: TestClient, auth_headers, sample_text_file):
        """Test uploading a document to a source."""
        # Create a source first
        create_response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Source with Document",
                "source_type": "book"
            }
        )
        source_id = create_response.json()["id"]

        # Mock file processing
        mock_process.return_value = {
            "word_count": 100,
            "character_count": 500,
            "processing_status": "completed"
        }

        # Upload document
        files = {
            "file": ("test.txt", sample_text_file, "text/plain")
        }
        response = client.post(
            f"/api/sources/{source_id}/documents",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
        assert "id" in data

    def test_upload_document_invalid_source(self, client: TestClient, auth_headers, sample_text_file):
        """Test uploading document to nonexistent source."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        files = {
            "file": ("test.txt", sample_text_file, "text/plain")
        }
        response = client.post(
            f"/api/sources/{fake_id}/documents",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 404

    def test_get_source_documents(self, client: TestClient, auth_headers):
        """Test getting documents for a source."""
        # Create a source first
        create_response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Source with Docs",
                "source_type": "book"
            }
        )
        source_id = create_response.json()["id"]

        response = client.get(f"/api/sources/{source_id}/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_sources(self, client: TestClient, auth_headers):
        """Test searching sources."""
        # Create test sources
        client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Lincoln Biography",
                "source_type": "book",
                "author": "David Herbert Donald",
                "tags": ["biography", "lincoln"]
            }
        )
        
        client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Civil War Letters",
                "source_type": "letter",
                "tags": ["civil war", "letters"]
            }
        )

        # Search by title
        response = client.get("/api/sources/search?q=Lincoln", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("Lincoln" in source["title"] for source in data)

        # Search by tag
        response = client.get("/api/sources/search?q=biography", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_filter_sources_by_type(self, client: TestClient, auth_headers):
        """Test filtering sources by type."""
        # Create sources of different types
        client.post(
            "/api/sources",
            headers=auth_headers,
            json={"title": "Test Book", "source_type": "book"}
        )
        
        client.post(
            "/api/sources",
            headers=auth_headers,
            json={"title": "Test Speech", "source_type": "speech"}
        )

        response = client.get("/api/sources?source_type=book", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(source["source_type"] == "book" for source in data)

    def test_filter_sources_by_reliability(self, client: TestClient, auth_headers):
        """Test filtering sources by reliability score."""
        # Create sources with different reliability scores
        client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "High Reliability Source",
                "source_type": "book",
                "reliability_score": 0.9
            }
        )
        
        client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Low Reliability Source",
                "source_type": "book",
                "reliability_score": 0.4
            }
        )

        response = client.get("/api/sources?min_reliability=0.8", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(source["reliability_score"] >= 0.8 for source in data)

    def test_source_validation(self, client: TestClient, auth_headers):
        """Test source data validation."""
        # Test missing required fields
        response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={"description": "Missing title and type"}
        )
        assert response.status_code == 422

        # Test invalid source type
        response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Test Source",
                "source_type": "invalid_type"
            }
        )
        assert response.status_code == 422

        # Test invalid reliability score
        response = client.post(
            "/api/sources",
            headers=auth_headers,
            json={
                "title": "Test Source",
                "source_type": "book",
                "reliability_score": 1.5  # Should be between 0 and 1
            }
        )
        assert response.status_code == 422

    def test_source_statistics(self, client: TestClient, auth_headers):
        """Test getting source statistics."""
        # Create some test sources
        for i in range(3):
            client.post(
                "/api/sources",
                headers=auth_headers,
                json={
                    "title": f"Test Source {i}",
                    "source_type": "book",
                    "reliability_score": 0.8
                }
            )

        response = client.get("/api/sources/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_sources" in data
        assert "by_type" in data
        assert "avg_reliability" in data
        assert data["total_sources"] >= 3