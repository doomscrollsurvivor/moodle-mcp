import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from moodle_mcp import api


class ObsidianSyncTests(unittest.TestCase):
    def test_resolve_obsidian_sync_dir_prefers_explicit_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "Academic" / "Moodle"
            self.assertEqual(api._resolve_obsidian_sync_dir(str(target)), target)

    def test_sync_writes_academic_moodle_notes_not_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "Vault"
            target = vault / "Academic" / "Moodle"
            courses = [
                {"id": 90, "fullname": "Matematika Teknik", "shortname": "RE205", "category": 1, "progress": 52.5, "format": "topics", "startdate": 0, "enddate": 0},
                {"id": 92, "fullname": "Design Thinking", "shortname": "RE207", "category": 1, "progress": None, "format": "topics", "startdate": 0, "enddate": 0},
            ]
            deadlines = [
                {"assignment_id": 340, "assignment_name": "Curve Fitting", "course_name": "Matematika Teknik", "duedate": 1785340800, "duedate_formatted": "2026-07-29T00:00:00+00:00", "submitted": False, "submission_status": "new"}
            ]
            grades = [
                {"courseid": 90, "course_name": "Matematika Teknik", "grade": "85", "rank": None},
            ]
            progress = [
                {"courseid": 90, "coursename": "Matematika Teknik", "progress_percentage": 52.5, "completed_activities": 10, "total_activities": 19},
            ]
            sections = [
                {"name": "Minggu 1", "section": 1, "visible": 1, "uservisible": True, "modules": [
                    {"id": 1, "name": "Modul Integral", "modname": "resource", "url": "https://example.test/modul", "contents": [{"filename": "modul.pdf", "fileurl": "https://example.test/modul.pdf"}]}
                ]}
            ]

            def fake_content(courseid):
                return sections if courseid == 90 else []

            with patch.object(api, "get_my_courses", return_value=courses), \
                 patch.object(api, "get_upcoming_deadlines", return_value=deadlines), \
                 patch.object(api, "get_grades", return_value=grades), \
                 patch.object(api, "get_course_progress", return_value=progress), \
                 patch.object(api, "get_course_content", side_effect=fake_content):
                result = api.sync_moodle_to_obsidian(target_dir=str(target))

            self.assertEqual(result["target_dir"], str(target))
            self.assertTrue((target / "Dashboard.md").exists())
            self.assertTrue((target / "Deadlines.md").exists())
            self.assertTrue((target / "Grades.md").exists())
            self.assertTrue((target / "Courses" / "RE205 - Matematika Teknik.md").exists())
            self.assertFalse((vault / "03 Projects" / "Academic" / "Moodle").exists())
            dashboard = (target / "Dashboard.md").read_text()
            self.assertIn("# Moodle Dashboard", dashboard)
            self.assertIn("[[Courses/RE205 - Matematika Teknik|RE205]]", dashboard)
            deadlines_text = (target / "Deadlines.md").read_text()
            self.assertIn("- [ ] Curve Fitting", deadlines_text)
            self.assertIn("📅 2026-07-29", deadlines_text)

    def test_export_deadlines_to_obsidian_writes_only_deadlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "Academic" / "Moodle"
            deadlines = [
                {"assignment_id": 1, "assignment_name": "Tugas A", "course_name": "Course A", "duedate": 1785340800, "duedate_formatted": "2026-07-29T00:00:00+00:00", "submitted": True, "submission_status": "submitted"}
            ]
            with patch.object(api, "get_upcoming_deadlines", return_value=deadlines):
                result = api.export_deadlines_to_obsidian(target_dir=str(target))
            self.assertEqual(result["files_written"], [str(target / "Deadlines.md")])
            text = (target / "Deadlines.md").read_text()
            self.assertIn("- [x] Tugas A", text)


if __name__ == "__main__":
    unittest.main()
