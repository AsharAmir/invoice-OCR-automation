import os
import pytesseract
from PIL import Image
import openpyxl
from openpyxl import Workbook
import google.generativeai as genai
import json

# Configure Google Generative AI
genai.configure(api_key="AIzaSyCUgMjF9_HMgu18O5nyhj1zAsnJLrAoxmg")

# Create the model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

def perform_ocr(image_path):
    """Load and perform OCR on the invoice image."""
    invoice_image = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(invoice_image)
    return extracted_text

def parse_invoice_with_genai(extracted_text):
    """Use Google Generative AI to extract invoice details in JSON format."""
    prompt = (
        f"Extract the following information from the text: Supplier Name, Invoice Number, Invoice Date, "
        f"Item Name, Package Weight, Quantity (also known as bill qty), Rate, GST, Sales Amount. Format the extracted "
        f"information in JSON format (no need for anything else, JUST GIVE THE OUTPUT A JSON OUTPUT NOTHING ELSE "
        f"NOT EVEN FORMATTED IN BACKTICKS, JUST RAW JSON) also for the entries with null, just ignore them in the output.\n\n{extracted_text}\n\n"
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)
    return response.text

def save_to_excel(parsed_data, output_excel_path):
    """Save parsed invoice data to a new Excel file."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Invoice Data"

    # Extract headers from the keys of the first item in the parsed data
    headers = list(parsed_data.keys())
    sheet.append(headers)

    # Append the values as a new row in the Excel sheet
    row = [parsed_data.get(header, "") for header in headers]
    sheet.append(row)

    # Save the new workbook
    workbook.save(output_excel_path)
    print(f"Data saved to {output_excel_path}")

def main():
    image_path = "1.png"  # Path to your image file
    output_excel_path = "output_invoice_data.xlsx"  # Path to the output Excel file

    # Perform OCR
    extracted_text = perform_ocr(image_path)
    
    # Parse extracted text using Google Generative AI
    parsed_data = parse_invoice_with_genai(extracted_text)
    
    # Debug: Print the raw response
    print("Raw Response from Google Generative AI:", parsed_data)
    
    # Load parsed data as JSON
    try:
        parsed_data_json = json.loads(parsed_data)
        print("Parsed JSON Data:", parsed_data_json)  # Debug: Print the parsed JSON
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return
    
    # Save parsed data to new Excel file
    save_to_excel(parsed_data_json, output_excel_path)

if __name__ == "__main__":
    main()
