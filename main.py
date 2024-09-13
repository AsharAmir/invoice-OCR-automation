from PIL import Image
import pytesseract
import cv2
import numpy as np

def preprocess_image(image):
    """Preprocess the image to enhance table extraction accuracy."""
    # Convert to grayscale
    gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    
    # Apply thresholding to create a binary image
    _, binary_image = cv2.threshold(blurred_image, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Detect and remove horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    horizontal_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        cv2.drawContours(binary_image, [contour], -1, (0, 0, 0), 3)
    
    # Detect and remove vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    vertical_lines = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        cv2.drawContours(binary_image, [contour], -1, (0, 0, 0), 3)
    
    return binary_image

def perform_ocr(image_path):
    """Perform OCR on a preprocessed image of an invoice."""
    try:
        invoice_image = Image.open(image_path)
        processed_image = preprocess_image(invoice_image)
        processed_image_pil = Image.fromarray(processed_image)
        
        custom_config = r'--psm 6 --oem 3 -c preserve_interword_spaces=1'
        extracted_text = pytesseract.image_to_string(processed_image_pil, config=custom_config)
        
        print("Extracted Text:", extracted_text)
        return extracted_text
    
    except Exception as e:
        print(f"Error during OCR processing: {e}")
        return ""



perform_ocr("C:/Users/ashaa/Downloads/source invoices/IMG_20240808_0008-1.jpg")