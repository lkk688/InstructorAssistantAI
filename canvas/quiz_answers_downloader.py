#!/usr/bin/env python3

import requests
import os
import json
import re
import argparse
from dotenv import load_dotenv
from datetime import datetime

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

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

def get_quizzes(course_id=None):
    """
    Get all quizzes for a course
    
    Args:
        course_id: The Canvas course ID (uses default from .env if not provided)
        
    Returns:
        list: List of quiz dictionaries
    """
    target_course_id = course_id or COURSE_ID
    
    if not target_course_id:
        print("Error: No course ID provided. Set CANVAS_COURSE_ID in .env or pass course_id parameter.")
        return []
    
    try:
        all_quizzes = []
        url = f'{API_URL}/courses/{target_course_id}/quizzes'
        params = {'per_page': 100}  # Maximum per page
        
        while url:
            quizzes_response = requests.get(url, headers=headers, params=params)
            
            if quizzes_response.status_code != 200:
                print(f"Failed to fetch quizzes. Status code: {quizzes_response.status_code}")
                print(f"Response: {quizzes_response.text}")
                return []
            
            quizzes = quizzes_response.json()
            all_quizzes.extend(quizzes)
            
            # Check for next page in Link header
            link_header = quizzes_response.headers.get('Link', '')
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
        
        return all_quizzes
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def get_quiz_submissions(course_id, quiz_id):
    """
    Get all submissions for a quiz using the Submissions API to access submission_history
    
    Args:
        course_id: The Canvas course ID
        quiz_id: The Canvas quiz ID
        
    Returns:
        list: List of quiz submission dictionaries
    """
    try:
        # Get the quiz to find the assignment_id
        quiz_response = requests.get(f"{API_URL}/courses/{course_id}/quizzes/{quiz_id}", headers=headers)
        if quiz_response.status_code != 200:
            print(f"Error fetching quiz: {quiz_response.status_code}")
            return []
        
        quiz_data = quiz_response.json()
        assignment_id = quiz_data.get('assignment_id')
        
        if not assignment_id:
            print("No assignment_id found for this quiz")
            return []
        
        all_submissions = []
        url = f'{API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions'
        params = {
            'per_page': 100, 
            'include': ['submission_history'],
        }  # Use Submissions API to get submission_history with student answers
        
        print(f"Getting submissions via Submissions API with include: {params['include']}")
        
        while url:
            submissions_response = requests.get(url, headers=headers, params=params)
            
            if submissions_response.status_code != 200:
                print(f"Failed to fetch quiz submissions. Status code: {submissions_response.status_code}")
                print(f"Response: {submissions_response.text}")
                return []
            
            response_data = submissions_response.json()
            # For Submissions API, the response is directly a list of submissions
            if isinstance(response_data, list):
                all_submissions.extend(response_data)
            elif 'quiz_submissions' in response_data:
                all_submissions.extend(response_data['quiz_submissions'])
            
            # Check for next page in Link header
            link_header = submissions_response.headers.get('Link', '')
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
        
        return all_submissions
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def get_quiz_questions(course_id, quiz_id):
    """
    Get all questions for a quiz
    
    Args:
        course_id: The Canvas course ID
        quiz_id: The Canvas quiz ID
        
    Returns:
        list: List of quiz question dictionaries
    """
    try:
        all_questions = []
        url = f'{API_URL}/courses/{course_id}/quizzes/{quiz_id}/questions'
        params = {'per_page': 100}  # Maximum per page
        
        while url:
            questions_response = requests.get(url, headers=headers, params=params)
            
            if questions_response.status_code != 200:
                print(f"Failed to fetch quiz questions. Status code: {questions_response.status_code}")
                print(f"Response: {questions_response.text}")
                return []
            
            questions = questions_response.json()
            all_questions.extend(questions)
            
            # Check for next page in Link header
            link_header = questions_response.headers.get('Link', '')
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
        
        return all_questions
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def get_quiz_submission_questions(quiz_submission_id):
    """
    Get all questions for a quiz submission
    
    Args:
        quiz_submission_id: The Canvas quiz submission ID
        
    Returns:
        list: List of quiz submission question dictionaries
    """
    try:
        all_questions = []
        url = f'{API_URL}/quiz_submissions/{quiz_submission_id}/questions'
        params = {'per_page': 100, 'include': ['quiz_question', 'submission', 'user', 'submission_data']}  # Include quiz question data, submission data, and user data
        
        print(f"Fetching quiz submission questions for submission ID: {quiz_submission_id}")
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        while url:
            questions_response = requests.get(url, headers=headers, params=params)
            
            if questions_response.status_code != 200:
                print(f"Failed to fetch quiz submission questions. Status code: {questions_response.status_code}")
                print(f"Response: {questions_response.text}")
                return []
            
            response_data = questions_response.json()
            print(f"Response structure: {list(response_data.keys())}")
            
            if 'quiz_submission_questions' in response_data:
                print(f"Found {len(response_data['quiz_submission_questions'])} submission questions")
                # Print first question structure (if available)
                if response_data['quiz_submission_questions']:
                    first_q = response_data['quiz_submission_questions'][0]
                    print(f"First question keys: {list(first_q.keys())}")
                    if 'answer' in first_q:
                        print(f"Answer type: {type(first_q['answer'])}, Preview: {str(first_q['answer'])[:100]}")
                    if 'answered' in first_q:
                        print(f"Question answered: {first_q['answered']}")
                    if 'submission_data' in first_q:
                        print(f"Submission data available: {bool(first_q['submission_data'])}")
                    if 'user_answer' in first_q:
                        print(f"User answer available: {bool(first_q['user_answer'])}")
                all_questions.extend(response_data['quiz_submission_questions'])
            
            # Check for next page in Link header
            link_header = questions_response.headers.get('Link', '')
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
        
        return all_questions
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def get_students(course_id=None):
    """
    Get all students for a course
    
    Args:
        course_id: The Canvas course ID (uses default from .env if not provided)
        
    Returns:
        list: List of student dictionaries
    """
    target_course_id = course_id or COURSE_ID
    
    if not target_course_id:
        print("Error: No course ID provided. Set CANVAS_COURSE_ID in .env or pass course_id parameter.")
        return []
    
    try:
        all_students = []
        url = f'{API_URL}/courses/{target_course_id}/users'
        params = {'per_page': 100, 'enrollment_type': 'student'}  # Only get students
        
        while url:
            students_response = requests.get(url, headers=headers, params=params)
            
            if students_response.status_code != 200:
                print(f"Failed to fetch students. Status code: {students_response.status_code}")
                print(f"Response: {students_response.text}")
                return []
            
            students = students_response.json()
            all_students.extend(students)
            
            # Check for next page in Link header
            link_header = students_response.headers.get('Link', '')
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
        
        return all_students
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def format_answer_for_markdown(question_type, answer, question_data=None):
    """
    Format a student's answer for markdown output based on question type
    
    Args:
        question_type: The type of question (multiple_choice_question, essay_question, etc.)
        answer: The student's answer
        question_data: The question data containing answer options (optional)
        
    Returns:
        str: Formatted answer for markdown
    """
    if answer is None:
        return "*No answer provided*"
    
    if question_type == 'multiple_choice_question':
        # For multiple choice, convert option ID to letter choice (A, B, C, D)
        if question_data and 'answers' in question_data:
            # Create mapping from option ID to letter
            option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
            id_to_letter = {}
            for idx, option in enumerate(question_data['answers']):
                if idx < len(option_letters):
                    id_to_letter[option['id']] = option_letters[idx]
            
            if isinstance(answer, list):
                letters = [id_to_letter.get(int(ans), f"Option {ans}") for ans in answer]
                return ', '.join(letters)
            else:
                return id_to_letter.get(int(answer), f"Option {answer}")
        else:
            # Fallback if no question data available
            if isinstance(answer, list):
                return f"Selected option ID(s): {', '.join(map(str, answer))}"
            return f"Selected option ID: {answer}"
    
    elif question_type == 'true_false_question':
        # For true/false, convert option ID to True/False
        if question_data and 'answers' in question_data:
            # Find which option corresponds to True/False
            for option in question_data['answers']:
                if option['id'] == int(answer):
                    option_text = option.get('text', '').strip().lower()
                    if 'true' in option_text:
                        return "True"
                    elif 'false' in option_text:
                        return "False"
            # Fallback - check if answer is numeric and map to True/False
            try:
                answer_int = int(answer)
                # Typically first option is True, second is False, but this varies
                if len(question_data['answers']) >= 2:
                    first_option = question_data['answers'][0]
                    if first_option['id'] == answer_int:
                        first_text = first_option.get('text', '').strip().lower()
                        return "True" if 'true' in first_text else "False"
                    else:
                        second_text = question_data['answers'][1].get('text', '').strip().lower()
                        return "True" if 'true' in second_text else "False"
            except (ValueError, IndexError):
                pass
        
        # Fallback for boolean or string answers
        if isinstance(answer, bool):
            return "True" if answer else "False"
        answer_str = str(answer).lower()
        if answer_str in ['true', '1']:
            return "True"
        elif answer_str in ['false', '0']:
            return "False"
        return str(answer)
    
    elif question_type in ['essay_question', 'short_answer_question']:
        # For essay and short answer, return the text
        if isinstance(answer, str):
            # Ensure proper markdown formatting for multi-line text
            formatted = answer.strip()
            if '\n' in formatted:
                return f"\n```\n{formatted}\n```"
            return formatted
        return str(answer)
    
    elif question_type == 'matching_question':
        # For matching questions, format the matches
        if isinstance(answer, list):
            matches = [f"{match.get('answer_id')}: {match.get('match_id')}" for match in answer]
            return "\n- " + "\n- ".join(matches)
        return str(answer)
    
    # Default case for other question types
    return str(answer)

