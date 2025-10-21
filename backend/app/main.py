from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import sys
import os
import tempfile
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Import LLM backend
from app.backend_llm import llm_backend, ChatRequest, ChatMessage, ChatResponse

# Add canvas directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../canvas'))

try:
    from canvas_main import (
        get_filtered_courses, 
        upload_quiz_from_file, 
        test_canvas_api,
        get_course_students,
        get_course_assignments,
        get_assignment_submissions,
        export_students_to_csv,
        export_submissions_to_csv,
        download_submission_files
    )
except ImportError as e:
    print(f"Error importing canvas_main: {e}")
    print("Make sure canvas_main.py is in the canvas directory")

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

class StudentResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    sis_user_id: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: int
    name: str
    points_possible: Optional[float] = None
    due_at: Optional[str] = None
    submission_types: List[str] = []

class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    assignment_id: int
    submitted_at: Optional[str] = None
    grade: Optional[str] = None
    score: Optional[float] = None
    user_name: Optional[str] = None

class ExportResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None
    total_records: Optional[int] = None

@app.get("/")
async def root():
    return {"message": "Instructor Assistant API is running"}

@app.get("/courses", response_model=List[CourseResponse])
async def get_courses(course_prefix: Optional[str] = None):
    """
    Get Canvas courses with optional prefix filtering
    Enhanced to use canvas_main.py functions with better error handling
    """
    try:
        courses = get_filtered_courses(course_prefix)
        if courses is None:
            raise HTTPException(status_code=500, detail="Failed to fetch courses from Canvas API")
        
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
    Test Canvas API connection and return detailed information
    Enhanced to provide more comprehensive API testing
    """
    try:
        success = test_canvas_api()
        if success:
            # Get additional info about available courses
            courses = get_filtered_courses()
            course_count = len(courses) if courses else 0
            
            return {
                "success": success, 
                "message": "API test completed successfully",
                "total_courses": course_count,
                "api_status": "Connected"
            }
        else:
            return {
                "success": False,
                "message": "API test failed - check credentials",
                "api_status": "Failed"
            }
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
        if not file.filename or not (file.filename.endswith('.md') or file.filename.endswith('.txt')):
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

@app.get("/courses/{course_id}/students", response_model=List[StudentResponse])
async def get_students(course_id: str):
    """
    Get all students enrolled in a course
    """
    try:
        students = get_course_students(course_id)
        if students is None:
            raise HTTPException(status_code=500, detail="Failed to fetch students")
        
        return [
            StudentResponse(
                id=student["id"],
                name=student.get("name", "Unknown"),
                email=student.get("email"),
                sis_user_id=student.get("sis_user_id")
            )
            for student in students
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch students: {str(e)}")

@app.get("/courses/{course_id}/assignments", response_model=List[AssignmentResponse])
async def get_assignments(course_id: str):
    """
    Get all assignments for a course
    """
    try:
        assignments = get_course_assignments(course_id)
        if assignments is None:
            raise HTTPException(status_code=500, detail="Failed to fetch assignments")
        
        return [
            AssignmentResponse(
                id=assignment["id"],
                name=assignment.get("name", "Unnamed Assignment"),
                points_possible=assignment.get("points_possible"),
                due_at=assignment.get("due_at"),
                submission_types=assignment.get("submission_types", [])
            )
            for assignment in assignments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch assignments: {str(e)}")

@app.get("/courses/{course_id}/assignments/{assignment_id}/submissions", response_model=List[SubmissionResponse])
async def get_submissions(course_id: str, assignment_id: str):
    """
    Get all submissions for a specific assignment
    """
    try:
        submissions = get_assignment_submissions(course_id, assignment_id)
        if submissions is None:
            raise HTTPException(status_code=500, detail="Failed to fetch submissions")
        
        return [
            SubmissionResponse(
                id=submission["id"],
                user_id=submission["user_id"],
                assignment_id=submission["assignment_id"],
                submitted_at=submission.get("submitted_at"),
                grade=submission.get("grade"),
                score=submission.get("score"),
                user_name=submission.get("user", {}).get("name") if submission.get("user") else None
            )
            for submission in submissions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch submissions: {str(e)}")

@app.post("/courses/{course_id}/students/export", response_model=ExportResponse)
async def export_students(course_id: str):
    """
    Export all students in a course to CSV
    """
    try:
        students = get_course_students(course_id)
        if students is None:
            raise HTTPException(status_code=500, detail="Failed to fetch students")
        
        # Get course name for file naming
        courses = get_filtered_courses()
        course_name = f"Course_{course_id}"
        for course in courses:
            if str(course["id"]) == course_id:
                course_name = course.get("name", course_name)
                break
        
        result = export_students_to_csv(students, course_name)
        if result:
            return ExportResponse(
                success=True,
                message="Students exported successfully",
                file_path=result["csv_file"],
                total_records=result["total_students"]
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to export students")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/courses/{course_id}/assignments/{assignment_id}/submissions/export", response_model=ExportResponse)
async def export_assignment_submissions(course_id: str, assignment_id: str):
    """
    Export all submissions for an assignment to CSV and download files
    """
    try:
        submissions = get_assignment_submissions(course_id, assignment_id)
        if submissions is None:
            raise HTTPException(status_code=500, detail="Failed to fetch submissions")
        
        # Get course and assignment names
        courses = get_filtered_courses()
        course_name = f"Course_{course_id}"
        for course in courses:
            if str(course["id"]) == course_id:
                course_name = course.get("name", course_name)
                break
        
        assignments = get_course_assignments(course_id)
        assignment_name = f"Assignment_{assignment_id}"
        if assignments:
            for assignment in assignments:
                if str(assignment["id"]) == assignment_id:
                    assignment_name = assignment.get("name", assignment_name)
                    break
        
        # Export submissions to CSV
        csv_result = export_submissions_to_csv(submissions, assignment_name, course_name)
        
        # Download submission files
        files_result = download_submission_files(submissions, assignment_name, course_name)
        
        if csv_result and files_result:
            return ExportResponse(
                success=True,
                message=f"Submissions exported successfully. CSV: {csv_result['csv_file']}, Files: {files_result['download_dir']}",
                file_path=csv_result["csv_file"],
                total_records=csv_result["total_submissions"]
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to export submissions")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# LLM Chat Endpoints
@app.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """
    Chat completion endpoint compatible with OpenAI API format
    Supports both OpenAI and Ollama models
    """
    try:
        return await llm_backend.chat_completion(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat completion endpoint
    """
    try:
        async def generate():
            async for chunk in llm_backend.stream_completion(request):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")

@app.get("/chat/models")
async def get_models() -> Dict[str, Any]:
    """
    Get available LLM models
    """
    try:
        return await llm_backend.get_available_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.get("/chat/health")
async def chat_health() -> Dict[str, Any]:
    """
    Health check for LLM services
    """
    try:
        return await llm_backend.health_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)