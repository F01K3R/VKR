from .base import CheckModule


class PageParamsCheck(CheckModule):
    def check(self, document, params):
        expected_size = params.get("page_size", "A4")
        margins = params.get("margins", {"left": 3, "right": 1, "top": 2, "bottom": 2})
        errors = []

        # Допуск для сравнения размеров (в см)
        tolerance = 0.1  # 1 мм

        # Ожидаемые размеры для A4
        a4_width = 21.0  # см
        a4_height = 29.7  # см

        # Проверяем все секции документа
        for i, section in enumerate(document.sections, start=1):
            width_cm = section.page_width.cm
            height_cm = section.page_height.cm

            # Проверяем размер страницы с учетом допуска
            if expected_size == "A4":
                if not (abs(width_cm - a4_width) <= tolerance and abs(height_cm - a4_height) <= tolerance):
                    errors.append(
                        f"Секция {i}: Incorrect page size ({width_cm:.2f} x {height_cm:.2f} см, expected {a4_width} x {a4_height} см)")

            # Проверяем поля
            if section.left_margin.cm < margins.get("left"):
                errors.append(
                    f"Секция {i}: Left margin ({section.left_margin.cm:.2f} см) is less than expected ({margins.get('left')} см)")
            if section.right_margin.cm < margins.get("right"):
                errors.append(
                    f"Секция {i}: Right margin ({section.right_margin.cm:.2f} см) is less than expected ({margins.get('right')} см)")
            if section.top_margin.cm < margins.get("top"):
                errors.append(
                    f"Секция {i}: Top margin ({section.top_margin.cm:.2f} см) is less than expected ({margins.get('top')} см)")
            if section.bottom_margin.cm < margins.get("bottom"):
                errors.append(
                    f"Секция {i}: Bottom margin ({section.bottom_margin.cm:.2f} см) is less than expected ({margins.get('bottom')} см)")

        # Отладочный вывод для проверки реальных значений
        #for i, section in enumerate(document.sections, start=1):
            #print(f"Секция {i}: {section.page_width.cm:.2f} x {section.page_height.cm:.2f} см")

        return errors if errors else "Page parameters check passed"