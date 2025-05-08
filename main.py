from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
from typing import List, Dict, Any, Optional
import random
from pathlib import Path
import os
from pydantic import BaseModel
import uvicorn

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DB_PATH = Path(os.path.dirname(os.path.dirname(BASE_DIR))) / "pte_vocabulary.db"

# Create FastAPI app
app = FastAPI(title="PTE Vocabulary Viewer")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# Get categories with counts
def get_categories_with_counts():
    conn = get_db_connection()
    categories = conn.execute('''
        SELECT c.id, c.name, c.display_name, COUNT(q.id) as question_count
        FROM categories c
        LEFT JOIN questions q ON c.id = q.category_id
        GROUP BY c.id
        ORDER BY c.display_name
    ''').fetchall()
    conn.close()
    return categories

# Home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    categories = get_categories_with_counts()
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "categories": categories,
            "total_questions": sum(cat["question_count"] for cat in categories),
            "num_categories": len(categories)
        }
    )

# All questions route (with optional category filtering)
@app.get("/questions", response_class=HTMLResponse)
async def questions(request: Request, category_id: Optional[int] = None):
    conn = get_db_connection()
    
    # Get all categories for the navigation
    categories = conn.execute(
        "SELECT id, name, display_name FROM categories ORDER BY display_name"
    ).fetchall()
    
    # Fetch questions based on category filter
    if category_id:
        # Get category name
        category = conn.execute(
            "SELECT id, name, display_name FROM categories WHERE id = ?",
            (category_id,)
        ).fetchone()
        
        if not category:
            conn.close()
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Get questions for this category
        questions = conn.execute('''
            SELECT q.*, c.display_name as category_name
            FROM questions q
            JOIN categories c ON q.category_id = c.id
            WHERE q.category_id = ?
            ORDER BY q.original_question_number
        ''', (category_id,)).fetchall()
        
        conn.close()
        
        # Return category-specific template
        return templates.TemplateResponse(
            "category_questions.html",
            {
                "request": request,
                "questions": questions,
                "category_name": category["display_name"],
                "current_category_id": category_id,
                "categories": categories,
                "total_questions": len(questions)
            }
        )
    else:
        # Get all questions grouped by category
        questions_by_category = {}
        
        for category in categories:
            cat_questions = conn.execute('''
                SELECT * FROM questions
                WHERE category_id = ?
                ORDER BY original_question_number
                LIMIT 10
            ''', (category["id"],)).fetchall()
            
            if cat_questions:
                questions_by_category[category["display_name"]] = cat_questions
        
        conn.close()
        
        return templates.TemplateResponse(
            "questions.html",
            {
                "request": request,
                "questions_by_category": questions_by_category,
                "categories": categories,
                "total_questions": sum(len(qs) for qs in questions_by_category.values()),
                "num_categories": len(categories)
            }
        )

# Start exam
@app.get("/exam/start", response_class=HTMLResponse)
async def start_exam(
    request: Request, 
    category_id: int,
    num_questions: int = 10
):
    conn = get_db_connection()
    
    # Get category information
    category = conn.execute(
        "SELECT id, name, display_name FROM categories WHERE id = ?",
        (category_id,)
    ).fetchone()
    
    if not category:
        conn.close()
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get random questions for this category
    questions = conn.execute('''
        SELECT * FROM questions
        WHERE category_id = ?
        ORDER BY RANDOM()
        LIMIT ?
    ''', (category_id, num_questions)).fetchall()
    
    conn.close()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this category")
    
    return templates.TemplateResponse(
        "exam.html", 
        {
            "request": request,
            "questions": questions,
            "category_name": category["display_name"],
            "category_id": category_id,
            "total_questions": len(questions)
        }
    )

