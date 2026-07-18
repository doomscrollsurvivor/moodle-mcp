"""Phase 4 — Assignment submission tools (TDD: write tests first)."""
import unittest
from unittest.mock import Mock, patch, call as mock_call

from moodle_mcp import api


class Phase4SubmissionTests(unittest.TestCase):

    # ------------------------------------------------------------------
    # get_submission_status_detail
    # ------------------------------------------------------------------

    def test_get_submission_status_detail_returns_structured_dict(self):
        raw = {
            "lastattempt": {
                "submission": {
                    "id": 32595,
                    "status": "submitted",
                    "timemodified": 1777704817,
                    "plugins": [
                        {
                            "type": "file",
                            "name": "File submissions",
                            "fileareas": [
                                {
                                    "area": "submission_files",
                                    "files": [
                                        {
                                            "filename": "report.pdf",
                                            "fileurl": "https://moodle.test/pluginfile.php/1/report.pdf",
                                            "filesize": 128815,
                                            "mimetype": "application/pdf",
                                        }
                                    ],
                                }
                            ],
                        },
                        {"type": "comments", "name": "Submission comments"},
                    ],
                },
                "submissionsenabled": True,
                "locked": False,
                "graded": False,
                "canedit": True,
                "cansubmit": False,
                "gradingstatus": "notgraded",
            },
            "assignmentdata": {"attachments": {"intro": []}},
            "warnings": [],
        }
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = api.get_submission_status_detail(assignid=546)

        self.assertEqual(result["assignid"], 546)
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["gradingstatus"], "notgraded")
        self.assertFalse(result["graded"])
        self.assertTrue(result["canedit"])
        self.assertEqual(len(result["submitted_files"]), 1)
        self.assertEqual(result["submitted_files"][0]["filename"], "report.pdf")

    def test_get_submission_status_detail_not_submitted(self):
        raw = {
            "lastattempt": {
                "submission": {
                    "id": 999,
                    "status": "new",
                    "timemodified": 0,
                    "plugins": [],
                },
                "submissionsenabled": True,
                "locked": False,
                "graded": False,
                "canedit": True,
                "cansubmit": True,
                "gradingstatus": "notgraded",
            },
            "assignmentdata": {},
            "warnings": [],
        }
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = api.get_submission_status_detail(assignid=687)

        self.assertEqual(result["status"], "new")
        self.assertTrue(result["cansubmit"])
        self.assertEqual(result["submitted_files"], [])

    # ------------------------------------------------------------------
    # submit_assignment_text
    # ------------------------------------------------------------------

    def test_submit_assignment_text_calls_save_submission(self):
        mock_response = {"warnings": []}
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=mock_response) as mock_api:
            result = api.submit_assignment_text(
                assignid=546,
                text="<p>Jawaban saya adalah 42.</p>",
                format=1,
            )
        self.assertTrue(result["success"])
        self.assertEqual(result["assignid"], 546)
        # pastikan dipanggil dengan parameter yang benar
        args, kwargs = mock_api.call_args
        self.assertEqual(args[0], api.APIFunction.mod_assign_save_submission)
        params = kwargs.get("extra_params") or args[1] if len(args) > 1 else kwargs
        self.assertIn("assignmentid", str(mock_api.call_args))

    def test_submit_assignment_text_raises_on_moodle_error(self):
        error = {"exception": "moodle_exception", "errorcode": "nopermissions",
                 "message": "Sorry, but you do not currently have permissions to do that."}
        with patch("moodle_mcp.api.get_moodle_api_data", side_effect=api.MoodleAPIError(
                "nopermissions", "Sorry, but you do not currently have permissions", "submit_assignment_text")):
            with self.assertRaises(api.MoodleAPIError):
                api.submit_assignment_text(assignid=687, text="test")

    # ------------------------------------------------------------------
    # get_assignment_feedback
    # ------------------------------------------------------------------

    def test_get_assignment_feedback_returns_grade_and_feedback(self):
        # get_assignment_feedback calls mod_assign_get_submission_status as step 1,
        # then (if graded=True) calls several more APIs to get grade from report.
        # Test the graded=False branch first (simpler, no extra calls).
        raw_status = {
            "lastattempt": {
                "submission": {
                    "id": 32595,
                    "status": "submitted",
                    "timemodified": 1778000000,
                    "plugins": [
                        {
                            "type": "comments",
                            "name": "Feedback comments",
                            "editorfields": [
                                {"name": "comments", "text": "Bagus, struktur laporan sudah rapi."}
                            ],
                        }
                    ],
                },
                "graded": True,
                "gradingstatus": "graded",
            },
            "warnings": [],
        }
        raw_assignments = {
            "courses": [
                {"id": 92, "assignments": [{"id": 546, "name": "Test"}]}
            ]
        }
        raw_site_info = {"userid": 2193}
        raw_report = {
            "usergrades": [
                {"gradeitems": [
                    {"itemmodule": "assign", "iteminstance": 546, "cmid": 1446,
                     "graderaw": 85.5, "feedback": ""}
                ]}
            ]
        }

        call_returns = [raw_status, raw_assignments, raw_site_info, raw_report]
        call_count = [0]

        def mock_api(fn, params=None, use_original_data=True):
            i = call_count[0]
            call_count[0] += 1
            return call_returns[i] if i < len(call_returns) else {}

        with patch("moodle_mcp.api.get_moodle_api_data", side_effect=mock_api):
            result = api.get_assignment_feedback(assignid=546)

        self.assertEqual(result["assignid"], 546)
        self.assertEqual(result["grade"], "85.5")
        self.assertEqual(result["gradingstatus"], "graded")
        self.assertIn("rapi", result["feedback_comments"])

    def test_get_assignment_feedback_not_graded_yet(self):
        raw = {
            "lastattempt": {
                "submission": {
                    "id": 999,
                    "status": "new",
                    "timemodified": 0,
                    "plugins": [],
                },
                "graded": False,
                "gradingstatus": "notgraded",
            },
            "warnings": [],
        }
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = api.get_assignment_feedback(assignid=687)

        self.assertIsNone(result["grade"])
        self.assertEqual(result["gradingstatus"], "notgraded")
        self.assertEqual(result["feedback_comments"], "")


if __name__ == "__main__":
    unittest.main()
