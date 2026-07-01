import pytest


class TestProjectAPI:
    def test_create_project(self, client):
        res = client.post("/api/projects", json={"name": "My Project", "source_lang": "en", "target_lang": "zh"})
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "My Project"
        assert data["total_segments"] == 0

    def test_list_projects(self, client):
        client.post("/api/projects", json={"name": "P1", "source_lang": "en", "target_lang": "zh"})
        res = client.get("/api/projects")
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_get_project_404(self, client):
        res = client.get("/api/projects/999")
        assert res.status_code == 404

    def test_delete_project(self, client):
        r = client.post("/api/projects", json={"name": "To Delete", "source_lang": "en", "target_lang": "fr"})
        pid = r.json()["id"]
        res = client.delete(f"/api/projects/{pid}")
        assert res.status_code == 204


class TestDocumentAPI:
    def test_upload_and_get_segments(self, client):
        r = client.post("/api/projects", json={"name": "Doc Test", "source_lang": "en", "target_lang": "zh"})
        pid = r.json()["id"]
        content = "First paragraph.\n\nSecond paragraph."
        files = {"file": ("test.txt", content.encode("utf-8"), "text/plain")}
        res = client.post(f"/api/projects/{pid}/documents", files=files)
        assert res.status_code == 201
        doc = res.json()
        assert doc["segment_count"] == 2
        seg_res = client.get(f"/api/documents/{doc['id']}")
        assert seg_res.status_code == 200
        segments = seg_res.json()
        assert len(segments) == 2
        assert segments[0]["source_text"] == "First paragraph."
        assert segments[0]["status"] == "untranslated"

    def test_list_documents(self, client):
        r = client.post("/api/projects", json={"name": "List Docs", "source_lang": "en", "target_lang": "zh"})
        pid = r.json()["id"]
        client.post(f"/api/projects/{pid}/documents", files={"file": ("a.txt", b"Hello", "text/plain")})
        client.post(f"/api/projects/{pid}/documents", files={"file": ("b.txt", b"World", "text/plain")})
        res = client.get(f"/api/projects/{pid}/documents")
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_delete_document(self, client):
        r = client.post("/api/projects", json={"name": "Del Doc", "source_lang": "en", "target_lang": "zh"})
        pid = r.json()["id"]
        doc = client.post(f"/api/projects/{pid}/documents", files={"file": ("x.txt", b"Hi", "text/plain")}).json()
        res = client.delete(f"/api/documents/{doc['id']}")
        assert res.status_code == 204


class TestSegmentAPI:
    @pytest.fixture
    def project_with_segment(self, client):
        r = client.post("/api/projects", json={"name": "Seg Test", "source_lang": "en", "target_lang": "zh"})
        pid = r.json()["id"]
        doc = client.post(f"/api/projects/{pid}/documents", files={"file": ("s.txt", b"Hello world", "text/plain")}).json()
        segs = client.get(f"/api/documents/{doc['id']}").json()
        return pid, segs[0]["id"]

    def test_update_translation(self, client, project_with_segment):
        pid, seg_id = project_with_segment
        res = client.put(f"/api/segments/{seg_id}", json={"target_text": "Ni hao shi jie", "status": "translated"})
        assert res.status_code == 200
        data = res.json()
        assert data["target_text"] == "Ni hao shi jie"
        assert data["status"] == "translated"

    def test_get_matches(self, client, project_with_segment):
        pid, seg_id = project_with_segment
        res = client.get(f"/api/segments/{seg_id}/matches")
        assert res.status_code == 200
        assert "matches" in res.json()

    def test_get_terms(self, client, project_with_segment):
        pid, seg_id = project_with_segment
        res = client.get(f"/api/segments/{seg_id}/terms")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
