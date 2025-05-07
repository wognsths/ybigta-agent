"""Minimal Excel test script with only openpyxl."""

import os
import openpyxl
from pathlib import Path

# Create directories
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

print("===== Minimal Excel Test =====")

# Create a simple workbook
wb = openpyxl.Workbook()
sheet = wb.active
sheet.title = "Sheet1"

# Add some data
sheet["A1"] = "Excel Agent Test Report"
sheet["A2"] = "Generated on: 2025-04-14"
sheet["A3"] = "Template: 가"
sheet["A4"] = "Date Range: 2025-04-14/19"

# Add some sample data
sheet["A6"] = "Category"
sheet["B6"] = "Value"
sheet["C6"] = "Percentage"

# Row 1
sheet["A7"] = "A"
sheet["B7"] = 100
sheet["C7"] = "40%"

# Row 2
sheet["A8"] = "B"
sheet["B8"] = 150
sheet["C8"] = "60%"

# Add a chart title
sheet["A10"] = "Total"
sheet["B10"] = "=SUM(B7:B8)"

# Create a second sheet
summary = wb.create_sheet("Summary")
summary["A1"] = "Summary View"
summary["A3"] = "Total Items"
summary["B3"] = 2
summary["A4"] = "Total Value"
summary["B4"] = "=Sheet1!B10"

# Save the file
output_file = output_dir / "excel_agent_test_result.xlsx"
wb.save(output_file)

print(f"Excel file created successfully at: {output_file}")
print("==============================") 