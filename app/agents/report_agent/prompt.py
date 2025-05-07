from typing import Dict, List

class ReportPrompt:
    def __init__(self):
        self.system_prompt = """당신은 전문적인 보고서 생성 에이전트입니다. 
사용자의 요청을 분석하고 적절한 형식의 보고서를 생성하는 것이 당신의 역할입니다.
다음과 같은 작업을 수행할 수 있습니다:
1. 자연어 질문을 분석하여 보고서 형식 결정
2. 데이터 구조화 및 정리
3. 적절한 템플릿 선택
4. 보고서 생성 및 포맷팅"""

        self.report_analysis_prompt = """다음 질문을 분석하여 적절한 보고서 형식을 결정해주세요:
질문: {query}

다음 형식으로 응답해주세요:
{
    "report_type": "분석/요약/비교 등",
    "template_type": "basic/advanced 등",
    "required_sections": ["섹션1", "섹션2", ...],
    "data_requirements": ["필요한 데이터1", "필요한 데이터2", ...]
}"""

        self.data_processing_prompt = """다음 데이터를 보고서 형식에 맞게 처리해주세요:
데이터: {data}

다음 형식으로 응답해주세요:
{
    "title": "보고서 제목",
    "description": "보고서 설명",
    "sections": [
        {
            "title": "섹션 제목",
            "content": "섹션 내용",
            "data": {...}
        },
        ...
    ]
}"""

    def get_system_prompt(self) -> str:
        return self.system_prompt

    def get_report_analysis_prompt(self, query: str) -> str:
        return self.report_analysis_prompt.format(query=query)

    def get_data_processing_prompt(self, data: Dict) -> str:
        return self.data_processing_prompt.format(data=data)

    def format_report_request(self, analysis_result: Dict, processed_data: Dict) -> Dict:
        """분석 결과와 처리된 데이터를 보고서 요청 형식으로 변환"""
        return {
            "query": analysis_result.get("report_type", ""),
            "data": {
                "title": processed_data.get("title", ""),
                "description": processed_data.get("description", ""),
                "sections": processed_data.get("sections", []),
                "generated_at": processed_data.get("generated_at", "")
            },
            "template_type": analysis_result.get("template_type", "basic"),
            "output_format": "pdf"
        } 