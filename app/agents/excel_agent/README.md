# Excel Agent

## 개요
Excel Agent는 DataFrame과 컨텍스트 정보를 입력으로 받아 Excel 파일(xlsx)과 파일명을 출력하는 기능을 제공합니다. LangGraph 기반 워크플로우로 구현되어 있으며 OpenAI API를 사용합니다.

## 주요 기능
- 5가지 템플릿 유형("가", "나", "다", "라", "마") 지원
- DataFrame을 Excel 형식으로 변환 및 매핑
- 사용자 정의 템플릿 적용

## 시스템 구성
- **LLM**: OpenAI API 사용
- **워크플로우 프레임워크**: LangGraph

## 워크플로우 구조
Host → Excel Agent 라우터 → LangGraph 워크플로우 흐름으로 구성되며, 다음과 같은 노드로 이루어져 있습니다:
1. **InputGateway**: 초기 입력 처리
2. **TemplateSelector**: 적합한 템플릿 유형 선택
3. **TemplateLoader**: 선택된 템플릿 로드
4. **DataPreprocessor**: 데이터 전처리
5. **MapperFiller**: 템플릿에 데이터 매핑
6. **WorkbookWriter**: Excel 워크북 생성
7. **OutputDispatcher**: 최종 Excel 파일 출력

## 주요 도구
- **load_template_wb**: 템플릿 워크북 로드
- **transform_df_for_template**: 템플릿에 맞게 DataFrame 변환
- **map_df_to_workbook**: DataFrame을 워크북에 매핑
- **save_workbook**: 워크북을 파일로 저장

## 테스트 및 문제 해결
- NumPy/Pandas DLL 로드 오류가 발생할 수 있으며, 환경 설정 확인 필요
- 테스트를 위한 간소화된 스크립트 제공
- 환경 설정 문제로 인한 서버 실행 불가 이슈 가능성 존재

## 프로젝트 제약사항
- excel_agent 디렉토리 내부만 수정 가능
- main.py 파일은 수정 불가
- 테스트 파일은 excel_agent 디렉토리 내에 위치 