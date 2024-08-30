import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import openpyxl
import json
import google.generativeai as genai

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

# Utility function to perform OCR and extract text from images
def perform_ocr(image_path):
    """Load and perform OCR on the invoice image."""
    invoice_image = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(invoice_image)
    print(extracted_text)
    return extracted_text

# Utility function to parse invoice using Google Generative AI
def parse_invoice_with_genai(extracted_text):
    """Use Google Generative AI to extract invoice details in JSON format."""
    prompt = (
    f"Follow the below json format for the output. This format MUST be followed at all costs:\n"
    f"{{\n"
    f"  \"Supplier Name\": \"Supplier Name\",\n"
    f"  \"Invoice Number\": \"Invoice Number\",\n"
    f"  \"items\": [\n"
    f"    {{\n"
    f"      \"Description\": \"Item Name\",\n"
    f"      \"Quantity\": \"Quantity\",\n"
    f"      \"Rate\": \"Rate\",\n"
    f"      \"GST\": \"GST\",\n"
    f"      \"Sales Amount\": \"Sales Amount\"\n"
    f"    }}\n"
    f"  ]\n"
    f"Extract the following information from the text; Supplier Name (use your sense to find it, it'd be a standalone company name dont confuse it with sender, receiver name), "
    f"Invoice Number (Bill No. / Invoice No / (NOT THE TAX NUMBER / GSTIN/UIN etc)), Package Weight (in kg), Quantity (Bill Qty / Qty, could also be listed as STR, BOX, nos etc), "
    f"Rate (calculated from total invoice amount divided by quantity), GST (maybe mentioned as GST rate, or calculated by CSST rate + SGST rate, we need the rate, not the amount so it'll be a whole number and will be the same throughout the invoice for all items, just need the sum of the both not each of them twice), Sales Amount (Net amount etc), "
    f"pls note that these are the only needed headers and nothing more. Format this info in JSON format. "
    f"If there are multiple items in the invoice, provide an array of objects, each representing a single item with its details. "
    "Ensure that:\n"
    "- The Invoice Number is extracted correctly even if it is in a tabular format or is not the most prominent number. It should not be confused with other numbers like those in tables or addresses.\n"
    f"For entries with null values, ignore them in the output. Also just give a RAW JSON OUTPUT, NOT EVEN BACKTICKS. The supplier name and invoice number would be the header. and the item would contain the rest \n\n{extracted_text}\n\n"
    )
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)
    response_text = response.text

    # Log the response for debugging
    print("API Response:", response_text)

    # Clean up the response if necessary
    response_text = response_text.strip()

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