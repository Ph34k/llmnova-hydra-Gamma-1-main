"""Document Processor Tool for the Gamma Engine.

This module defines the DocumentProcessorTool, which handles the extraction
of text from various document formats (PDF, images) and conversion to Markdown.
It utilizes OCR capabilities for image-based text extraction.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from .base import Tool
from pydantic import BaseModel

# Placeholder for external libraries
try:
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("pypdf not available. PDF text extraction will be limited.")

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract or Pillow not available. Image OCR will be limited.")

logger = logging.getLogger(__name__)

class OCRTool:
    """
    Internal OCR tool used by DocumentProcessor for text extraction from images.
    """
    def recognize(self, image_path: str) -> str:
        """
        Recognizes text from an image file using OCR.
        """
        if not TESSERACT_AVAILABLE:
            return "Error: OCR requires pytesseract and Pillow. Install with: pip install pytesseract Pillow && apt-get install tesseract-ocr"
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            return text
        except Exception as e:
            return f"Error during OCR: {e}"

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text content from a PDF file.
    """
    if not PDF_AVAILABLE:
        return "Error: PDF text extraction requires pypdf. Install with: pip install pypdf"
    try:
        reader = pypdf.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

def extract_text_from_image(file_path: str) -> str:
    """
    Extracts text content from an image file using OCR.
    """
    return OCRTool().recognize(file_path)

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text content from various file types.
    Supports PDF, common image formats (via OCR), and plain text files.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
        return extract_text_from_image(file_path)
    elif file_extension in [".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml"]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading text file {file_path}: {e}"
    else:
        return f"Error: Unsupported file type for text extraction: {file_extension}"

class DocumentProcessorTool(Tool):
    """
    A tool for processing various document formats.
    """

    def __init__(self):
        super().__init__(
            name="document_processor",
            description=(
                "Process various document formats (PDF, images, text) to extract text. "
                "Actions: 'extract_text', 'convert_to_markdown'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["extract_text", "convert_to_markdown"],
                        "description": "The action to perform on the document."
                    },
                    "file_path": {
                        "type": "string",
                        "description": "The path to the document file."
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional: Path to save the converted Markdown file (for 'convert_to_markdown')."
                    }
                },
                "required": ["file_path"]
            }
        )

    def convert_to_markdown(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Converts the text content of a file (PDF or image) to Markdown.
        This is a placeholder and would involve more sophisticated conversion logic.
        """
        text_content = extract_text_from_file(file_path)

        if "Error:" in text_content:
            return text_content # Propagate error from extraction

        markdown_content = f"# Document Content from {file_path}\n\n" + text_content

        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                return f"Converted content saved to: {output_path}"
            except Exception as e:
                return f"Error saving Markdown file: {e}"

        return markdown_content

    def execute(self, file_path: str, action: str = "extract_text", output_path: Optional[str] = None, **kwargs) -> Any:
        """
        Executes the specified document processing action.
        """
        if action == "extract_text":
            return extract_text_from_file(file_path)
        elif action == "convert_to_markdown":
            return self.convert_to_markdown(file_path, output_path)
        else:
            return extract_text_from_file(file_path) # Default
