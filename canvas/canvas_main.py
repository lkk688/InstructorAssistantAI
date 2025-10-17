#enhanced over the canvasquiz.py
import requests
import re
import os
import csv
from datetime import datetime
from dotenv import load_dotenv
from question_parsers import parse_questions_markdown, parse_questions, parse_questions_cmpe_format

# Load environment variables from .env file
load_dotenv()

API_URL = os.getenv('CANVAS_API_URL', 'https://<your-canvas-domain>/api/v1')
ACCESS_TOKEN = os.getenv('CANVAS_ACCESS_TOKEN')
COURSE_ID = os.getenv('CANVAS_COURSE_ID')

# Validate required environment variables
if not ACCESS_TOKEN:
    raise ValueError("CANVAS_ACCESS_TOKEN environment variable is required. Please set it in your .env file.")
if not API_URL or API_URL == 'https://<your-canvas-domain>/api/v1':
    raise ValueError("CANVAS_API_URL environment variable is required. Please set it in your .env file.")
if not COURSE_ID:
    print("Warning: CANVAS_COURSE_ID not set. You can set it after running the test_canvas_api() function to see available course IDs.")
QUIZ_TITLE = 'Auto Quiz Upload'

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

def get_filtered_courses(course_prefix=None):
    """
    Get courses from Canvas API with optional prefix filtering.
    Handles pagination to fetch all courses (not limited to 100).
    
    Args:
        course_prefix (str, optional): Filter courses that start with this prefix
    
    Returns:
        list: List of course dictionaries, or empty list if error/no matches
    """
    try:
        all_courses = []
        url = f'{API_URL}/courses'
        params = {'per_page': 100}  # Maximum per page
        
        while url:
            courses_response = requests.get(url, headers=headers, params=params)
            
            if courses_response.status_code != 200:
                print(f"Failed to fetch courses. Status code: {courses_response.status_code}")
                return []
            
            courses = courses_response.json()
            all_courses.extend(courses)
            
            # Check for next page in Link header
            link_header = courses_response.headers.get('Link', '')
            url = None  # Reset URL
            
            # Parse Link header to find 'next' URL
            if link_header:
                links = link_header.split(',')
                for link in links:
                    if 'rel="next"' in link:
                        # Extract URL from <URL>; rel="next"
                        url = link.split(';')[0].strip('<> ')
                        params = {}  # Clear params as URL already contains them
                        break
        
        # Filter courses by prefix if specified
        if course_prefix:
            filtered_courses = []
            for course in all_courses:
                course_name = course.get('name', '')
                course_code = course.get('course_code', '')
                # Check if either course name or course code starts with the prefix
                if course_name.startswith(course_prefix) or course_code.startswith(course_prefix):
                    filtered_courses.append(course)
            return filtered_courses
        
        return all_courses
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

