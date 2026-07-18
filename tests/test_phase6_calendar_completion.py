"""Phase 6 — Calendar & Completion tools (TDD: write tests first)."""
import unittest
from unittest.mock import patch

from moodle_mcp import api


class Phase6CalendarTests(unittest.TestCase):

    # ------------------------------------------------------------------
    # create_calendar_event
    # ------------------------------------------------------------------

    def test_create_calendar_event_returns_event_id(self):
        raw = {
            "events": [
                {
                    "id": 9001,
                    "name": "Belajar Kalkulus",
                    "timestart": 1800000000,
                    "timeduration": 7200,
                    "eventtype": "user",
                    "description": "Review chapter 5",
                }
            ],
            "warnings": [],
        }
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = api.create_calendar_event(
                name="Belajar Kalkulus",
                timestart=1800000000,
                eventtype="user",
                description="Review chapter 5",
                timeduration=7200,
            )

        self.assertEqual(result["id"], 9001)
        self.assertEqual(result["name"], "Belajar Kalkulus")
        self.assertEqual(result["eventtype"], "user")

    def test_create_calendar_event_minimal(self):
        raw = {
            "events": [{"id": 9002, "name": "Deadline RE204", "timestart": 1800001000,
                        "timeduration": 0, "eventtype": "user", "description": ""}],
            "warnings": [],
        }
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = api.create_calendar_event(name="Deadline RE204", timestart=1800001000)

        self.assertEqual(result["id"], 9002)
        self.assertEqual(result["name"], "Deadline RE204")


class Phase6CompletionTests(unittest.TestCase):

    # ------------------------------------------------------------------
    # get_activity_completion
    # ------------------------------------------------------------------

    def test_get_activity_completion_returns_list(self):
        raw = {
            "statuses": [
                {"cmid": 101, "modname": "resource", "instance": 10,
                 "tracking": 1, "state": 1, "timecompleted": 1770000000},
                {"cmid": 102, "modname": "assign", "instance": 20,
                 "tracking": 1, "state": 0, "timecompleted": 0},
            ]
        }
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = api.get_activity_completion(courseid=89)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["cmid"], 101)
        self.assertTrue(result[0]["completed"])
        self.assertFalse(result[1]["completed"])
        self.assertEqual(result[0]["timecompleted"], 1770000000)

    def test_get_activity_completion_empty_course(self):
        raw = {"statuses": []}
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = api.get_activity_completion(courseid=99)
        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # mark_activity_complete
    # ------------------------------------------------------------------

    def test_mark_activity_complete_calls_api_with_correct_params(self):
        raw = {"status": True, "warnings": []}
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw) as mock_api:
            result = api.mark_activity_complete(cmid=101, completed=True)

        self.assertTrue(result["success"])
        self.assertEqual(result["cmid"], 101)
        args, kwargs = mock_api.call_args
        self.assertEqual(args[0], api.APIFunction.core_completion_update_activity_completion_status_manually)

    def test_mark_activity_incomplete(self):
        raw = {"status": True, "warnings": []}
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = api.mark_activity_complete(cmid=102, completed=False)

        self.assertFalse(result["completed"])
        self.assertEqual(result["cmid"], 102)

    # ------------------------------------------------------------------
    # get_course_updates
    # ------------------------------------------------------------------

    def test_get_course_updates_returns_instances(self):
        sections = [
            {"name": "Week 1", "section": 1, "modules": [
                {"id": 10, "name": "Materi", "modname": "resource", "contents": []},
                {"id": 11, "name": "Tugas", "modname": "assign", "contents": []},
            ]}
        ]
        raw = {
            "instances": [
                {
                    "contextlevel": "module",
                    "id": 10,
                    "updates": [
                        {"name": "configuration", "timeupdated": 1778000000},
                        {"name": "contentfiles", "timeupdated": 1778001000, "itemids": [55, 56]},
                    ],
                }
            ],
            "warnings": [],
        }

        call_returns = [sections, raw]
        call_count = [0]

        def mock_api(fn, params=None, use_original_data=True):
            i = call_count[0]
            call_count[0] += 1
            return call_returns[i] if i < len(call_returns) else {}

        with patch("moodle_mcp.api.get_moodle_api_data", side_effect=mock_api):
            result = api.get_course_updates(courseid=89)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 10)
        self.assertEqual(len(result[0]["updates"]), 2)

    def test_get_course_updates_no_changes(self):
        sections = [
            {"name": "Week 1", "section": 1, "modules": [
                {"id": 10, "name": "Materi", "modname": "resource", "contents": []},
            ]}
        ]
        raw = {"instances": [], "warnings": []}

        call_returns = [sections, raw]
        call_count = [0]

        def mock_api(fn, params=None, use_original_data=True):
            i = call_count[0]
            call_count[0] += 1
            return call_returns[i] if i < len(call_returns) else {}

        with patch("moodle_mcp.api.get_moodle_api_data", side_effect=mock_api):
            result = api.get_course_updates(courseid=89)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
