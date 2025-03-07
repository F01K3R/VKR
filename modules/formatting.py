from .base import CheckModule

class FormattingCheck(CheckModule):
    def check(self, doc_xml, styles, params):
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        errors = []
        expected_font = params.get("font", "Times New Roman")
        expected_size = params.get("font_size", 12) * 2  # Размер в half-points для DOCX

        # Проходим по всем параграфам в XML
        for para_idx, para in enumerate(doc_xml.findall('.//w:p', namespaces=ns), start=1):
            page_number = self._get_page_number(para_idx)
            # Собираем текст параграфа из всех <w:t> элементов
            text_elements = para.findall('.//w:t', namespaces=ns)
            para_text = "".join(t.text for t in text_elements if t.text) if text_elements else ""

            # Проверяем форматирование каждого текстового блока (run)
            for run in para.findall('.//w:r', namespaces=ns):
                rpr = run.find('.//w:rPr', namespaces=ns)
                if rpr is not None:
                    error_msg = []
                    font = rpr.find('.//w:rFonts', namespaces=ns)
                    font_name = font.get(f'{{{ns["w"]}}}ascii') if font is not None else None
                    sz = rpr.find('.//w:sz', namespaces=ns)
                    font_size = int(sz.get(f'{{{ns["w"]}}}val')) if sz is not None else None

                    if font_name and font_name != expected_font:
                        error_msg.append(f"шрифт '{font_name}' вместо '{expected_font}'")
                    if font_size and font_size != expected_size:
                        error_msg.append(f"размер {font_size // 2}pt вместо {expected_size // 2}pt")

                    if error_msg and para_text.strip():
                        errors.append(
                            f"Страница {page_number}: {' и '.join(error_msg)} в тексте '{para_text.strip()[:50]}'"
                        )

        return errors if errors else "Formatting check passed"

    def _get_page_number(self, para_idx):
        # Примерная эвристика для номера страницы
        return (para_idx // 5) + 1  # Предполагаем 5 параграфов на страницу