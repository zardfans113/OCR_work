from image_to_text import images_to_text
from pdf_to_image import pdf_to_images
from selected import extract_tables_by_page, input_table_columns

def main():
    # pdf_path = ""
    # output_dir = "/root/textocr/Image_pdf/Images"
    # pdf_to_images(pdf_path, output_dir)
    # image_dir = "/root/textocr/Image_pdf/Images"
    output_txt = "/root/textocr/Image_pdf/text/transcript.txt"
    # images_to_text(image_dir, output_txt)
    # 多次表格選取
    idx = 1
    while True:
        print(f"\n第{idx}次表格選取，請輸入欄位名稱（直接 Enter 結束）")
        columns = input_table_columns()
        if not columns:
            print("已結束所有表格選取。")
            break
        model = "llama3.1:8b"
        matched = extract_tables_by_page(output_txt, columns, model=model)
        output_table_path = f"/root/textocr/Image_pdf/text/selected_tables_{idx}.txt"
        with open(output_table_path, 'w', encoding='utf-8') as out_f:
            for table in matched:
                out_f.write(f"{table}\n")
        print(f"output to {output_table_path}")
        idx += 1

if __name__ == "__main__":
    main()