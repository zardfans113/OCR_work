import requests
from tqdm import tqdm
import csv
import re  
def detect_table_structure(txt_path):
    print("[Agent] 讀取樣本...")
    with open(txt_path, 'r', encoding='utf-8') as f:
        sample = '\n'.join([next(f).strip() for _ in range(15)])
    print("[Agent] 樣本讀取完成，準備組 prompt...")
    # Persona 1: Table Structure Detector
    table_detect_prompt = f"""
You are Persona 1: a professional table structure detector. Carefully observe the following txt sample and infer the table structure. Your output must be a JSON object with:
1. Detect how many columns the table has and the title of each column.
2. Describe how to split the table content into columns (e.g., by delimiter, regex, or other rules).
3. Provide several example rows (as JSON objects) to help the next persona write correct Python code.
Note: Do not delete or modify any content from the original table.
Output only the JSON object, no explanation or markdown.
Then, based on the JSON example's splitting method, provide a txt example separated by commas (,) so persona2 can clearly understand the column splitting rule (no explanation, no markdown).
Finally, give a brief English explanation of the table structure and splitting rule for persona2's reference (no markdown, no extra explanation).
Sample:\n{sample}
"""
    print("[Agent] 呼叫 LLM 進行表格偵測...")
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "qwen2.5-coder:14b",
        "prompt": table_detect_prompt,
        "stream": False
    }
    response = requests.post(url, json=data, timeout=180)
    table_structure_and_example = response.json().get("response", "")
    return table_structure_and_example

def generate_prompt_for_code_writer(table_structure_and_example, txt_path, csv_path):
    # Persona 2: Prompt Engineer
    prompt_engineer_prompt = f"""
You are Persona 2: a prompt engineer. You will receive a JSON schema, a txt example, and an English explanation of the table structure.
Your job is to write a clear, detailed prompt for a Python code writer (persona3), based on all three sources.

Instructions:
- Carefully analyze the JSON schema, txt example, and English explanation together.
- Clearly describe the table structure, column names, and the exact delimiter or splitting rules for each column.
- If the delimiter is a single character (e.g., comma, tab), specify that csv.reader/csv.writer can be used.
- If the delimiter is multiple spaces, variable whitespace, or a regex pattern, specify that re.split or re.match should be used.
- If any column (such as Description) may contain spaces or the delimiter, specify a robust parsing strategy (e.g., use regex to extract the first and last columns, and treat the rest as Description).
- Include the txt example as a reference.
- List any edge cases (such as fields with commas, quotes, newlines, missing or extra columns) that must be handled.
- Require the code writer to preserve all table content, column order, and data format. Do not delete or omit any content.
- Specify that the code must read from {txt_path} and write to {csv_path} using the full variable path, not a hardcoded filename.
- Require the output to be only Python code, no explanations or comments.
- Please describe and explain as detailed and explicit as possible. The more specific, the better.
- Strictly follow the format of the .txt example provided by persona1 when writing code.

Table schema, txt example, and explanation:
{table_structure_and_example}
"""
    print("[Agent] Persona2 產生給 persona3 的 prompt...")
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "qwen2.5-coder:14b",
        "prompt": prompt_engineer_prompt,
        "stream": False
    }
    response = requests.post(url, json=data, timeout=180)
    prompt_for_code_writer = response.json().get("response", "")
    return prompt_for_code_writer

def generate_python_code(prompt_for_code_writer, txt_path, csv_path, table_structure_and_example):
    # Persona 3: Python Engineer
    python_code_prompt = f"""
You are Persona 3: a professional Python engineer.
Please write Python code to convert the content of {txt_path} to a CSV and save it to {csv_path}, strictly following the prompt provided by persona2 below.
Do not attempt to modify, add, skip , or delete any content from {txt_path}.

Persona2's prompt:
{prompt_for_code_writer}
Table schema, txt example, and explanation for your reference:
{table_structure_and_example}
""" + f"""Strictly follow the format of the .txt example provided by persona1 when writing code."""
    print("[Agent] 呼叫 LLM 產生 Python code...")
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "qwen2.5-coder:14b",
        "prompt": python_code_prompt,
        "stream": False
    }
    response = requests.post(url, json=data, timeout=180)
    code = response.json().get("response", "")
    return code

def agent_review_and_validate_code(code_str, txt_path, csv_path, table_structure_and_example):
    review_prompt = f"""
You are Persona 4: a senior Python engineer and code reviewer. Your job is to review the Python code generated by Persona 2, given the JSON schema and examples.

Review steps:
1. Strictly check all details of the code, including logic, format, field names, data completeness, and edge case handling (such as commas, quotes, newlines, and missing/extra columns).
2. If there are any issues, provide concrete, detailed feedback in English for each problem you find. Your feedback should cover code logic, output format, field mapping, data loss, and any potential edge cases. Do not just reply OK or give a simple explanation—be specific and thorough.
3. If the code is correct, reply exactly: OK
4. If the code is incorrect, reply with a detailed review explaining all issues and ask Persona 2 to rewrite the code according to your review and the JSON schema and examples.

Repeat this process until the code is correct.

Python script:
{code_str}

Schema and examples:
{table_structure_and_example}
"""
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "qwen2.5-coder:14b",
        "prompt": review_prompt,
        "stream": False
    }
    response = requests.post(url, json=data, timeout=180)
    review = response.json().get("response", "").strip()
    return review

def main(txt_path, csv_path):
    import sys
    import re
    log_path = '/root/textocr/Image_pdf/log.txt'
    with open(log_path, 'w', encoding='utf-8') as log:
        table_structure_and_example = detect_table_structure(txt_path)
        log.write("----- LLM 生成的表格結構和範例 -----\n\n")
        log.write(table_structure_and_example + "\n")
        review_comment = ""
        prompt_for_code_writer = generate_prompt_for_code_writer(table_structure_and_example, txt_path, csv_path)
        while True:
            code_str = generate_python_code(prompt_for_code_writer, txt_path, csv_path, table_structure_and_example)
            code_blocks = re.findall(r"```python(.*?)```", code_str, re.DOTALL)
            if not code_blocks:
                code_blocks = re.findall(r"```(.*?)```", code_str, re.DOTALL)
            if code_blocks:
                code_str_clean = code_blocks[0].strip()
            else:
                code_str_clean = code_str.strip()
            log.write("----- LLM 生成的 code -----\n\n")
            log.write(code_str_clean + "\n")
            review_result = agent_review_and_validate_code(code_str_clean, txt_path, csv_path, table_structure_and_example)
            log.write("----- Persona3 Review -----\n\n")
            log.write(review_result + "\n")
            if review_result.strip() == "OK":
                exec(code_str_clean)
                break
            else:
                prompt_for_code_writer += f"\n\nPersona3 review: {review_result}"

if __name__ == "__main__":
    txt_path = "/root/textocr/Image_pdf/text/selected_tables_1.txt"
    csv_path = "/root/textocr/Image_pdf/csv/selected_tables_1.csv"
    main(txt_path, csv_path)