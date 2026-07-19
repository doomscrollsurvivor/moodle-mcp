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


class SemesterArchiveTests(unittest.TestCase):
    """Tests for _detect_and_archive_semester and semester state tracking."""

    def _make_target(self, tmp: str) -> Path:
        target = Path(tmp) / "Academic" / "Moodle"
        target.mkdir(parents=True, exist_ok=True)
        return target

    def test_first_sync_initializes_state_no_archive(self):
        """First-ever sync: no archive, state file written."""
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_target(tmp)
            courses = [{"id": 86}, {"id": 87}, {"id": 88}]
            result = api._detect_and_archive_semester(target, courses)
            self.assertIsNone(result)
            state_file = target / api._SEMESTER_STATE_FILE
            self.assertTrue(state_file.exists())
            import json
            data = json.loads(state_file.read_text())
            self.assertEqual(set(data["course_ids"]), {86, 87, 88})

    def test_same_courses_no_archive(self):
        """Same courses across two syncs → no archive triggered."""
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_target(tmp)
            courses = [{"id": 86}, {"id": 87}, {"id": 88}]
            api._detect_and_archive_semester(target, courses)  # init
            result = api._detect_and_archive_semester(target, courses)  # same
            self.assertIsNone(result)
            archive_parent = target.parent / "Archive"
            self.assertFalse(archive_parent.exists())

    def test_partial_change_no_archive(self):
        """Minor change (less than half) → no archive."""
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_target(tmp)
            courses_old = [{"id": 86}, {"id": 87}, {"id": 88}, {"id": 89}]
            courses_new = [{"id": 86}, {"id": 87}, {"id": 88}, {"id": 99}]  # 1 of 4 changed
            api._detect_and_archive_semester(target, courses_old)
            result = api._detect_and_archive_semester(target, courses_new)
            self.assertIsNone(result)

    def test_full_semester_rollover_archives(self):
        """Completely new courses → archive created with README."""
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_target(tmp)
            # Write a dummy file to represent existing sync content
            (target / "Dashboard.md").write_text("# Old Dashboard\n")
            (target / "Courses").mkdir()
            (target / "Courses" / "OldCourse.md").write_text("# Old Course\n")

            courses_old = [{"id": 86}, {"id": 87}, {"id": 88}]
            courses_new = [{"id": 201}, {"id": 202}, {"id": 203}]  # completely new

            api._detect_and_archive_semester(target, courses_old)  # init with old
            result = api._detect_and_archive_semester(target, courses_new)  # rollover

            self.assertIsNotNone(result)
            archive_dir = Path(result)  # type: ignore[arg-type]
            self.assertTrue(archive_dir.exists())
            # Original files copied to archive
            self.assertTrue((archive_dir / "Dashboard.md").exists())
            self.assertTrue((archive_dir / "Courses" / "OldCourse.md").exists())
            # README auto-created
            readme = archive_dir / "Archive-README.md"
            self.assertTrue(readme.exists())
            self.assertIn("pergantian semester", readme.read_text())
            self.assertIn("[86, 87, 88]", readme.read_text())

    def test_majority_courses_changed_triggers_archive(self):
        """More than half courses replaced → archive triggered."""
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_target(tmp)
            courses_old = [{"id": 86}, {"id": 87}, {"id": 88}, {"id": 89}]
            courses_new = [{"id": 201}, {"id": 202}, {"id": 203}, {"id": 89}]  # 3 of 4 new
            (target / "Dashboard.md").write_text("# Old\n")
            api._detect_and_archive_semester(target, courses_old)
            result = api._detect_and_archive_semester(target, courses_new)
            self.assertIsNotNone(result)

    def test_archive_dir_avoids_overwrite(self):
        """If archive dir already exists, create versioned variant."""
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_target(tmp)
            courses_old = [{"id": 86}, {"id": 87}]
            courses_new = [{"id": 201}, {"id": 202}]
            (target / "Dashboard.md").write_text("# Old\n")
            api._detect_and_archive_semester(target, courses_old)
            result1 = api._detect_and_archive_semester(target, courses_new)

            # Simulate second rollover same month
            courses_new2 = [{"id": 301}, {"id": 302}]
            (target / "Dashboard.md").write_text("# Second\n")
            result2 = api._detect_and_archive_semester(target, courses_new2)

            self.assertIsNotNone(result1)
            self.assertIsNotNone(result2)
            self.assertNotEqual(result1, result2)

    def test_sync_result_includes_semester_archived_field(self):
        """ObsidianSyncResult must contain semester_archived key."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "Academic" / "Moodle"
            courses = [{"id": 90, "fullname": "Matematika Teknik", "shortname": "RE205", "category": 1, "progress": 52.5, "format": "topics", "startdate": 0, "enddate": 0}]
            deadlines: list = []
            grades: list = []
            progress: list = []
            with patch.object(api, "get_my_courses", return_value=courses), \
                 patch.object(api, "get_upcoming_deadlines", return_value=deadlines), \
                 patch.object(api, "get_grades", return_value=grades), \
                 patch.object(api, "get_course_progress", return_value=progress), \
                 patch.object(api, "get_course_content", return_value=[]):
                result = api.sync_moodle_to_obsidian(target_dir=str(target))
            self.assertIn("semester_archived", result)
            self.assertIsNone(result["semester_archived"])  # first sync → no archive


if __name__ == "__main__":
    unittest.main()

