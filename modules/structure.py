from .base import CheckModule


class StructureCheck(CheckModule):
    def check(self, document, params):
        errors = []

        # Получаем параметры из шаблона
        require_headings = params.get("require_headings", True)
        required_sections = params.get("required_sections", [
            "Оглавление",
            "Введение",
            "Основная часть",
            "Заключение",
            "Список литературы"
        ])

        # Проверка наличия заголовков
        if require_headings:
            headings = [p for p in document.paragraphs if p.style.name.startswith('Heading')]
            if not headings:
                errors.append("В документе отсутствуют заголовки (стиль 'Heading')")

        # Проверка обязательных разделов
        found_sections = {}
        for i, para in enumerate(document.paragraphs):
            text = para.text.strip()
            for section in required_sections:
                if text.lower().startswith(section.lower()):
                    found_sections[section] = i  # Записываем позицию раздела
                    break

        # Проверка отсутствующих разделов
        missing_sections = [s for s in required_sections if s not in found_sections]
        if missing_sections:
            errors.append(f"Отсутствуют обязательные разделы: {', '.join(missing_sections)}")

        # Проверка порядка разделов
        if len(found_sections) > 1:
            prev_section = None
            prev_pos = -1
            for section in required_sections:
                if section in found_sections:
                    curr_pos = found_sections[section]
                    if curr_pos < prev_pos:
                        errors.append(f"Нарушение порядка разделов: '{section}' находится после '{prev_section}'")
                    prev_pos = curr_pos
                    prev_section = section

        return errors if errors else "Structure check passed"