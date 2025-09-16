# OCR work

## **Background explanation**

### **Why this tool**

1. 手寫的表格以及 scanned 的 PDF (Image-based PDF) 無法直接透過 
ctrl + A， ctrl + C， ctrl + V，或者是寫個簡單的小程式就可以轉成欲轉換的格式。
2.  當表格內容過多時，一個一個複製耗時費力。
3. 市面上沒有類似解決這個問題的工具
### **Capabilities and Features**

透過 OCR 轉為可用文字，並可選取**所需表格**來轉換格式

### **What does “OCR” means**

OCR stands for "Optical Character Recognition." It is a technology that recognizes text within a digital image. It is commonly used to recognize text in scanned documents and images.
## **Overview:**

**PDF → Image → text → selected content → auto coding → csv**
### PDF → Image

使用python 的 package(套件) — **pdf2image**，其功能為**將 PDF 每一頁轉換成 image 格式(**此為PNG)
<img width="668" height="279" alt="image" src="https://github.com/user-attachments/assets/ea6e477b-497d-488c-b770-8f1b1e0c20ac" />
### Image → text

使用python 的 package(套件) — **pytesseract**，是主要OCR的部分。

- **先概述一下 Pytesseract**
    
    Pytesseract is a Python library that functions as a wrapper for Google's Tesseract-OCR Engine. Its primary purpose is to facilitate Optical Character Recognition (OCR) within Python applications, enabling the extraction of text from images and documents.
  <img width="921" height="442" alt="image" src="https://github.com/user-attachments/assets/bc4d0200-9529-4801-8567-c1275cd517df" />
**Explanation**:

使用 Tesseract OCR 引擎對每張圖片進行文字辨識，並將所有圖片的辨識結果整合成一個 .txt 輸出。
最後文字將以 UTF-8 編碼寫入指定的輸出文字檔中。

### Select table

這裡要求 user 輸入column 數以及每個 column 的名稱，例:3(enter) A(enter) B(enter) C (enter)

接著 code 會以所輸入的column names 為上界，再由頁尾開始往上刪除，直到 user input “y”

這裡 LLM 的角色為”輔助” user 判斷，而不是全部交給 LLM 判斷，原因如下:
LLM 其實不清楚”表格內容”是什麼，判斷的基準是”隨機性”的。
如果 fine-tune LLM，可能會讓 LLM ”只按照” 範例來挑選他認為的內容，可能會刪掉重要資訊且保留雜訊。所以這裡使用最穩健的方式保證表格內容不會遺失。

### 針對 table 來撰寫 code 的 agent

**overview**: 使用 **muti-agent & persona** 的概念，加上langchain 管理 pipeline，
讓 LLM 分別扮演四個 persona
 ”table structure analyst ”、”prompt engineer”、” python engineer” and
 “code reviwer” 等角色，各司其職，最後生成一個.csv

遵守以下結構:
明確 persona 身份
指定對象（給誰用）
規則簡明、無重複
結構化輸出（JSON，欄位明確）
範例明確
最重要的 task 放最後

**LLM**
**Persona 1 - *Table Structure Analyst***: Analyzes the table and produces a schema and examples.

**Persona 2 - *Prompt Engineer***: Creates the prompt for the Python Engineer to develop code.

**Persona 3 - *Python Engineer***: Writes Python code based on the prompt, schema, and examples provided.

**Persona 4 - *Code Reviewer***: Reviews the Python code.
If correct → executes code → outputs CSV
If incorrect → provides code feedback and requests Persona 3 to revise the code.

**Langchain**

本系統透過 **LangChain** 管理 persona 的 prompt 、memory、串接多輪任務流程（LLMChain），使整個 txt→CSV 轉換流程自動化且具可維護性。
<img width="1609" height="435" alt="image" src="https://github.com/user-attachments/assets/3b4ebac5-a975-403e-b6d8-f9ac70a94637" />

## Future work

**方向** :

1. 提高 OCR 的品質
2. select table 的完全自動化 + 可以使用”選取範圍”的方式選擇所需表格內容(而不是讓 user input(有點像是在電腦截圖的時候圈選的方式)
3. 轉.csv的成功率，這裡指的成功率是指可以正確轉換成”使用者想像結果”的成功率
4. 支援其他格式的轉換，像是 .json、**.**xlsx….。