# Exam results
@app.post("/exam/results", response_class=HTMLResponse)
async def exam_results(
    request: Request,
    category_id: int = Form(...),
    question_ids: List[int] = Form(...)
):
    conn = get_db_connection()
    
    # Get category information
    category = conn.execute(
        "SELECT id, name, display_name FROM categories WHERE id = ?", 
        (category_id,)
    ).fetchone()
    
    if not category:
        conn.close()
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Process results
    questions_data = []
    correct_count = 0
    
    # Get form data
    form_data = await request.form()
    
    for q_id in question_ids:
        # Get the question details
        question = conn.execute(
            "SELECT * FROM questions WHERE id = ?", 
            (q_id,)
        ).fetchone()
        
        if question:
            # Get user's answer
            answer_key = f"answer_{q_id}"
            user_answer = form_data.get(answer_key, "")
            
            # Check if correct
            is_correct = user_answer == question["correct_answer"]
            if is_correct:
                correct_count += 1
            
            # Add to results
            q_dict = dict(question)
            q_dict["user_answer"] = user_answer
            q_dict["is_correct"] = is_correct
            questions_data.append(q_dict)
    
    conn.close()
    
    # Calculate score percentage
    total_questions = len(questions_data)
    score_percent = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "questions": questions_data,
            "category_name": category["display_name"],
            "correct_count": correct_count,
            "total_questions": total_questions,
            "score_percent": score_percent
        }
    )

# Flashcards route
@app.get("/flashcards", response_class=HTMLResponse)
async def flashcards(request: Request, category_id: Optional[int] = None):
    conn = get_db_connection()
    
    # Get all categories
    categories = conn.execute(
        "SELECT id, name, display_name FROM categories ORDER BY display_name"
    ).fetchall()
    
    # Query flashcards
    if category_id:
        # Get specific category flashcards
        category = conn.execute(
            "SELECT id, name, display_name FROM categories WHERE id = ?",
            (category_id,)
        ).fetchone()
        
        if not category:
            conn.close()
            raise HTTPException(status_code=404, detail="Category not found")
        
        flashcards = conn.execute('''
            SELECT * FROM flashcards
            WHERE category_id = ?
            ORDER BY RANDOM()
            LIMIT 50
        ''', (category_id,)).fetchall()
        
        conn.close()
        
        return templates.TemplateResponse(
            "category_flashcards.html",
            {
                "request": request,
                "flashcards": flashcards,
                "category_name": category["display_name"],
                "categories": categories,
                "current_category_id": category_id
            }
        )
    else:
        # Get a sample of flashcards from each category
        flashcards_by_category = {}
        
        for category in categories:
            cat_flashcards = conn.execute('''
                SELECT * FROM flashcards
                WHERE category_id = ?
                ORDER BY RANDOM()
                LIMIT 5
            ''', (category["id"],)).fetchall()
            
            if cat_flashcards:
                flashcards_by_category[category["display_name"]] = cat_flashcards
        
        conn.close()
        
        return templates.TemplateResponse(
            "flashcards.html",
            {
                "request": request,
                "flashcards_by_category": flashcards_by_category,
                "categories": categories
            }
        )

# Study mode
@app.get("/study", response_class=HTMLResponse)
async def study_mode(request: Request, category_id: Optional[int] = None):
    conn = get_db_connection()
    
    # Get all categories
    categories = conn.execute(
        "SELECT id, name, display_name FROM categories ORDER BY display_name"
    ).fetchall()
    
    if category_id:
        # Get category details
        category = conn.execute(
            "SELECT id, name, display_name FROM categories WHERE id = ?",
            (category_id,)
        ).fetchone()
        
        if not category:
            conn.close()
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Get all questions for this category
        questions = conn.execute('''
            SELECT * FROM questions
            WHERE category_id = ?
            ORDER BY original_question_number
        ''', (category_id,)).fetchall()
        
        conn.close()
        
        return templates.TemplateResponse(
            "study_mode.html",
            {
                "request": request,
                "questions": questions,
                "category_name": category["display_name"],
                "categories": categories,
                "current_category_id": category_id
            }
        )
    else:
        # Show study dashboard with category options
        conn.close()
        return templates.TemplateResponse(
            "study_dashboard.html",
            {
                "request": request,
                "categories": categories
            }
        )

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
