import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Access the variables
gemini_key = os.getenv("GEMINI_API_KEY")
poppler_path = os.getenv("POPLER_PATH")
tesseract_path = os.getenv("TESSERACT_PATH")

print("Gemini Key:", gemini_key[:10] + "..." if gemini_key else "Not found")
print("Poppler Path:", poppler_path if poppler_path else "Not found")
print("Tesseract Path:", tesseract_path if tesseract_path else "Not found")