def generate_quiz_answers_markdown(course_id, quiz_id, output_file=None):
    """
    Generate a markdown file with all student answers for a quiz
    
    Args:
        course_id: The Canvas course ID
        quiz_id: The Canvas quiz ID
        output_file: The output file path (optional, defaults to quiz_answers_{quiz_id}.md)
        
    Returns:
        str: Path to the generated markdown file
    """
    # Get quiz details
    print(f"Fetching quiz details for quiz ID {quiz_id}...")
    quiz_response = requests.get(f'{API_URL}/courses/{course_id}/quizzes/{quiz_id}', headers=headers)
    if quiz_response.status_code != 200:
        print(f"Failed to fetch quiz details. Status code: {quiz_response.status_code}")
        return None
    
    quiz = quiz_response.json()
    quiz_title = quiz.get('title', f"Quiz {quiz_id}")
    
    # Get all questions for this quiz
    print("Fetching quiz questions...")
    questions = get_quiz_questions(course_id, quiz_id)
    questions_dict = {q['id']: q for q in questions}
    
    # Get all submissions for this quiz
    print("Fetching quiz submissions...")
    submissions = get_quiz_submissions(course_id, quiz_id)
    
    # Get all students
    print("Fetching student information...")
    students = get_students(course_id)
    students_dict = {s['id']: s for s in students}
    
    # Create output file name if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"quiz_answers_{quiz_id}_{timestamp}.md"
    
    # Generate markdown content
    print("Generating markdown content...")
    markdown_content = f"# {quiz_title} - Student Answers\n\n"
    markdown_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    markdown_content += f"Course ID: {course_id}\n\n"
    markdown_content += f"Quiz ID: {quiz_id}\n\n"
    markdown_content += f"Total Submissions: {len(submissions)}\n\n"
    markdown_content += "**Note:** If this quiz was administered using Respondus LockDown Browser, some student answers may not be accessible through the Canvas API due to security restrictions. In such cases, you will see messages indicating that answers were submitted but are not accessible.\n\n"
    
    # Add quiz questions section
    markdown_content += "## Quiz Questions\n\n"
    for i, question in enumerate(questions, 1):
        q_text = question.get('question_text', '').strip()
        # Remove HTML tags from question text
        q_text = re.sub(r'<[^>]+>', '', q_text)
        
        markdown_content += f"### Question {i}: {question.get('question_name', f'Question {i}')}\n\n"
        markdown_content += f"**Type**: {question.get('question_type', 'Unknown')}\n\n"
        markdown_content += f"**Text**: {q_text}\n\n"
        
        # Add answer options for multiple choice and true/false questions
        if question.get('question_type') in ['multiple_choice_question', 'true_false_question'] and 'answers' in question:
            markdown_content += "**Options**:\n\n"
            for answer in question.get('answers', []):
                answer_text = answer.get('text', '').strip()
                # Remove HTML tags from answer text
                answer_text = re.sub(r'<[^>]+>', '', answer_text)
                markdown_content += f"- {answer.get('id')}: {answer_text}" + (" (Correct)" if answer.get('weight', 0) > 0 else "") + "\n"
            markdown_content += "\n"
    
    # Add student answers section
    markdown_content += "## Student Answers\n\n"
    
    # Sort submissions by student name if available
    sorted_submissions = sorted(
        submissions, 
        key=lambda s: students_dict.get(s.get('user_id', 0), {}).get('sortable_name', '')
    )
    
    for submission in sorted_submissions:
        user_id = submission.get('user_id')
        student = students_dict.get(user_id, {'name': f"User {user_id}", 'sortable_name': f"User {user_id}"})
        
        markdown_content += f"### {student.get('name')} (ID: {user_id})\n\n"
        markdown_content += f"**Score**: {submission.get('score', 'Not graded')} / {quiz.get('points_possible', 'Unknown')}\n\n"
        markdown_content += f"**Submitted**: {submission.get('finished_at', 'Not completed')}\n\n"
        
        markdown_content += "#### Answers\n\n"
        
        # Process submission_history to extract student answers
        submission_history = submission.get('submission_history', [])
        
        # Get the latest submission attempt
        latest_submission = None
        if submission_history:
            # Get the most recent submission
            latest_submission = submission_history[-1]
        
        # Extract submission_data from the latest submission
        submission_data = []
        if latest_submission and 'submission_data' in latest_submission:
            submission_data = latest_submission['submission_data']
        elif 'submission_data' in submission:
            submission_data = submission['submission_data']
        
        # Create a mapping of question_id to submission answers for quick lookup
        answer_map = {}
        for answer_data in submission_data:
            question_id = answer_data.get('question_id')
            if question_id:
                # Look for answer in various possible fields
                answer_text = None
                if 'answer_id' in answer_data:
                    answer_text = answer_data['answer_id']
                elif 'text' in answer_data:
                    answer_text = answer_data['text']
                elif 'answer' in answer_data:
                    answer_text = answer_data['answer']
                
                if answer_text is not None:
                    answer_map[question_id] = {
                        'answer': answer_text,
                        'correct': answer_data.get('correct', False),
                        'points': answer_data.get('points', 0)
                    }
        
        for i, question in enumerate(questions, 1):
            q_id = question.get('id')
            q_type = question.get('question_type')
            
            # Get question type display name
            type_display = {
                'multiple_choice_question': 'Multiple Choice',
                'true_false_question': 'True/False',
                'short_answer_question': 'Short Answer',
                'essay_question': 'Essay',
                'numerical_question': 'Numerical Answer',
                'matching_question': 'Matching',
                'fill_in_multiple_blanks_question': 'Fill in the Blanks',
                'multiple_answers_question': 'Multiple Answers',
                'multiple_dropdowns_question': 'Multiple Dropdowns'
            }.get(q_type, q_type.replace('_', ' ').title() if q_type else 'Unknown')
            
            # Look for this question's answer in the answer_map
            if q_id in answer_map:
                answer_info = answer_map[q_id]
                formatted_answer = format_answer_for_markdown(q_type, answer_info['answer'], question)
                markdown_content += f"**Question {i} ({type_display})**: {formatted_answer}\n\n"
            else:
                # Check if the quiz has a score, which would indicate an answer was submitted
                if submission.get('score') is not None and submission.get('score') > 0:
                    markdown_content += f"**Question {i} ({type_display})**: *Answer submitted but not accessible (likely due to Respondus LockDown Browser restrictions)*\n\n"
                else:
                    markdown_content += f"**Question {i} ({type_display})**: *No answer found*\n\n"
    
    # Write markdown content to file
    with open(output_file, 'w') as f:
        f.write(markdown_content)
    
    print(f"\nMarkdown file generated: {output_file}")
    return output_file

