from lxml import etree as ET
from zipfile import ZipFile
from io import BytesIO

def extract_xml(file_path):
    with ZipFile(file_path, 'r') as zip_ref:
        doc_xml_data = zip_ref.read('word/document.xml')
        styles_xml_data = zip_ref.read('word/styles.xml')
    doc_xml = ET.parse(BytesIO(doc_xml_data))
    styles_xml = ET.parse(BytesIO(styles_xml_data))
    return doc_xml, styles_xml

def get_styles(styles_xml):
    styles = {}
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    for style in styles_xml.findall('.//w:style', namespaces=ns):
        style_id = style.get(f'{{{ns["w"]}}}styleId')
        style_name = style.find('.//w:name', namespaces=ns).get(f'{{{ns["w"]}}}val')
        styles[style_id] = style_name
    return styles