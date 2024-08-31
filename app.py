import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import openpyxl
import json
import google.generativeai as genai
from PIL import Image, ImageEnhance, ImageFilter
import openai

# Flask app configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PROCESSED_FOLDER'] = 'processed/'
app.config['OUTPUT_FOLDER'] = 'output/'
app.config['SECRET_KEY'] = 'your_secret_key'

# Configure Google Generative AI
genai.configure(api_key="AIzaSyCUgMjF9_HMgu18O5nyhj1zAsnJLrAoxmg")

# Ensure folders exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'], app.config['OUTPUT_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

def preprocess_image(image):
    """
    Preprocess the image to enhance OCR accuracy.
    
    Args:
    - image (PIL.Image.Image): The original image to preprocess.
    
    Returns:
    - PIL.Image.Image: The preprocessed image.
    """
    # Convert image to grayscale
    image = image.convert('L')
    
    # Apply image enhancements
    image = ImageEnhance.Contrast(image).enhance(2.0)  # Increase contrast
    image = ImageEnhance.Sharpness(image).enhance(2.0)  # Increase sharpness
    
    # Apply a filter to reduce noise
    image = image.filter(ImageFilter.MedianFilter(size=3))
    
    return image

def perform_ocr(image_path):
    """Load and perform OCR on the invoice image with enhanced settings for tables."""
    
    # Open the image file
    invoice_image = Image.open(image_path)
    
    # Preprocess the image for better OCR accuracy
    processed_image = preprocess_image(invoice_image)
    
    # Custom configuration for Tesseract to enhance table recognition
    custom_config = r'--psm 6 --oem 1 -c preserve_interword_spaces=1'
    
    # Apply OCR with the custom configuration
    extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
    
    # Print the extracted text (for debugging purposes)
    print(extracted_text)
    
    # Return the extracted text
    return extracted_text



    # prompt = (
    #     "Follow the below JSON format for the output. This format MUST be followed at all costs:\n"
    #     "{\n"
    #     "  \"Supplier Name\": \"Supplier Name\",\n"
    #     "  \"Invoice Number\": \"Invoice Number\",\n"
    #     "  \"items\": [\n"
    #     "    {\n"
    #     "      \"Description\": \"Item Name\",\n"
    #     "      \"Quantity\": \"Quantity\",\n"
    #     "      \"Rate\": \"Rate\",\n"
    #     "      \"GST\": \"GST\",\n"
    #     "      \"Sales Amount\": \"Sales Amount\"\n"
    #     "    }\n"
    #     "  ]\n"
    #     "}\n\n"
    #     "Extract the following information from the text:\n"
    #     "Supplier Name (usually appears in the first lines of the invoice, and is likely a standalone company name, not to be confused with sender or receiver names),\n"
    #     "Invoice Number (labelled as Bill No. / Invoice No / but NOT the TAX NUMBER / GSTIN/UIN etc.),\n"
    #     "Package Weight (in kg, if mentioned),\n"
    #     "Quantity (look for Bill Qty / Qty / Pc / STR / BOX / nos / kgs / g etc., based on the column position patterns below),\n"
    #     "Rate (calculated from the total invoice amount divided by quantity),\n"
    #     "GST (sum of CGST and SGST rates if both are mentioned, or the GST rate if only that is provided),\n"
    #     "Sales Amount (Net amount or similar, BUT NOT THE TAXABLE AMOUNT).\n\n"
    #     "Use the following steps to extract the data:\n\n"
    #     "1. **Identify the number of columns in the invoice**:\n"
    #     "   - Each line in the invoice represents a row.\n"
    #     "   - Columns are separated by spaces, but the description may contain spaces within a single column (consider them one column).\n"
    #     "   - Consider the product description as a single column (ending in brackets or parentheses).\n"
    #     "   - Accurately determine the number of columns for each line by identifying the structure.\n\n"
    #     "2. **Apply the appropriate rules based on the number of columns**:\n"
    #         "if there are 16 columns, then quantity is in the 6th column!"
    #     "For entries with null values, ignore them in the output. Provide a RAW JSON OUTPUT, NOT EVEN BACKTICKS. The supplier name and invoice number would be the header. The item would contain the rest.\n\n"
    #     f"{extracted_text}\n\n"
    # )




