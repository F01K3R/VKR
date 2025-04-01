from .base import CheckModule
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PageParamsCheck(CheckModule):
    PAGE_SIZES = {
        "A4": (21.0, 29.7),  # ширина, высота в см (портретная ориентация)
        "A3": (29.7, 42.0),
        "Letter": (21.59, 27.94)
    }

    def check(self, document, params=None):
        # Проверка входных параметров
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return [f"Ошибка: params должен быть словарем, получено: {type(params)}"]

        expected_size = params.get("page_size", "A4")
        if expected_size not in self.PAGE_SIZES:
            return [f"Ошибка: неподдерживаемый размер страницы: {expected_size}"]

        margins = params.get("margins", {"left": 3, "right": 1, "top": 2, "bottom": 2})
        if not isinstance(margins, dict):
            return [f"Ошибка: margins должен быть словарем, получено: {type(margins)}"]

        required_keys = ["left", "right", "top", "bottom"]
        for key in required_keys:
            if key not in margins:
                return [f"Ошибка: в margins отсутствует ключ {key}"]
            if not isinstance(margins[key], (int, float)) or margins[key] < 0:
                return [f"Ошибка: margins[{key}] должен быть неотрицательным числом, получено: {margins[key]}"]

        # Допуски
        tolerance = 0.1  # 1 мм для размеров страницы
        tolerance_margin = 0.1  # 1 мм для полей

        # Ожидаемые размеры для портретной ориентации
        expected_width, expected_height = self.PAGE_SIZES[expected_size]

        errors = []

        # Проверяем секции документа
        try:
            sections = document.sections
        except Exception as e:
            return [f"Ошибка при доступе к секциям документа: {str(e)}"]

        # Проверка нумерации страниц
        page_numbers = []
        for i, section in enumerate(sections):
            try:
                # Проверяем колонтитулы для нумерации
                header = section.header
                for para in header.paragraphs:
                    if para.text.strip() and para.text.strip().isdigit():
                        page_numbers.append((int(para.text.strip()), i))
                        # Проверка расположения номера (должно быть по центру)
                        if para.alignment != 1:  # 1 соответствует выравниванию по центру
                            errors.append(f"Секция {i+1}: Номер страницы должен быть выровнен по центру верхнего поля")
            except Exception as e:
                errors.append(f"Секция {i+1}: Ошибка при проверке нумерации страниц: {str(e)}")
                continue

        # Проверка последовательности нумерации
        if page_numbers:
            # Первая страница (титульный лист) не должна иметь номера
            if page_numbers[0][0] == 1 and page_numbers[0][1] == 0:
                errors.append("Титульный лист (первая страница) не должен содержать номер страницы")
            # Вторая страница должна начинаться с номера 2
            if len(page_numbers) > 1 and page_numbers[1][0] != 2:
                errors.append(f"Вторая страница должна иметь номер 2, текущий номер: {page_numbers[1][0]}")
            # Проверка сквозной нумерации
            for idx, (num, sec_idx) in enumerate(page_numbers[1:], start=1):
                expected_num = idx + 1
                if num != expected_num:
                    errors.append(f"Нарушение сквозной нумерации страниц: ожидается номер {expected_num}, получен {num} в секции {sec_idx+1}")

        for i, section in enumerate(sections, start=1):
            try:
                section_data = {
                    "width_cm": section.page_width.cm if section.page_width is not None else 0,
                    "height_cm": section.page_height.cm if section.page_height is not None else 0,
                    "left_margin": section.left_margin.cm if section.left_margin is not None else 0,
                    "right_margin": section.right_margin.cm if section.right_margin is not None else 0,
                    "top_margin": section.top_margin.cm if section.top_margin is not None else 0,
                    "bottom_margin": section.bottom_margin.cm if section.bottom_margin is not None else 0
                }
            except Exception as e:
                errors.append(f"Секция {i}: Ошибка при получении параметров страницы: {str(e)}")
                continue

            # Проверка допустимых значений
            if section_data["width_cm"] <= 0 or section_data["height_cm"] <= 0:
                errors.append(f"Секция {i}: Некорректные размеры страницы ({section_data['width_cm']:.2f} x {section_data['height_cm']:.2f} см)")
                continue

            # Определяем ориентацию страницы
            is_landscape = section_data["width_cm"] > section_data["height_cm"]

            # Проверка размера страницы с учётом ориентации
            if is_landscape:
                # Если альбомная ориентация, меняем местами ожидаемые ширину и высоту
                if not (abs(section_data["width_cm"] - expected_height) <= tolerance and
                        abs(section_data["height_cm"] - expected_width) <= tolerance):
                    errors.append(
                        f"Секция {i}: Размер страницы не соответствует ожидаемому ({expected_size}, альбомная ориентация): "
                        f"получено {section_data['width_cm']:.2f} x {section_data['height_cm']:.2f} см, "
                        f"ожидается {expected_height:.2f} x {expected_width:.2f} см"
                    )
                errors.append(f"Секция {i}: Ориентация страницы альбомная, ожидается портретная")
            else:
                # Если портретная ориентация
                if not (abs(section_data["width_cm"] - expected_width) <= tolerance and
                        abs(section_data["height_cm"] - expected_height) <= tolerance):
                    errors.append(
                        f"Секция {i}: Размер страницы не соответствует ожидаемому ({expected_size}, портретная ориентация): "
                        f"получено {section_data['width_cm']:.2f} x {section_data['height_cm']:.2f} см, "
                        f"ожидается {expected_width:.2f} x {expected_height:.2f} см"
                    )

            # Проверка полей с допуском
            if not (abs(section_data["left_margin"] - margins["left"]) <= tolerance_margin):
                errors.append(
                    f"Секция {i}: Поле слева ({section_data['left_margin']:.2f} см) не соответствует ожидаемому ({margins['left']} см ± {tolerance_margin} см)"
                )
            if not (abs(section_data["right_margin"] - margins["right"]) <= tolerance_margin):
                errors.append(
                    f"Секция {i}: Поле справа ({section_data['right_margin']:.2f} см) не соответствует ожидаемому ({margins['right']} см ± {tolerance_margin} см)"
                )
            if not (abs(section_data["top_margin"] - margins["top"]) <= tolerance_margin):
                errors.append(
                    f"Секция {i}: Верхнее поле ({section_data['top_margin']:.2f} см) не соответствует ожидаемому ({margins['top']} см ± {tolerance_margin} см)"
                )
            if not (abs(section_data["bottom_margin"] - margins["bottom"]) <= tolerance_margin):
                errors.append(
                    f"Секция {i}: Нижнее поле ({section_data['bottom_margin']:.2f} см) не соответствует ожидаемому ({margins['bottom']} см ± {tolerance_margin} см)"
                )

            # Отладочный вывод через логирование
            logger.debug(f"Секция {i}: {section_data['width_cm']:.2f} x {section_data['height_cm']:.2f} см, "
                         f"ориентация: {'альбомная' if is_landscape else 'портретная'}")

        return errors