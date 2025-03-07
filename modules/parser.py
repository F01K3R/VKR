import os
from docx import Document as DocxDocument
from pdfminer.high_level import extract_text
from odf.opendocument import load as load_odt


class DocumentParser:
    def parse(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.docx':
            return DocxDocument(file_path)
        elif ext == '.pdf':
            return extract_text(file_path)
        elif ext == '.odt':
            return load_odt(file_path)
        else:
            raise ValueError("Unsupported file format")