import re
import requests
from tqdm import tqdm

def input_table_columns():
    """
    Let the user input only the table column names.
    return: columns (list of str)
    """
    columns = []
    try:
        col_n = int(input("Enter the number of columns: "))
        for j in range(col_n):
            col_name = input(f"Enter the name of column {j+1}: ")
            columns.append(col_name)
    except ValueError:
        print("Please enter a number. No column names were entered.")
    return columns

def check_with_llm(lines, context_lines=None, model = "llama3.1:8b"): 
    """
    判斷這幾行是否還屬於表格內容，可參考前5行上下文。
    return: True (yes) or False (no)
    """
    prompt = 'You are a professional table analyst. Your goal is to determine whether the following content belongs to a table. Please answer only yes or no.\n'
    if context_lines:
        prompt += '【First 5 lines of context】\n' + '\n'.join(context_lines) + '\n'
    prompt += '【Content to be judged】\n' + '\n'.join(lines)
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        answer = result.get("response", "").strip().lower()
        result_bool = answer.startswith('y')
        return result_bool
    except Exception as e:
        print(f"[錯誤] LLM 請求失敗: {e}")
        return False # 若 LLM 失敗，預設不繼續

def extract_tables_by_page(txt_path, columns, model="llama3.1:8b"):
    """
    以每個 --- page_x.png --- 為分段，尋找同時包含所有 columns 的段落，
    並從 columns 名稱那一行開始，遇到第一個空白行就停止。
    """
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 分割每個 page
    pages = re.split(r'(?=--- page_\d+\.png ---)', content)
    matched_tables = []
    debug_lines = []
    no_list = []
    for page in tqdm(pages, desc="Processing pages"):
        lines = page.splitlines()
        col_line_idx = None
        for idx, line in enumerate(lines):
            if all(col in line for col in columns):
                col_line_idx = idx
                break
        # 取得表格起始行的前五行作為 context
        context_lines = lines[col_line_idx:col_line_idx+5] if col_line_idx is not None else []
        if col_line_idx is not None:
            # 移除頁尾雜訊：從最後一行往回判斷，直到 LLM+人工確認為表格內容
            tail_idx = len(lines) - 1
            while tail_idx > col_line_idx:
                tail_line = lines[tail_idx]
                if tail_line in no_list:
                    tail_idx -= 1
                    continue
                # 使用 LLM 判斷
                llm_result = check_with_llm([tail_line], context_lines=context_lines, model=model)
                debug_lines.append(f"[tail_check]:\n{tail_line}")
                debug_lines.append(f"[LLM 判斷結果]: {llm_result}")
                debug_lines.append(f"[目前 context_lines]:\n{chr(10).join(context_lines)}")
                # 人工覆蓋
                user_fb = input(f"LLM 判斷尾行: {tail_line} => {'yes' if llm_result else 'no'}, y(表格)/n(雜訊)/Enter(接受LLM): ").strip().lower()
                if user_fb == 'y':
                    llm_result = True
                elif user_fb == 'n':
                    llm_result = False
                if llm_result:
                    break  # 找到最後表格行，停止移除
                else:
                    no_list.append(tail_line)
                    tail_idx -= 1
            # 擷取從起始行到 tail_idx 的內容
            table_block = lines[col_line_idx:tail_idx+1]
            matched_tables.append('\n'.join(table_block))
            continue  # 下一頁
    # 輸出 debug 訊息
    with open('/root/textocr/Image_pdf/text/debug_llm.txt', 'w', encoding='utf-8') as dbg:
        dbg.write('\n\n'.join(debug_lines))
    return matched_tables

if __name__ == "__main__":
    columns = input_table_columns()
    txt_path = "/root/textocr/Image_pdf/text/transcript.txt"
    model = "llama3.1:8b"
    matched = extract_tables_by_page(txt_path, columns, model=model)
    output_path = "/root/textocr/Image_pdf/text/selected_tables.txt"
    with open(output_path, 'w', encoding='utf-8') as out_f:
        for table in matched:
            # 移除 --- Table N --- 標記，只寫入純表格內容
            out_f.write(f"{table}\n")
    print(f"output to {output_path}")



# prompt = (
#     "你是一個表格內容判斷專家。請依下列步驟操作：\n"
#     "Step 1: 你必須詳讀前五行的內容，並詳細說明你如何判斷這行內容是否屬於表格內容或雜訊。\n"
#     "Step 2: 最後只回答 yes 或 no，不要加其他說明。\n"
#     "內容如下：\n"
#     + '\n'.join(lines)
# )