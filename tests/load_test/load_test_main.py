import time
from operator import length_hint

import psutil
import os
import threading
import random
import string
from multiprocessing import Pool
from docx import Document
from docx.shared import Pt
from modules.parser import DocumentParser
from modules.template import CheckTemplate

def generate_random_text(length):
    """Генерирует случайный текст заданной длины."""
    return ''.join(random.choices(string.ascii_letters + string.digits + " ", k=length))

def generate_test_doc(filename, num_paragraphs, include_references=False):
    """Генерирует тестовый документ с уникальным содержимым."""
    doc = Document()
    doc.add_heading("Оглавление", level=1)
    doc.add_heading("Введение", level=1)
    for i in range(num_paragraphs):
        p = doc.add_paragraph(f"Тестовый параграф {i}: {generate_random_text(500)}")
        p.style.font.name = "Times New Roman"
        p.style.font.size = Pt(14)
    doc.add_heading("Заключение", level=1)
    if include_references:
        doc.add_paragraph("Список литературы")
        doc.add_paragraph(f"Иванов И.И. Статья // Журнал. {random.randint(2010, 2023)}. № {random.randint(1, 10)}. С. 1-5.")
    doc.save(filename)

def monitor_resources(stop_event, interval=1):
    """Мониторит использование ресурсов в реальном времени."""
    process = psutil.Process()
    print("\nМониторинг ресурсов в реальном времени (Ctrl+C для остановки):")
    print("Time (s) | CPU (%) | Memory (%)")
    start_time = time.time()
    while not stop_event.is_set():
        cpu_usage = psutil.cpu_percent(interval=None)
        memory_usage = process.memory_percent()
        elapsed_time = time.time() - start_time
        print(f"{elapsed_time:.2f}s    | {cpu_usage:6.1f} | {memory_usage:6.2f}")
        time.sleep(interval)

def process_document(file_path):
    """Обрабатывает один документ и возвращает метрики производительности."""
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

    start_time = time.time()
    start_cpu = psutil.cpu_percent(interval=None)
    start_memory = psutil.virtual_memory().percent

    results = diploma_template.apply(doc, file_path)

    end_time = time.time()
    end_cpu = psutil.cpu_percent(interval=None)
    end_memory = psutil.virtual_memory().percent

    return {
        "file": file_path,
        "time": end_time - start_time,
        "cpu_diff": end_cpu - start_cpu,
        "memory_diff": end_memory - start_memory,
        "results": results
    }

def infinite_load_test(num_files=10, base_paragraphs=100):
    """Бесконечное тестирование с N различными файлами."""
    test_files_dir = "test_files"
    os.makedirs(test_files_dir, exist_ok=True)

    # Генерируем N различных файлов
    file_paths = []
    print(f"Генерация {num_files} тестовых файлов...")
    for i in range(num_files):
        # Разное количество параграфов для разнообразия
        num_paragraphs = base_paragraphs + random.randint(-50, 50)
        file_path = os.path.join(test_files_dir, f"test_file_{i}.docx")
        generate_test_doc(file_path, num_paragraphs, include_references=True)
        file_paths.append(file_path)

    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event,))
    monitor_thread.start()

    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\nИтерация {iteration}: Тестирование {num_files} файлов")
            start_time = time.time()
            with Pool(processes=8) as pool:
                results = pool.map(process_document, file_paths)
            total_time = time.time() - start_time

            for i, result in enumerate(results):
                print(f"File {result['file']}: Time={result['time']:.2f}s, CPU Diff={result['cpu_diff']:.1f}%, Memory Diff={result['memory_diff']:.1f}%")
            print(f"Total Time for {num_files} files: {total_time:.2f}s")

    except KeyboardInterrupt:
        print("\nОстановка тестирования...")
        stop_event.set()
        monitor_thread.join()
        print("Тестирование завершено.")

if __name__ == "__main__":
    # Запускаем бесконечное тестирование с 100 файлами
    infinite_load_test(num_files=100, base_paragraphs=100)