from datetime import datetime
from .structure import StructureCheck
from .page_params import PageParamsCheck
from .formatting import FormattingCheck
from .references import ReferencesCheck
from utils.xml_utils import extract_xml, get_styles


class CheckTemplate:
    def __init__(self, structure_params=None, page_params=None, formatting_params=None, references_params=None):
        self.structure_params = structure_params or {"require_headings": True}
        self.page_params = page_params or {
            "page_size": "A4",
            "margins": {"left": 2, "right": 1, "top": 2, "bottom": 2}
        }
        self.formatting_params = formatting_params or {"font": "Times New Roman", "font_size": 12}
        self.references_params = references_params or {"standard": "ГОСТ Р 7.0.5-2008"}

    def apply(self, doc, file_path, report_file=None):
        results = {}

        structure_check = StructureCheck()
        results["structure"] = structure_check.check(doc, self.structure_params)

        page_params_check = PageParamsCheck()
        results["page_params"] = page_params_check.check(doc, self.page_params)

        formatting_check = FormattingCheck()
        doc_xml, styles_xml = extract_xml(file_path)
        styles = get_styles(styles_xml)
        results["formatting"] = formatting_check.check(doc_xml, styles, self.formatting_params)

        references_check = ReferencesCheck()
        results["references"] = references_check.check(doc, self.references_params)

        if report_file:
            self._save_report(results, report_file)
        return results

    def _save_report(self, results, report_file):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Отчет о проверке документа\n")
            f.write(f"Дата и время: {now}\n\n")
            total_errors = 0
            for check, result in results.items():
                f.write(f"## {check.capitalize()}\n")
                if isinstance(result, str):
                    f.write(f"{result}\n")
                elif isinstance(result, list):
                    f.write("Ошибки:\n")
                    for error in result:
                        f.write(f"- {error}\n")
                    total_errors += len(result)
                f.write("\n")
            f.write(f"**Общее количество ошибок: {total_errors}**\n")