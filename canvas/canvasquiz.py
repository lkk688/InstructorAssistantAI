import requests
import re
import os
from dotenv import load_dotenv

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

def parse_questions_markdown(filename):
    """
    Parse questions from a markdown file with the following format:
    
    ### True/False Questions (T/F) - 2 points each
    **1. T/F: Question text**
    **Answer:** ...
    **Explanation:** ...
    
    ### Multiple Choice Questions (MCQ) - 3 points each
    **13. Question text**
    a) Option A
    b) Option B
    c) Option C
    d) Option D
    **Answer:** ...
    **Explanation:** ...
    
    ### Short Answer Questions - 4 points each
    1. **Topic**
       Question text
       **Answer:** ...
       **Explanation:** ...
       
    Returns:
        tuple: (questions_list, section_metadata_dict)
    """
    with open(filename, 'r') as f:
        content = f.read()
    
    # Group questions by type
    question_groups = {
        'true_false_question': [],
        'multiple_choice_question': [],
        'short_answer_question': []
    }
    
    # Track section metadata (points per question type)
    section_metadata = {}
    
    lines = content.split('\n')
    current_section = None
    current_points = 1  # default points
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for section headers
        if line.startswith('### '):
            section_title = line[4:].strip().lower()
            
            # Extract points from section title
            import re
            points_match = re.search(r'(\d+)\s*points?\s*each', section_title)
            current_points = int(points_match.group(1)) if points_match else 1
            
            if 'true/false' in section_title or 't/f' in section_title:
                current_section = 'true_false_question'
                section_metadata['true_false_question'] = current_points
            elif 'multiple choice' in section_title or 'mcq' in section_title:
                current_section = 'multiple_choice_question'
                section_metadata['multiple_choice_question'] = current_points
            elif 'short answer' in section_title:
                current_section = 'short_answer_question'
                section_metadata['short_answer_question'] = current_points
            else:
                current_section = None
            i += 1
            continue
        
        # Skip empty lines and non-question lines
        if not line or not current_section:
            i += 1
            continue
        
        # Parse questions based on section type
        if current_section == 'true_false_question':
            # Look for T/F questions: **1. T/F: Question text**
            if line.startswith('**') and ('T/F:' in line or 't/f:' in line.lower()):
                # Extract question text after T/F:
                question_text = line
                # Remove markdown formatting and numbering
                question_text = question_text.replace('**', '')
                # Find T/F: and extract everything after it
                tf_index = question_text.lower().find('t/f:')
                if tf_index != -1:
                    question_text = question_text[tf_index + 4:].strip()
                    
                    # Look for the answer in the following lines
                    correct_answer = None
                    j = i + 1
                    while j < len(lines) and j < i + 10:  # Look ahead up to 10 lines
                        answer_line = lines[j].strip()
                        if answer_line.startswith('**Answer:**'):
                            answer_text = answer_line.replace('**Answer:**', '').strip()
                            correct_answer = answer_text.lower() in ['true', 't', '1', 'yes']
                            break
                        j += 1
                    
                    # Create answers array with correct answer marked
                    answers = [
                        {"answer_text": "True", "weight": 100 if correct_answer else 0},
                        {"answer_text": "False", "weight": 0 if correct_answer else 100}
                    ]
                    
                    question_groups['true_false_question'].append({
                        "question_text": question_text,
                        "question_type": "true_false_question",
                        "points_possible": current_points,
                        "answers": answers
                    })
        
        elif current_section == 'multiple_choice_question':
            # Look for MCQ questions: **13. Question text**
            if line.startswith('**') and line.endswith('**') and not line.startswith('**Answer:') and not line.startswith('**Explanation:'):
                question_text = line.replace('**', '')
                # Remove numbering (e.g., "13. ")
                import re
                question_text = re.sub(r'^\d+\.\s*', '', question_text)
                
                # Collect answer options - handle both formats: a), b), c), d) and A., B., C., D.
                j = i + 1
                answer_options = []
                correct_answer_text = None
                option_format = None  # Track which format is being used
                
                while j < len(lines):
                    option_line = lines[j].strip()
                    
                    # Check for lowercase format: a), b), c), d)
                    if option_line.startswith(('a)', 'b)', 'c)', 'd)')):
                        answer_options.append(option_line[2:].strip())
                        option_format = 'lowercase_paren'
                        j += 1
                    # Check for uppercase format: A), B), C), D)
                    elif option_line.startswith(('A)', 'B)', 'C)', 'D)')):
                        answer_options.append(option_line[2:].strip())
                        option_format = 'uppercase_paren'
                        j += 1
                    # Check for uppercase dot format: A., B., C., D.
                    elif option_line.startswith(('A.', 'B.', 'C.', 'D.')):
                        answer_options.append(option_line[2:].strip())
                        option_format = 'uppercase_dot'
                        j += 1
                    # Check for lowercase dot format: a., b., c., d.
                    elif option_line.startswith(('a.', 'b.', 'c.', 'd.')):
                        answer_options.append(option_line[2:].strip())
                        option_format = 'lowercase_dot'
                        j += 1
                    elif option_line.startswith('**Answer:**'):
                        # Extract the correct answer (e.g., "b) [-1, 1]" or "C" or "b)")
                        answer_text = option_line.replace('**Answer:**', '').strip()
                        correct_answer_text = answer_text
                        break
                    else:
                        j += 1
                
                if answer_options and correct_answer_text:
                    # Parse the correct answer to find which option is correct
                    correct_option_letter = None
                    if correct_answer_text and len(correct_answer_text) > 0:
                        # Handle different answer formats: "b)", "C", "b) [-1, 1]", etc.
                        first_char = correct_answer_text[0].lower()
                        if first_char in ['a', 'b', 'c', 'd']:
                            correct_option_letter = first_char
                    
                    # Create Canvas API format answers with weights
                    canvas_answers = []
                    option_letters = ['a', 'b', 'c', 'd']
                    
                    for idx, option_text in enumerate(answer_options):
                        if idx < len(option_letters):
                            is_correct = option_letters[idx] == correct_option_letter
                            canvas_answers.append({
                                "answer_text": option_text,
                                "weight": 100 if is_correct else 0
                            })
                    
                    question_groups['multiple_choice_question'].append({
                        "question_text": question_text,
                        "question_type": "multiple_choice_question",
                        "answers": canvas_answers,
                        "points_possible": current_points
                    })
                elif answer_options:  # Fallback for questions without answers
                    question_groups['multiple_choice_question'].append({
                        "question_text": question_text,
                        "question_type": "multiple_choice_question",
                        "answer_options": answer_options,
                        "points_possible": current_points
                    })
        
        elif current_section == 'short_answer_question':
            # Look for short answer questions in multiple formats:
            # Format 1: number. **Question text**
            # Format 2: **number. Question text**
            import re
            
            # Format 1: number. **Question text**
            if re.match(r'^\d+\.\s*\*\*.*\*\*$', line):
                # Extract question text from between ** markers
                question_match = re.search(r'\*\*(.*?)\*\*', line)
                if question_match:
                    question_text = question_match.group(1).strip()
                    question_groups['short_answer_question'].append({
                        "question_text": question_text,
                        "question_type": "short_answer_question",
                        "points_possible": current_points
                    })
            
            # Format 2: **number. Question text**
            elif line.startswith('**') and line.endswith('**') and not line.startswith('**Answer:') and not line.startswith('**Explanation:'):
                # Check if this line contains a numbered question
                line_content = line.replace('**', '').strip()
                if re.match(r'^\d+\.\s+', line_content):
                    # Remove the number and extract question text
                    question_text = re.sub(r'^\d+\.\s+', '', line_content)
                    question_groups['short_answer_question'].append({
                        "question_text": question_text,
                        "question_type": "short_answer_question",
                        "points_possible": current_points
                    })
        
        i += 1
    
    # Flatten the grouped questions into a single list, maintaining type grouping
    questions = []
    for question_type in ['true_false_question', 'multiple_choice_question', 'short_answer_question']:
        questions.extend(question_groups[question_type])
    
    return questions, section_metadata

