"""
LLM Backend for Instructor Assistant AI Chatbot
Supports OpenAI-compatible APIs with OpenAI and local Ollama model support
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging
import sys
from pathlib import Path

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add the canvas directory to the path to import canvas_main
canvas_path = Path(__file__).parent.parent.parent / "canvas"
sys.path.append(str(canvas_path))

try:
    import canvas_main
except ImportError:
    canvas_main = None

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation state management
class ConversationState(BaseModel):
    """Manages the state of a conversation with Canvas operations"""
    current_operation: Optional[str] = None  # "main_menu", "quiz_upload", "data_operations", "course_selection", etc.
    selected_course_id: Optional[str] = None
    selected_assignment_id: Optional[str] = None
    quiz_title: Optional[str] = None
    quiz_time_limit: Optional[int] = None
    questions_file: Optional[str] = None
    step: int = 0  # Current step in the workflow
    
class CanvasOperation(BaseModel):
    """Represents a Canvas operation result"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    next_step: Optional[str] = None

# Global conversation states (in production, use Redis or database)
conversation_states: Dict[str, ConversationState] = {}

class CanvasIntegration:
    """Handles Canvas operations through conversational interface"""
    
    @staticmethod
    def get_main_menu_options() -> str:
        """Returns the main menu options as a formatted string"""
        return """🎓 Canvas Management Tool - Available Operations:

1. 📝 Interactive Quiz Upload
   - Select a course
   - Configure quiz settings (title, time limit)
   - Choose questions file
   - Upload quiz to Canvas

2. 📊 Canvas Data Operations
   - Download student information to CSV
   - Download assignment submissions and files

3. 🔧 Test API Connection & List Courses
   - Verify Canvas API connectivity
   - View available courses

4. ❌ Exit

Please tell me which operation you'd like to perform, or ask me any questions about Canvas management!"""

    @staticmethod
    def handle_canvas_operation(user_input: str, session_id: str = "default") -> CanvasOperation:
        """
        Handles Canvas operations based on user input and conversation state
        """
        if not canvas_main:
            return CanvasOperation(
                success=False,
                message="Canvas integration is not available. Please check the canvas_main module.",
                next_step="error"
            )
        
        # Get or create conversation state
        if session_id not in conversation_states:
            conversation_states[session_id] = ConversationState()
        
        state = conversation_states[session_id]
        user_input_lower = user_input.lower().strip()
        
        try:
            # Main menu navigation
            if state.current_operation is None:
                if any(word in user_input_lower for word in ["quiz", "upload", "1"]):
                    state.current_operation = "quiz_upload"
                    state.step = 1
                    return CanvasOperation(
                        success=True,
                        message="🚀 Starting Interactive Quiz Upload!\n\nStep 1: Course Selection\nLet me get the available courses for you...",
                        next_step="course_selection"
                    )
                elif any(word in user_input_lower for word in ["data", "student", "assignment", "download", "2"]):
                    state.current_operation = "data_operations"
                    state.step = 1
                    return CanvasOperation(
                        success=True,
                        message="📊 Starting Canvas Data Operations!\n\nStep 1: Course Selection\nLet me get the available courses for you...",
                        next_step="course_selection"
                    )
                elif any(word in user_input_lower for word in ["test", "connection", "api", "course", "3"]):
                    return CanvasIntegration._test_canvas_connection()
                elif any(word in user_input_lower for word in ["exit", "quit", "4"]):
                    return CanvasOperation(
                        success=True,
                        message="👋 Goodbye! Feel free to ask if you need help with Canvas operations later.",
                        next_step="exit"
                    )
                else:
                    return CanvasOperation(
                        success=True,
                        message=CanvasIntegration.get_main_menu_options(),
                        next_step="main_menu"
                    )
            
            # Handle course selection
            elif state.step == 1 and state.current_operation in ["quiz_upload", "data_operations"]:
                return CanvasIntegration._handle_course_selection(user_input, state)
            
            # Handle quiz upload workflow
            elif state.current_operation == "quiz_upload":
                return CanvasIntegration._handle_quiz_upload_workflow(user_input, state)
            
            # Handle data operations workflow
            elif state.current_operation == "data_operations":
                return CanvasIntegration._handle_data_operations_workflow(user_input, state)
            
            else:
                # Reset state and show main menu
                conversation_states[session_id] = ConversationState()
                return CanvasOperation(
                    success=True,
                    message="Let me help you get back to the main menu.\n\n" + CanvasIntegration.get_main_menu_options(),
                    next_step="main_menu"
                )
                
        except Exception as e:
            # Reset state on error
            conversation_states[session_id] = ConversationState()
            return CanvasOperation(
                success=False,
                message=f"❌ An error occurred: {str(e)}\n\nLet me reset and show you the main menu.\n\n" + CanvasIntegration.get_main_menu_options(),
                next_step="main_menu"
            )
    
    @staticmethod
    def _test_canvas_connection() -> CanvasOperation:
        """Test Canvas API connection and list courses"""
        try:
            success = canvas_main.test_canvas_api()
            if success:
                courses = canvas_main.get_filtered_courses()
                if courses:
                    course_list = "\n".join([f"• {course['name']} (ID: {course['id']})" for course in courses[:10]])
                    message = f"✅ Canvas API Connection Successful!\n\n📚 Available Courses:\n{course_list}"
                    if len(courses) > 10:
                        message += f"\n\n... and {len(courses) - 10} more courses"
                else:
                    message = "✅ Canvas API Connection Successful!\n\n⚠️ No courses found or you don't have access to any courses."
                
                return CanvasOperation(
                    success=True,
                    message=message + "\n\n" + CanvasIntegration.get_main_menu_options(),
                    data={"courses": courses},
                    next_step="main_menu"
                )
            else:
                return CanvasOperation(
                    success=False,
                    message="❌ Canvas API connection failed. Please check your .env file configuration.\n\n" + CanvasIntegration.get_main_menu_options(),
                    next_step="main_menu"
                )
        except Exception as e:
            return CanvasOperation(
                success=False,
                message=f"❌ Configuration Error: {str(e)}\n\nPlease check your .env file configuration.\n\n" + CanvasIntegration.get_main_menu_options(),
                next_step="main_menu"
            )
    
    @staticmethod
    def _handle_course_selection(user_input: str, state: ConversationState) -> CanvasOperation:
        """Handle course selection step"""
        try:
            courses = canvas_main.get_filtered_courses()
            if not courses:
                return CanvasOperation(
                    success=False,
                    message="❌ No courses found. Please check your Canvas API configuration.\n\n" + CanvasIntegration.get_main_menu_options(),
                    next_step="main_menu"
                )
            
            # If user provided a course ID or name
            user_input_lower = user_input.lower().strip()
            selected_course = None
            
            # Try to match by ID
            for course in courses:
                if str(course['id']) == user_input.strip():
                    selected_course = course
                    break
            
            # Try to match by name (partial match)
            if not selected_course:
                for course in courses:
                    if user_input_lower in course['name'].lower():
                        selected_course = course
                        break
            
            if selected_course:
                state.selected_course_id = str(selected_course['id'])
                state.step = 2
                
                if state.current_operation == "quiz_upload":
                    return CanvasOperation(
                        success=True,
                        message=f"✅ Selected Course: {selected_course['name']}\n\nStep 2: Quiz Configuration\nPlease provide:\n1. Quiz title\n2. Time limit (in minutes)\n\nExample: 'My Quiz, 60 minutes' or just tell me the title and I'll ask for the time limit.",
                        data={"selected_course": selected_course},
                        next_step="quiz_config"
                    )
                else:  # data_operations
                    return CanvasOperation(
                        success=True,
                        message=f"✅ Selected Course: {selected_course['name']}\n\nStep 2: Data Operation Selection\nWhat would you like to do?\n1. Download all student information to CSV\n2. Download assignment submissions to CSV and files\n\nPlease choose option 1 or 2, or tell me what you'd like to download.",
                        data={"selected_course": selected_course},
                        next_step="data_operation_selection"
                    )
            else:
                # Show available courses
                course_list = "\n".join([f"{i+1}. {course['name']} (ID: {course['id']})" for i, course in enumerate(courses[:10])])
                message = f"📚 Available Courses:\n{course_list}"
                if len(courses) > 10:
                    message += f"\n\n... and {len(courses) - 10} more courses"
                message += "\n\nPlease provide the course ID or name you'd like to select."
                
                return CanvasOperation(
                    success=True,
                    message=message,
                    data={"courses": courses},
                    next_step="course_selection"
                )
                
        except Exception as e:
            return CanvasOperation(
                success=False,
                message=f"❌ Error getting courses: {str(e)}\n\n" + CanvasIntegration.get_main_menu_options(),
                next_step="main_menu"
            )
    
    @staticmethod
    def _handle_quiz_upload_workflow(user_input: str, state: ConversationState) -> CanvasOperation:
        """Handle quiz upload workflow steps"""
        if state.step == 2:  # Quiz configuration
            return CanvasIntegration._handle_quiz_config(user_input, state)
        elif state.step == 3:  # Questions file selection
            return CanvasIntegration._handle_questions_file_selection(user_input, state)
        elif state.step == 4:  # Final upload
            return CanvasIntegration._handle_quiz_upload(user_input, state)
        else:
            # Reset and go back to main menu
            return CanvasOperation(
                success=True,
                message="Let me reset the quiz upload process.\n\n" + CanvasIntegration.get_main_menu_options(),
                next_step="main_menu"
            )
    
    @staticmethod
    def _handle_data_operations_workflow(user_input: str, state: ConversationState) -> CanvasOperation:
        """Handle data operations workflow steps"""
        if state.step == 2:  # Data operation selection
            return CanvasIntegration._handle_data_operation_selection(user_input, state)
        elif state.step == 3:  # Assignment selection (for option 2)
            return CanvasIntegration._handle_assignment_selection(user_input, state)
        elif state.step == 4:  # Execute operation
            return CanvasIntegration._execute_data_operation(user_input, state)
        else:
            # Reset and go back to main menu
            return CanvasOperation(
                success=True,
                message="Let me reset the data operations process.\n\n" + CanvasIntegration.get_main_menu_options(),
                next_step="main_menu"
            )
    
    @staticmethod
    def _handle_quiz_config(user_input: str, state: ConversationState) -> CanvasOperation:
        """Handle quiz configuration input"""
        try:
            # Parse quiz title and time limit from user input
            user_input = user_input.strip()
            
            # Try to extract title and time limit
            if ',' in user_input:
                parts = user_input.split(',')
                title = parts[0].strip()
                time_part = parts[1].strip()
                
                # Extract number from time part
                import re
                time_match = re.search(r'(\d+)', time_part)
                time_limit = int(time_match.group(1)) if time_match else 30
            else:
                # Check if it's just a number (time limit)
                import re
                if re.match(r'^\d+$', user_input):
                    if state.quiz_title:
                        time_limit = int(user_input)
                        title = state.quiz_title
                    else:
                        return CanvasOperation(
                            success=True,
                            message="Please provide the quiz title first, then the time limit.\nExample: 'My Quiz Title'",
                            next_step="quiz_config"
                        )
                else:
                    title = user_input
                    time_limit = None
            
            state.quiz_title = title
            if time_limit:
                state.quiz_time_limit = time_limit
                state.step = 3
                return CanvasOperation(
                    success=True,
                    message=f"✅ Quiz Configuration:\n• Title: {title}\n• Time Limit: {time_limit} minutes\n\nStep 3: Questions File Selection\nPlease provide the path to your questions file, or tell me the filename if it's in the current directory.\n\nSupported formats: .txt, .md (markdown)",
                    next_step="questions_file"
                )
            else:
                return CanvasOperation(
                    success=True,
                    message=f"✅ Quiz Title: {title}\n\nNow please provide the time limit in minutes (e.g., '60' for 60 minutes):",
                    next_step="quiz_config"
                )
                
        except Exception as e:
            return CanvasOperation(
                success=False,
                message=f"❌ Error parsing quiz configuration: {str(e)}\n\nPlease provide quiz title and time limit.\nExample: 'My Quiz, 60 minutes'",
                next_step="quiz_config"
            )
    
    @staticmethod
    def _handle_questions_file_selection(user_input: str, state: ConversationState) -> CanvasOperation:
        """Handle questions file selection"""
        try:
            file_path = user_input.strip()
            
            # Check if file exists
            if os.path.exists(file_path):
                state.questions_file = file_path
                state.step = 4
                return CanvasOperation(
                    success=True,
                    message=f"✅ Questions File: {file_path}\n\n🚀 Ready to Upload Quiz!\n\nSummary:\n• Course ID: {state.selected_course_id}\n• Quiz Title: {state.quiz_title}\n• Time Limit: {state.quiz_time_limit} minutes\n• Questions File: {state.questions_file}\n\nType 'upload' to proceed with the quiz upload, or 'cancel' to go back to the main menu.",
                    next_step="quiz_upload_confirm"
                )
            else:
                return CanvasOperation(
                    success=False,
                    message=f"❌ File not found: {file_path}\n\nPlease provide a valid file path to your questions file.\nMake sure the file exists and you have the correct path.",
                    next_step="questions_file"
                )
                
        except Exception as e:
            return CanvasOperation(
                success=False,
                message=f"❌ Error checking file: {str(e)}\n\nPlease provide a valid file path.",
                next_step="questions_file"
            )
    
    @staticmethod
    def _handle_quiz_upload(user_input: str, state: ConversationState) -> CanvasOperation:
        """Handle final quiz upload"""
        user_input_lower = user_input.lower().strip()
        
        if user_input_lower == 'cancel':
            return CanvasOperation(
                success=True,
                message="Quiz upload cancelled.\n\n" + CanvasIntegration.get_main_menu_options(),
                next_step="main_menu"
            )
        elif user_input_lower == 'upload':
            try:
                # Perform the actual quiz upload
                quiz_result = canvas_main.upload_quiz_from_file(
                    state.questions_file,
                    state.quiz_title,
                    course_id=state.selected_course_id,
                    time_limit=state.quiz_time_limit
                )
                
                if quiz_result:
                    message = f"🎉 Quiz Upload Successful!\n\n"
                    message += f"📋 Quiz Title: {quiz_result['quiz_title']}\n"
                    message += f"🆔 Quiz ID: {quiz_result['quiz_id']}\n"
                    message += f"📊 Questions: {quiz_result['successful_uploads']}/{quiz_result['total_questions']}\n"
                    message += f"🔗 Quiz URL: {quiz_result['quiz_url']}\n\n"
                    message += CanvasIntegration.get_main_menu_options()
                    
                    # Reset state
                    state.current_operation = None
                    state.step = 0
                    
                    return CanvasOperation(
                        success=True,
                        message=message,
                        data=quiz_result,
                        next_step="main_menu"
                    )
                else:
                    return CanvasOperation(
                        success=False,
                        message="❌ Quiz upload failed. Please check the error messages and try again.\n\n" + CanvasIntegration.get_main_menu_options(),
                        next_step="main_menu"
                    )
                    
            except Exception as e:
                return CanvasOperation(
                    success=False,
                    message=f"❌ Error during quiz upload: {str(e)}\n\n" + CanvasIntegration.get_main_menu_options(),
                    next_step="main_menu"
                )
        else:
            return CanvasOperation(
                success=True,
                message="Please type 'upload' to proceed with the quiz upload, or 'cancel' to go back to the main menu.",
                next_step="quiz_upload_confirm"
            )
    
    @staticmethod
    def _handle_data_operation_selection(user_input: str, state: ConversationState) -> CanvasOperation:
        """Handle data operation selection"""
        user_input_lower = user_input.lower().strip()
        
        if any(word in user_input_lower for word in ["1", "student", "students"]):
            state.step = 4
            return CanvasOperation(
                success=True,
                message="✅ Selected: Download Student Information\n\nI'll download all student information to a CSV file. Type 'proceed' to start the download.",
                next_step="execute_student_download"
            )
        elif any(word in user_input_lower for word in ["2", "assignment", "submission"]):
            state.step = 3
            return CanvasOperation(
                success=True,
                message="✅ Selected: Download Assignment Submissions\n\nStep 3: Assignment Selection\nLet me get the available assignments for this course...",
                next_step="assignment_selection"
            )
        else:
            return CanvasOperation(
                success=True,
                message="Please choose:\n1. Download all student information to CSV\n2. Download assignment submissions to CSV and files\n\nType '1' or '2', or describe what you'd like to download.",
                next_step="data_operation_selection"
            )
    
    @staticmethod
    def _handle_assignment_selection(user_input: str, state: ConversationState) -> CanvasOperation:
        """Handle assignment selection for data operations"""
        try:
            assignments = canvas_main.get_course_assignments(state.selected_course_id)
            if not assignments:
                return CanvasOperation(
                    success=False,
                    message="❌ No assignments found for this course.\n\n" + CanvasIntegration.get_main_menu_options(),
                    next_step="main_menu"
                )
            
            # Try to match assignment by ID or name
            user_input_lower = user_input.lower().strip()
            selected_assignment = None
            
            # Try to match by ID
            for assignment in assignments:
                if str(assignment['id']) == user_input.strip():
                    selected_assignment = assignment
                    break
            
            # Try to match by name (partial match)
            if not selected_assignment:
                for assignment in assignments:
                    if user_input_lower in assignment['name'].lower():
                        selected_assignment = assignment
                        break
            
            if selected_assignment:
                state.selected_assignment_id = str(selected_assignment['id'])
                state.step = 4
                return CanvasOperation(
                    success=True,
                    message=f"✅ Selected Assignment: {selected_assignment['name']}\n\nI'll download all submissions for this assignment to CSV and download the submitted files. Type 'proceed' to start the download.",
                    data={"selected_assignment": selected_assignment},
                    next_step="execute_assignment_download"
                )
            else:
                # Show available assignments
                assignment_list = "\n".join([f"{i+1}. {assignment['name']} (ID: {assignment['id']})" for i, assignment in enumerate(assignments[:10])])
                message = f"📋 Available Assignments:\n{assignment_list}"
                if len(assignments) > 10:
                    message += f"\n\n... and {len(assignments) - 10} more assignments"
                message += "\n\nPlease provide the assignment ID or name you'd like to select."
                
                return CanvasOperation(
                    success=True,
                    message=message,
                    data={"assignments": assignments},
                    next_step="assignment_selection"
                )
                
        except Exception as e:
            return CanvasOperation(
                success=False,
                message=f"❌ Error getting assignments: {str(e)}\n\n" + CanvasIntegration.get_main_menu_options(),
                next_step="main_menu"
            )
    
    @staticmethod
    def _execute_data_operation(user_input: str, state: ConversationState) -> CanvasOperation:
        """Execute the selected data operation"""
        user_input_lower = user_input.lower().strip()
        
        if user_input_lower != 'proceed':
            return CanvasOperation(
                success=True,
                message="Type 'proceed' to start the download, or 'cancel' to go back to the main menu.",
                next_step="execute_operation"
            )
        
        try:
            if state.selected_assignment_id:
                # Download assignment submissions
                course_response = canvas_main.requests.get(f"{canvas_main.API_URL}/courses/{state.selected_course_id}", headers=canvas_main.headers)
                course_name = course_response.json().get('name', f'Course_{state.selected_course_id}') if course_response.status_code == 200 else f'Course_{state.selected_course_id}'
                
                assignment_response = canvas_main.requests.get(f"{canvas_main.API_URL}/courses/{state.selected_course_id}/assignments/{state.selected_assignment_id}", headers=canvas_main.headers)
                assignment_name = assignment_response.json().get('name', f'Assignment_{state.selected_assignment_id}') if assignment_response.status_code == 200 else f'Assignment_{state.selected_assignment_id}'
                
                submissions = canvas_main.get_assignment_submissions(state.selected_course_id, state.selected_assignment_id)
                if submissions:
                    csv_result = canvas_main.export_submissions_to_csv(submissions, assignment_name, course_name)
                    download_result = canvas_main.download_submission_files(submissions, assignment_name, course_name)
                    
                    if csv_result and download_result:
                        message = f"🎉 Assignment Submissions Download Successful!\n\n"
                        message += f"📊 Total submissions: {csv_result['total_submissions']}\n"
                        message += f"📁 CSV file: {csv_result['csv_file']}\n"
                        message += f"📂 Files downloaded: {download_result['successful_downloads']}/{download_result['total_files']}\n"
                        message += f"📁 Download folder: {download_result['download_folder']}\n\n"
                        message += CanvasIntegration.get_main_menu_options()
                        
                        return CanvasOperation(
                            success=True,
                            message=message,
                            data={"csv_result": csv_result, "download_result": download_result},
                            next_step="main_menu"
                        )
                    else:
                        return CanvasOperation(
                            success=False,
                            message="❌ Failed to complete assignment submissions download.\n\n" + CanvasIntegration.get_main_menu_options(),
                            next_step="main_menu"
                        )
                else:
                    return CanvasOperation(
                        success=False,
                        message="❌ No submissions found for this assignment.\n\n" + CanvasIntegration.get_main_menu_options(),
                        next_step="main_menu"
                    )
            else:
                # Download student information
                course_response = canvas_main.requests.get(f"{canvas_main.API_URL}/courses/{state.selected_course_id}", headers=canvas_main.headers)
                course_name = course_response.json().get('name', f'Course_{state.selected_course_id}') if course_response.status_code == 200 else f'Course_{state.selected_course_id}'
                
                students = canvas_main.get_course_students(state.selected_course_id)
                if students:
                    result = canvas_main.export_students_to_csv(students, course_name)
                    if result:
                        message = f"🎉 Student Information Download Successful!\n\n"
                        message += f"📊 Total students: {result['total_students']}\n"
                        message += f"📁 CSV file: {result['csv_file']}\n\n"
                        message += CanvasIntegration.get_main_menu_options()
                        
                        return CanvasOperation(
                            success=True,
                            message=message,
                            data=result,
                            next_step="main_menu"
                        )
                    else:
                        return CanvasOperation(
                            success=False,
                            message="❌ Failed to export student information to CSV.\n\n" + CanvasIntegration.get_main_menu_options(),
                            next_step="main_menu"
                        )
                else:
                    return CanvasOperation(
                        success=False,
                        message="❌ No students found for this course.\n\n" + CanvasIntegration.get_main_menu_options(),
                        next_step="main_menu"
                    )
                    
        except Exception as e:
            return CanvasOperation(
                success=False,
                message=f"❌ Error during download: {str(e)}\n\n" + CanvasIntegration.get_main_menu_options(),
                next_step="main_menu"
            )
        finally:
            # Reset state
            state.current_operation = None
            state.step = 0

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = Field(default="gpt-3.5-turbo", description="Model to use for completion")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1000, gt=0)
    stream: Optional[bool] = Field(default=False)

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None

