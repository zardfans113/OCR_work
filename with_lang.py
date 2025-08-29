import requests
from tqdm import tqdm
import csv
import re  
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_community.llms.ollama import Ollama

# =====================
# 初始化 LLM
# =====================
llm = Ollama(
    base_url="http://localhost:11434",
    model="qwen2.5-coder:14b",
    temperature=0,
    timeout=180
)

# =====================
# Persona 1: Table Structure Analyst
# =====================
def detect_table_structure(txt_path):
    print("[Agent] 讀取樣本...")
    from itertools import islice
    with open(txt_path, 'r', encoding='utf-8') as f:
        sample = '\n'.join([line.strip() for line in islice(f, 15)])
    # Persona 1: Table Structure Analyst
    table_detect_prompt = f"""
You are Persona 1: a table structure analyst. Your output will be used by persona2 (prompt engineer).

RULE: Observe the txt sample and infer the table structure.

Output only a JSON object with the following fields:
- columns: list of column names
- split_rule: description of how to split each line (delimiter, regex, etc.)
- samples: at least 10 CSV example rows (as strings, comma separated, no markdown; include edge cases if possible)
- explanation: concise English explanation of the table structure and splitting rule

If unable to parse, output: {{"error": "Failed to parse"}}
Output only the JSON object, no explanation or markdown.

Sample:\n{sample}
"""
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "qwen2.5-coder:14b",
        "prompt": table_detect_prompt,
        "stream": False,
        "temperature": 0,
    }
    response = requests.post(url, json=data, timeout=180)
    table_structure_and_example = response.json().get("response", "")
    with open("/root/textocr/Image_pdf/text/example.txt", 'w', encoding='utf-8') as f:
        f.write(table_structure_and_example)
    # 嘗試自動擷取 csv 範例並寫入 example.csv
    csv_match = re.findall(r'(?:[A-Za-z0-9_ ]+,)+[A-Za-z0-9_ ]+\n(?:.+\n)+', table_structure_and_example)
    if csv_match:
        csv_example = csv_match[-1].strip()
        with open("/root/textocr/Image_pdf/csv/example.csv", 'w', encoding='utf-8') as f:
            f.write(csv_example)
    return table_structure_and_example

def generate_prompt_for_code_writer(table_structure_and_example, txt_path, csv_path, csv_example_content):
    # Persona 2: Prompt Engineer
    prompt_engineer_prompt = f"""
You are Persona 2: a prompt engineer. Your output will be used by persona3 (Python code engineer).

RULE: Write a clear, detailed prompt for the code writer based on the JSON schema and examples below.

Output format: only text prompt, no code, no markdown, no explanation.
If unable to generate prompt, output: {{ "error": "Failed to generate prompt" }}

The prompt you generate must require the code writer to strictly match the CSV example and handle edge cases as shown.

JSON schema and explanation:
{table_structure_and_example}

CSV Example:
{csv_example_content}
"""
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "qwen2.5-coder:14b",
        "prompt": prompt_engineer_prompt,
        "stream": False,
        "temperature": 0,
    }
    response = requests.post(url, json=data, timeout=180)
    prompt_for_code_writer = response.json().get("response", "")
    with open("/root/textocr/Image_pdf/text/example.txt", 'w', encoding='utf-8') as f:
        f.write("__prompt_for_code_writer__\n")
        f.write("\n")
        f.write(prompt_for_code_writer)
    return prompt_for_code_writer

def extract_python_code_block(llm_output: str):
    code_blocks = re.findall(r"```(?:python)?(.*?)```", llm_output, re.DOTALL)
    return code_blocks[0].strip() if code_blocks else llm_output.strip()

# =====================
# Persona 3/4: Memory-enabled LLMChain
# =====================
memory = ConversationBufferMemory(memory_key="history")
persona3_prompt = PromptTemplate(
    input_variables=["input", "history"],
    template="""
You are Persona 3: a Python code engineer. Your code will be executed and reviewed by persona4 (code reviewer).

RULES:
- Write Python code to convert the content of txt_path to a CSV and save it to csv_path, strictly following the prompt provided by persona2 and the CSV example below.
- Function name MUST be convert_txt_to_csv(txt_path, csv_path). Do not use any other name. Do not include example usage or main block.
- Output MUST match the CSV example exactly in format, delimiter, column order, whitespace, punctuation, and line endings. The output CSV must be byte-for-byte identical to the provided example.
- If you are unsure, always follow the example exactly.
- If you encounter data or edge cases not covered by the example, output it as-is without modification or deletion.
- Output format: only Python code block, no explanation, no markdown.
- If unable to generate correct code, output: {{ "error": "Failed to generate code" }}
- The code will be reviewed by persona4 for strict correctness.

Here is the previous feedback and your code history:
{history}

{input}
"""
)
persona3_chain = LLMChain(llm=llm, prompt=persona3_prompt, memory=memory)
persona4_prompt = PromptTemplate(
    input_variables=["input", "history"],
    template="""
You are Persona 4: a code reviewer. Your review will be given to persona3 (code engineer).

RULES:
- Review the Python code generated by Persona 3 using the provided JSON schema, CSV examples, and English explanation of the table structure and splitting rules.
- The code output MUST match the CSV example exactly in format, delimiter, column order, whitespace, punctuation, and line endings. You MUST compare the actual output of the code (by running it with txt_path and csv_path) line-by-line and character-by-character with the provided CSV example. If any line, field, or character in the output CSV is different from the example, reply with a detailed error and do not accept.
- Do NOT accept any output that does not strictly follow the example format.
- Do NOT infer, guess, or invent any rule or format not present in the example.
- If you encounter data or edge cases not covered by the example, the code should output it as-is without modification or deletion.
- Output format: only text review, no code, no markdown.
- If the code is correct and the output CSV is exactly the same as the example, reply exactly: OK
- If the code is incorrect, reply with a detailed review explaining all issues, and instruct Persona 3 to rewrite the code according to your review and the JSON schema, CSV examples, and English explanation.

Here is the previous feedback and code history:
{history}

{input}
"""
)
persona4_chain = LLMChain(llm=llm, prompt=persona4_prompt, memory=memory)

