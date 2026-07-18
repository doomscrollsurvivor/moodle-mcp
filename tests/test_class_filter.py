"""Tests for class-slot classifier and assignment filtering."""
import unittest
from unittest.mock import patch


class ClassSlotClassifierTests(unittest.TestCase):
    """Unit tests for extract_class_slot and is_my_assignment."""

    def setUp(self):
        import sys
        sys.path.insert(0, "src")
        from moodle_mcp import api
        self.api = api

    # ------------------------------------------------------------------
    # extract_class_slot
    # ------------------------------------------------------------------

    def test_pagi_c_variations(self):
        cases = [
            "AAS Kelas Pagi C",
            "ATS kelas Pagi C",
            "Praktikum Kelas C Pagi",
            "Pengumpulan Laporan Kelas C",
            "Tugas Vektor Gaya PBL (Pagi C)",
            "Tugas - Mekanisme Gerak (Kelas Pagi C)",
        ]
        for name in cases:
            with self.subTest(name=name):
                self.assertEqual(self.api.extract_class_slot(name), "Pagi C", name)

    def test_pagi_a_variations(self):
        cases = [
            "AAS Kelas Pagi A",
            "Kelas A Pagi Modul 1",
            "Laporan Simulasi Kelas Pagi A",
            "Tugas Vektor Gaya PBL (Pagi A)",
        ]
        for name in cases:
            with self.subTest(name=name):
                self.assertEqual(self.api.extract_class_slot(name), "Pagi A", name)

    def test_malam_b_variations(self):
        cases = [
            "Laporan Praktikum Kelas Malam B",
            "Pengumpulan ATS Kelas B Malam",
            "Praktikum Modul 1 Kelas Malam B",
            "Transistor Kelas Malam B",
        ]
        for name in cases:
            with self.subTest(name=name):
                self.assertEqual(self.api.extract_class_slot(name), "Malam B", name)

    def test_no_class_tag_returns_none(self):
        cases = [
            "Laporan Praktikum 1 Gauss Seidel",
            "Project Review",
            "Assignment #1. System Requirement Review",
            "Jawaban ATS",
            "Practice Kelas Pak Veven",   # "Kelas" tapi bukan slot kelas
            "Upload Concept Design Review (CDR) Document",
        ]
        for name in cases:
            with self.subTest(name=name):
                self.assertIsNone(self.api.extract_class_slot(name), name)

    # ------------------------------------------------------------------
    # is_my_assignment
    # ------------------------------------------------------------------

    def test_my_class_pagi_c_matches(self):
        self.assertTrue(self.api.is_my_assignment("AAS Kelas Pagi C", "Pagi C"))

    def test_other_class_rejected(self):
        self.assertFalse(self.api.is_my_assignment("AAS Kelas Pagi A", "Pagi C"))
        self.assertFalse(self.api.is_my_assignment("AAS Kelas Malam B", "Pagi C"))
        self.assertFalse(self.api.is_my_assignment("Tugas Vektor Gaya PBL (Pagi B)", "Pagi C"))

    def test_no_class_tag_always_included(self):
        self.assertTrue(self.api.is_my_assignment("Laporan Praktikum 1", "Pagi C"))
        self.assertTrue(self.api.is_my_assignment("Project Review", "Pagi C"))
        self.assertTrue(self.api.is_my_assignment("Jawaban ATS", "Pagi C"))

    def test_case_insensitive(self):
        self.assertTrue(self.api.is_my_assignment("ATS kelas Pagi C", "pagi c"))
        self.assertFalse(self.api.is_my_assignment("ATS kelas Pagi A", "PAGI C"))

    # ------------------------------------------------------------------
    # get_assignments with filter_by_class
    # ------------------------------------------------------------------

    def test_get_assignments_filters_other_classes(self):
        raw = {
            "courses": [
                {
                    "id": 91,
                    "fullname": "Sistem Elektronika/RE206",
                    "assignments": [
                        {"id": 1, "name": "Laporan Kelas Pagi C", "duedate": 0,
                         "cutoffdate": 0, "intro": ""},
                        {"id": 2, "name": "Laporan Kelas Pagi A", "duedate": 0,
                         "cutoffdate": 0, "intro": ""},
                        {"id": 3, "name": "Laporan Kelas Malam B", "duedate": 0,
                         "cutoffdate": 0, "intro": ""},
                        {"id": 4, "name": "Laporan Gauss Seidel", "duedate": 0,
                         "cutoffdate": 0, "intro": ""},  # no class tag
                    ],
                }
            ]
        }
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = self.api.get_assignments(my_class="Pagi C", filter_by_class=True)

        names = [a["name"] for a in result]
        self.assertIn("Laporan Kelas Pagi C", names, "Pagi C should be included")
        self.assertIn("Laporan Gauss Seidel", names, "No-class-tag should be included")
        self.assertNotIn("Laporan Kelas Pagi A", names, "Pagi A should be excluded")
        self.assertNotIn("Laporan Kelas Malam B", names, "Malam B should be excluded")
        self.assertEqual(len(result), 2)

    def test_get_assignments_unfiltered(self):
        raw = {
            "courses": [
                {
                    "id": 91,
                    "fullname": "RE206",
                    "assignments": [
                        {"id": 1, "name": "Kelas Pagi C", "duedate": 0, "cutoffdate": 0, "intro": ""},
                        {"id": 2, "name": "Kelas Pagi A", "duedate": 0, "cutoffdate": 0, "intro": ""},
                    ],
                }
            ]
        }
        with patch("moodle_mcp.api.get_moodle_api_data", return_value=raw):
            result = self.api.get_assignments(filter_by_class=False)
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