# Utility function to parse invoice using Google Generative AI
# def parse_invoice_with_genai(extracted_text):
#     """Use Google Generative AI to extract invoice details in JSON format."""
#     prompt = (
#     f"Follow the below json format for the output. This format MUST be followed at all costs:\n"
#     f"{{\n"
#     f"  \"Supplier Name\": \"Supplier Name\",\n"
#     f"  \"Invoice Number\": \"Invoice Number\",\n"
#     f"  \"items\": [\n"
#     f"    {{\n"
#     f"      \"Description\": \"Item Name\",\n"
#     f"      \"Quantity\": \"Quantity\",\n"
#     f"      \"Rate\": \"Rate\",\n"
#     f"      \"GST\": \"GST\",\n"
#     f"      \"Sales Amount\": \"Sales Amount\"\n"
#     f"    }}\n"
#     f"  ]\n"
#     f"Extract the following information from the text; Supplier Name (use your sense to find it, it'd be a standalone company name dont confuse it with sender, receiver name), "
#     f"Invoice Number (Bill No. / Invoice No / (NOT THE TAX NUMBER / GSTIN/UIN etc)), Package Weight (in kg), Quantity (Bill Qty / Qty/ Total Pcs/ Tot Pcs/ EA, could also be listed as STR, BOX, nos etc), "
#     f"Rate (calculated from total invoice amount divided by quantity), GST (maybe mentioned as GST rate, or calculated by CSST rate + SGST rate, we need the rate, not the amount so it'll be a whole number and will be the same throughout the invoice for all items, just need the sum of the both not each of them twice), Sales Amount (Net amount etc), "
#     f"pls note that these are the only needed headers and nothing more. Format this info in JSON format. "
#     f"If there are multiple items in the invoice, provide an array of objects, each representing a single item with its details. "
#     "Ensure that:\n"
#     "- The Invoice Number is extracted correctly even if it is in a tabular format or is not the most prominent number. It should not be confused with other numbers like those in tables or addresses.\n"
#     f"For entries with null values, ignore them in the output. Also just give a RAW JSON OUTPUT, NOT EVEN BACKTICKS. The supplier name and invoice number would be the header. and the item would contain the rest \n\n{extracted_text}\n\n"
#     )

#     model = genai.GenerativeModel(model_name="gemini-1.5-flash")
#     chat_session = model.start_chat(history=[])
#     response = chat_session.send_message(prompt)
#     response_text = response.text

#     # Log the response for debugging
#     print("API Response:", response_text)

#     # Clean up the response if necessary
#     response_text = response_text.strip()

#     if not response_text:
#         raise ValueError("Empty response received from API")

#     try:
#         # Ensure the data is in list format for items
#         data = json.loads(response_text)
#         if isinstance(data, dict):
#             items = data.get("items", [])
#             other_info = {k: v for k, v in data.items() if k != "items"}
#             return {"other_info": other_info, "items": items}
#         else:
#             raise ValueError("Invalid JSON format: Expected a dictionary")
#     except json.JSONDecodeError as e:
#         print("Error decoding JSON:", e)
#         raise


# openai.api_key = "sk-vuKI5Wd0tPW-kKOEWFwfzkv5ORE2rNFG2_Douou8sNT3BlbkFJg_x4khcW-TA1pqHdBCZnFbWD9Bs2LjIG75C0XxHQ8A"
openai.api_key = "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"

