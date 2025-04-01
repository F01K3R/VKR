import os
import time
import logging
import argparse
from multiprocessing import Pool, cpu_count
from modules.parser import DocumentParser
from modules.template import CheckTemplate

# Настройка логирования (вызываем один раз)
if not logging.getLogger().hasHandlers():  # Проверяем, чтобы не добавлять дублирующие обработчики
    logging.basicConfig(
        level=logging.DEBUG,  # Устанавливаем уровень DEBUG, чтобы записывать все сообщения
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("processing.log", mode='w', encoding='utf-8'),  # Перезаписываем файл
            logging.StreamHandler()
        ]
    )
logger = logging.getLogger(__name__)

def process_file(args):
    """Обрабатывает один файл и возвращает результаты вместе с временем обработки."""
    file_path, file_index = args
    logger.debug(f"Начало обработки файла: {file_path} (индекс: {file_index})")
    try:
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            return {
                "file_path": file_path,
                "results": {"error": [f"Файл не найден: {file_path}"]},
                "time": 0.0
            }
        if not file_path.lower().endswith('.docx'):
            logger.error(f"Неподдерживаемый формат файла: {file_path}")
            return {
                "file_path": file_path,
                "results": {"error": ["Неподдерживаемый формат файла, ожидается .docx"]},
                "time": 0.0
            }

        parser = DocumentParser()
        doc = parser.parse(file_path)

        diploma_template = CheckTemplate(
            structure_params={
                "require_headings": True,
                "required_sections": ["Оглавление", "Введение", "Заключение", "Список литературы"]
            },
            page_params={"page_size": "A4", "margins": {"left": 3, "right": 1, "top": 2, "bottom": 2}},
            formatting_params={
                "font": "Times New Roman",
                "font_size": 14,
                "line_spacing": 1.5,
                "alignment": "justify",
                "first_line_indent": 1.25
            },
            references_params={"standard": "ГОСТ Р 7.0.5-2008"},
            tables_params={"use_chapter_numbering": False},
            illustrations_params={"use_chapter_numbering": False},
            appendices_params={"appendix_number_style": "numeric"}
        )

        reports_dir = "reports"
        try:
            os.makedirs(reports_dir, exist_ok=True)
            os.chmod(reports_dir, 0o700)
        except Exception as e:
            logger.error(f"Ошибка при создании директории reports: {str(e)}")
            return {
                "file_path": file_path,
                "results": {"error": [f"Ошибка при создании директории reports: {str(e)}"]},
                "time": 0.0
            }

        report_filename = f"report_check_file_{file_index}.md"
        report_file = os.path.join(reports_dir, report_filename)

        start_time = time.time()
        results = diploma_template.apply(doc, file_path, report_file=report_file)
        end_time = time.time()
        processing_time = end_time - start_time

        logger.info(f"Файл {file_path} обработан за {processing_time:.2f} секунд")
        logger.debug(f"Результаты для файла {file_path}: {results}")

        return {
            "file_path": file_path,
            "results": results,
            "time": processing_time
        }

    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file_path}: {str(e)}")
        return {
            "file_path": file_path,
            "results": {"error": [f"Ошибка при обработке файла: {str(e)}"]},
            "time": 0.0
        }

def process_multiple_files(file_paths, num_processes=None):
    """Обрабатывает несколько файлов параллельно."""
    if not file_paths:
        logger.error("Список файлов пуст")
        return []

    if num_processes is None:
        num_processes = min(cpu_count(), len(file_paths))
    num_processes = max(1, num_processes)

    logger.info(f"Обработка {len(file_paths)} файлов с использованием {num_processes} процессов...")

    file_args = [(file_path, idx) for idx, file_path in enumerate(file_paths)]

    try:
        with Pool(processes=num_processes) as pool:
            results_list = pool.map(process_file, file_args)
    except Exception as e:
        logger.error(f"Ошибка при параллельной обработке: {str(e)}")
        return []

    return results_list

def format_results(results):
    """Форматирует результаты для вывода."""
    if not results:
        return "Нет результатов"

    output = []
    for check, res in results.items():
        if isinstance(res, list):
            if not res:
                output.append(f"{check}: Проверка пройдена успешно")
            else:
                output.append(f"{check}:")
                for error in res:
                    output.append(f"  - {error}")
        else:
            output.append(f"{check}: {res}")
    return "\n".join(output)

def main():
    """Основная функция для консольного запуска."""
    parser = argparse.ArgumentParser(description="Проверка документов .docx на соответствие требованиям.")
    parser.add_argument("files", nargs='+', help="Путь к файлам .docx для обработки")
    parser.add_argument("--processes", type=int, default=None,
                        help="Количество процессов для параллельной обработки (по умолчанию: число CPU или количество файлов)")

    args = parser.parse_args()

    logger.debug("Запуск программы")

    # Проверяем входные файлы
    input_files = args.files
    valid_files = [f for f in input_files if os.path.exists(f)]
    if len(valid_files) != len(input_files):
        missing_files = set(input_files) - set(valid_files)
        logger.warning(f"Следующие файлы не найдены и будут пропущены: {missing_files}")
        input_files = valid_files

    if not input_files:
        logger.error("Нет доступных файлов для обработки")
        print("Ошибка: Нет доступных файлов для обработки. Укажите существующие файлы .docx.")
        return

    # Обрабатываем файлы
    results_list = process_multiple_files(input_files, num_processes=args.processes)

    # Выводим результаты
    for result in results_list:
        file_path = result["file_path"]
        file_results = result["results"]
        processing_time = result["time"]
        file_index = input_files.index(file_path)
        print(f"\nРезультаты для файла {file_path} (ID: file_{file_index}) (время обработки: {processing_time:.2f} секунд):")
        print(format_results(file_results))

    logger.debug("Программа завершена")

if __name__ == "__main__":
    main()