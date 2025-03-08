import os
from datetime import datetime
from multiprocessing import Pool
from modules.parser import DocumentParser
from modules.template import CheckTemplate
from utils.xml_utils import extract_xml, get_styles


def process_file(file_path):
    """Обрабатывает один файл и возвращает результаты."""
    parser = DocumentParser()
    doc = parser.parse(file_path)

    diploma_template = CheckTemplate(
        structure_params={
            "require_headings": True,
            "required_sections": ["Оглавление", "Введение", "Заключение", "Список литературы"]
        },
        page_params={"page_size": "A4", "margins": {"left": 3, "right": 1, "top": 2, "bottom": 2}},
        formatting_params={"font": "Times New Roman", "font_size": 14},
        references_params={"standard": "ГОСТ Р 7.0.5-2008"}
    )

    # Создаём директорию reports, если её нет
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)

    # Генерируем путь для отчёта в директории reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"report_check_{os.path.basename(file_path).replace('.docx', '')}_{timestamp}.md"
    report_file = os.path.join(reports_dir, report_filename)

    results = diploma_template.apply(doc, file_path, report_file=report_file)
    return {file_path: results}


def process_multiple_files(file_paths, num_processes=8):
    """Обрабатывает несколько файлов параллельно."""
    with Pool(processes=num_processes) as pool:
        results_list = pool.map(process_file, file_paths)

    # Объединяем результаты в один словарь
    combined_results = {}
    for result in results_list:
        combined_results.update(result)

    return combined_results


if __name__ == "__main__":
    # Список файлов для обработки
    input_files = [
        "student_report.docx",
        "student_report1.docx",
    ]

    print(f"Обработка {len(input_files)} файлов параллельно...")
    results = process_multiple_files(input_files, num_processes=8)

    # Вывод результатов
    for file_path, file_results in results.items():
        print(f"\nРезультаты для {file_path}:")
        for check, result in file_results.items():
            print(f"  {check}: {result}")