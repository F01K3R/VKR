import sys
import os
import logging
import time
import concurrent.futures
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QTextEdit, QProgressBar, QFileDialog, QLabel)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from logging.handlers import QueueHandler
import queue
import traceback

# Импортируем вашу существующую логику
from main import process_file, format_results

# Настройка логирования
log_queue = queue.Queue()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
queue_handler = QueueHandler(log_queue)
queue_handler.setLevel(logging.DEBUG)
logger.handlers = []  # Удаляем старые обработчики
logger.addHandler(queue_handler)

# Добавляем логирование в файл для диагностики
file_handler = logging.FileHandler("debug.log")
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

def process_file_wrapper(args):
    """Функция-обёртка для обработки одного файла."""
    file_path, file_index, reports_dir = args  # Добавляем reports_dir
    logger.debug(f"Начало обработки файла: {file_path} (индекс: {file_index})")
    start_time = time.time()
    result = process_file((file_path, file_index, reports_dir))
    end_time = time.time()
    return {
        "file_path": file_path,
        "file_index": file_index,
        "results": result,
        "time": end_time - start_time
    }

class ProcessingThread(QThread):
    progress = pyqtSignal(int)  # Сигнал для обновления прогресса
    log_message = pyqtSignal(str)  # Сигнал для логов
    file_processed = pyqtSignal(dict)  # Сигнал для обработки одного файла
    finished = pyqtSignal(list)  # Сигнал для завершения обработки
    error = pyqtSignal(str)  # Сигнал для ошибок

    def __init__(self, file_paths, reports_dir):
        super().__init__()
        self.file_paths = file_paths
        self.reports_dir = reports_dir  # Сохраняем путь к директории для отчётов
        self._is_running = True  # Флаг для управления выполнением
        self.futures = []  # Список для хранения Future объектов

    def run(self):
        logger.debug("ProcessingThread: Начало обработки в потоке")
        total_files = len(self.file_paths)
        if total_files == 0:
            self.error.emit("Нет файлов для обработки")
            return

        try:
            # Определяем количество процессов
            max_workers = min(os.cpu_count() or 1, 8)  # Ограничиваем до 8 процессов
            logger.debug(f"ProcessingThread: Используется {max_workers} процессов для обработки")

            results_list = []
            completed_files = 0

            # Создаём список задач с индексами и передаём reports_dir
            tasks = [(file_path, i, self.reports_dir) for i, file_path in enumerate(self.file_paths)]

            # Используем ProcessPoolExecutor для параллельной обработки
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Запускаем задачи
                self.futures = [executor.submit(process_file_wrapper, task) for task in tasks]

                # Обрабатываем результаты по мере их завершения
                for future in concurrent.futures.as_completed(self.futures):
                    if not self._is_running:
                        logger.debug("ProcessingThread: Обработка прервана")
                        break
                    try:
                        result = future.result()
                        results_list.append(result)
                        completed_files += 1
                        # Отправляем сигнал о завершении обработки одного файла
                        self.file_processed.emit(result)
                        # Обновляем прогресс
                        progress_value = int((completed_files) / total_files * 100)
                        self.progress.emit(progress_value)
                    except Exception as e:
                        error_msg = f"Ошибка при обработке файла: {str(e)}\n{traceback.format_exc()}"
                        logger.error(error_msg)
                        self.error.emit(error_msg)

            if self._is_running:
                self.finished.emit(results_list)
        except Exception as e:
            error_msg = f"Критическая ошибка при обработке файлов: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.error.emit(error_msg)

    def stop(self):
        logger.debug("ProcessingThread: Остановка потока")
        self._is_running = False
        # Отменяем все незавершённые задачи
        for future in self.futures:
            future.cancel()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Автоматический нормоконтроль отчётов")
        self.setGeometry(100, 100, 800, 600)

        # Основной виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Кнопка для выбора директории для отчётов
        self.select_reports_dir_btn = QPushButton("Выбрать директорию для отчётов")
        self.select_reports_dir_btn.clicked.connect(self.select_reports_dir)
        layout.addWidget(self.select_reports_dir_btn)

        # Поле для отображения выбранной директории
        self.reports_dir_label = QLabel("Директория для отчётов: (не выбрана)")
        layout.addWidget(self.reports_dir_label)
        self.reports_dir = None  # Переменная для хранения пути к директории

        # Кнопка для выбора файлов
        self.select_files_btn = QPushButton("Выбрать файлы")
        self.select_files_btn.clicked.connect(self.select_files)
        layout.addWidget(self.select_files_btn)

        # Список выбранных файлов
        self.file_list = QListWidget()
        layout.addWidget(QLabel("Выбранные файлы:"))
        layout.addWidget(self.file_list)

        # Кнопка для запуска обработки
        self.process_btn = QPushButton("Запустить обработку")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)

        # Кнопка для отмены обработки
        self.cancel_btn = QPushButton("Отменить обработку")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        layout.addWidget(self.cancel_btn)

        # Кнопка для очистки окон
        self.clear_btn = QPushButton("Очистить окна")
        self.clear_btn.clicked.connect(self.clear_all)
        layout.addWidget(self.clear_btn)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(QLabel("Прогресс обработки:"))
        layout.addWidget(self.progress_bar)

        # Текстовое поле для логов
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Логи:"))
        layout.addWidget(self.log_text)

        # Текстовое поле для результатов
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(QLabel("Результаты:"))
        layout.addWidget(self.results_text)

        # Флаг для управления log_thread
        self._log_thread_running = True

        # Буфер для логов
        self.log_buffer = []
        self.last_log_update = 0

        # Поток для обработки логов
        self.log_thread = QThread()
        self.log_thread.run = self.process_log_queue
        self.log_thread.start()

        # Таймер для периодического обновления логов
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.flush_log_buffer)
        self.log_timer.start(500)  # Обновляем логи каждые 500 мс

    def select_reports_dir(self):
        """Открывает диалог для выбора директории для сохранения отчётов."""
        directory = QFileDialog.getExistingDirectory(self, "Выбрать директорию для отчётов", "")
        if directory:
            self.reports_dir = directory
            self.reports_dir_label.setText(f"Директория для отчётов: {directory}")
            self.log_text.append(f"Выбрана директория для отчётов: {directory}")
        else:
            self.reports_dir = None
            self.reports_dir_label.setText("Директория для отчётов: (не выбрана)")
            self.log_text.append("Директория для отчётов не выбрана")

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выбрать файлы", "", "DOCX Files (*.docx)")
        if files:
            self.file_list.clear()
            self.file_list.addItems(files)
            self.process_btn.setEnabled(True)
            self.log_text.append(f"Выбрано {len(files)} файлов")
        else:
            self.log_text.append("Файлы не выбраны")

    def start_processing(self):
        file_paths = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        if not file_paths:
            self.log_text.append("Ошибка: Не выбраны файлы для обработки.")
            return

        # Проверяем, выбрана ли директория для отчётов
        if not self.reports_dir:
            self.log_text.append("Ошибка: Не выбрана директория для сохранения отчётов.")
            return

        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.clear_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.results_text.clear()
        self.log_text.append("Начало обработки...")

        # Запуск обработки в отдельном потоке
        self.processing_thread = ProcessingThread(file_paths, self.reports_dir)
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.log_message.connect(self.log_text.append)
        self.processing_thread.file_processed.connect(self.file_processed)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error.connect(self.handle_error)
        self.processing_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def handle_error(self, error_msg):
        self.log_text.append(error_msg)
        self.results_text.append("Обработка завершена с ошибкой. Подробности в логах.")
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)

    def file_processed(self, result):
        try:
            if result is None:  # Пропускаем, если обработка была прервана
                return
            file_path = result["file_path"]
            file_index = result["file_index"]
            file_results = result["results"]
            processing_time = result["time"]
            self.results_text.append(
                f"\nРезультаты для файла (ID: file_{file_index}) (время обработки: {processing_time:.2f}s):")
            formatted_result = format_results(file_results)
            self.results_text.append(formatted_result if formatted_result else "Нет данных для отображения")
            # Прокручиваем результаты вниз
            self.results_text.verticalScrollBar().setValue(self.results_text.verticalScrollBar().maximum())
        except Exception as e:
            error_msg = f"Ошибка в file_processed: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.log_text.append(error_msg)

    def processing_finished(self, results_list):
        try:
            logger.debug("processing_finished: Начало обработки результатов")
            self.log_text.append(f"Обработка завершена. Получено {len(results_list)} результатов.")
            self.process_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.clear_btn.setEnabled(True)
            logger.debug("processing_finished: Завершение обработки результатов")
        except Exception as e:
            error_msg = f"Ошибка в processing_finished: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.log_text.append(error_msg)
            self.process_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.clear_btn.setEnabled(True)

    def cancel_processing(self):
        if hasattr(self, 'processing_thread') and self.processing_thread.isRunning():
            self.log_text.append("Отмена обработки...")
            self.processing_thread.stop()
            self.processing_thread.quit()
            self.processing_thread.wait()
            self.process_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self.clear_btn.setEnabled(True)
            self.log_text.append("Обработка отменена")

    def clear_all(self):
        self.file_list.clear()
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.results_text.clear()
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.log_text.append("Окна очищены")

    def process_log_queue(self):
        while self._log_thread_running:
            try:
                record = log_queue.get(timeout=0.1)
                if record is None:
                    break
                msg = queue_handler.format(record)
                # Добавляем сообщение в буфер
                self.log_buffer.append(msg)
            except queue.Empty:
                continue
            except Exception as e:
                error_msg = f"Ошибка в process_log_queue: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                self.log_buffer.append(error_msg)
        logger.debug("process_log_queue: Завершение потока обработки логов")

    def flush_log_buffer(self):
        if not self.log_buffer:
            return
        current_time = time.time()
        # Обновляем логи не чаще, чем раз в 500 мс
        if current_time - self.last_log_update < 0.5:
            return
        # Ограничиваем длину логов
        if self.log_text.toPlainText().count('\n') > 1000:
            self.log_text.clear()
            self.log_text.append("Логи очищены из-за превышения лимита")
        # Обновляем UI одним вызовом
        self.log_text.append("\n".join(self.log_buffer))
        self.log_buffer.clear()
        self.last_log_update = current_time
        # Прокручиваем логи вниз
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def closeEvent(self, event):
        logger.debug("closeEvent: Начало закрытия приложения")

        # Останавливаем log_thread
        self._log_thread_running = False
        log_queue.put(None)  # Отправляем сигнал завершения
        self.log_timer.stop()  # Останавливаем таймер
        self.log_thread.quit()
        self.log_thread.wait(1000)  # Даём потоку 1 секунду на завершение
        if self.log_thread.isRunning():
            logger.warning("closeEvent: log_thread не завершился вовремя, принудительное завершение")
            self.log_thread.terminate()

        # Останавливаем processing_thread, если он существует
        if hasattr(self, 'processing_thread') and self.processing_thread.isRunning():
            logger.debug("closeEvent: Остановка processing_thread")
            self.processing_thread.stop()
            self.processing_thread.quit()
            self.processing_thread.wait(1000)  # Даём потоку 1 секунду на завершение
            if self.processing_thread.isRunning():
                logger.warning("closeEvent: processing_thread не завершился вовремя, принудительное завершение")
                self.processing_thread.terminate()

        logger.debug("closeEvent: Все потоки завершены, приложение закрывается")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())  # Используем sys.exit для корректного завершения