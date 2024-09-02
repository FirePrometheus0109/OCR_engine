import boto3
import json
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize the Textract client
textract_client = boto3.client("textract")

# Function to analyze a single page document
def analyze_document(page_bytes):
    response = textract_client.analyze_document(
        Document={"Bytes": page_bytes}, FeatureTypes=['TABLES', 'FORMS']
    )
    return response

# Function to process a single page and analyze it
def process_page(page, page_number):
    writer = PdfWriter()
    writer.add_page(page)

    # Write the single page to a bytes object
    page_bytes_io = BytesIO()
    writer.write(page_bytes_io)
    page_bytes_io.seek(0)

    # Analyze the single page
    return analyze_document(page_bytes_io.read())

# Function to process the entire PDF using parallel processing
def process_pdf(file_path):
    reader = PdfReader(file_path)
    num_pages = len(reader.pages)

    responses = []
    with ThreadPoolExecutor() as executor:
        # Submit all page processing tasks
        futures = {executor.submit(process_page, reader.pages[i], i): i for i in range(num_pages)}

        # Collect results as they complete
        for future in as_completed(futures):
            try:
                page_response = future.result()
                responses.append(page_response)
            except Exception as e:
                print(f"Error processing page {futures[future]}: {e}")

    return responses

# Main function to process the document
def main():
    input_pdf_path = "input.pdf"

    # Process the PDF and get responses for each page
    responses = process_pdf(input_pdf_path)

    # Write the results to a JSON file
    with open("response.json", "w") as output_file:
        json.dump(responses, output_file)

if __name__ == "__main__":
    main()