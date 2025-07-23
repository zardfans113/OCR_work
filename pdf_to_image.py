from pdf2image import convert_from_path
import os

def pdf_to_images(pdf_path, output_dir):
    """
    Convert each page of the PDF to an image and save to output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    images = convert_from_path(pdf_path)
    for i, img in enumerate(images, 1):
        img_path = os.path.join(output_dir, f"page_{i}.png")
        img.save(img_path, "PNG")
        print(f"Saved: {img_path}")
    print(f"Converted {len(images)} pages to images.")

if __name__ == "__main__":
    pdf_path = ""
    output_dir = "/root/textocr/Image_pdf/Images"
    pdf_to_images(pdf_path, output_dir)