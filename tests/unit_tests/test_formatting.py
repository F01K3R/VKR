import unittest
from docx import Document
from docx.shared import Pt
from modules.formatting import FormattingCheck

class TestFormattingCheck(unittest.TestCase):
    def setUp(self):
        """Инициализация перед каждым тестом."""
        self.checker = FormattingCheck()

    def test_formatting_correct(self):
        """Проверяет документ с правильным форматированием."""
        doc = Document()
        p = doc.add_paragraph()
        run = p.add_run("Текст")
        run.font.name = "Times New Roman"
        run.font.size = Pt(14)
        params = {"font": "Times New Roman", "font_size": 14}
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        result = self.checker.check(doc, ns, params)
        self.assertEqual(result, "Formatting check passed")

    def test_formatting_incorrect_font_and_size(self):
        """Проверяет документ с неправильным шрифтом и размером."""
        doc = Document()
        p = doc.add_paragraph()
        run = p.add_run("Неверный текст для проверки формата")
        run.font.name = "Arial"  # Неправильный шрифт
        run.font.size = Pt(12)   # Неправильный размер (12pt вместо 14pt)
        params = {"font": "Times New Roman", "font_size": 14}
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        result = self.checker.check(doc, ns, params)
        expected_error = "Страница 1: шрифт 'Arial' вместо 'Times New Roman' и размер 12pt вместо 14pt в тексте 'Неверный текст для проверки формата'"
        self.assertTrue(any(expected_error in error for error in result))

    def test_formatting_incorrect_font(self):
        """Проверяет документ с неправильным шрифтом."""
        doc = Document()
        p = doc.add_paragraph()
        run = p.add_run("Текст с неверным шрифтом")
        run.font.name = "Arial"
        run.font.size = Pt(14)
        params = {"font": "Times New Roman", "font_size": 14}
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        result = self.checker.check(doc, ns, params)
        expected_error = "Страница 1: шрифт 'Arial' вместо 'Times New Roman' в тексте 'Текст с неверным шрифтом'"
        self.assertTrue(any(expected_error in error for error in result))

    def test_formatting_incorrect_size(self):
        """Проверяет документ с неправильным размером шрифта."""
        doc = Document()
        p = doc.add_paragraph()
        run = p.add_run("Текст с неверным размером шрифта")
        run.font.name = "Times New Roman"
        run.font.size = Pt(12)
        params = {"font": "Times New Roman", "font_size": 14}
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        result = self.checker.check(doc, ns, params)
        expected_error = "Страница 1: размер 12pt вместо 14pt в тексте 'Текст с неверным размером шрифта'"
        self.assertTrue(any(expected_error in error for error in result))

if __name__ == '__main__':
    unittest.main()