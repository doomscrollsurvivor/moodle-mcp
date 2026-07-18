import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from moodle_mcp import api


class Phase3DownloadTests(unittest.TestCase):
    def test_append_moodle_token_adds_token_param_without_exposing_result_to_logs(self):
        url = api._append_moodle_token("https://moodle.test/pluginfile.php/1/mod_resource/content/file.pdf", "secret-token")
        self.assertIn("token=secret-token", url)
        self.assertIn("pluginfile.php", url)

    def test_download_file_sanitizes_filename_and_writes_bytes(self):
        response = Mock()
        response.status_code = 200
        response.content = b"PDFDATA"
        response.headers = {"content-type": "application/pdf"}
        response.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as tmp, patch.object(api.requests, "get", return_value=response) as get:
            result = api._download_file(
                "https://moodle.test/pluginfile.php/1/x.pdf",
                Path(tmp),
                "../unsafe:name?.pdf",
                token="secret-token",
            )
            written = Path(result["path"])
            self.assertEqual(written.name, "unsafe-name-.pdf")
            self.assertEqual(written.read_bytes(), b"PDFDATA")
            self.assertEqual(result["status"], "downloaded")
            self.assertNotIn("secret-token", result["source_url"])
            self.assertIn("token=", get.call_args.args[0])

    def test_list_course_material_files_extracts_contents(self):
        sections = [
            {"name": "Week 1", "section": 1, "visible": 1, "uservisible": True, "modules": [
                {"id": 10, "name": "Module A", "modname": "resource", "url": "https://moodle.test/mod/resource/view.php?id=10", "contents": [
                    {"filename": "materi.pdf", "fileurl": "https://moodle.test/pluginfile.php/10/materi.pdf", "filesize": 123, "mimetype": "application/pdf"},
                    {"filename": ".", "fileurl": "", "filesize": 0},
                ]},
                {"id": 11, "name": "URL only", "modname": "url", "url": "https://example.test", "contents": None},
            ]}
        ]
        with patch.object(api, "get_course_content", return_value=sections):
            files = api.list_course_material_files(90)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["filename"], "materi.pdf")
        self.assertEqual(files[0]["section_name"], "Week 1")
        self.assertEqual(files[0]["module_name"], "Module A")

    def test_download_course_materials_downloads_files_to_course_folder(self):
        files = [{
            "courseid": 90,
            "section_name": "Week 1",
            "module_id": 10,
            "module_name": "Module A",
            "module_type": "resource",
            "filename": "materi.pdf",
            "fileurl": "https://moodle.test/pluginfile.php/10/materi.pdf",
            "filesize": 123,
            "mimetype": "application/pdf",
        }]
        response = Mock(status_code=200, content=b"PDF")
        response.headers = {"content-type": "application/pdf"}
        response.raise_for_status.return_value = None
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(api, "list_course_material_files", return_value=files), \
             patch.object(api, "get_my_courses", return_value=[]), \
             patch.object(api.requests, "get", return_value=response):
            result = api.download_course_materials(90, target_dir=tmp)
            self.assertEqual(result["downloaded_count"], 1)
            self.assertTrue(Path(result["files"][0]["path"]).exists())
            self.assertIn("Course 90", result["files"][0]["path"])

    def test_download_assignment_attachments_uses_introattachments(self):
        assignments = [{
            "id": 340,
            "name": "Curve Fitting",
            "course": 90,
            "introattachments": [
                {"filename": "soal.pdf", "fileurl": "https://moodle.test/pluginfile.php/340/soal.pdf", "filesize": 456, "mimetype": "application/pdf"}
            ],
        }]
        response = Mock(status_code=200, content=b"SOAL")
        response.headers = {"content-type": "application/pdf"}
        response.raise_for_status.return_value = None
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(api, "_get_assignment_raw", return_value=assignments), \
             patch.object(api.requests, "get", return_value=response):
            result = api.download_assignment_attachments(340, target_dir=tmp)
            self.assertEqual(result["downloaded_count"], 1)
            self.assertTrue(Path(result["files"][0]["path"]).exists())
            self.assertIn("Assignment 340 - Curve Fitting", result["files"][0]["path"])


if __name__ == "__main__":
    unittest.main()