# Canvas API Testing Function
def test_canvas_api(course_prefix=None):
    """
    Test Canvas API connection and list available courses with their IDs.
    This function helps verify API credentials and shows available courses.
    
    Args:
        course_prefix (str, optional): Filter courses that start with this prefix (e.g., "SP25")
    """
    try:
        # Test API connection by getting user profile
        profile_response = requests.get(f'{API_URL}/users/self/profile', headers=headers)
        
        if profile_response.status_code != 200:
            print(f"API connection failed. Status code: {profile_response.status_code}")
            print(f"Response: {profile_response.text}")
            return False
        
        profile = profile_response.json()
        print(f"API connection successful! Logged in as: {profile.get('name', 'Unknown')}")
        print(f"User ID: {profile.get('id', 'Unknown')}")
        print("-" * 50)
        
        # Get list of courses (with optional filtering)
        if course_prefix:
            print(f"Filtering courses with prefix: '{course_prefix}'")
        
        courses = get_filtered_courses(course_prefix)
        
        if not courses:
            filter_msg = f" matching prefix '{course_prefix}'" if course_prefix else ""
            print(f"No courses found{filter_msg}.")
            return True
        
        filter_msg = f" (filtered by '{course_prefix}')" if course_prefix else ""
        print(f"Available Courses{filter_msg} - Total fetched: {len(courses)}:")
        print(f"{'Course ID':<12} {'Course Name':<50} {'Course Code':<20}")
        print("-" * 82)
        
        for course in courses:
            course_id = course.get('id', 'N/A')
            course_name = course.get('name', 'Unnamed Course')[:47] + '...' if len(course.get('name', '')) > 50 else course.get('name', 'Unnamed Course')
            course_code = course.get('course_code', 'N/A')[:17] + '...' if len(course.get('course_code', '')) > 20 else course.get('course_code', 'N/A')
            
            print(f"{course_id:<12} {course_name:<50} {course_code:<20}")
        
        total_msg = f" matching '{course_prefix}'" if course_prefix else ""
        print(f"\nTotal courses found{total_msg}: {len(courses)}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def interactive_course_selection(course_prefix=None):
    """
    Interactive course selection that displays courses and allows user to choose one.
    
    Args:
        course_prefix (str, optional): Filter courses that start with this prefix
    
    Returns:
        str: Selected course ID, or None if selection failed
    """
    try:
        # Test API connection first
        profile_response = requests.get(f'{API_URL}/users/self/profile', headers=headers)
        
        if profile_response.status_code != 200:
            print(f"❌ API connection failed. Status code: {profile_response.status_code}")
            return None
        
        profile = profile_response.json()
        print(f"✅ Connected to Canvas as: {profile.get('name', 'Unknown')}")
        print("=" * 60)
        
        # Get courses
        courses = get_filtered_courses(course_prefix)
        
        if not courses:
            filter_msg = f" matching prefix '{course_prefix}'" if course_prefix else ""
            print(f"❌ No courses found{filter_msg}.")
            return None
        
        # Display courses with numbers for selection
        filter_msg = f" (filtered by '{course_prefix}')" if course_prefix else ""
        print(f"📚 Available Courses{filter_msg}:")
        print("-" * 60)
        
        for i, course in enumerate(courses, 1):
            course_id = course.get('id', 'N/A')
            course_name = course.get('name', 'Unnamed Course')
            course_code = course.get('course_code', 'N/A')
            print(f"{i:2}. [{course_id}] {course_name}")
            if course_code != 'N/A':
                print(f"    Code: {course_code}")
        
        print("-" * 60)
        
        # Get user selection
        while True:
            try:
                selection = input(f"\n🎯 Select a course (1-{len(courses)}) or 'q' to quit: ").strip()
                
                if selection.lower() == 'q':
                    print("👋 Goodbye!")
                    return None
                
                course_index = int(selection) - 1
                if 0 <= course_index < len(courses):
                    selected_course = courses[course_index]
                    course_id = str(selected_course.get('id'))
                    course_name = selected_course.get('name', 'Unknown Course')
                    print(f"✅ Selected: [{course_id}] {course_name}")
                    return course_id
                else:
                    print(f"❌ Please enter a number between 1 and {len(courses)}")
                    
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
                
    except Exception as e:
        print(f"❌ Error during course selection: {e}")
        return None


def interactive_assignment_selection(course_id):
    """
    Interactive assignment selection that displays assignments and allows user to choose one.
    
    Args:
        course_id (str): Canvas course ID
    
    Returns:
        dict: Selected assignment dictionary, or None if selection failed
    """
    try:
        # Get assignments
        assignments = get_course_assignments(course_id)
        
        if not assignments:
            print("❌ No assignments found in this course.")
            return None
        
        # Display assignments with numbers for selection
        print(f"📋 Available Assignments:")
        print("-" * 60)
        
        for i, assignment in enumerate(assignments, 1):
            assignment_id = assignment.get('id', 'N/A')
            assignment_name = assignment.get('name', 'Unnamed Assignment')
            due_date = assignment.get('due_at', 'No due date')
            points = assignment.get('points_possible', 'N/A')
            
            print(f"{i:2}. [{assignment_id}] {assignment_name}")
            print(f"    Due: {due_date} | Points: {points}")
        
        print("-" * 60)
        
        # Get user selection
        while True:
            try:
                selection = input(f"\n🎯 Select an assignment (1-{len(assignments)}) or 'q' to quit: ").strip()
                
                if selection.lower() == 'q':
                    print("👋 Goodbye!")
                    return None
                
                assignment_index = int(selection) - 1
                if 0 <= assignment_index < len(assignments):
                    selected_assignment = assignments[assignment_index]
                    assignment_name = selected_assignment.get('name', 'Unknown Assignment')
                    assignment_id = selected_assignment.get('id')
                    print(f"✅ Selected: [{assignment_id}] {assignment_name}")
                    return selected_assignment
                else:
                    print(f"❌ Please enter a number between 1 and {len(assignments)}")
                    
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None
                
    except Exception as e:
        print(f"❌ Error during assignment selection: {e}")
        return None


def get_quiz_details():
    """
    Interactive prompts to get quiz name and time limit from user.
    
    Returns:
        tuple: (quiz_title, time_limit) or (None, None) if cancelled
    """
    try:
        print("\n" + "=" * 60)
        print("📝 Quiz Configuration")
        print("=" * 60)
        
        # Get quiz title
        while True:
            quiz_title = input("📋 Enter quiz title (or 'q' to quit): ").strip()
            
            if quiz_title.lower() == 'q':
                return None, None
            
            if quiz_title:
                break
            else:
                print("❌ Quiz title cannot be empty. Please try again.")
        
        # Get time limit
        while True:
            try:
                time_input = input("⏰ Enter time limit in minutes (default: 30): ").strip()
                
                if time_input.lower() == 'q':
                    return None, None
                
                if not time_input:
                    time_limit = 30
                    break
                
                time_limit = int(time_input)
                if time_limit > 0:
                    break
                else:
                    print("❌ Time limit must be a positive number")
                    
            except ValueError:
                print("❌ Please enter a valid number for time limit")
        
        print(f"✅ Quiz: '{quiz_title}' | Time: {time_limit} minutes")
        return quiz_title, time_limit
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return None, None


def get_questions_file():
    """
    Interactive file selection with validation and default options.
    
    Returns:
        str: File path or None if cancelled
    """
    try:
        print("\n" + "=" * 60)
        print("📁 Question File Selection")
        print("=" * 60)
        
        # Show available sample files
        sample_files = []
        data_dir = "data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(('.md', '.txt')):
                    sample_files.append(os.path.join(data_dir, file))
        
        # Show current directory files
        current_files = []
        for file in os.listdir('.'):
            if file.endswith(('.md', '.txt')):
                current_files.append(file)
        
        all_files = sample_files + current_files
        
        if all_files:
            print("📋 Available question files:")
            for i, file in enumerate(all_files, 1):
                print(f"{i:2}. {file}")
            print("-" * 60)
        
        while True:
            if all_files:
                file_input = input(f"📁 Enter file path, select number (1-{len(all_files)}), or 'q' to quit: ").strip()
            else:
                file_input = input("📁 Enter file path or 'q' to quit: ").strip()
            
            if file_input.lower() == 'q':
                return None
            
            # Check if it's a number selection
            try:
                file_index = int(file_input) - 1
                if 0 <= file_index < len(all_files):
                    file_path = all_files[file_index]
                else:
                    print(f"❌ Please enter a number between 1 and {len(all_files)}")
                    continue
            except ValueError:
                # It's a file path
                file_path = file_input
            
            # Validate file exists
            if os.path.exists(file_path):
                if file_path.endswith(('.md', '.txt')):
                    print(f"✅ Selected file: {file_path}")
                    return file_path
                else:
                    print("❌ File must be a .md or .txt file")
            else:
                print(f"❌ File not found: {file_path}")
                
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return None


def interactive_quiz_upload():
    """
    Complete interactive quiz upload process similar to the frontend.
    """
    print("🚀 Interactive Quiz Upload to Canvas")
    print("=" * 60)
    
    # Step 1: Select course
    print("Step 1: Course Selection")
    course_id = interactive_course_selection()
    if not course_id:
        return
    
    # Step 2: Get quiz details
    print("\nStep 2: Quiz Configuration")
    quiz_title, time_limit = get_quiz_details()
    if not quiz_title:
        return
    
    # Step 3: Select questions file
    print("\nStep 3: Question File Selection")
    questions_file = get_questions_file()
    if not questions_file:
        return
    
    # Step 4: Upload quiz
    print("\n" + "=" * 60)
    print("🚀 Uploading Quiz to Canvas...")
    print("=" * 60)
    print(f"📚 Course ID: {course_id}")
    print(f"📋 Quiz Title: {quiz_title}")
    print(f"⏰ Time Limit: {time_limit} minutes")
    print(f"📁 Questions File: {questions_file}")
    print("-" * 60)
    
    try:
        quiz_result = upload_quiz_from_file(
            questions_file, 
            quiz_title, 
            course_id=course_id, 
            time_limit=time_limit
        )
        
        if quiz_result:
            print("\n🎉 Quiz Upload Successful!")
            print("=" * 60)
            print(f"📋 Quiz Title: {quiz_result['quiz_title']}")
            print(f"🆔 Quiz ID: {quiz_result['quiz_id']}")
            print(f"📊 Questions: {quiz_result['successful_uploads']}/{quiz_result['total_questions']}")
            print(f"🔗 Quiz URL: {quiz_result['quiz_url']}")
            print("=" * 60)
        else:
            print("\n❌ Quiz upload failed. Please check the error messages above.")
            
    except Exception as e:
        print(f"\n❌ Error during quiz upload: {e}")
        print("Please check your configuration and try again.")





def create_quiz_question_group(quiz_id, group_name, question_count, points_per_question, course_id=None):
    """
    Create a question group for a quiz using Canvas API
    
    Args:
        quiz_id: The ID of the quiz
        group_name: Name of the question group
        question_count: Number of questions to pick from this group (use question_count for all questions)
        points_per_question: Points per question in this group
        course_id: Course ID (optional, uses default if not provided)
    
    Returns:
        dict: Question group data if successful, None if failed
    """
    if not course_id:
        course_id = COURSE_ID
    
    url = f"{API_URL}/courses/{course_id}/quizzes/{quiz_id}/groups"
    
    group_data = {
        'quiz_groups[][name]': group_name,
        'quiz_groups[][pick_count]': question_count,  # Pick all questions in the group
        'quiz_groups[][question_points]': points_per_question  # Points per question from section title
    }
    
    try:
        response = requests.post(url, headers=headers, data=group_data)
        response.raise_for_status()
        
        result = response.json()
        if 'quiz_groups' in result and len(result['quiz_groups']) > 0:
            group = result['quiz_groups'][0]
            print(f"Created question group: {group['name']} (ID: {group['id']})")
            return group
        else:
            print(f"Failed to create question group: {group_name}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error creating question group '{group_name}': {e}")
        return None

def upload_quiz_from_file(questions_file, quiz_title=None, course_id=None, time_limit=30, published=False):
    """
    Create a Canvas quiz and upload questions from a file.
    
    Args:
        questions_file (str): Path to the questions file
        quiz_title (str): Title for the quiz (defaults to QUIZ_TITLE)
        course_id (str): Canvas course ID (defaults to COURSE_ID)
        time_limit (int): Quiz time limit in minutes (default: 30)
        published (bool): Whether to publish the quiz immediately (default: False)
    
    Returns:
        dict: Quiz information including quiz_id, or None if failed
    """
    try:
        # Use provided parameters or fall back to global defaults
        title = quiz_title or QUIZ_TITLE
        target_course_id = course_id or COURSE_ID
        
        if not target_course_id:
            print("Error: No course ID provided. Set CANVAS_COURSE_ID in .env or pass course_id parameter.")
            return None
        
        # Step 1: Create the quiz
        quiz_payload = {
            'quiz': {
                'title': title,
                'published': published,
                'quiz_type': 'assignment',
                'time_limit': time_limit,
                'shuffle_answers': True
            }
        }

        print(f"Creating quiz: {title}")
        response = requests.post(f'{API_URL}/courses/{target_course_id}/quizzes', headers=headers, json=quiz_payload)
        
        if response.status_code != 200:
            print(f"Failed to create quiz. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        quiz = response.json()
        quiz_id = quiz['id']
        print(f"Created quiz with ID: {quiz_id}")

        # Step 2: Parse questions from file
        print(f"Parsing questions from: {questions_file}")
        
        # Determine which parser to use based on file content and name
        if questions_file.endswith('.md'):
            # Check if it's the CMPE format by looking for specific patterns
            try:
                with open(questions_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Check for CMPE format indicators: separator and answer format
                if '⸻' in content and 'Answer:' in content:
                    questions, section_metadata = parse_questions_cmpe_format(questions_file)
                    print(f"Found {len(questions)} questions (parsed from CMPE format)")
                else:
                    questions, section_metadata = parse_questions_markdown(questions_file)
                    print(f"Found {len(questions)} questions (parsed from standard Markdown)")
            except Exception as e:
                print(f"Error reading file for format detection: {e}")
                questions, section_metadata = parse_questions_markdown(questions_file)
                print(f"Found {len(questions)} questions (parsed from standard Markdown)")
        else:
            questions = parse_questions(questions_file)
            section_metadata = {}  # No metadata for text format
            print(f"Found {len(questions)} questions (parsed from text format)")

        # Step 3: Create question groups for each question type
        print("Creating question groups...")
        question_groups = {}
        
        # Group questions by type
        questions_by_type = {
            'true_false_question': [],
            'multiple_choice_question': [],
            'short_answer_question': [],
            'essay_question': []
        }
        
        for q in questions:
            q_type = q['question_type']
            if q_type in questions_by_type:
                questions_by_type[q_type].append(q)
        
        # Create Canvas question groups for each type that has questions
        group_name_mapping = {
            'true_false_question': 'True/False Questions',
            'multiple_choice_question': 'Multiple Choice Questions',
            'short_answer_question': 'Short Answer Questions',
            'essay_question': 'Essay Questions'
        }
        
        for q_type, type_questions in questions_by_type.items():
            if type_questions:  # Only create group if there are questions of this type
                group_name = group_name_mapping[q_type]
                question_count = len(type_questions)
                points_per_question = section_metadata.get(q_type, 1)  # Default to 1 if not found
                group = create_quiz_question_group(quiz_id, group_name, question_count, points_per_question, target_course_id)
                if group:
                    question_groups[q_type] = group['id']
                    print(f"Created group '{group_name}' with {len(type_questions)} questions ({points_per_question} points each)")
                else:
                    print(f"Warning: Failed to create group for {q_type}")

        # Step 4: Upload questions
        successful_uploads = 0
        for i, q in enumerate(questions, 1):
            # Base question payload
            question_data = {
                'question_name': f"Question {i}",
                'question_text': q['question_text'],
                'question_type': q['question_type'],
                'points_possible': q.get('points_possible', 1)
            }
            
            # Assign question to its group if group was created successfully
            q_type = q['question_type']
            if q_type in question_groups:
                question_data['quiz_group_id'] = question_groups[q_type]
            
            # Add type-specific data
            if q['question_type'] in ['multiple_choice_question', 'true_false_question']:
                if 'answers' in q:
                    question_data['answers'] = q['answers']
                else:
                    # For questions parsed from Markdown without predefined answers
                    # Create default answers based on question type
                    if q['question_type'] == 'true_false_question':
                        question_data['answers'] = [
                            {'answer_text': 'True', 'answer_weight': 100},
                            {'answer_text': 'False', 'answer_weight': 0}
                        ]
                    elif q['question_type'] == 'multiple_choice_question':
                        # For multiple choice without predefined answers, make it a short answer instead
                        question_data['question_type'] = 'short_answer_question'
            elif q['question_type'] == 'short_answer_question':
                # Short answer questions don't need predefined answers in Canvas
                # But we can add a sample answer as a comment if provided
                if 'sample_answer' in q:
                    question_data['neutral_comments'] = f"Sample answer: {q['sample_answer']}"
            elif q['question_type'] == 'essay_question':
                # Essay questions don't need predefined answers
                # But we can add a sample answer as a comment if provided
                if 'sample_answer' in q:
                    question_data['neutral_comments'] = f"Sample answer: {q['sample_answer']}"
            
            question_payload = {'question': question_data}

            r = requests.post(
                f'{API_URL}/courses/{target_course_id}/quizzes/{quiz_id}/questions',
                headers=headers,
                json=question_payload
            )
            
            if r.status_code == 200:
                successful_uploads += 1
                question_type_display = q['question_type'].replace('_', ' ').title()
                print(f"✓ Uploaded question {i}/{len(questions)} ({question_type_display})")
            else:
                print(f"✗ Failed to add question {i}: {q['question_text'][:50]}...")
                print(f"  Status: {r.status_code}, Response: {r.text[:100]}")

        print(f"\nQuiz upload completed: {successful_uploads}/{len(questions)} questions uploaded successfully!")
        
        return {
            'quiz_id': quiz_id,
            'quiz_title': title,
            'total_questions': len(questions),
            'successful_uploads': successful_uploads,
            'quiz_url': f'{API_URL.replace("/api/v1", "")}/courses/{target_course_id}/quizzes/{quiz_id}'
        }
        
    except FileNotFoundError:
        print(f"Error: Questions file '{questions_file}' not found.")
        return None
    except Exception as e:
        print(f"Error uploading quiz: {e}")
        return None

# Example usage - uncomment to use
# quiz_result = upload_quiz_from_file("quiz_questions.txt", "My Custom Quiz", time_limit=45)
# if quiz_result:
#     print(f"Quiz created successfully! Visit: {quiz_result['quiz_url']}")

# Example usage of the Canvas API testing function

def get_course_students(course_id):
    """
    Fetch all students enrolled in a course.
    
    Args:
        course_id (str): The Canvas course ID
        
    Returns:
        list: List of student dictionaries with their information
    """
    try:
        students = []
        url = f"{API_URL}/courses/{course_id}/users"
        params = {
            'enrollment_type[]': 'student',
            'per_page': 100,
            'include[]': ['email', 'enrollments']
        }
        
        while url:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            page_students = response.json()
            students.extend(page_students)
            
            # Check for next page
            if 'next' in response.links:
                url = response.links['next']['url']
                params = {}  # Clear params for subsequent requests
            else:
                url = None
        
        print(f"✅ Found {len(students)} students in the course")
        return students
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching students: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def get_course_assignments(course_id):
    """
    Fetch all assignments for a course.
    
    Args:
        course_id (str): The Canvas course ID
        
    Returns:
        list: List of assignment dictionaries
    """
    try:
        assignments = []
        url = f"{API_URL}/courses/{course_id}/assignments"
        params = {
            'per_page': 100,
            'include[]': ['submission']
        }
        
        while url:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            page_assignments = response.json()
            assignments.extend(page_assignments)
            
            # Check for next page
            if 'next' in response.links:
                url = response.links['next']['url']
                params = {}  # Clear params for subsequent requests
            else:
                url = None
        
        print(f"✅ Found {len(assignments)} assignments in the course")
        return assignments
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching assignments: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def get_assignment_submissions(course_id, assignment_id):
    """
    Fetch all submissions for a specific assignment.
    
    Args:
        course_id (str): The Canvas course ID
        assignment_id (str): The Canvas assignment ID
        
    Returns:
        list: List of submission dictionaries
    """
    try:
        submissions = []
        url = f"{API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions"
        params = {
            'per_page': 100,
            'include[]': ['user', 'attachments']
        }
        
        while url:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            page_submissions = response.json()
            submissions.extend(page_submissions)
            
            # Check for next page
            if 'next' in response.links:
                url = response.links['next']['url']
                params = {}  # Clear params for subsequent requests
            else:
                url = None
        
        print(f"✅ Found {len(submissions)} submissions for the assignment")
        return submissions
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching submissions: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def download_file(url, local_path):
    """
    Download a file from a URL to a local path.
    
    Args:
        url (str): The URL to download from
        local_path (str): The local file path to save to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading file from {url}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error downloading file: {e}")
        return False


def export_students_to_csv(students, course_name, output_dir="downloads"):
    """
    Export student information to a CSV file.
    
    Args:
        students (list): List of student dictionaries
        course_name (str): Name of the course for file naming
        output_dir (str): Directory to save the CSV file
        
    Returns:
        dict: Result information with file path and count
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        safe_course_name = re.sub(r'[^\w\s-]', '', course_name).strip()
        safe_course_name = re.sub(r'[-\s]+', '-', safe_course_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_course_name}_students_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'name', 'sortable_name', 'short_name', 'email', 'login_id', 'enrollment_state']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for student in students:
                # Get enrollment info
                enrollment_state = 'unknown'
                if 'enrollments' in student and student['enrollments']:
                    enrollment_state = student['enrollments'][0].get('enrollment_state', 'unknown')
                
                writer.writerow({
                    'id': student.get('id', ''),
                    'name': student.get('name', ''),
                    'sortable_name': student.get('sortable_name', ''),
                    'short_name': student.get('short_name', ''),
                    'email': student.get('email', ''),
                    'login_id': student.get('login_id', ''),
                    'enrollment_state': enrollment_state
                })
        
        return {
            'csv_file': filepath,
            'total_students': len(students)
        }
        
    except Exception as e:
        print(f"❌ Error exporting students to CSV: {e}")
        return None


def export_submissions_to_csv(submissions, assignment_name, course_name, output_dir="downloads"):
    """
    Export assignment submissions to a CSV file.
    
    Args:
        submissions (list): List of submission dictionaries
        assignment_name (str): Name of the assignment
        course_name (str): Name of the course
        output_dir (str): Directory to save the CSV file
        
    Returns:
        dict: Result information with file path and count
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        safe_course_name = re.sub(r'[^\w\s-]', '', course_name).strip()
        safe_course_name = re.sub(r'[-\s]+', '-', safe_course_name)
        safe_assignment_name = re.sub(r'[^\w\s-]', '', assignment_name).strip()
        safe_assignment_name = re.sub(r'[-\s]+', '-', safe_assignment_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_course_name}_{safe_assignment_name}_submissions_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'submission_id', 'user_id', 'user_name', 'user_email', 
                'submitted_at', 'score', 'grade', 'workflow_state', 
                'submission_type', 'body', 'url', 'attachment_count', 'attachment_files'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for submission in submissions:
                # Get user info
                user = submission.get('user', {})
                
                # Get attachment info
                attachments = submission.get('attachments', [])
                attachment_files = []
                if attachments:
                    for att in attachments:
                        attachment_files.append(f"{att.get('filename', 'unknown')} ({att.get('url', 'no-url')})")
                
                writer.writerow({
                    'submission_id': submission.get('id', ''),
                    'user_id': user.get('id', ''),
                    'user_name': user.get('name', ''),
                    'user_email': user.get('email', ''),
                    'submitted_at': submission.get('submitted_at', ''),
                    'score': submission.get('score', ''),
                    'grade': submission.get('grade', ''),
                    'workflow_state': submission.get('workflow_state', ''),
                    'submission_type': submission.get('submission_type', ''),
                    'body': submission.get('body', ''),
                    'url': submission.get('url', ''),
                    'attachment_count': len(attachments),
                    'attachment_files': '; '.join(attachment_files)
                })
        
        return {
            'csv_file': filepath,
            'total_submissions': len(submissions)
        }
        
    except Exception as e:
        print(f"❌ Error exporting submissions to CSV: {e}")
        return None


def download_submission_files(submissions, assignment_name, course_name, output_dir="downloads"):
    """
    Download all submission files for an assignment.
    
    Args:
        submissions (list): List of submission dictionaries
        assignment_name (str): Name of the assignment
        course_name (str): Name of the course
        output_dir (str): Base directory for downloads
        
    Returns:
        dict: Result information with download statistics
    """
    try:
        # Create safe names for directories
        safe_course_name = re.sub(r'[^\w\s-]', '', course_name).strip()
        safe_course_name = re.sub(r'[-\s]+', '-', safe_course_name)
        safe_assignment_name = re.sub(r'[^\w\s-]', '', assignment_name).strip()
        safe_assignment_name = re.sub(r'[-\s]+', '-', safe_assignment_name)
        
        # Create download directory structure
        download_folder = os.path.join(output_dir, safe_course_name, safe_assignment_name)
        os.makedirs(download_folder, exist_ok=True)
        
        successful_downloads = 0
        total_files = 0
        
        for submission in submissions:
            user = submission.get('user', {})
            user_name = user.get('name', f"User_{submission.get('user_id', 'unknown')}")
            safe_user_name = re.sub(r'[^\w\s-]', '', user_name).strip()
            safe_user_name = re.sub(r'[-\s]+', '-', safe_user_name)
            
            # Create user directory
            user_folder = os.path.join(download_folder, safe_user_name)
            os.makedirs(user_folder, exist_ok=True)
            
            # Download attachments
            attachments = submission.get('attachments', [])
            for attachment in attachments:
                total_files += 1
                filename = attachment.get('filename', f'file_{attachment.get("id", "unknown")}')
                file_url = attachment.get('url')
                
                if file_url:
                    local_path = os.path.join(user_folder, filename)
                    if download_file(file_url, local_path):
                        successful_downloads += 1
                        print(f"✅ Downloaded: {filename} for {user_name}")
                    else:
                        print(f"❌ Failed to download: {filename} for {user_name}")
        
        return {
            'download_folder': download_folder,
            'successful_downloads': successful_downloads,
            'total_files': total_files
        }
        
    except Exception as e:
        print(f"❌ Error downloading submission files: {e}")
        return None


def interactive_canvas_data_operations():
    """
    Complete interactive Canvas data operations process.
    Allows downloading student information and assignment submissions.
    """
    print("📊 Interactive Canvas Data Operations")
    print("=" * 60)
    
    # Step 1: Select course
    print("Step 1: Course Selection")
    course_id = interactive_course_selection()
    if not course_id:
        return
    
    # Get course name for file naming
    try:
        course_response = requests.get(f"{API_URL}/courses/{course_id}", headers=headers)
        course_name = course_response.json().get('name', f'Course_{course_id}') if course_response.status_code == 200 else f'Course_{course_id}'
    except:
        course_name = f'Course_{course_id}'
    
    # Step 2: Select operation
    print("\nStep 2: Data Operation Selection")
    print("=" * 60)
    print("📋 Available operations:")
    print("1. Download all student information to CSV")
    print("2. Download assignment submissions to CSV and files")
    print("-" * 60)
    
    while True:
        choice = input("📊 Select operation (1-2) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            print("👋 Operation cancelled.")
            return
        
        if choice == '1':
            # Download student information
            print("\n" + "=" * 60)
            print("👥 Downloading Student Information...")
            print("=" * 60)
            print(f"📚 Course: {course_name}")
            print(f"🆔 Course ID: {course_id}")
            print("-" * 60)
            
            try:
                students = get_course_students(course_id)
                if students:
                    result = export_students_to_csv(students, course_name)
                    if result:
                        print("\n🎉 Student Information Download Successful!")
                        print("=" * 60)
                        print(f"📊 Total students: {result['total_students']}")
                        print(f"📁 CSV file: {result['csv_file']}")
                        print("=" * 60)
                    else:
                        print("\n❌ Failed to export student information to CSV.")
                else:
                    print("\n❌ No students found or failed to fetch student data.")
                    
            except Exception as e:
                print(f"\n❌ Error during student information download: {e}")
            
            break
            
        elif choice == '2':
            # Download assignment submissions
            print("\nStep 3: Assignment Selection")
            assignment_id = interactive_assignment_selection(course_id)
            if not assignment_id:
                return
            
            # Get assignment name
            try:
                assignment_response = requests.get(f"{API_URL}/courses/{course_id}/assignments/{assignment_id}", headers=headers)
                assignment_name = assignment_response.json().get('name', f'Assignment_{assignment_id}') if assignment_response.status_code == 200 else f'Assignment_{assignment_id}'
            except:
                assignment_name = f'Assignment_{assignment_id}'
            
            print("\n" + "=" * 60)
            print("📝 Downloading Assignment Submissions...")
            print("=" * 60)
            print(f"📚 Course: {course_name}")
            print(f"📋 Assignment: {assignment_name}")
            print(f"🆔 Assignment ID: {assignment_id}")
            print("-" * 60)
            
            try:
                submissions = get_assignment_submissions(course_id, assignment_id)
                if submissions:
                    # Export to CSV
                    csv_result = export_submissions_to_csv(submissions, assignment_name, course_name)
                    
                    # Download files
                    download_result = download_submission_files(submissions, assignment_name, course_name)
                    
                    if csv_result and download_result:
                        print("\n🎉 Assignment Submissions Download Successful!")
                        print("=" * 60)
                        print(f"📊 Total submissions: {csv_result['total_submissions']}")
                        print(f"📁 CSV file: {csv_result['csv_file']}")
                        print(f"📂 Files downloaded: {download_result['successful_downloads']}/{download_result['total_files']}")
                        print(f"📁 Download folder: {download_result['download_folder']}")
                        print("=" * 60)
                    else:
                        print("\n❌ Failed to complete assignment submissions download.")
                else:
                    print("\n❌ No submissions found or failed to fetch submission data.")
                    
            except Exception as e:
                print(f"\n❌ Error during assignment submissions download: {e}")
            
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 'q'.")


def interactive_main_menu():
    """
    Interactive main menu for selecting Canvas operations.
    """
    print("🎓 Canvas Management Tool")
    print("=" * 60)
    print("📋 Available operations:")
    print("1. 📝 Interactive Quiz Upload")
    print("2. 📊 Canvas Data Operations (Students & Assignments)")
    print("3. 🔧 Test API Connection & List Courses")
    print("4. ❌ Exit")
    print("-" * 60)
    
    while True:
        choice = input("🎯 Select operation (1-4): ").strip()
        
        if choice == '1':
            print("\n" + "=" * 60)
            interactive_quiz_upload()
            break
        elif choice == '2':
            print("\n" + "=" * 60)
            interactive_canvas_data_operations()
            break
        elif choice == '3':
            print("\n" + "=" * 60)
            print("🔧 Testing Canvas API Connection...")
            print("=" * 60)
            try:
                success = test_canvas_api()
                if success:
                    print("\n✅ Canvas API test completed successfully!")
                    print("You can now use any of the course IDs listed above.")
                else:
                    print("\n❌ Canvas API test failed. Please check your .env file configuration.")
            except ValueError as e:
                print(f"\n❌ Configuration Error: {e}")
                print("\nSetup Instructions:")
                print("1. Copy .env.example to .env: cp .env.example .env")
                print("2. Edit .env file with your Canvas credentials")
            break
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    import sys
    
    # Check if user wants to upload a quiz directly
    if len(sys.argv) > 1 and sys.argv[1] == "upload":
        if len(sys.argv) < 3:
            print("Usage: python canvas_main.py upload <questions_file> [quiz_title] [time_limit]")
            print("Example: python canvas_main.py upload sample_mixed_questions.txt 'My Quiz' 60")
            print("Example: python canvas_main.py upload cmpe257_exam_questions.md 'CMPE257 Exam' 90")
            sys.exit(1)
        
        questions_file = sys.argv[2]
        quiz_title = sys.argv[3] if len(sys.argv) > 3 else None
        time_limit = int(sys.argv[4]) if len(sys.argv) > 4 else 30
        
        print(f"Uploading quiz from: {questions_file}")
        print("=" * 50)
        
        quiz_result = upload_quiz_from_file(questions_file, quiz_title, time_limit=time_limit)
        if quiz_result:
            print(f"\nQuiz created successfully!")
            print(f"Quiz Title: {quiz_result['quiz_title']}")
            print(f"Quiz ID: {quiz_result['quiz_id']}")
            print(f"Questions: {quiz_result['successful_uploads']}/{quiz_result['total_questions']}")
            print(f"Visit: {quiz_result['quiz_url']}")
        else:
            print("\nFailed to create quiz. Please check your configuration and try again.")
            sys.exit(1)
    
    elif len(sys.argv) > 1 and sys.argv[1] == "quiz":
        # Direct quiz upload mode
        interactive_quiz_upload()
    
    elif len(sys.argv) > 1 and sys.argv[1] == "data":
        # Direct data operations mode
        interactive_canvas_data_operations()
    
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Direct API test mode
        print("🔧 Testing Canvas API Connection...")
        print("=" * 50)
        try:
            success = test_canvas_api()
            if success:
                print("\n✅ Canvas API test completed successfully!")
            else:
                print("\n❌ Canvas API test failed.")
        except ValueError as e:
            print(f"\n❌ Configuration Error: {e}")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "help":
        # Help mode
        print("🎓 Canvas Management Tool - Help")
        print("=" * 60)
        print("Available command line modes:")
        print("1. python canvas_main.py                    - Interactive main menu (recommended)")
        print("2. python canvas_main.py quiz               - Direct quiz upload")
        print("3. python canvas_main.py data               - Direct data operations")
        print("4. python canvas_main.py test               - Test API connection")
        print("5. python canvas_main.py upload <file>      - Direct upload with args")
        print("6. python canvas_main.py help               - Show this help")
        print("=" * 60)
        print("\nSetup Instructions:")
        print("1. Copy .env.example to .env: cp .env.example .env")
        print("2. Edit .env file with your Canvas credentials:")
        print("   - CANVAS_API_URL: Your Canvas domain")
        print("   - CANVAS_ACCESS_TOKEN: Your Canvas API token")
        print("   - CANVAS_COURSE_ID: Course ID (optional)")
        print("\nTo install dependencies: pip install -r requirements.txt")
    
    else:
        # Default behavior: interactive main menu
        try:
            interactive_main_menu()
        except KeyboardInterrupt:
            print("\n\n👋 Operation cancelled by user. Goodbye!")
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please check your configuration and try again.")