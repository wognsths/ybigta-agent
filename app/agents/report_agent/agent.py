from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
from utils.pdf_generator import PDFGenerator
from utils.template_loader import TemplateLoader
from prompt import ReportPrompt

app = FastAPI()

class ReportRequest(BaseModel):
    query: str
    data: Dict
    template_type: str = "basic"
    output_format: str = "pdf"

class ReportAgent:
    def __init__(self):
        self.pdf_generator = PDFGenerator()
        self.template_loader = TemplateLoader()
        self.prompt = ReportPrompt()
        
    async def generate_report(self, request: ReportRequest) -> Dict:
        try:
            # 1. 질문 분석
            analysis_result = self._analyze_query(request.query)
            
            # 2. 데이터 처리
            processed_data = self._process_data(request.data)
            
            # 3. 보고서 요청 형식으로 변환
            report_request = self.prompt.format_report_request(analysis_result, processed_data)
            
            # 4. 템플릿 선택
            template = self.template_loader.get_template(report_request["template_type"])
            
            # 5. PDF 생성
            pdf_path = self.pdf_generator.generate(
                template=template,
                data=report_request["data"],
                output_format=report_request["output_format"]
            )
            
            return {
                "status": "success",
                "file_path": pdf_path,
                "message": "Report generated successfully"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    def _analyze_query(self, query: str) -> Dict:
        # 실제 구현에서는 LLM을 사용하여 질문 분석
        # 현재는 간단한 예시 응답 반환
        return {
            "report_type": "분석",
            "template_type": "basic",
            "required_sections": ["개요", "분석", "결론"],
            "data_requirements": ["기본 데이터"]
        }
    
    def _process_data(self, data: Dict) -> Dict:
        # 데이터 전처리 로직
        return data

@app.post("/generate-report")
async def generate_report(request: ReportRequest):
    agent = ReportAgent()
    return await agent.generate_report(request) 