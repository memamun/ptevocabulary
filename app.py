from fastapi import FastAPI, Request, Form, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import random
from typing import Dict, List, Any, Optional

app = FastAPI(title="PTE Vocabulary Viewer")

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pte_vocabulary.db")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_categories_with_counts_optimized() -> List[Dict]:
    """Get all categories from the database with their respective question counts, optimized."""
    conn = get_db_connection()
    categories_with_counts = conn.execute("""
        SELECT c.id, c.name, c.display_name, COUNT(q.id) as question_count
        FROM categories c
        LEFT JOIN questions q ON c.id = q.category_id
        GROUP BY c.id, c.name, c.display_name
        ORDER BY c.display_name  -- Or c.id, depending on desired sort order
    """).fetchall()
    conn.close()
    return [dict(row) for row in categories_with_counts]

def get_categories():
    """Get all categories from the database"""
    conn = get_db_connection()
    categories = conn.execute("SELECT id, name, display_name FROM categories").fetchall()
    conn.close()
    return categories

def get_questions_by_category(category_id: Optional[int] = None) -> List[Dict]:
    """Get questions from the database, optionally filtered by category"""
    conn = get_db_connection()
    
    if category_id:
        # Get questions from a specific category
        questions = conn.execute("""
            SELECT 
                q.id, q.category_id, q.word, q.sentence, q.italicized_word, 
                q.idiomatic_expression, q.question_text, q.option_a, q.option_b,
                q.option_c, q.option_d, q.correct_answer, q.explanation,
                c.display_name as category_name, c.name as category_code
            FROM questions q
            JOIN categories c ON q.category_id = c.id
            WHERE q.category_id = ?
            ORDER BY q.id
        """, (category_id,)).fetchall()
    else:
        # Get all questions
        questions = conn.execute("""
            SELECT 
                q.id, q.category_id, q.word, q.sentence, q.italicized_word, 
                q.idiomatic_expression, q.question_text, q.option_a, q.option_b,
                q.option_c, q.option_d, q.correct_answer, q.explanation,
                c.display_name as category_name, c.name as category_code
            FROM questions q
            JOIN categories c ON q.category_id = c.id
            ORDER BY c.id, q.id
        """).fetchall()
    
    # Convert to list of dicts
    result = [dict(q) for q in questions]
    conn.close()
    return result

def get_questions_by_category_grouped() -> Dict[str, List[Dict]]:
    """Get all questions from the database, grouped by category"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all categories
    categories = cursor.execute("SELECT id, display_name FROM categories").fetchall()
    
    # Get all questions with their category name
    questions = cursor.execute("""
        SELECT 
            q.id, q.category_id, q.word, q.sentence, q.italicized_word, 
            q.idiomatic_expression, q.question_text, q.option_a, q.option_b,
            q.option_c, q.option_d, q.correct_answer, q.explanation,
            c.display_name as category_name, c.name as category_code
        FROM questions q
        JOIN categories c ON q.category_id = c.id
        ORDER BY c.id, q.id
    """).fetchall()
    
    # Group questions by category
    grouped: Dict[str, List[Dict[str, Any]]] = {cat["display_name"]: [] for cat in categories}
    for q in questions:
        question_dict = dict(q)
        grouped[q["category_name"]].append(question_dict)
    
    conn.close()
    return grouped

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page with category selection"""
    categories_with_counts = get_categories_with_counts_optimized()

    total_questions_val = sum(c['question_count'] for c in categories_with_counts)
    num_categories_val = len(categories_with_counts)
    
    # The get_categories() call is for the general layout/navigation if it needs it.
    # If index.html's direct category listing is the only consumer, 
    # we might not need the original 'categories' variable in this specific route's context.
    # For now, let's assume the base template might still use `categories` from get_categories().
    # However, the main content of index.html will be driven by categories_with_counts.
    # Let's check if the original `categories` variable is truly needed for index.html context.
    # Based on current index.html, it seems we can replace it.

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "categories_data": categories_with_counts, # Use this for the main category listing and chart
            "total_questions": total_questions_val,
            "num_categories": num_categories_val,
            "categories": get_categories() # Keep this if base layout used by index.html needs it for nav, otherwise can be removed.
                                          # For safety and assuming a shared base template, let's keep it.
                                          # If index.html is standalone or its base doesn't use it, this can be omitted.
        }
    )

@app.get("/questions", response_class=HTMLResponse)
async def view_questions(
    request: Request, 
    category_id: Optional[int] = Query(None)
):
    """View all questions, optionally filtered by category"""
    categories = get_categories()
    
    if category_id:
        # Get questions for a specific category
        questions = get_questions_by_category(category_id)
        category_name = next((c["display_name"] for c in categories if c["id"] == category_id), "Unknown")
        
        return templates.TemplateResponse(
            "category_questions.html",
            {
                "request": request,
                "questions": questions,
                "category_name": category_name,
                "categories": categories,
                "total_questions": len(questions),
                "current_category_id": category_id
            }
        )
    else:
        # Group questions by category
        questions_by_category = get_questions_by_category_grouped()
        total_questions = sum(len(questions) for questions in questions_by_category.values())
        
        return templates.TemplateResponse(
            "questions.html",
            {
                "request": request, 
                "questions_by_category": questions_by_category,
                "total_questions": total_questions,
                "num_categories": len(questions_by_category),
                "categories": categories
            }
        )

