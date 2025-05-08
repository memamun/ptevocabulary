# PTE Vocabulary Question Viewer

A clean and responsive FastAPI application to display PTE vocabulary questions from a SQLite database, with category-based filtering and exam functionality.

## Features

- **Homepage with Category Selection**: Easily browse all available vocabulary categories
- **Category-based Filtering**: View questions from specific categories
- **Exam Mode**: Take exams with a customizable number of questions per category
- **Exam Results**: Detailed feedback with scoring and explanations
- **Clean UI**: Responsive design with Tailwind CSS
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Prerequisites

- Python 3.8+ (if running locally without Docker)
- Docker and Docker Compose (if running with Docker)

## Running Locally

### Option 1: With Python

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Make sure `pte_vocabulary.db` is in the project directory

3. Run the application:
   ```
   uvicorn app:app --reload
   ```

4. Open your browser and go to [http://localhost:8000](http://localhost:8000)

### Option 2: With Docker

1. Make sure Docker and Docker Compose are installed

2. On Windows: Run the provided batch file:
   ```
   docker-start.bat
   ```
   
   On Linux/Mac: Run the shell script:
   ```
   chmod +x run.sh
   ./run.sh
   ```

3. Open your browser and go to [http://localhost:8000](http://localhost:8000)

## Using the Application

1. **Browse Questions**:
   - The homepage displays all available categories
   - Click "View Questions" to see all questions in a category
   - Use the category tabs to switch between categories

2. **Take an Exam**:
   - From the homepage, select a category and click on one of the question count options (10, 20, or 50)
   - Answer all questions and submit to see your results
   - Review your answers, see explanations, and try again if desired

## Deploying to Railway

1. Create a new project on [Railway](https://railway.app/)

2. Connect your GitHub repository

3. The deployment configuration is already set up in `railway.toml`

4. Make sure your `pte_vocabulary.db` file is included in the repository

5. Deploy!

## Project Structure

```
pte_viewer/
├── app.py                 # FastAPI application
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── pte_vocabulary.db      # SQLite database with questions
├── requirements.txt       # Python dependencies
├── railway.toml           # Railway deployment configuration
├── run.sh                 # Linux/Mac startup script
├── run.bat                # Windows startup script
├── docker-start.bat       # Docker-specific Windows startup
├── static/                # Static files
│   └── style.css          # Custom CSS styles
└── templates/             # Jinja2 templates
    ├── index.html         # Homepage with category selection
    ├── questions.html     # All questions view
    ├── category_questions.html # Single category view
    ├── exam.html          # Exam taking page
    ├── results.html       # Exam results page
    └── error.html         # Error page
```

## License

This project is for educational purposes only. # ptevocabulary
