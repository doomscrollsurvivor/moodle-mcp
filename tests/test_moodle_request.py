import unittest
from unittest.mock import Mock, patch

from moodle_mcp import moodle


class MoodleRequestTests(unittest.TestCase):
    def test_get_moodle_api_data_uses_post_and_browser_user_agent(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"ok": True}

        with patch.object(moodle.requests, "post", return_value=response) as post:
            result = moodle.get_moodle_api_data(moodle.APIFunction.core_webservice_get_site_info)

        self.assertEqual(result, {"ok": True})
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["data"]["wsfunction"], "core_webservice_get_site_info")
        self.assertIn("User-Agent", kwargs["headers"])
        self.assertIn("Mozilla/5.0", kwargs["headers"]["User-Agent"])
        self.assertEqual(kwargs["timeout"], 30)


if __name__ == "__main__":
    unittest.main()