@app.get("/exam/start", response_class=HTMLResponse)
async def start_exam(
    request: Request, 
    category_id: Optional[int] = Query(None), 
    num_questions: int = Query(10)
):
    """Start an exam with a specified number of questions, optionally from a specific category."""
    categories = get_categories()
    all_questions: List[Dict[str, Any]]
    category_name: str
    effective_category_id: int

    if category_id is None:
        # All categories exam
        all_questions = get_questions_by_category(None)
        category_name = "All Categories"
        effective_category_id = 0
    else:
        # Specific category exam
        category_name = next((c["display_name"] for c in categories if c["id"] == category_id), "Unknown Category")
        all_questions = get_questions_by_category(category_id)
        effective_category_id = category_id
    
    # Randomly select questions for the exam
    total_available = len(all_questions)
    num_to_use = min(num_questions, total_available)
    
    if num_to_use < 1:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": f"No questions available in this category",
                "categories": categories
            }
        )
    
    exam_questions = random.sample(all_questions, num_to_use)
    
    return templates.TemplateResponse(
        "exam.html",
        {
            "request": request,
            "questions": exam_questions,
            "category_name": category_name,
            "category_id": effective_category_id,
            "total_questions": num_to_use,
            "categories": categories
        }
    )

@app.post("/exam/results", response_class=HTMLResponse)
async def process_exam_results(
    request: Request,
    category_id: int = Form(...),
    question_ids: List[int] = Form(...)
):
    """Process exam results and show the score"""
    form_data = await request.form()
    categories = get_categories()
    category_name: str

    if category_id == 0:
        category_name = "All Categories"
    else:
        category_name = next((c["display_name"] for c in categories if c["id"] == category_id), "Unknown Category")
    
    # Get all questions that were in the exam
    conn = get_db_connection()
    placeholders = ",".join("?" for _ in question_ids)
    questions = conn.execute(f"""
        SELECT id, correct_answer, option_a, option_b, option_c, option_d, explanation
        FROM questions
        WHERE id IN ({placeholders})
    """, question_ids).fetchall()
    conn.close()
    
    # Calculate score
    questions_data = []
    correct_count = 0
    
    for q in questions:
        q_id = str(q["id"])
        user_answer = form_data.get(f"answer_{q_id}", "")
        is_correct = user_answer == q["correct_answer"]
        
        if is_correct:
            correct_count += 1
        
        questions_data.append({
            "id": q_id,
            "correct_answer": q["correct_answer"],
            "user_answer": user_answer,
            "is_correct": is_correct,
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "option_d": q["option_d"],
            "explanation": q["explanation"]
        })
    
    total_questions = len(questions)
    score_percent = correct_count / total_questions * 100 if total_questions > 0 else 0
    
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "questions": questions_data,
            "category_name": category_name,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "score_percent": score_percent,
            "categories": categories
        }
    )

# Add health check endpoint for monitoring
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/study", response_class=HTMLResponse)
async def study_mode(
    request: Request, 
    category_id: Optional[int] = Query(None)
):
    """Study mode view with answers shown for efficient learning"""
    categories = get_categories()
    
    if category_id:
        # Get questions for a specific category
        questions = get_questions_by_category(category_id)
        category_name = next((c["display_name"] for c in categories if c["id"] == category_id), "Unknown")
        
        return templates.TemplateResponse(
            "study.html",
            {
                "request": request,
                "questions": questions,
                "category_name": category_name,
                "categories": categories,
                "total_questions": len(questions),
                "num_categories": len(categories),
                "current_category_id": category_id
            }
        )
    else:
        # Get all questions
        questions = get_questions_by_category()
        
        return templates.TemplateResponse(
            "study.html",
            {
                "request": request, 
                "questions": questions,
                "categories": categories,
                "total_questions": len(questions),
                "num_categories": len(categories),
                "current_category_id": None
            }
        )

# Add custom 404 error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    # For other HTTPExceptions, you might want to re-raise or handle differently
    # For now, let's let FastAPI handle other status codes by default or re-raise
    # This can be customized further if needed.
    # Example: return HTMLResponse(content=str(exc.detail), status_code=exc.status_code)
    # For a generic handler of all other HTTP exceptions, you might want to use StarletteHTTPException
    # from starlette.exceptions import HTTPException as StarletteHTTPException
    # and handle that. But for now, just specific 404 is requested.
    return HTMLResponse(content=str(exc.detail), status_code=exc.status_code) # Default FastAPI behavior for non-404s

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 