def list_quizzes(course_id=None):
    """
    List all quizzes for a course
    
    Args:
        course_id: The Canvas course ID (uses default from .env if not provided)
    """
    target_course_id = course_id or COURSE_ID
    
    if not target_course_id:
        print("Error: No course ID provided. Set CANVAS_COURSE_ID in .env or pass course_id parameter.")
        return
    
    quizzes = get_quizzes(target_course_id)
    
    if not quizzes:
        print(f"No quizzes found for course ID {target_course_id}.")
        return
    
    print(f"\nQuizzes for course ID {target_course_id}:\n")
    print(f"{'Quiz ID':<10} {'Title':<50} {'Questions':<10} {'Points':<10}")
    print("-" * 80)
    
    for quiz in quizzes:
        quiz_id = quiz.get('id', 'N/A')
        title = quiz.get('title', 'Untitled Quiz')[:47] + '...' if len(quiz.get('title', '')) > 50 else quiz.get('title', 'Untitled Quiz')
        question_count = quiz.get('question_count', 'N/A')
        points_possible = quiz.get('points_possible', 'N/A')
        
        print(f"{quiz_id:<10} {title:<50} {question_count:<10} {points_possible:<10}")

def generate_quiz_answers_json(course_id, quiz_id, output_file=None, short_answer_only=False):
    """
    Generate a JSON file with quiz answers, optionally filtering for short answer questions only
    
    Args:
        course_id: The Canvas course ID
        quiz_id: The Canvas quiz ID
        output_file: The output file path (optional, defaults to quiz_answers_{quiz_id}.json)
        short_answer_only: If True, only include short answer and essay questions
        
    Returns:
        str: Path to the generated JSON file
    """
    # Get quiz details
    print(f"Fetching quiz details for quiz ID {quiz_id}...")
    quiz_response = requests.get(f'{API_URL}/courses/{course_id}/quizzes/{quiz_id}', headers=headers)
    if quiz_response.status_code != 200:
        print(f"Failed to fetch quiz details. Status code: {quiz_response.status_code}")
        return None
    
    quiz = quiz_response.json()
    quiz_title = quiz.get('title', f"Quiz {quiz_id}")
    
    # Get all questions for this quiz
    print("Fetching quiz questions...")
    questions = get_quiz_questions(course_id, quiz_id)
    questions_dict = {q['id']: q for q in questions}
    
    # Filter for short answer questions if requested
    if short_answer_only:
        questions = [q for q in questions if q.get('question_type') in ['essay_question', 'short_answer_question']]
        questions_dict = {q['id']: q for q in questions}
        print(f"Filtered to {len(questions)} short answer/essay questions")
    
    # Get all submissions for this quiz
    print("Fetching quiz submissions...")
    submissions = get_quiz_submissions(course_id, quiz_id)
    
    # Get all students
    print("Fetching student information...")
    students = get_students(course_id)
    students_dict = {s['id']: s for s in students}
    
    # Create output file name if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "_short_answer" if short_answer_only else ""
        output_file = f"quiz_answers_{quiz_id}{suffix}_{timestamp}.json"
    
    # Build JSON structure
    print("Generating JSON content...")
    quiz_data = {
        "quiz_info": {
            "quiz_id": quiz_id,
            "course_id": course_id,
            "title": quiz_title,
            "generated_on": datetime.now().isoformat(),
            "short_answer_only": short_answer_only,
            "total_submissions": len(submissions)
        },
        "questions": [],
        "submissions": []
    }
    
    # Add questions to JSON
    for question in questions:
        q_text = question.get('question_text', '').strip()
        q_text = re.sub(r'<[^>]+>', '', q_text)  # Remove HTML tags
        
        question_data = {
            "id": question.get('id'),
            "question_name": question.get('question_name', f"Question {question.get('position', '')}"),
            "question_type": question.get('question_type'),
            "question_text": q_text,
            "points_possible": question.get('points_possible', 0),
            "position": question.get('position')
        }
        
        # Add answer options for multiple choice and true/false questions
        if question.get('question_type') in ['multiple_choice_question', 'true_false_question'] and 'answers' in question:
            question_data["answer_options"] = []
            for answer in question.get('answers', []):
                answer_text = answer.get('text', '').strip()
                answer_text = re.sub(r'<[^>]+>', '', answer_text)  # Remove HTML tags
                question_data["answer_options"].append({
                    "id": answer.get('id'),
                    "text": answer_text,
                    "correct": answer.get('weight', 0) > 0
                })
        
        quiz_data["questions"].append(question_data)
    
    # Sort submissions by student name
    sorted_submissions = sorted(
        submissions, 
        key=lambda s: students_dict.get(s.get('user_id', 0), {}).get('sortable_name', '')
    )
    
    # Process submissions
    for submission in sorted_submissions:
        user_id = submission.get('user_id')
        student = students_dict.get(user_id, {})
        
        if not submission.get('submission_history'):
            continue
            
        # Get the latest submission
        latest_submission = submission['submission_history'][-1]
        submission_data = latest_submission.get('submission_data', [])
        
        if not submission_data:
            continue
        
        # Create answer map
        answer_map = {}
        for answer_data in submission_data:
            question_id = answer_data.get('question_id')
            if question_id in questions_dict:
                answer_map[question_id] = answer_data.get('text') or answer_data.get('answer')
        
        # Build submission data
        submission_info = {
            "user_id": user_id,
            "student_name": student.get('name', 'Unknown Student'),
            "sortable_name": student.get('sortable_name', ''),
            "submission_id": submission.get('id'),
            "quiz_submission_id": latest_submission.get('quiz_submission_id'),
            "submitted_at": submission.get('submitted_at'),
            "attempt": submission.get('attempt', 1),
            "answers": []
        }
        
        # Add answers for each question
        for question in questions:
            question_id = question['id']
            answer = answer_map.get(question_id)
            
            answer_info = {
                "question_id": question_id,
                "question_type": question.get('question_type'),
                "question_name": question.get('question_name', f"Question {question.get('position', '')}"),
                "points_possible": question.get('points_possible', 0),
                "student_answer": answer,
                "formatted_answer": format_answer_for_markdown(question.get('question_type'), answer, question) if answer is not None else None,
                "score": None,  # To be filled by AI grading
                "comment": None  # To be filled by AI grading
            }
            
            submission_info["answers"].append(answer_info)
        
        quiz_data["submissions"].append(submission_info)
    
    # Write JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(quiz_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nJSON file generated successfully: {output_file}")
        print(f"Total questions: {len(quiz_data['questions'])}")
        print(f"Total submissions: {len(quiz_data['submissions'])}")
        
        return output_file
        
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        return None

