import os
import logging
from datetime import datetime
from modules.structure import StructureCheck
from modules.page_params import PageParamsCheck
from modules.formatting import FormattingCheck
from modules.references import ReferencesCheck
from modules.tables import TablesCheck
from modules.illustrations import IllustrationsCheck
from modules.appendices import AppendicesCheck

# Настройка логирования (вызываем только если обработчики ещё не добавлены)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("processing.log", mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
logger = logging.getLogger(__name__)

class CheckTemplate:
    def __init__(self, structure_params=None, page_params=None, formatting_params=None, references_params=None,
                 tables_params=None, illustrations_params=None, appendices_params=None):
        # Параметры для существующих проверок
        self.structure_params = structure_params or {"require_headings": True}
        self.page_params = page_params or {
            "page_size": "A4",
            "margins": {"left": 2, "right": 1, "top": 2, "bottom": 2}
        }
        self.formatting_params = formatting_params or {
            "font": "Times New Roman",
            "font_size": 14,
            "line_spacing": 1.5,
            "alignment": "justify",
            "first_line_indent": 1.25
        }
        self.references_params = references_params or {"standard": "ГОСТ Р 7.0.5-2008"}

        # Параметры для новых проверок
        self.tables_params = tables_params or {"use_chapter_numbering": False}
        self.illustrations_params = illustrations_params or {"use_chapter_numbering": False}
        self.appendices_params = appendices_params or {"appendix_number_style": "numeric"}

        # Инициализация модулей проверки
        self.structure_check = StructureCheck()
        self.page_params_check = PageParamsCheck()
        self.formatting_check = FormattingCheck()
        self.references_check = ReferencesCheck()
        self.tables_check = TablesCheck()
        self.illustrations_check = IllustrationsCheck()
        self.appendices_check = AppendicesCheck()

    def apply(self, doc, file_path, report_file=None):
        logger.debug(f"Начало применения шаблона проверки для файла: {file_path}")
        results = {}

        # Проверка структуры
        try:
            results["structure"] = self.structure_check.check(doc, self.structure_params)
            logger.debug(f"Результат проверки структуры: {results['structure']}")
        except Exception as e:
            logger.error(f"Ошибка при проверке структуры для файла {file_path}: {str(e)}")
            results["structure"] = [f"Ошибка при проверке структуры: {str(e)}"]

        # Проверка параметров страницы
        try:
            results["page_params"] = self.page_params_check.check(doc, self.page_params)
            logger.debug(f"Результат проверки параметров страницы: {results['page_params']}")
        except Exception as e:
            logger.error(f"Ошибка при проверке параметров страницы для файла {file_path}: {str(e)}")
            results["page_params"] = [f"Ошибка при проверке параметров страницы: {str(e)}"]

        # Проверка форматирования
        try:
            results["formatting"] = self.formatting_check.check(doc, file_path, self.formatting_params)
            logger.debug(f"Результат проверки форматирования: {results['formatting']}")
        except Exception as e:
            logger.error(f"Ошибка при проверке форматирования для файла {file_path}: {str(e)}")
            results["formatting"] = [f"Ошибка при проверке форматирования: {str(e)}"]

        # Проверка списка литературы
        try:
            results["references"] = self.references_check.check(doc, self.references_params)
            logger.debug(f"Результат проверки ссылок: {results['references']}")
        except Exception as e:
            logger.error(f"Ошибка при проверке ссылок для файла {file_path}: {str(e)}")
            results["references"] = [f"Ошибка при проверке ссылок: {str(e)}"]

        # Проверка таблиц
        try:
            results["tables"] = self.tables_check.check(doc, self.tables_params)
            logger.debug(f"Результат проверки таблиц: {results['tables']}")
        except Exception as e:
            logger.error(f"Ошибка при проверке таблиц для файла {file_path}: {str(e)}")
            results["tables"] = [f"Ошибка при проверке таблиц: {str(e)}"]

        # Проверка иллюстраций
        try:
            results["illustrations"] = self.illustrations_check.check(doc, self.illustrations_params)
            logger.debug(f"Результат проверки иллюстраций: {results['illustrations']}")
        except Exception as e:
            logger.error(f"Ошибка при проверке иллюстраций для файла {file_path}: {str(e)}")
            results["illustrations"] = [f"Ошибка при проверке иллюстраций: {str(e)}"]

        # Проверка приложений
        try:
            results["appendices"] = self.appendices_check.check(doc, self.appendices_params)
            logger.debug(f"Результат проверки приложений: {results['appendices']}")
        except Exception as e:
            logger.error(f"Ошибка при проверке приложений для файла {file_path}: {str(e)}")
            results["appendices"] = [f"Ошибка при проверке приложений: {str(e)}"]

        # Сохранение отчёта, если указано
        if report_file:
            try:
                self._save_report(results, report_file, file_path)
            except Exception as e:
                logger.error(f"Ошибка при сохранении отчёта для файла {file_path}: {str(e)}")
                results["report"] = [f"Ошибка при сохранении отчёта: {str(e)}"]

        logger.debug(f"Завершение применения шаблона проверки для файла: {file_path}")
        return results

    def _save_report(self, results, report_file, file_path):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_index = os.path.basename(report_file).replace("report_check_file_", "").replace(".md", "")

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"# Отчёт о проверке документа (ID: file_{file_index})\n")
                f.write(f"Дата и время: {now}\n\n")
                total_errors = 0
                for check, result in results.items():
                    f.write(f"## {check.capitalize()}\n")
                    if not result:
                        f.write("Проверка пройдена успешно\n")
                    else:
                        f.write("Ошибки:\n")
                        for error in result:
                            f.write(f"- {error}\n")
                        total_errors += len(result)
                    f.write("\n")
                f.write(f"**Общее количество ошибок: {total_errors}**\n")
            os.chmod(report_file, 0o600)
            logger.info(f"Отчёт сохранён: {report_file}")
        except Exception as e:
            logger.error(f"Не удалось сохранить отчёт: {str(e)}")
            raise Exception(f"Не удалось сохранить отчёт: {str(e)}")