class LLMBackend:
    """LLM Backend supporting OpenAI and Ollama models"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Default models
        self.openai_models = [
            "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
        ]
        self.ollama_models = [
            "llama2", "llama2:13b", "codellama", "mistral", "neural-chat"
        ]
        
        # System prompt for the instructor assistant
        self.system_prompt = """You are an AI assistant for instructors using Canvas LMS. You help with:
- Canvas course management and operations
- Quiz creation and formatting
- Student data analysis
- Assignment management
- Educational content creation
- Technical support for Canvas integration

Be helpful, professional, and provide accurate information about Canvas operations and educational best practices."""

    def _is_ollama_model(self, model: str) -> bool:
        """Check if the model is an Ollama model"""
        return any(model.startswith(ollama_model) for ollama_model in self.ollama_models)

    def _prepare_messages(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """Prepare messages for API call"""
        # Add system message if not present
        formatted_messages = []
        has_system = any(msg.role == "system" for msg in messages)
        
        if not has_system:
            formatted_messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # Add user messages
        for msg in messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return formatted_messages

    async def _call_openai_api(self, request: ChatRequest) -> ChatResponse:
        """Call OpenAI-compatible API"""
        if not self.openai_api_key:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
            )

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": request.model,
            "messages": self._prepare_messages(request.messages),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.openai_base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return ChatResponse(**response.json())
            
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"OpenAI API error: {e.response.text}"
                )
            except Exception as e:
                logger.error(f"OpenAI API call failed: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to call OpenAI API: {str(e)}"
                )

    async def _call_ollama_api(self, request: ChatRequest) -> ChatResponse:
        """Call Ollama API"""
        payload = {
            "model": request.model,
            "messages": self._prepare_messages(request.messages),
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.ollama_base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                ollama_response = response.json()
                
                # Convert Ollama response to OpenAI format
                return ChatResponse(
                    id=f"ollama-{datetime.now().timestamp()}",
                    created=int(datetime.now().timestamp()),
                    model=request.model,
                    choices=[{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": ollama_response.get("message", {}).get("content", "")
                        },
                        "finish_reason": "stop"
                    }]
                )
            
            except httpx.ConnectError:
                logger.error("Failed to connect to Ollama. Make sure Ollama is running.")
                raise HTTPException(
                    status_code=503,
                    detail="Ollama service is not available. Please make sure Ollama is running on your system."
                )
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Ollama API error: {e.response.text}"
                )
            except Exception as e:
                logger.error(f"Ollama API call failed: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to call Ollama API: {str(e)}"
                )

    async def _stream_openai_response(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream OpenAI response"""
        if not self.openai_api_key:
            raise HTTPException(
                status_code=500, 
                detail="OpenAI API key not configured"
            )

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": request.model,
            "messages": self._prepare_messages(request.messages),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.openai_base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.error(f"Streaming failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Main chat completion method with Canvas integration"""
        try:
            # Extract the latest user message
            user_messages = [msg for msg in request.messages if msg.role == "user"]
            if not user_messages:
                raise HTTPException(status_code=400, detail="No user message found")
            
            latest_user_message = user_messages[-1].content
            
            # Check if this is a Canvas-related request
            canvas_keywords = ["canvas", "quiz", "upload", "course", "assignment", "student", "submission", "menu"]
            is_canvas_request = any(keyword.lower() in latest_user_message.lower() for keyword in canvas_keywords)
            
            # Handle Canvas operations
            if is_canvas_request or self._has_active_canvas_session(request):
                return await self._handle_canvas_chat(request, latest_user_message)
            
            # Regular LLM chat completion
            if self._is_ollama_model(request.model):
                return await self._call_ollama_api(request)
            else:
                return await self._call_openai_api(request)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Chat completion failed: {str(e)}"
            )

    def _has_active_canvas_session(self, request: ChatRequest) -> bool:
        """Check if there's an active Canvas session based on conversation history"""
        # Look for Canvas-related context in recent messages
        recent_messages = request.messages[-5:] if len(request.messages) > 5 else request.messages
        for msg in recent_messages:
            if msg.role == "assistant" and any(keyword in msg.content.lower() for keyword in 
                ["canvas menu", "select option", "course selection", "quiz upload", "data operations"]):
                return True
        return False

    async def _handle_canvas_chat(self, request: ChatRequest, user_input: str) -> ChatResponse:
        """Handle Canvas-integrated chat completion"""
        try:
            # Generate a session ID from the conversation context
            session_id = self._generate_session_id(request)
            
            # Handle Canvas operation
            canvas_result = CanvasIntegration.handle_canvas_operation(user_input, session_id)
            
            if canvas_result.success:
                # Create response with Canvas operation result
                response_content = canvas_result.message
                
                # If there's additional data, format it nicely
                if canvas_result.data:
                    if "courses" in canvas_result.data:
                        courses = canvas_result.data["courses"]
                        response_content += "\n\nAvailable courses:\n"
                        for i, course in enumerate(courses, 1):
                            response_content += f"{i}. {course['name']} (ID: {course['id']})\n"
                    elif "assignments" in canvas_result.data:
                        assignments = canvas_result.data["assignments"]
                        response_content += "\n\nAvailable assignments:\n"
                        for i, assignment in enumerate(assignments, 1):
                            response_content += f"{i}. {assignment['name']} (ID: {assignment['id']})\n"
                
                return ChatResponse(
                    id=f"canvas-{datetime.now().timestamp()}",
                    created=int(datetime.now().timestamp()),
                    model=request.model,
                    choices=[{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_content
                        },
                        "finish_reason": "stop"
                    }]
                )
            else:
                # Canvas operation failed, fall back to regular LLM with context
                enhanced_messages = self._enhance_messages_with_canvas_context(request.messages, canvas_result.message)
                enhanced_request = ChatRequest(
                    messages=enhanced_messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=request.stream
                )
                
                if self._is_ollama_model(request.model):
                    return await self._call_ollama_api(enhanced_request)
                else:
                    return await self._call_openai_api(enhanced_request)
                    
        except Exception as e:
            logger.error(f"Canvas chat handling failed: {str(e)}")
            # Fall back to regular LLM completion
            if self._is_ollama_model(request.model):
                return await self._call_ollama_api(request)
            else:
                return await self._call_openai_api(request)

    def _generate_session_id(self, request: ChatRequest) -> str:
        """Generate a session ID based on conversation context"""
        # Use a simple hash of the first few messages to create a consistent session ID
        context = ""
        for msg in request.messages[:3]:
            context += f"{msg.role}:{msg.content[:50]}"
        return str(hash(context))

    def _enhance_messages_with_canvas_context(self, messages: List[ChatMessage], canvas_error: str) -> List[ChatMessage]:
        """Enhance messages with Canvas context for better LLM responses"""
        system_message = ChatMessage(
            role="system",
            content=f"""You are an AI assistant helping with Canvas LMS operations. 
            The user is trying to perform Canvas operations but encountered an issue: {canvas_error}
            
            Available Canvas operations:
            1. Quiz Upload - Upload quizzes to Canvas courses
            2. Data Operations - Download student information or assignment submissions
            3. Test Canvas Connection - Verify API connectivity
            
            Please help the user with their Canvas-related questions and guide them through the available options.
            If they need to perform Canvas operations, guide them to use the Canvas menu options."""
        )
        
        return [system_message] + messages

    async def stream_completion(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream chat completion"""
        if self._is_ollama_model(request.model):
            # For Ollama, we'll simulate streaming by yielding the complete response
            response = await self._call_ollama_api(request)
            content = response.choices[0]["message"]["content"]
            # Simulate streaming by yielding words
            words = content.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.05)  # Small delay to simulate streaming
        else:
            async for chunk in self._stream_openai_response(request):
                yield chunk

    async def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models"""
        available_models = {
            "openai": [],
            "ollama": []
        }

        # Check OpenAI models
        if self.openai_api_key:
            available_models["openai"] = self.openai_models

        # Check Ollama models
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    ollama_data = response.json()
                    available_models["ollama"] = [model["name"] for model in ollama_data.get("models", [])]
        except Exception as e:
            logger.warning(f"Could not fetch Ollama models: {str(e)}")

        return available_models

    async def health_check(self) -> Dict[str, Any]:
        """Health check for LLM services"""
        status = {
            "openai": {"available": False, "error": None},
            "ollama": {"available": False, "error": None}
        }

        # Check OpenAI
        if self.openai_api_key:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{self.openai_base_url}/models",
                        headers={"Authorization": f"Bearer {self.openai_api_key}"}
                    )
                    if response.status_code == 200:
                        status["openai"]["available"] = True
            except Exception as e:
                status["openai"]["error"] = str(e)
        else:
            status["openai"]["error"] = "API key not configured"

        # Check Ollama
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    status["ollama"]["available"] = True
        except Exception as e:
            status["ollama"]["error"] = str(e)

        return status

# Global LLM backend instance
llm_backend = LLMBackend()