def update_quiz_scores(course_id, quiz_id, scores_file):
    """
    Update quiz submission scores using Canvas API
    
    Args:
        course_id: The Canvas course ID
        quiz_id: The Canvas quiz ID
        scores_file: Path to JSON file containing scores and comments
    """
    try:
        print(f"Loading scores from file: {scores_file}")
        # Load scores from JSON file
        with open(scores_file, 'r', encoding='utf-8') as f:
            scores_data = json.load(f)
        
        print(f"Loaded scores for {len(scores_data.get('submissions', []))} submissions")
        
        # Get quiz submissions to get version information
        print("Fetching quiz submissions to get version information...")
        quiz_submissions_url = f'{API_URL}/courses/{course_id}/quizzes/{quiz_id}/submissions'
        quiz_subs_response = requests.get(quiz_submissions_url, headers=headers)
        
        if quiz_subs_response.status_code != 200:
            print(f"Failed to fetch quiz submissions: {quiz_subs_response.status_code}")
            return
            
        quiz_submissions = quiz_subs_response.json().get('quiz_submissions', [])
        
        # Create a mapping of user_id to quiz submission data (including version)
        quiz_sub_map = {}
        for quiz_sub in quiz_submissions:
            user_id = quiz_sub.get('user_id')
            if user_id:
                quiz_sub_map[user_id] = quiz_sub
        
        print(f"Found {len(quiz_submissions)} quiz submissions from Canvas API")
        print(f"Quiz submission user IDs: {sorted(quiz_sub_map.keys())}")
        
        # Debug: Show students in scores file
        scores_user_ids = [s.get('user_id') for s in scores_data.get('submissions', []) if s.get('user_id')]
        print(f"Found {len(scores_user_ids)} students in scores file")
        print(f"Scores file user IDs: {sorted(scores_user_ids)}")
        
        # Show missing students
        missing_in_quiz = set(scores_user_ids) - set(quiz_sub_map.keys())
        if missing_in_quiz:
            print(f"Students in scores file but NOT in quiz submissions: {sorted(missing_in_quiz)}")
        
        print(f"Processing submissions...")
        
        updated_count = 0
        
        # Process each submission
        for submission_data in scores_data.get('submissions', []):
            user_id = submission_data.get('user_id')
            student_name = submission_data.get('student_name', 'Unknown')
            
            if not user_id:
                print(f"Warning: No user ID found for {student_name}")
                continue
                
            # Get the quiz submission data for this user
            quiz_sub_data = quiz_sub_map.get(user_id)
            if not quiz_sub_data:
                print(f"Warning: No quiz submission found for {student_name}")
                continue
                
            quiz_submission_id = quiz_sub_data.get('id')
            # Use version if available, otherwise fall back to attempt
            version_or_attempt = quiz_sub_data.get('version', quiz_sub_data.get('attempt', 1))
            
            print(f"Processing submission for {student_name} (Quiz Sub ID: {quiz_submission_id}, Version: {version_or_attempt})")
            
            # Prepare questions data for update
            questions_update = {}
            total_score_update = 0
            
            for answer in submission_data.get('answers', []):
                question_id = answer.get('question_id')
                score = answer.get('score')
                comment = answer.get('comment')
                
                if score is not None:
                    questions_update[str(question_id)] = {
                        'score': float(score)  # Ensure score is a number
                    }
                    if comment:
                        questions_update[str(question_id)]['comment'] = comment
                    
                    total_score_update += float(score)
            
            if not questions_update:
                print(f"No scores to update for {student_name}")
                continue
            
            # Prepare request body according to Canvas API documentation
            # Use version instead of attempt to fix the silent failure issue
            request_body = {
                'quiz_submissions': [{
                    'attempt': version_or_attempt,  # Use version number instead of attempt
                    'fudge_points': 0,  # Can be used for overall adjustment
                    'questions': questions_update
                }]
            }
            
            # Make PUT request to update scores using the correct Canvas API endpoint
            url = f'{API_URL}/courses/{course_id}/quizzes/{quiz_id}/submissions/{quiz_submission_id}'
            
            print(f"Updating scores for {student_name} (submission {quiz_submission_id})...")
            print(f"  Questions to update: {len(questions_update)}")
            print(f"  Total points: {total_score_update}")
            print(f"  Using version/attempt: {version_or_attempt}")
            
            response = requests.put(url, headers=headers, json=request_body)
            
            if response.status_code == 200:
                print(f"  ✓ Successfully updated scores for {student_name}")
                updated_count += 1
            else:
                print(f"  ✗ Failed to update scores for {student_name}")
                print(f"    Status code: {response.status_code}")
                print(f"    Response: {response.text[:500]}...")
        
        print(f"\nScore update process completed! Successfully updated {updated_count} submissions.")
        
    except FileNotFoundError:
        print(f"Error: Scores file '{scores_file}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{scores_file}'.")
    except Exception as e:
        print(f"Error updating scores: {e}")

