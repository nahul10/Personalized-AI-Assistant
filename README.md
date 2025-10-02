# Personalized-AI-Assistant
A personalized AI assistant that allows you to upload documents, ask questions, generate SQL queries, translate text, and more. Built with FastAPI backend and React frontend.

## Features

- Document ingestion (PDF, DOCX, TXT)
- RAG (Retrieval-Augmented Generation) for Q&A
- SQL query generation and execution
- Text translation
- File and history management
- Web interface for easy interaction

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Git
- A Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
- Poppler for PDF processing (download from [poppler releases](https://blog.alivate.com.au/poppler-windows/))
- Tesseract OCR (download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki))

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd personal_coach
   ```

2. Set up Python virtual environment:
   ```bash
   python -m venv first_venv
   first_venv\Scripts\activate  # On Windows
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Node.js dependencies for the web app:
   ```bash
   cd web
   npm install
   cd ..
   ```

## Setup

1. Create a `.env` file in the root directory with the following variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   POPLER_PATH=C:\path\to\poppler\bin
   TESSERACT_PATH=C:\path\to\tesseract.exe
   ```

   - Replace `your_gemini_api_key_here` with your actual Gemini API key.
   - Update the paths to match your Poppler and Tesseract installations.

2. Initialize the database:
   ```bash
   python scripts/init_db.py
   ```

3. (Optional) If you want to use a different database, run:
   ```bash
   python scripts/init_mydb.py
   ```

## Running the Application

1. Start the backend server:
   ```bash
   uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
   ```

2. In a new terminal, start the web app:
   ```bash
   cd web
   npm run dev
   ```

3. Open your browser and go to `http://localhost:5173` (or the URL shown by Vite).

## API Endpoints

The backend provides the following endpoints:

- `GET /health` - Health check
- `POST /upload` - Upload and index a file
- `POST /ask` - Ask a question with RAG
- `POST /sql/generate` - Generate SQL from natural language
- `POST /sql/run` - Execute SQL query
- `POST /translate` - Translate text
- `POST /reset_index` - Reset the index
- `GET /files` - List uploaded files
- `GET /history` - Get Q&A history

## Usage

1. Upload documents through the web interface or API.
2. Ask questions about the uploaded content.
3. Use the SQL generator to query the database.
4. Translate text to different languages.
5. View your Q&A history and uploaded files.

## Troubleshooting

- If you encounter issues with PDF processing, ensure Poppler is correctly installed and the path is set in `.env`.
- For OCR issues, verify Tesseract installation and path.
- Make sure your Gemini API key is valid and has sufficient quota.
- If the web app doesn't load, check that the backend is running on port 8000.

## Development

- Backend: FastAPI with SQLAlchemy
- Frontend: React with Vite, Tailwind CSS
- Database: SQLite
- AI: Google Gemini

## License

[Add your license here]
