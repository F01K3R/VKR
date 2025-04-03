import re
import logging
from .base import CheckModule
from docx.document import Document

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ReferencesCheck(CheckModule):
    # Скомпилированные регулярные выражения
    REF_FILTER_PATTERN = re.compile(r"\d{4}|\s//|\sС\.|\sURL:|\sдис\.|\sканд\.|\sдокт\.")
    PATTERNS = {
        "ГОСТ Р 7.0.5-2008": {
            "article": re.compile(r"^[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.(\s*,\s*[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.)*(\s*и\s*др\.)?\s+.+?\s+//\s+.+?\.\s+\d{4}\.\s+№\s*\d+\.\s+(С\.|стр\.)\s+\d+(-\d+)?\.?$"),

            "book": re.compile(r"^[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\."
                               r"(\s*,\s*[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.)*"
                               r"(\s*и\s*др\.)?\s+.+?\.\s+[А-ЯЁA-Z][а-яёa-z]+:\s+.+?,\s+\d{4}\.\s+\d+\s+с\.?$"),

            "electronic": re.compile(r"^[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.(\s*,\s*[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.)*(\s*и\s*др\.)?\s+.+?\s+//\s+.+?\.\s+(URL:|Режим доступа:)\s+https?://[^\s]+\s+\(дата\s+обращения:\s+\d{2}\.\d{2}\.\d{4}\)\.?$")
        }
    }
    REF_HEADERS = [
        r"^(?:\d+\.\s*)?список\s+(?:источников|литературы)$",
        r"^(?:\d+\.\s*)?литература$",
        r"^(?:\d+\.\s*)?бibliography$",
        r"^(?:\d+\.\s*)?references$",
        r"^(?:\d+\.\s*)?список\s+использованных\s+источников$"
    ]
    REF_HEADERS = [re.compile(pattern) for pattern in REF_HEADERS]
    # Регулярное выражение для затекстовых ссылок
    CITATION_PATTERN = re.compile(r'\[([^\]]+)\]')

    def check(self, doc, params=None):
        # Проверка входных параметров
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return [f"Ошибка: params должен быть словарем, получено: {type(params)}"]
        if not isinstance(doc, Document):
            return [f"Ошибка: doc должен быть объектом Document, получено: {type(doc)}"]

        standard = params.get("standard", "ГОСТ Р 7.0.5-2008")
        if standard not in self.PATTERNS:
            return [f"References check for standard {standard} is not implemented"]

        patterns = self.PATTERNS[standard]

        # Собираем текст из параграфов
        paragraphs = []
        try:
            for p in doc.paragraphs:
                text = p.text.strip() if p.text else ""
                paragraphs.append(text)
        except Exception as e:
            return [f"Ошибка при доступе к параграфам документа: {str(e)}"]

        ref_section = []
        in_references = False
        has_ref_header = False

        # Ищем начало списка источников
        for para in paragraphs:
            para_lower = para.lower()
            if not in_references and any(pattern.match(para_lower) for pattern in self.REF_HEADERS):
                in_references = True
                has_ref_header = True
                continue
            elif in_references:
                if re.match(r"^(Приложение|Выводы|Заключение|Рисунок|Таблица)", para):
                    break
                ref_section.append(para)

        # Если заголовка нет, возвращаем ошибку
        if not has_ref_header:
            return ["No references section found"]

        # Проверяем, есть ли хоть одна ссылка
        valid_refs = [line for line in ref_section if line.strip() and self.REF_FILTER_PATTERN.search(line)]
        if not valid_refs:
            return ["References section is empty"]

        errors = []
        # Проверка формата ссылок в списке литературы
        ref_entries = []
        for line in ref_section:
            if not line.strip() or not self.REF_FILTER_PATTERN.search(line):
                continue

            # Проверяем соответствие хотя бы одному шаблону
            matches_any = False
            for ref_type, pattern in patterns.items():
                if pattern.match(line):
                    matches_any = True
                    break
            if not matches_any:
                logger.debug(f"Неверный формат ссылки: {line}")
                errors.append(f"Неверный формат ссылки по ГОСТ Р 7.0.5-2008 в строке {ref_section.index(line) + 1}")
            else:
                ref_entries.append(line)

        # Проверка сквозной нумерации в списке литературы
        numbered_refs = [line for line in ref_section if re.match(r'^\d+\.\s', line)]
        if numbered_refs:
            for i, line in enumerate(numbered_refs, start=1):
                expected_num = f"{i}."
                if not line.startswith(expected_num):
                    errors.append(f"Нарушение сквозной нумерации в списке литературы: ожидается номер {expected_num}, строка: {line}")

        # Проверка алфавитного порядка
        ref_titles = [re.sub(r'^\d+\.\s', '', line).strip() for line in numbered_refs]
        if ref_titles:
            # Проверяем, что иностранные источники идут перед русскоязычными
            foreign_refs = [t for t in ref_titles if re.match(r'^[A-Z]', t)]
            russian_refs = [t for t in ref_titles if re.match(r'^[А-ЯЁ]', t)]
            all_refs = foreign_refs + russian_refs
            if all_refs != ref_titles:
                errors.append("Иностранные источники должны идти перед русскоязычными в списке литературы")
            # Проверка алфавитного порядка внутри групп
            if foreign_refs and foreign_refs != sorted(foreign_refs):
                errors.append("Иностранные источники в списке литературы не отсортированы по алфавиту")
            if russian_refs and russian_refs != sorted(russian_refs):
                errors.append("Русскоязычные источники в списке литературы не отсортированы по алфавиту")

        # Проверка затекстовых ссылок
        citations = []
        for i, para in enumerate(paragraphs):
            matches = self.CITATION_PATTERN.findall(para)
            for match in matches:
                citations.append((match, i))

        # Проверка формата затекстовых ссылок
        for citation, para_idx in citations:
            # Проверка формата ссылки
            if not re.match(r'^(?:[А-ЯЁ][а-яё]+(?:,\s*[А-ЯЁ][а-яё]+){0,2}|.+?)(?:,\s*\d{4})?(?:,\s*(?:ч\.|вып\.)\s*\d+)?,\s*с\.\s*\d+(?:-\d+)?$', citation):
                errors.append(f"Неверный формат затекстовой ссылки в параграфе {para_idx+1}: [{citation}]")
            else:
                # Извлекаем информацию из ссылки
                parts = citation.split(',')
                ref_part = parts[0].strip()
                page_part = parts[-1].strip()
                year = None
                volume = None
                for part in parts[1:-1]:
                    part = part.strip()
                    if re.match(r'\d{4}', part):
                        year = part
                    elif re.match(r'(?:ч\.|вып\.)\s*\d+', part):
                        volume = part

                # Проверка количества авторов
                authors = ref_part.split(',')
                if len(authors) > 3:
                    # Если больше 3 авторов, должно быть название
                    if not re.match(r'^[^\s].*?(?:\.\.\.)?$', ref_part):
                        errors.append(f"Затекстовая ссылка в параграфе {para_idx+1} должна содержать название документа для 4+ авторов: [{citation}]")
                else:
                    # Проверяем, что указаны фамилии
                    for author in authors:
                        if not re.match(r'^[А-ЯЁ][а-яё]+$', author.strip()):
                            errors.append(f"Затекстовая ссылка в параграфе {para_idx+1} должна содержать фамилии авторов (1-3): [{citation}]")

                # Проверка сокращения заглавий
                if '...' in ref_part:
                    if not re.match(r'^[^\s].*?\.\.\.$', ref_part):
                        errors.append(f"Неверное сокращение заглавия в затекстовой ссылке в параграфе {para_idx+1}: [{citation}]")

                # Проверка соответствия записи в списке литературы
                found = False
                for ref in ref_entries:
                    ref_clean = re.sub(r'^\d+\.\s', '', ref).strip()
                    if ref_part in ref_clean or (year and year in ref_clean) or (volume and volume in ref_clean):
                        found = True
                        break
                if not found:
                    errors.append(f"Затекстовая ссылка в параграфе {para_idx+1} не соответствует ни одной записи в списке литературы: [{citation}]")

        return errors