from weasyprint import HTML
import os
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate(self, template: str, data: dict, output_format: str = "pdf") -> str:
        # HTML 렌더링
        html_content = template.render(**data)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.{output_format}"
        output_path = os.path.join(self.output_dir, filename)
        
        if output_format == "pdf":
            # PDF 생성
            HTML(string=html_content).write_pdf(output_path)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        return output_path 