# 設定 memory 不帶 input_key，讓其自動推斷（預設 'input'），但 persona3_prompt input_variables 改回 'prompt_for_code_writer'，run 時也傳 prompt_for_code_writer=pfw_full
def persona3_4_pipeline(prompt_for_code_writer, table_structure_and_example, csv_example_content, txt_path, csv_path):
    review_comment = ""
    iteration = 0
    log_path = "/root/textocr/Image_pdf/text/log.txt"
    # 讀取 input txt 範例（前 10 行）
    with open(txt_path, 'r', encoding='utf-8') as f:
        txt_example_lines = [line.rstrip('\n') for _, line in zip(range(10), f)]
    txt_example_content = '\n'.join(txt_example_lines)
    with open(log_path, 'w', encoding='utf-8') as log:
        while True:
            iteration += 1
            print(f"[Persona3] 第 {iteration} 次嘗試生成程式碼...")
            pfw_full = prompt_for_code_writer + review_comment + "\n\nCSV Example:\n" + csv_example_content
            code_str_clean = persona3_chain.run(
                input=pfw_full
            )
            code_str_clean = extract_python_code_block(code_str_clean)
            # 強制檢查 output 是否為 Python function，且 signature 至少有 txt_path, csv_path
            if not re.search(r'def\s+\w+\s*\(\s*txt_path\s*,\s*csv_path', code_str_clean):
                print("[Pipeline] Persona3 輸出非正確 Python function，要求重寫...")
                log.write(f"\n----- Persona3 Code (Iter {iteration}) -----\n{code_str_clean}\n")
                review_comment = "\n\n[Pipeline feedback]: Your output was not a valid Python function that takes txt_path and csv_path as arguments. Please output only a Python function (no markdown, no explanation) that takes txt_path and csv_path as parameters and writes the correct CSV."
                continue
            log.write(f"\n----- Persona3 Code (Iter {iteration}) -----\n{code_str_clean}\n")
            print(f"[Pipeline] 執行 code 並比對 output...")
            # pipeline 先執行 code 並比對 output 與 example，產生 diff
            try:
                exec(code_str_clean, globals())
                if 'convert_txt_to_csv' in globals():
                    convert_txt_to_csv(txt_path, csv_path)
                print("[Pipeline] Output 格式正確，進入 Persona4 review...")
                persona4_input = f"""Review the following code:\n{code_str_clean}\n\nThe expected CSV output format is:\n{csv_example_content}\n\nJSON schema and explanation:\n{table_structure_and_example}\n\nPipeline diff between example and output: (no diff, files are identical)"""
                review_result = persona4_chain.run(
                    input=persona4_input
                ).strip()
                log.write(f"\n----- Persona4 Review (Iter {iteration}) -----\n{review_result}\n")
                if review_result == "OK":
                    print("[Pipeline] 程式碼審核通過，執行程式...")
                    print("[Pipeline] 程式碼執行成功 ✅")
                    break
                else:
                    print("[Pipeline] Persona4 回報問題，重新生成程式碼")
                    review_comment = f"\n\nPersona4 feedback:\n{review_result}"
                continue
            except Exception as e:
                review_comment = f"\n\n[Pipeline feedback]: Exception occurred when running your code: {str(e)}. Please fix the code."
                continue
            # # output 完全一致才進入 Persona4 review
            # persona4_input = f"""Review the following code:\n{code_str_clean}\n\nThe expected CSV output format is:\n{csv_example_content}\n\nJSON schema and explanation:\n{table_structure_and_example}\n\nPipeline diff between example and output: (no diff, files are identical)"""
            # review_result = persona4_chain.run(
            #     input=persona4_input
            # ).strip()
            # log.write(f"\n----- Persona4 Review (Iter {iteration}) -----\n{review_result}\n")
            # if review_result == "OK":
            #     print("[Pipeline] 程式碼審核通過，執行程式...")
            #     print("[Pipeline] 程式碼執行成功 ✅")
            #     break
            # else:
            #     print("[Pipeline] Persona4 回報問題，重新生成程式碼")
            #     review_comment = f"\n\nPersona4 feedback:\n{review_result}"

def main(txt_path, csv_path):
    import sys
    import re
    log_path = '/root/textocr/Image_pdf/text/log.txt'
    with open(log_path, 'w', encoding='utf-8') as log:
        table_structure_and_example = detect_table_structure(txt_path)
        with open("/root/textocr/Image_pdf/csv/example.csv", "r+", encoding="utf-8") as f:
            csv_example_content = f.read()
        log.write("----- LLM 生成的表格結構和範例 -----\n\n")
        log.write(table_structure_and_example + "\n")
        prompt_for_code_writer = generate_prompt_for_code_writer(table_structure_and_example, txt_path, csv_path, csv_example_content)
        persona3_4_pipeline(prompt_for_code_writer, table_structure_and_example, csv_example_content, txt_path, csv_path)

if __name__ == "__main__":
    txt_path = "/root/textocr/Image_pdf/text/selected_tables_1.txt"
    csv_path = "/root/textocr/Image_pdf/csv/selected_tables_1.csv"
    main(txt_path, csv_path)
