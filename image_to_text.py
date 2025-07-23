from PIL import Image
import pytesseract
import os
from tqdm import tqdm

def images_to_text(image_dir, output_txt, lang="chi_tra+eng"):
    # 依檔名中的數字排序，確保由頁數小到大
    def extract_num(filename):
        import re
        match = re.search(r'\d+', filename)
        return int(match.group()) if match else 0
    image_files = sorted(
        [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
        key=extract_num
    )
    all_text = []
    for img_file in tqdm(image_files, desc="Processing images"):
        img_path = os.path.join(image_dir, img_file)
        text = pytesseract.image_to_string(Image.open(img_path), lang=lang, config='--psm 6')
        all_text.append(f"--- {img_file} ---\n{text.rstrip()}\n")
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(''.join(all_text))
    print(f"All OCR results have been saved to: {output_txt}")

if __name__ == "__main__":
    image_dir = "/root/textocr/Image_pdf/Images"
    output_txt = "/root/textocr/Image_pdf/text/transcript.txt"
    images_to_text(image_dir, output_txt)


# def enhance_image(img):
#     """Use OpenCV to process the image to improve OCR performance"""
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#     thresh = cv2.adaptiveThreshold(
#         gray, 255,
#         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY,
#         blockSize=11, C=2
#     )

#     resized = cv2.resize(thresh, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

#     return resized

# def images_to_text(image_dir, output_txt, lang="chi_tra+eng"):
#     """
#     Perform OCR on all images in the folder in order and merge the results into a single text file.
#     """
#     image_files = sorted([f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
#     all_text = []
#     for img_file in tqdm(image_files, desc="Processing images"):
#         img_path = os.path.join(image_dir, img_file)
#         img = cv2.imread(img_path)
#         enhanced_img = enhance_image(img)
#         pil_img = Image.fromarray(enhanced_img)
#         text = pytesseract.image_to_string(pil_img, lang=lang, config='--psm 6')
#         all_text.append(f"--- {img_file} ---\n{text.strip()}\n")
#     with open(output_txt, 'w', encoding='utf-8') as f:
#         f.write('\n'.join(all_text))
#     print(f"All OCR results have been saved to: {output_txt}")

# if __name__ == "__main__":
#     image_dir = "/root/textocr/Image_pdf/Images"
#     output_txt = "/root/textocr/Image_pdf/text/transcript.txt"
#     images_to_text(image_dir, output_txt)