def main():
    parser = argparse.ArgumentParser(description='Download Canvas quiz answers and generate a markdown file for AI grading.')
    parser.add_argument('--course', type=str, default='1615883', help='Canvas course ID (overrides .env setting)')
    parser.add_argument('--quiz', type=str, default='1869206', help='Canvas quiz ID')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--list', action='store_true', help='List all quizzes for the course')
    parser.add_argument('--short-answer-only', action='store_true', help='Filter and save only short answer questions')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown', help='Output format (markdown or json)')
    parser.add_argument('--update-scores', action='store_true', help='Enable score update mode to upload AI-generated scores to Canvas')
    parser.add_argument('--scores-file', type=str, help='JSON file containing AI-generated scores for short answer questions')
    
    args = parser.parse_args()
    
    # Use provided course ID or fall back to .env
    course_id = args.course or COURSE_ID
    
    if not course_id:
        print("Error: No course ID provided. Set CANVAS_COURSE_ID in .env or use --course parameter.")
        return
    
    if args.list:
        list_quizzes(course_id)
        return
    
    if args.update_scores:
        if not args.quiz:
            print("Error: Quiz ID required for score updates. Use --quiz parameter.")
            return
        if not args.scores_file:
            print("Error: Scores file required for score updates. Use --scores-file parameter.")
            return
        update_quiz_scores(course_id, args.quiz, args.scores_file)
        return
    
    if not args.quiz:
        print("Error: No quiz ID provided. Use --quiz parameter.")
        print("\nTo see available quizzes, use --list")
        return
    
    if args.format == 'json':
        generate_quiz_answers_json(course_id, args.quiz, args.output, args.short_answer_only)
    else:
        generate_quiz_answers_markdown(course_id, args.quiz, args.output)

if __name__ == "__main__":
    main()