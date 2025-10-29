from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
import tempfile
from typing import List, Optional
from pydantic import BaseModel

# Add canvas directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../canvas'))

try:
    from canvasquiz import get_filtered_courses, upload_quiz_from_file, test_canvas_api
except ImportError as e:
    print(f"Error importing canvasquiz: {e}")
    print("Make sure canvasquiz.py is in the canvas directory")

app = FastAPI(title="Instructor Assistant API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CourseResponse(BaseModel):
    id: int
    name: str
    course_code: str

class QuizUploadResponse(BaseModel):
    quiz_id: int
    quiz_title: str
    total_questions: int
    successful_uploads: int
    quiz_url: str

@app.get("/")
async def root():
    return {"message": "Instructor Assistant API is running"}

@app.get("/courses", response_model=List[CourseResponse])
async def get_courses(course_prefix: Optional[str] = None):
    """
    Get Canvas courses with optional prefix filtering
    """
    try:
        courses = get_filtered_courses(course_prefix)
        return [
            CourseResponse(
                id=course["id"],
                name=course.get("name", "Unnamed Course"),
                course_code=course.get("course_code", "N/A")
            )
            for course in courses
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {str(e)}")

@app.post("/test-api")
async def test_api():
    """
    Test Canvas API connection
    """
    try:
        success = test_canvas_api()
        return {"success": success, "message": "API test completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API test failed: {str(e)}")

@app.post("/upload-quiz", response_model=QuizUploadResponse)
async def upload_quiz(
    file: UploadFile = File(...),
    course_id: str = Form(...),
    quiz_title: str = Form(...),
    time_limit: int = Form(30),
    published: bool = Form(False)
):
    """
    Upload a quiz from a markdown or text file
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.md', '.txt')):
            raise HTTPException(status_code=400, detail="Only .md and .txt files are supported")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Upload quiz using canvasquiz function
            result = upload_quiz_from_file(
                questions_file=temp_file_path,
                quiz_title=quiz_title,
                course_id=course_id,
                time_limit=time_limit,
                published=published
            )
            
            if not result:
                raise HTTPException(status_code=500, detail="Failed to create quiz")
            
            return QuizUploadResponse(
                quiz_id=result["quiz_id"],
                quiz_title=result["quiz_title"],
                total_questions=result["total_questions"],
                successful_uploads=result["successful_uploads"],
                quiz_url=result["quiz_url"]
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error details: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
