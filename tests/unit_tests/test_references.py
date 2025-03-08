import unittest
from docx import Document
from modules.references import ReferencesCheck


class TestReferencesCheck(unittest.TestCase):
    def setUp(self):
        """Инициализация перед каждым тестом."""
        self.checker = ReferencesCheck()

    def test_correct_references(self):
        """Проверяет документ с корректными ссылками по ГОСТ Р 7.0.5-2008."""
        doc = Document()
        doc.add_paragraph("Список литературы")
        doc.add_paragraph("Иванов И.И., Петров П.П. Статья о чём-то // Журнал науки. 2020. № 5. С. 10-15.")
        doc.add_paragraph("Сидоров С.С. Книга о знаниях. Москва: Издательство, 2019. 200 с.")
        doc.add_paragraph(
            "Козлов К.К. Электронный ресурс // Сайт. URL: https://example.com (дата обращения: 01.01.2023).")

        params = {"standard": "ГОСТ Р 7.0.5-2008"}
        result = self.checker.check(doc, params)
        self.assertEqual(result, "References check passed")

    def test_incorrect_references(self):
        """Проверяет документ с некорректными ссылками."""
        doc = Document()
        doc.add_paragraph("Список литературы")
        doc.add_paragraph("Иванов И.И. Неправильная статья, 2020")  # Нет журнала, страниц
        doc.add_paragraph("Петров П.П. Книга без города, 2019")  # Нет города, издательства
        doc.add_paragraph("Сидоров С.С. URL: http://site.com")  # Нет даты обращения

        params = {"standard": "ГОСТ Р 7.0.5-2008"}
        result = self.checker.check(doc, params)
        expected_errors = [
            "Неверный формат ссылки по ГОСТ Р 7.0.5-2008: Иванов И.И. Неправильная статья, 2020",
            "Неверный формат ссылки по ГОСТ Р 7.0.5-2008: Петров П.П. Книга без города, 2019",
            "Неверный формат ссылки по ГОСТ Р 7.0.5-2008: Сидоров С.С. URL: http://site.com"
        ]
        for expected_error in expected_errors:
            self.assertTrue(any(expected_error in error for error in result))

    def test_no_references_section(self):
        """Проверяет документ без списка литературы."""
        doc = Document()
        doc.add_paragraph("Введение")
        doc.add_paragraph("Текст документа")
        doc.add_paragraph("Заключение")

        params = {"standard": "ГОСТ Р 7.0.5-2008"}
        result = self.checker.check(doc, params)
        self.assertEqual(result, "No references section found")

    def test_unsupported_standard(self):
        """Проверяет документ с неподдерживаемым стандартом."""
        doc = Document()
        doc.add_paragraph("References")
        doc.add_paragraph("Some reference")

        params = {"standard": "APA"}
        result = self.checker.check(doc, params)
        self.assertEqual(result, "References check for standard APA is not implemented")

    def test_empty_references_section(self):
        """Проверяет документ с пустым списком литературы."""
        doc = Document()
        doc.add_paragraph("Список литературы")
        doc.add_paragraph("")  # Пустая строка
        doc.add_paragraph("Заключение")

        params = {"standard": "ГОСТ Р 7.0.5-2008"}
        result = self.checker.check(doc, params)
        self.assertEqual(result, "References section is empty")

    def test_mixed_references(self):
        """Проверяет документ со смесью корректных и некорректных ссылок."""
        doc = Document()
        doc.add_paragraph("Литература")
        doc.add_paragraph("Иванов И.И. Статья // Журнал. 2021. № 3. С. 5-10.")
        doc.add_paragraph("Петров П.П. Неправильная книга 2020")  # Нет формата книги

        params = {"standard": "ГОСТ Р 7.0.5-2008"}
        result = self.checker.check(doc, params)
        expected_error = "Неверный формат ссылки по ГОСТ Р 7.0.5-2008: Петров П.П. Неправильная книга 2020"
        self.assertTrue(any(expected_error in error for error in result))

    def test_references_interrupted(self):
        """Проверяет документ, где список литературы прерывается другим разделом."""
        doc = Document()
        doc.add_paragraph("Список источников")
        doc.add_paragraph("Иванов И.И. Статья // Журнал. 2020. № 1. С. 1-5.")
        doc.add_paragraph("Приложение")  # Прерывание списка
        doc.add_paragraph("Петров П.П. Книга. Москва: Изд-во, 2019. 150 с.")  # После прерывания

        params = {"standard": "ГОСТ Р 7.0.5-2008"}
        result = self.checker.check(doc, params)
        # Ожидаем, что проверяется только до "Приложения"
        self.assertEqual(result, "References check passed")


if __name__ == '__main__':
    unittest.main()