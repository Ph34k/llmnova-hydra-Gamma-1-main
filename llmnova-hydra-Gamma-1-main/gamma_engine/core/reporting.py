from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório Gamma', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

def generate_report_pdf(data: dict) -> bytes:
    """
    Gera um relatório em PDF a partir dos dados fornecidos.
    """
    pdf = PDF()
    pdf.add_page()

    # Título e Data
    pdf.chapter_title(f"Relatório da Sessão: {data.get('session_id', 'N/A')}")
    pdf.chapter_body(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Conteúdo do Relatório
    pdf.chapter_title("Resultado da Análise")
    content = data.get('content', 'Nenhum conteúdo fornecido.')
    pdf.chapter_body(content)

    # Retorna o PDF como bytes
    return pdf.output(dest='S').encode('latin-1')

