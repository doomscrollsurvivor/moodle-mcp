import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from moodle_mcp import api


class Phase1TrackingTests(unittest.TestCase):
    def test_detect_new_assignments_reports_new_and_changed_deadlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "assignments.json"
            state.write_text(json.dumps({
                "assignments": {
                    "1": {"id": 1, "name": "Old", "duedate": 100, "courseid": 10, "coursename": "Course"},
                    "2": {"id": 2, "name": "Changed", "duedate": 200, "courseid": 10, "coursename": "Course"},
                }
            }))
            current = [
                {"id": 1, "name": "Old", "duedate": 100, "courseid": 10, "coursename": "Course", "cutoffdate": 0, "intro": None},
                {"id": 2, "name": "Changed", "duedate": 250, "courseid": 10, "coursename": "Course", "cutoffdate": 0, "intro": None},
                {"id": 3, "name": "New", "duedate": 300, "courseid": 11, "coursename": "Other", "cutoffdate": 0, "intro": None},
            ]
            with patch.object(api, "get_assignments", return_value=current):
                result = api.detect_new_assignments(state_path=str(state), update_state=False)

            self.assertEqual([a["id"] for a in result["new_assignments"]], [3])
            self.assertEqual(result["changed_deadlines"][0]["id"], 2)
            self.assertEqual(result["changed_deadlines"][0]["old_duedate"], 200)
            self.assertEqual(result["changed_deadlines"][0]["new_duedate"], 250)

    def test_detect_grade_changes_reports_new_and_changed_grades(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "grades.json"
            state.write_text(json.dumps({
                "grades": {
                    "10:Course A": {"courseid": 10, "course_name": "Course A", "grade": "80"},
                    "11:Course B": {"courseid": 11, "course_name": "Course B", "grade": "70"},
                }
            }))
            current = [
                {"courseid": 10, "course_name": "Course A", "grade": "85", "rank": None},
                {"courseid": 11, "course_name": "Course B", "grade": "70", "rank": None},
                {"courseid": 12, "course_name": "Course C", "grade": "90", "rank": None},
            ]
            with patch.object(api, "get_grades", return_value=current):
                result = api.detect_grade_changes(state_path=str(state), update_state=False)

            self.assertEqual(result["new_grades"][0]["courseid"], 12)
            self.assertEqual(result["changed_grades"][0]["courseid"], 10)
            self.assertEqual(result["changed_grades"][0]["old_grade"], "80")
            self.assertEqual(result["changed_grades"][0]["new_grade"], "85")

    def test_deadline_watchdog_filters_unsubmitted_deadlines(self):
        deadlines = [
            {"assignment_id": 1, "assignment_name": "Due Soon", "course_name": "Course", "duedate": 2000, "duedate_formatted": "soon", "submitted": False, "submission_status": "new"},
            {"assignment_id": 2, "assignment_name": "Submitted", "course_name": "Course", "duedate": 2000, "duedate_formatted": "soon", "submitted": True, "submission_status": "submitted"},
            {"assignment_id": 3, "assignment_name": "Later", "course_name": "Course", "duedate": 999999, "duedate_formatted": "later", "submitted": False, "submission_status": "new"},
        ]
        with patch.object(api, "get_upcoming_deadlines", return_value=deadlines):
            result = api.deadline_watchdog(days_ahead=1, now_ts=1000)

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["alerts"][0]["assignment_id"], 1)
        self.assertEqual(result["alerts"][0]["urgency"], "critical")


if __name__ == "__main__":
    unittest.main()