def parse_invoice_with_genai(extracted_text):
    """Use OpenAI to extract invoice details in JSON format."""
    prompt = (
        "Follow the JSON format below for the output. This format MUST be strictly followed:\n"
        "{\n"
        "  \"Supplier Name\": \"Supplier Name\",\n"
        "  \"Invoice Number\": \"Invoice Number\",\n"
        "  \"items\": [\n"
        "    {\n"
        "      \"Description\": \"Item Name\",\n"
        "      \"Quantity\": \"Quantity\",\n"
        "      \"Rate\": \"Rate\",\n"
        "      \"GST\": \"GST\",\n"
        "      \"Sales Amount\": \"Sales Amount\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Extract the following information from the text:\n"
        "- Supplier Name: This should be a standalone company name and should not be confused with sender or receiver names.\n"
        "- Invoice Number: This could be labeled as Bill No., Invoice No., etc. (NOT the tax number, GSTIN/UIN, etc.).\n"
        "- Quantity: (would never exist in the product description) This could be labeled as Bill Qty, Qty, EA, Total Pcs. , Tot Pcs, EA, (str, nos, box) etc., If quantity is written in a hyphenated format like 0-1 STR, consider the second number (1). Quantity can also be identified as EA.\n"
        "- Rate: This is calculated from the total invoice amount divided by the quantity.\n"
        "- GST: This could be labeled as GST rate or calculated by adding CSST rate + SGST rate. We need the rate as a whole number, not the amount. It will be the same throughout the invoice for all items, just the sum of both (not each of them twice).\n"
        "- Sales Amount: This could be labeled as Net amount, etc. Not to be calculateed, but rather to be picked from the data.\n\n"
        "Please note:\n"
        "- These are the only needed headers; do not include anything else.\n"
        "- Do not generate any commas, or anything that will cause error when parsing the json decoding\n"
        "- If there are multiple items in the invoice, provide an array of objects, each representing a single item with its details.\n"
        "- The Invoice Number must be correctly extracted even if it is in a tabular format or not the most prominent number. It should not be confused with other numbers in tables or addresses.\n"
        "- For entries with null values, ignore them in the output.\n"
        "- Lastly, since the raw text is OCR fetched, there sometimes might be issues in fetching the quantity field especially, so in that case, you are to calculate quantity from the sales amount divided by the rate (the quantity will always ofc be a lowerbound whole number).\n"
        "- Provide a RAW JSON OUTPUT, with no backticks or formatting. The supplier name and invoice number should be the headers, and the items should contain the rest.\n\n"
        f"{extracted_text}\n\n"
    )
    # prompt = (
    # f"Follow the below json format for the output. This format MUST be followed at all costs:\n"
    # f"{{\n"
    # f"  \"Supplier Name\": \"Supplier Name\",\n"
    # f"  \"Invoice Number\": \"Invoice Number\",\n"
    # f"  \"items\": [\n"
    # f"    {{\n"
    # f"      \"Description\": \"Item Name\",\n"
    # f"      \"Quantity\": \"Quantity\",\n"
    # f"      \"Rate\": \"Rate\",\n"
    # f"      \"GST\": \"GST\",\n"
    # f"      \"Sales Amount\": \"Sales Amount\"\n"
    # f"    }}\n"
    # f"  ]\n"
    # f"Extract the following information from the text; Supplier Name (use your sense to find it, it'd be a standalone company name dont confuse it with sender, receiver name), "
    # f"Invoice Number (Bill No. / Invoice No / (NOT THE TAX NUMBER / GSTIN/UIN etc)), Package Weight (in kg), Quantity (Bill Qty / Qty/ Total Pcs/ Tot Pcs/ EA, could also be listed as STR, BOX, nos etc (quantity wont exist in the product name, would always be a integer no decimals (use this clue to identify quantity easily, wont be immediately next to the product name either))), "
    # f"Rate (calculated from total invoice amount divided by quantity), GST (maybe mentioned as GST rate, or calculated by CSST rate + SGST rate, we need the rate, not the amount so it'll be a whole number and will be the same throughout the invoice for all items, just need the sum of the both not each of them twice), Sales Amount (Net amount etc), "
    # f"pls note that these are the only needed headers and nothing more. Format this info in JSON format. "
    # f"If there are multiple items in the invoice, provide an array of objects, each representing a single item with its details. "
    # "Ensure that:\n"
    # "- The Invoice Number is extracted correctly even if it is in a tabular format or is not the most prominent number. It should not be confused with other numbers like those in tables or addresses.\n"
    # f"For entries with null values, ignore them in the output. Also just give a RAW JSON OUTPUT, NOT EVEN BACKTICKS. The supplier name and invoice number would be the header. and the item would contain the rest \n\n{extracted_text}\n\n"
    # )


    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response['choices'][0]['message']['content'].strip()

    # Log the response for debugging
    print("API Response:", response_text)

    response_text = response_text.replace("\\", "\\\\")

    if not response_text:
        raise ValueError("Empty response received from API")

    try:
        # Ensure the data is in list format for items
        data = json.loads(response_text)
        if isinstance(data, dict):
            items = data.get("items", [])
            other_info = {k: v for k, v in data.items() if k != "items"}
            return {"other_info": other_info, "items": items}
        else:
            raise ValueError("Invalid JSON format: Expected a dictionary")
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)
        raise



# Utility function to save parsed data to Excel
def save_to_excel(parsed_data_list, output_excel_path):
    """Save parsed invoice data to a new Excel file."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Invoice Data"

    # Extract headers from the keys of the first item in the parsed data
    if parsed_data_list:
        headers = list(parsed_data_list[0].keys())
        sheet.append(headers)

        # Append each item as a new row in the Excel sheet
        for item in parsed_data_list:
            row = [item.get(header, "") for header in headers]
            sheet.append(row)

    # Save the new workbook
    workbook.save(output_excel_path)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('files[]')
        processed_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Perform OCR and parse the invoice
                extracted_text = perform_ocr(filepath)
                parsed_data = parse_invoice_with_genai(extracted_text)

                # Save the parsed data for review
                processed_file = {
                    'filename': filename,
                    'data': parsed_data
                }
                processed_files.append(processed_file)
        
        return render_template('review.html', processed_files=processed_files)
    
    return render_template('index.html')

@app.route('/accept', methods=['POST'])
def accept():
    parsed_data_list = request.form['parsed_data']
    try:
        parsed_data_json = json.loads(parsed_data_list)
    except json.JSONDecodeError as e:
        flash(f"Error decoding JSON data: {e}", 'danger')
        return redirect(url_for('index'))
    
    # Save parsed data to Excel
    output_excel_path = os.path.join(app.config['OUTPUT_FOLDER'], 'output_invoice_data.xlsx')
    save_to_excel(parsed_data_json, output_excel_path)
    
    return send_file(output_excel_path, as_attachment=True)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    app.run(debug=True)