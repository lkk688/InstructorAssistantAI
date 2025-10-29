import requests
import re
import os
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

        if isinstance(result, list):
            # Some Canvas responses return a list of quiz groups
            group_candidates = result
        elif isinstance(result, dict) and 'quiz_groups' in result:
            group_candidates = result['quiz_groups']
        else:
            print(f"Unexpected question group response: {result}")
            return None

        if group_candidates:
            group = group_candidates[0]
            if isinstance(group, dict):
                print(f"Created question group: {group.get('name')} (ID: {group.get('id')})")
                return group
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
            'quiz[title]': title,
            'quiz[published]': 'true' if published else 'false',
            'quiz[quiz_type]': 'assignment',
            'quiz[time_limit]': str(time_limit),
            'quiz[shuffle_answers]': 'true'
        }

        print(f"Creating quiz: {title}")
        response = requests.post(
            f'{API_URL}/courses/{target_course_id}/quizzes',
            headers=headers,
            data=quiz_payload
        )
        
        if response.status_code not in (200, 201):
            print(f"Failed to create quiz. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        quiz = response.json()

        # Canvas may wrap the quiz object or return unexpected structures; normalize here
        if isinstance(quiz, dict) and 'quiz' in quiz and isinstance(quiz['quiz'], dict):
            quiz_data = quiz['quiz']
        elif isinstance(quiz, dict):
            quiz_data = quiz
        elif isinstance(quiz, list):
            quiz_data = next((item for item in quiz if isinstance(item, dict) and item.get('title') == title), None)
            if quiz_data is None:
                print(f"Unexpected quiz creation response: {quiz}")
                return None
        else:
            print(f"Unexpected quiz creation response type: {type(quiz)} - {quiz}")
            return None

        if not isinstance(quiz_data, dict):
            print(f"Unexpected quiz creation payload: {quiz_data}")
            return None

        if quiz_data.get('title') != title:
            print(f"Quiz creation did not return the requested title '{title}'. Raw response: {quiz}")
            return None

        quiz_id = quiz_data.get('id')
        if not quiz_id:
            print(f"Quiz ID missing in response: {quiz_data}")
            return None
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
                            {'answer_text': 'True', 'weight': 100},
                            {'answer_text': 'False', 'weight': 0}
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
            
            if r.status_code in (200, 201):
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
if __name__ == "__main__":
    import sys
    
    # Check if user wants to upload a quiz
    if len(sys.argv) > 1 and sys.argv[1] == "upload":
        if len(sys.argv) < 3:
            print("Usage: python canvasquiz.py upload <questions_file> [quiz_title] [time_limit]")
            print("Example: python canvasquiz.py upload sample_mixed_questions.txt 'My Quiz' 60")
            print("Example: python canvasquiz.py upload cmpe257_exam_questions.md 'CMPE257 Exam' 90")
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
    
    elif len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # Interactive mode - similar to frontend experience
        interactive_quiz_upload()
    
    else:
        # Default behavior: test API connection
        print("Canvas Quiz Management Tool")
        print("=" * 50)
        print("Available modes:")
        print("1. python canvasquiz.py                    - Test API connection and list courses")
        print("2. python canvasquiz.py interactive        - Interactive quiz upload (recommended)")
        print("3. python canvasquiz.py upload <file>      - Direct upload with command line args")
        print("=" * 50)
        
        try:
            # Test the API connection and list courses
            print("\nTesting Canvas API connection...")
            print("=" * 50)
            # Uncomment the line below to filter courses by prefix (e.g., "SP25")
            # success = test_canvas_api(course_prefix="SP25")
            success = test_canvas_api()
            
            if success:
                print("\n" + "=" * 50)
                print("Canvas API test completed successfully!")
                print("You can now use any of the course IDs listed above by setting CANVAS_COURSE_ID in your .env file.")
                print("\nRecommended: Use interactive mode for the best experience:")
                print("python canvasquiz.py interactive")
                print("\nOr use direct upload:")
                print("python canvasquiz.py upload sample_mixed_questions.txt 'Test Quiz'")
                print("python canvasquiz.py upload cmpe257_exam_questions.md 'CMPE257 Exam'")
            else:
                print("\n" + "=" * 50)
                print("Canvas API test failed. Please check your .env file configuration.")
                
        except ValueError as e:
            print("\n" + "=" * 50)
            print(f"Configuration Error: {e}")
            print("\nSetup Instructions:")
            print("1. Copy .env.example to .env: cp .env.example .env")
            print("2. Edit .env file with your Canvas credentials:")
            print("   - CANVAS_API_URL: Your Canvas domain (e.g., https://yourschool.instructure.com/api/v1)")
            print("   - CANVAS_ACCESS_TOKEN: Your Canvas API token")
            print("   - CANVAS_COURSE_ID: Course ID (optional, can be set after testing)")
            print("\nTo generate an access token:")
            print("1. Go to your Canvas account settings")
            print("2. Click on 'New Access Token'")
            print("3. Copy the generated token to your .env file")
        print("\nTo install dependencies: pip install -r requirements.txt")
