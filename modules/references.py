import re
from .base import CheckModule

class ReferencesCheck(CheckModule):
    def check(self, doc, params):
        standard = params.get("standard", "ГОСТ Р 7.0.5-2008")
        if standard != "ГОСТ Р 7.0.5-2008":
            return f"References check for standard {standard} is not implemented"

        # Шаблоны с поддержкой латинских букв
        patterns = {
            "article": r"^[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.(\s*,\s*[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.)*(\s*и\s*др\.)?\s+.+?\s+//\s+.+?\.\s+\d{4}\.\s+№\s*\d+\.\s+С\.\s+\d+(-\d+)?\.?$",
            "book": r"^[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.(\s*,\s*[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.)*(\s*и\s*др\.)?\s+.+?\.\s+[А-ЯЁA-Z][а-яёa-z]+:\s+.+?,\s+\d{4}\.\s+\d+\s+с\.?$",
            "electronic": r"^[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.(\s*,\s*[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.)*(\s*и\s*др\.)?\s+.+?\s+//\s+.+?\.\s+URL:\s+https?://[^\s]+\s+\(дата\s+обращения:\s+\d{2}\.\d{2}\.\d{4}\)\.?$"
        }

        # Собираем текст из параграфов
        paragraphs = [p.text.strip() for p in doc.paragraphs]
        ref_section = []
        in_references = False
        ref_headers = ["список источников", "список литературы", "литература", "references"]

        # Ищем начало списка источников
        has_ref_header = False
        for para in paragraphs:
            para_lower = para.lower()
            if not in_references and para_lower in ref_headers:
                in_references = True
                has_ref_header = True
                continue
            elif in_references:
                if re.match(r"^(Приложение|Выводы|Заключение|Рисунок|Таблица)", para):
                    break
                ref_section.append(para)

        # Если заголовка нет, возвращаем ошибку об отсутствии раздела
        if not has_ref_header:
            return "No references section found"

        # Проверяем, есть ли хоть одна ссылка
        valid_refs = [line for line in ref_section if line.strip() and re.search(r"\d{4}|\s//|\sС\.|\sURL:", line)]
        if not valid_refs:
            return "References section is empty"

        errors = []
        for line in ref_section:
            if not line.strip():
                continue
            # Пропускаем строки, не похожие на записи
            if not re.search(r"\d{4}|\s//|\sС\.|\sURL:", line):
                continue

            # Проверяем соответствие хотя бы одному шаблону
            matches_any = False
            for ref_type, pattern in patterns.items():
                if re.match(pattern, line):
                    matches_any = True
                    break
            if not matches_any:
                errors.append(f"Неверный формат ссылки по ГОСТ Р 7.0.5-2008: {line}")

        return errors if errors else "References check passed"