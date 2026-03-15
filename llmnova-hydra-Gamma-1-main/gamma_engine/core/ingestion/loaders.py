
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os

class DocumentLoader(ABC):
    @abstractmethod
    def load(self, file_path: str) -> str:
        pass

class TextLoader(DocumentLoader):
    def load(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

class PDFLoader(DocumentLoader):
    def load(self, file_path: str) -> str:
        try:
            import pypdf
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            return "Error: pypdf not installed."

class DocxLoader(DocumentLoader):
    def load(self, file_path: str) -> str:
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            return "Error: python-docx not installed."

class LoaderFactory:
    @staticmethod
    def get_loader(file_path: str) -> DocumentLoader:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return PDFLoader()
        elif ext in [".docx", ".doc"]:
            return DocxLoader()
        else:
            return TextLoader()
