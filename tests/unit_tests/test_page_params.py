import unittest
from docx import Document
from docx.shared import Cm
from modules.page_params import PageParamsCheck


class TestPageParamsCheck(unittest.TestCase):
    def setUp(self):
        """Инициализация перед каждым тестом."""
        self.checker = PageParamsCheck()

    def test_correct_a4_params(self):
        """Проверяет документ с корректными параметрами A4 и полями."""
        doc = Document()
        section = doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(1.0)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)

        params = {
            "page_size": "A4",
            "margins": {"left": 3, "right": 1, "top": 2, "bottom": 2}
        }
        result = self.checker.check(doc, params)
        self.assertEqual(result, "Page parameters check passed")

    def test_incorrect_page_size(self):
        """Проверяет документ с некорректным размером страницы (Letter вместо A4)."""
        doc = Document()
        section = doc.sections[0]
        section.page_width = Cm(21.59)  # US Letter
        section.page_height = Cm(27.94)  # US Letter
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(1.0)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)

        params = {"page_size": "A4"}
        result = self.checker.check(doc, params)
        expected_error = "Секция 1: Incorrect page size (21.59 x 27.94 см, expected 21.0 x 29.7 см)"
        self.assertTrue(any(expected_error in error for error in result))

    def test_incorrect_margins_all(self):
        """Проверяет документ с полями меньше ожидаемых."""
        doc = Document()
        section = doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(2.5)  # Меньше 3 см
        section.right_margin = Cm(0.5)  # Меньше 1 см
        section.top_margin = Cm(1.5)  # Меньше 2 см
        section.bottom_margin = Cm(1.0)  # Меньше 2 см

        params = {"page_size": "A4", "margins": {"left": 3, "right": 1, "top": 2, "bottom": 2}}
        result = self.checker.check(doc, params)

        expected_errors = [
            "Секция 1: Left margin (2.50 см) is less than expected (3 см)",
            "Секция 1: Right margin (0.50 см) is less than expected (1 см)",
            "Секция 1: Top margin (1.50 см) is less than expected (2 см)",
            "Секция 1: Bottom margin (1.00 см) is less than expected (2 см)"
        ]
        for expected_error in expected_errors:
            self.assertTrue(any(expected_error in error for error in result))

    def test_multiple_sections(self):
        """Проверяет документ с несколькими секциями, одна из которых некорректна."""
        doc = Document()
        # Первая секция (корректная)
        section1 = doc.sections[0]
        section1.page_width = Cm(21.0)
        section1.page_height = Cm(29.7)
        section1.left_margin = Cm(3.0)
        section1.right_margin = Cm(1.0)
        section1.top_margin = Cm(2.0)
        section1.bottom_margin = Cm(2.0)

        # Добавляем вторую секцию (некорректную)
        doc.add_section()
        section2 = doc.sections[1]
        section2.page_width = Cm(21.0)
        section2.page_height = Cm(29.7)
        section2.left_margin = Cm(2.0)  # Меньше 3 см

        params = {"page_size": "A4", "margins": {"left": 3, "right": 1, "top": 2, "bottom": 2}}
        result = self.checker.check(doc, params)
        expected_error = "Секция 2: Left margin (2.00 см) is less than expected (3 см)"
        self.assertTrue(any(expected_error in error for error in result))
        self.assertFalse(any("Секция 1" in error for error in result))  # Первая секция корректна

    def test_custom_params(self):
        """Проверяет документ с кастомными параметрами страницы и полей."""
        doc = Document()
        section = doc.sections[0]
        section.page_width = Cm(15.0)  # Не A4
        section.page_height = Cm(20.0)  # Не A4
        section.left_margin = Cm(1.5)  # Меньше 2 см
        section.right_margin = Cm(1.0)
        section.top_margin = Cm(1.0)
        section.bottom_margin = Cm(1.0)

        params = {
            "page_size": "Custom",
            "margins": {"left": 2, "right": 1, "top": 1, "bottom": 1}
        }
        result = self.checker.check(doc, params)
        expected_error = "Секция 1: Left margin (1.50 см) is less than expected (2 см)"
        self.assertTrue(any(expected_error in error for error in result))
        self.assertFalse(any("Incorrect page size" in error for error in result))  # Размер не проверяется для "Custom"

    def test_tolerance_edge_case(self):
        """Проверяет допуск размеров страницы (в пределах 0.1 см)."""
        doc = Document()
        section = doc.sections[0]
        section.page_width = Cm(21.05)  # В пределах допуска
        section.page_height = Cm(29.65)  # В пределах допуска
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(1.0)
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)

        params = {"page_size": "A4"}
        result = self.checker.check(doc, params)
        self.assertEqual(result, "Page parameters check passed")


if __name__ == '__main__':
    unittest.main()