def parse_questions(filename):
    """
    Parse questions from a text file supporting multiple question types:
    
    Multiple Choice:
    Q: Question text
    A) Answer option A
    B) Answer option B
    C) Answer option C
    D) Answer option D
    Answer: A
    
    True/False:
    Q: Question text
    Type: true_false
    Answer: True
    
    Short Answer/Essay:
    Q: Question text
    Type: short_answer
    Answer: Sample answer (optional)
    
    Essay:
    Q: Question text
    Type: essay
    Answer: Sample answer (optional)
    """
    with open(filename, 'r') as f:
        content = f.read()

    questions = []
    raw_questions = re.split(r'\n\s*\n', content.strip())
    
    for block in raw_questions:
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        if not lines:
            continue
            
        question_text = lines[0].split("Q:")[1].strip()
        
        # Check if question type is specified
        question_type = "multiple_choice_question"  # default
        type_line = None
        answer_line = None
        
        for i, line in enumerate(lines[1:], 1):
            if line.startswith("Type:"):
                type_spec = line.split("Type:")[1].strip().lower()
                if type_spec == "true_false":
                    question_type = "true_false_question"
                elif type_spec == "short_answer":
                    question_type = "short_answer_question"
                elif type_spec == "essay":
                    question_type = "essay_question"
                type_line = i
            elif line.startswith("Answer:"):
                answer_line = i
                break
        
        question_obj = {
            "question_text": question_text,
            "question_type": question_type
        }
        
        if question_type == "multiple_choice_question":
            # Parse multiple choice answers
            answer_lines = []
            for line in lines[1:]:
                if line.startswith("Answer:"):
                    break
                if re.match(r'^[A-Z]\)', line):
                    answer_lines.append(line)
            
            correct_answer = lines[-1].split("Answer:")[1].strip()
            correct_index = ord(correct_answer.upper()) - ord('A')
            
            answer_objs = []
            for i, ans in enumerate(answer_lines):
                answer_text = ans[2:].strip()  # Remove "A)", "B)", etc.
                answer_objs.append({
                    "answer_text": answer_text,
                    "weight": 100 if i == correct_index else 0
                })
            
            question_obj["answers"] = answer_objs
            
        elif question_type == "true_false_question":
            # Parse true/false answer
            correct_answer = lines[-1].split("Answer:")[1].strip().lower()
            is_true = correct_answer in ['true', 't', '1', 'yes']
            
            question_obj["answers"] = [
                {"answer_text": "True", "weight": 100 if is_true else 0},
                {"answer_text": "False", "weight": 0 if is_true else 100}
            ]
            
        elif question_type in ["short_answer_question", "essay_question"]:
            # For short answer and essay, we can optionally store a sample answer
            if answer_line:
                sample_answer = lines[answer_line].split("Answer:")[1].strip()
                question_obj["sample_answer"] = sample_answer
        
        questions.append(question_obj)
    
    return questions

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
        
        # Determine which parser to use based on file extension
        if questions_file.endswith('.md'):
            questions, section_metadata = parse_questions_markdown(questions_file)
            print(f"Found {len(questions)} questions (parsed from Markdown)")
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
    else:
        # Default behavior: test API connection
        print("Testing Canvas API connection...")
        print("=" * 50)
        
        try:
            # Test the API connection and list courses
            # Uncomment the line below to filter courses by prefix (e.g., "SP25")
            # success = test_canvas_api(course_prefix="SP25")
            success = test_canvas_api()
            
            if success:
                print("\n" + "=" * 50)
                print("Canvas API test completed successfully!")
                print("You can now use any of the course IDs listed above by setting CANVAS_COURSE_ID in your .env file.")
                print("\nTip: To filter courses by prefix, use: test_canvas_api(course_prefix='SP25')")
                print("\nTo upload a quiz:")
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