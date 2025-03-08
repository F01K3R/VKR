import unittest
from docx import Document
from modules.structure import StructureCheck


class TestStructureCheck(unittest.TestCase):
    def setUp(self):
        """Инициализация перед каждым тестом."""
        self.checker = StructureCheck()

    def test_correct_structure(self):
        """Проверяет документ с корректной структурой и заголовками."""
        doc = Document()
        doc.add_heading("Оглавление", level=1)
        doc.add_heading("Введение", level=1)
        doc.add_heading("Основная часть", level=1)
        doc.add_heading("Заключение", level=1)
        doc.add_heading("Список литературы", level=1)

        params = {
            "require_headings": True,
            "required_sections": ["Оглавление", "Введение", "Основная часть", "Заключение", "Список литературы"]
        }
        result = self.checker.check(doc, params)
        self.assertEqual(result, "Structure check passed")

    def test_no_headings(self):
        """Проверяет документ без заголовков при require_headings=True."""
        doc = Document()
        doc.add_paragraph("Оглавление")  # Обычный текст, не заголовок
        doc.add_paragraph("Введение")
        doc.add_paragraph("Основная часть")
        doc.add_paragraph("Заключение")
        doc.add_paragraph("Список литературы")

        params = {"require_headings": True}
        result = self.checker.check(doc, params)
        expected_error = "В документе отсутствуют заголовки (стиль 'Heading')"
        self.assertTrue(any(expected_error in error for error in result))

    def test_missing_sections(self):
        """Проверяет документ с отсутствующими обязательными разделами."""
        doc = Document()
        doc.add_heading("Оглавление", level=1)
        doc.add_heading("Введение", level=1)
        # Пропущены "Основная часть", "Заключение", "Список литературы"

        params = {
            "required_sections": ["Оглавление", "Введение", "Основная часть", "Заключение", "Список литературы"]
        }
        result = self.checker.check(doc, params)
        expected_error = "Отсутствуют обязательные разделы: Основная часть, Заключение, Список литературы"
        self.assertTrue(any(expected_error in error for error in result))

    def test_incorrect_order(self):
        """Проверяет документ с нарушением порядка разделов."""
        doc = Document()
        doc.add_heading("Введение", level=1)
        doc.add_heading("Оглавление", level=1)  # "Оглавление" после "Введения"
        doc.add_heading("Основная часть", level=1)
        doc.add_heading("Заключение", level=1)
        doc.add_heading("Список литературы", level=1)

        params = {
            "required_sections": ["Оглавление", "Введение", "Основная часть", "Заключение", "Список литературы"]
        }
        result = self.checker.check(doc, params)
        expected_error = "Нарушение порядка разделов: 'Введение' находится после 'Оглавление'"
        self.assertTrue(any(expected_error in error for error in result))

    def test_custom_sections_no_headings(self):
        """Проверяет кастомные разделы без требования заголовков."""
        doc = Document()
        doc.add_paragraph("Аннотация")
        doc.add_paragraph("Введение")
        doc.add_paragraph("Выводы")

        params = {
            "require_headings": False,
            "required_sections": ["Аннотация", "Введение", "Выводы"]
        }
        result = self.checker.check(doc, params)
        self.assertEqual(result, "Structure check passed")

    def test_empty_document(self):
        """Проверяет пустой документ."""
        doc = Document()  # Нет параграфов

        params = {
            "require_headings": True,
            "required_sections": ["Оглавление", "Введение"]
        }
        result = self.checker.check(doc, params)
        expected_errors = [
            "В документе отсутствуют заголовки (стиль 'Heading')",
            "Отсутствуют обязательные разделы: Оглавление, Введение"
        ]
        for expected_error in expected_errors:
            self.assertTrue(any(expected_error in error for error in result))

    def test_case_insensitivity(self):
        """Проверяет нечувствительность к регистру в названиях разделов."""
        doc = Document()
        doc.add_heading("оглавление", level=1)  # Разный регистр
        doc.add_heading("ВВЕДЕНИЕ", level=1)
        doc.add_heading("основная часть", level=1)

        params = {
            "required_sections": ["Оглавление", "Введение", "Основная часть"]
        }
        result = self.checker.check(doc, params)
        self.assertEqual(result, "Structure check passed")


if __name__ == '__main__':
    unittest.main()