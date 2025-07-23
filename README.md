# OCR_work

本專案為 OCR（光學字元辨識）與表格資料擷取工具，支援 PDF 轉圖片、圖片轉文字、以及從文字檔中選取表格資料。

## 目錄結構

- `main.py`：主程式，整合各模組流程。
- `pdf_to_image.py`：將 PDF 轉換為圖片。
- `image_to_text.py`：將圖片轉換為純文字。
- `selected.py`：根據欄位名稱從文字檔中擷取表格資料。
- `txt_to_csv.py`：將文字檔轉換為 CSV 格式。
- `desktop.ini`：Windows 系統檔案（可忽略）。

## 各模組功能說明

### pdf_to_image.py
- `pdf_to_images(pdf_path, output_dir)`: 將指定 PDF 檔案的每一頁轉換為圖片，並儲存到指定資料夾。

### image_to_text.py
- 主要使用 pytesseract (Tesseract-OCR) 進行圖片的文字辨識。
- `images_to_text(image_dir, output_txt)`: 將指定資料夾內的所有圖片進行 OCR 辨識，並將辨識結果輸出為純文字檔。
- 本專案 OCR 辨識主要使用 [pytesseract](https://github.com/madmaze/pytesseract)（Python 封裝）與 [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract)（Google 開源引擎）。
- 請確認已安裝 Tesseract-OCR 並設定好環境變數。

### selected.py
- 利用大型語言模型（LLM）協助根據使用者輸入的欄位名稱，自動從 OCR 文字檔中選擇並擷取對應的表格資料。
- `extract_tables_by_page(output_txt, columns, model)`: 傳入文字檔、欄位名稱與 LLM 模型名稱，自動比對並擷取相關表格。
- `input_table_columns()`: 互動式讓使用者輸入欲擷取的表格欄位名稱。

### txt_to_csv.py
- 將 OCR 或表格擷取後的純文字檔，依照指定格式轉換為 CSV 檔案，方便後續資料分析與處理。
- 本模組利用多階段 LLM 協作自動完成 txt 轉 csv，流程如下：
    1. **表格結構偵測**：LLM 讀取 txt 樣本，自動判斷欄位數、欄位名稱與分割規則，並產生 JSON schema、分割範例與英文說明。
    2. **Prompt 工程**：LLM 根據 schema 與範例，自動產生給 Python 工程師的詳細轉換需求（prompt），明確規範分割規則、欄位對應、邊界情境等。
    3. **Python 生成**：LLM 依據 prompt 自動產生 Python 轉檔程式碼，確保完全符合欄位結構與資料格式。
    4. **自動審查**：LLM 以 reviewer 身份檢查程式碼正確性，若有問題會回饋並要求重寫，直到審查通過才執行轉檔。
- 這種方法可大幅減少人工分析與撰寫程式的負擔，並確保轉換結果正確。

## 執行環境

- Python 3.7+
- 需安裝相關套件（如 `pytesseract`, `pdf2image` 等）

## 安裝套件範例

```sh
pip install pytesseract pdf2image pillow
```