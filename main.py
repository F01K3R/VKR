from modules.parser import DocumentParser
from modules.template import CheckTemplate
from utils.xml_utils import extract_xml, get_styles

if __name__ == "__main__":
    file_path = "student_report.docx"
    parser = DocumentParser()
    doc = parser.parse(file_path)

    # Пример шаблона с требованиями к структуре
    diploma_template = CheckTemplate(
        structure_params={
            "require_headings": True,
            "required_sections": ["Оглавление","Введение", "Заключение", "Список литературы"]
        },
        page_params={"page_size": "A4", "margins": {"left": 3, "right": 1, "top": 2, "bottom": 2}},
        formatting_params={"font": "Times New Roman", "font_size": 14},
        references_params={"standard": "ГОСТ Р 7.0.5-2008"}
    )

    results = diploma_template.apply(doc, file_path, report_file="report_check.md")
    for check, result in results.items():
        print(f"{check}: {result}")