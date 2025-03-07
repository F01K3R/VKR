import zipfile
import xml.etree.ElementTree as ET


def extract_xml(file_path):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall('extracted_docx')
    doc_xml = ET.parse('extracted_docx/word/document.xml')
    styles_xml = ET.parse('extracted_docx/word/styles.xml')
    return doc_xml, styles_xml

def get_styles(styles_xml):
    styles = {}
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    for style in styles_xml.findall('.//w:style', namespaces=ns):
        style_id = style.get(f'{{{ns["w"]}}}styleId')
        style_name = style.find('.//w:name', namespaces=ns).get(f'{{{ns["w"]}}}val')
        styles[style_id] = style_name
    return styles