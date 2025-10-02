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

2. Set up Python virtual environment (if not already present):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
=======
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
   npm install
   npm run dev
   ```

3. Open your browser and go to `http://localhost:5173` (or the URL shown by Vite).

<<<<<<< HEAD
## Pushing to GitHub

If you want to push this project to a new GitHub repository:

1. Initialize Git (if not already done):
   ```bash
   git init
   ```

2. Add all files:
   ```bash
   git add .
   ```

3. Commit the changes:
   ```bash
   git commit -m "Initial commit: Personal AI Coach project"
   ```

4. Create a new repository on GitHub (via web interface).

5. Add the remote origin:
   ```bash
   git remote add origin https://github.com/your-username/your-repo-name.git
   ```

6. Push to GitHub:
   ```bash
   git push -u origin main
   ```

   Replace `your-username` and `your-repo-name` with your actual GitHub username and repository name.

=======
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

## FFmpeg Setup Instructions

This project requires FFmpeg for media processing. Follow these steps to download and set up FFmpeg:

1. Download FFmpeg:
   - Go to the official FFmpeg website: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html).
   - Select the appropriate build for your operating system:
     - **Windows**: Download the latest static build from [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
     - **macOS**: Use Homebrew (`brew install ffmpeg`).
     - **Linux**: Install via your package manager (e.g., `sudo apt install ffmpeg`).

2. Extract the FFmpeg Archive:
   - Extract the downloaded `.zip` or `.tar.gz` file to a directory of your choice (e.g., `C:\ffmpeg` on Windows).

3. Add FFmpeg to the System PATH:
   - Windows:
     1. Open the Start Menu and search for "Environment Variables."
     2. Click "Edit the system environment variables."
     3. In the "System Properties" window, click "Environment Variables."
     4. Under "System variables," find the `Path` variable and click "Edit."
     5. Click "New" and add the path to the `bin` folder inside the extracted FFmpeg directory (e.g., `C:\ffmpeg\bin`).
     6. Click "OK" to save the changes.
   - macOS/Linux:
     - Add the following line to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.):
       ```bash
       export PATH="/path/to/ffmpeg/bin:$PATH"
       ```
     - Replace `/path/to/ffmpeg/bin` with the actual path to the `bin` folder inside the extracted FFmpeg directory.
     - Run `source ~/.bashrc` or `source ~/.zshrc` to apply the changes.

4. Verify the Installation:
   - Open a terminal or command prompt and run:
     ```bash
     ffmpeg -version
     ```
   - You should see the FFmpeg version information if it is installed correctly.

5. Update the [.env](http://_vscodecontentref_/2) File:
   - Add the path to the FFmpeg `bin` folder in the [.env](http://_vscodecontentref_/3) file:
     ```plaintext
     FFMPEG_PATH=C:\ffmpeg\bin
     ```

---

### Step 2: Update the [.env](http://_vscodecontentref_/4) File
Ensure the [.env](http://_vscodecontentref_/5) file includes the `FFMPEG_PATH` variable:
FFMPEG_PATH=C:\ffmpeg\bin

### Step 3: Modify the Code to Use FFMPEG_PATH
If your code explicitly references FFmpeg, update it to use the FFMPEG_PATH variable from the .env file. For example:
```
import os
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")  # Default to "ffmpeg" if not set

# Example usage
command = f"{FFMPEG_PATH} -i input.mp4 output.mp4"
os.system(command) 

```

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

## MIT License

Copyright (c) 2025 nahul10

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
