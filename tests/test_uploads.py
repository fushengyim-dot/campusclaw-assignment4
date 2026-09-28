import os
import sqlite3
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

os.environ["CAMPUSCLAW_SKIP_APP"] = "1"
from app import create_app  # noqa: E402


class MaterialUploadTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database = self.root / "test.db"
        self.upload_dir = self.root / "uploads"
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-only-secret",
                "DATABASE": str(self.database),
                "UPLOAD_FOLDER": str(self.upload_dir),
                "SEED_TEACHER_PASSWORD": "teacher-a-pass",
                "SEED_STUDENT_A_PASSWORD": "student-a-pass",
                "SEED_STUDENT_B_PASSWORD": "student-b-pass",
            }
        )
        self.client = self.app.test_client()
        self.client.post(
            "/login",
            data={"username": "teacher_a", "password": "teacher-a-pass"},
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def upload(self, name, content):
        return self.client.post(
            "/materials/upload",
            data={"file": (BytesIO(content), name)},
            content_type="multipart/form-data",
        )

    def rows(self, query, params=()):
        connection = sqlite3.connect(self.database)
        try:
            connection.row_factory = sqlite3.Row
            return connection.execute(query, params).fetchall()
        finally:
            connection.close()

    def test_upload_page_explains_supported_types(self):
        response = self.client.get("/materials")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b".txt / .md", response.data)
        self.assertIn("改扩展名也不能转换格式".encode(), response.data)
        self.assertIn(b"knowledge-search-form", response.data)
        self.assertIn(b"/static/search.js", response.data)

    def test_other_extension_is_rejected_without_database_write(self):
        before = len(self.rows("SELECT id FROM materials"))
        response = self.upload("lesson.pdf", b"not a supported extension")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(self.rows("SELECT id FROM materials")), before)

    def test_renamed_pdf_is_rejected_without_database_write(self):
        before = len(self.rows("SELECT id FROM materials"))
        response = self.upload("lesson.txt", b"%PDF-1.7\nnot plain text")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(self.rows("SELECT id FROM materials")), before)

    def test_duplicate_names_are_numbered_and_old_file_is_preserved(self):
        first_content = "第一份课堂笔记".encode("utf-8")
        second_content = "第二份课堂笔记".encode("utf-8")
        self.assertEqual(self.upload("lesson.md", first_content).status_code, 302)
        self.assertEqual(self.upload("lesson.md", second_content).status_code, 302)

        materials = self.rows(
            "SELECT id, filename, storage_name FROM materials "
            "WHERE class_id = 'A' AND filename IN (?, ?) ORDER BY id",
            ("lesson.md", "lesson (1).md"),
        )
        self.assertEqual([row["filename"] for row in materials], ["lesson.md", "lesson (1).md"])
        self.assertNotEqual(materials[0]["storage_name"], materials[1]["storage_name"])
        self.assertEqual((self.upload_dir / materials[0]["storage_name"]).read_bytes(), first_content)
        self.assertEqual((self.upload_dir / materials[1]["storage_name"]).read_bytes(), second_content)

    def test_same_class_student_can_view_and_download_original_file(self):
        content = "同班可见内容".encode("utf-8")
        self.assertEqual(self.upload("class-note.md", content).status_code, 302)
        material = self.rows(
            "SELECT id FROM materials WHERE class_id = 'A' AND filename = ?",
            ("class-note.md",),
        )[0]

        teacher_download = self.client.get(f"/materials/{material['id']}/download")
        self.assertEqual(teacher_download.status_code, 200)
        self.assertEqual(teacher_download.data, content)
        teacher_download.close()

        student = self.app.test_client()
        student.post("/login", data={"username": "student_a1", "password": "student-a-pass"})
        detail = student.get(f"/materials/{material['id']}")
        download = student.get(f"/materials/{material['id']}/download")

        self.assertEqual(detail.status_code, 200)
        self.assertIn(content, detail.data)
        self.assertIn(b"\xe4\xb8\x8b\xe8\xbd\xbd\xe5\x8e\x9f\xe5\xa7\x8b\xe6\x96\x87\xe4\xbb\xb6", detail.data)
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.data, content)
        self.assertIn("class-note.md", download.headers["Content-Disposition"])
        download.close()

    def test_other_class_cannot_view_or_download_material(self):
        self.assertEqual(self.upload("class-note.md", b"A class only").status_code, 302)
        material = self.rows(
            "SELECT id FROM materials WHERE class_id = 'A' AND filename = ?",
            ("class-note.md",),
        )[0]

        student = self.app.test_client()
        student.post("/login", data={"username": "student_b1", "password": "student-b-pass"})
        detail = student.get(f"/materials/{material['id']}")
        download = student.get(f"/materials/{material['id']}/download")

        self.assertEqual(detail.status_code, 404)
        self.assertNotIn(b"A class only", detail.data)
        self.assertEqual(download.status_code, 404)
        self.assertNotIn(b"A class only", download.data)

    def test_unauthenticated_download_redirects_to_login(self):
        response = self.client.get("/materials")
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            session.clear()
        download = self.client.get("/materials/1/download")
        self.assertEqual(download.status_code, 302)
        self.assertIn("/login", download.headers["Location"])

    def test_search_returns_same_class_source_metadata(self):
        self.assertEqual(self.upload("search-note.md", "A班检索目标内容".encode()).status_code, 302)
        response = self.client.get("/api/knowledge/search?q=检索目标")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["class_id"], "A")
        self.assertEqual(payload["results"][0]["source_filename"], "search-note.md")
        self.assertIn("A班检索目标内容", payload["results"][0]["content"])

    def test_search_requires_login_and_respects_class_scope(self):
        self.assertEqual(self.upload("private-note.md", "A班私有检索词".encode()).status_code, 302)
        anonymous = self.app.test_client().get("/api/knowledge/search?q=私有检索词")
        self.assertEqual(anonymous.status_code, 401)

        student = self.app.test_client()
        student.post("/login", data={"username": "student_b1", "password": "student-b-pass"})
        response = student.get("/api/knowledge/search?q=私有检索词")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["results"], [])


if __name__ == "__main__":
    unittest.main()
