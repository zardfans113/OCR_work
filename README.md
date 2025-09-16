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
