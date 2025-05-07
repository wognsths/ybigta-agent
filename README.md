# ybigta-agent

Repository for building **remote agents**.

## Directory Structure

Each agent lives in its own folder:

```text
{agent_name}_agent/
├── __init__.py
├── __main__.py
├── agent.py
├── tools.py
├── task_manager.py
└── README.md
```

추가적인 헬퍼 모듈(예: 공통 Pydantic 모델 등)은 편의를 위해 동일 폴더 내에 자유롭게 배치해도 됩니다.

### Required Files

* **README.md**  —  템플릿 규칙은 없지만, 에이전트의 역할과 사용 방법을 명확하게 정리해 주세요.

## Example Usage

### Excel Agent

The Excel Agent transforms data and generates Excel files based on templates:

```python
import pandas as pd
import requests
import json
import base64
import pickle

# Create sample DataFrame
df = pd.DataFrame({
    "date": ["2025-04-14", "2025-04-15", "2025-04-16"],
    "category": ["A", "B", "A"],
    "value": [100, 150, 120],
    "quantity": [10, 15, 12],
})

# Pickle and encode DataFrame
pickled_df = pickle.dumps(df)
b64_df = base64.b64encode(pickled_df).decode('utf-8')

# Prepare request payload
payload = {
    "df": b64_df,
    "context": {
        "template": "가",
        "date_range": "2025-04-14/16",
        "date_column": "date",
        "pivot_column": "category",
        "value_column": "value"
    }
}

# Send request to Excel Agent API
response = requests.post(
    "http://localhost:8000/excel",
    json=payload,
    headers={"Content-Type": "application/json"}
)

# Save the Excel file
if response.status_code == 200:
    with open("report.xlsx", "wb") as f:
        f.write(response.content)
    print("Excel file saved successfully!")
else:
    print(f"Error: {response.text}")
```

## Reference Repositories

### A2A

* [https://github.com/ai-boost/awesome-a2a](https://github.com/ai-boost/awesome-a2a)
* [https://github.com/google/A2A](https://github.com/google/A2A)

### Excel Agents

* [https://github.com/jenyss/ExcelWorkerLLMToolCallAgent](https://github.com/jenyss/ExcelWorkerLLMToolCallAgent)
* [https://github.com/jenyss/ExcelWorkerReActAgent](https://github.com/jenyss/ExcelWorkerReActAgent)
* [https://github.com/inoueakimitsu/ExcelAgentTemplate](https://github.com/inoueakimitsu/ExcelAgentTemplate)

### Report Agents

* [https://github.com/Pranjalya/llm-agent-pdf-reader](https://github.com/Pranjalya/llm-agent-pdf-reader)
* [https://github.com/pyr0mind/AI-powered-PDF-agent-project](https://github.com/pyr0mind/AI-powered-PDF-agent-project)
* [https://github.com/svanirudh1809/ReportGenerator](https://github.com/svanirudh1809/ReportGenerator)

### Email Agents

* [https://github.com/parthshr370/Email-AI-Agent](https://github.com/parthshr370/Email-AI-Agent)
* [https://github.com/Tonyloyt/Email-Automation-with-python](https://github.com/Tonyloyt/Email-Automation-with-python)
* https://github.com/Shy2593666979/mcp-server-email

### Database Agents

* [https://github.com/connor-john/ai-db-agent](https://github.com/connor-john/ai-db-agent)
* [https://github.com/jorgeandrespadilla/sql-agent](https://github.com/jorgeandrespadilla/sql-agent)
* [https://github.com/svanirudh1809/ReportGenerator](https://github.com/svanirudh1809/ReportGenerator)
