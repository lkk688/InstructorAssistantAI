"""
Question parsing utilities for Canvas quiz generation.

This module contains various parsers for different question formats:
- Markdown format with sections (parse_questions_markdown)
- Simple text format (parse_questions)
- CMPE format with separators (parse_questions_cmpe_format)
"""

import re
import sys
import os

# Add the canvas directory to the path for importing math_converter
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from math_converter import batch_convert_questions


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
    
    # Convert math equations to Canvas format before returning
    questions = batch_convert_questions(questions)
    
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
    
    # Convert math equations to Canvas format before returning
    questions = batch_convert_questions(questions)
    
    return questions


def parse_questions_cmpe_format(filename):
    """
    Parse questions from CMPE format markdown file with the following structure:
    
    # CMPE 249 Exam Questions
    **FORMAT**: CMPE
    
    ## True/False Questions (T/F) - 2 points each
    
    1. T/F: Question text
    Answer: True/False
    Explanation: ...
    
    ⸻
    
    ## Multiple Choice Questions (MCQ) - 3 points each
    
    1. MCQ: Question text
    a) Option A
    b) Option B
    c) Option C
    d) Option D
    
    Answer: b) Option text
    Explanation: ...
    
    ⸻
    
    Short Answer Questions - 4 points each
    
    Q: Question text
    Answer: Sample answer
    Explanation: ...
    
    ⸻
    
    Returns:
        tuple: (questions_list, section_metadata_dict)
    """
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for FORMAT: CMPE at the beginning for simplified assessment
    format_detected = False
    if '**FORMAT**: CMPE' in content or '**FORMAT**: cmpe' in content.lower():
        format_detected = True
    
    # Split content by the separator ⸻ or similar Unicode separators
    sections = re.split(r'[⸻\u2e3b\u2014\u2015\u2500-\u257f]+', content)
    
    questions = []
    section_metadata = {}
    current_section_type = None
    current_points = 1
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        if not lines:
            continue
        
        # Check for section headers (including markdown headers as separators)
        section_header = None
        for line in lines:
            if (line.startswith('## ') or 
                line.startswith('True/False') or 
                line.startswith('Multiple Choice') or 
                line.startswith('Short Answer')):
                section_header = line
                break
        
        if section_header:
            section_title = section_header.replace('##', '').strip().lower()
            
            # Extract points from section title
            points_match = re.search(r'(\d+)\s*points?\s*each', section_title)
            current_points = int(points_match.group(1)) if points_match else 1
            
            if 'true/false' in section_title or 't/f' in section_title:
                current_section_type = 'true_false_question'
                section_metadata['true_false_question'] = current_points
            elif 'multiple choice' in section_title or 'mcq' in section_title:
                current_section_type = 'multiple_choice_question'
                section_metadata['multiple_choice_question'] = current_points
            elif 'short answer' in section_title:
                current_section_type = 'essay_question'  # Changed to essay_question for Canvas compatibility
                section_metadata['essay_question'] = current_points
            
            # Don't skip this section - continue to parse questions in it
            # continue
        
        # Parse individual questions
        if not current_section_type:
            continue
            
        # Find question text - improved pattern matching
        question_text = None
        question_line_idx = -1
        
        for i, line in enumerate(lines):
            # Look for various question patterns:
            # T/F questions: "T/F: " or "1. T/F: " or "1. (T/F)" 
            # MCQ questions: "MCQ: " or "1. MCQ: " or "1. (MCQ)" or just "1. "
            # Short Answer: "Q: " or "1. (Short Answer)" or just "1. "
            if (re.match(r'^\d*\.?\s*T/F:', line) or          # T/F questions with T/F: prefix
                re.match(r'^\d*\.?\s*\(T/F\)', line) or       # T/F questions with (T/F) prefix
                re.match(r'^\d*\.?\s*MCQ:', line) or          # MCQ questions with MCQ: prefix
                re.match(r'^\d*\.?\s*\(MCQ\)', line) or       # MCQ questions with (MCQ) prefix
                re.match(r'^\d*\.?\s*\(Short Answer\)', line) or  # Short answer with (Short Answer) prefix
                re.match(r'^Q:', line) or                     # Short answer with Q: prefix
                (re.match(r'^\d+[.:]?\s+', line) and not line.startswith('Answer:') and not line.startswith('Explanation:') and not line.startswith('**Answer:**'))):  # Numbered questions (excluding Answer/Explanation lines)
                question_text = line
                question_line_idx = i
                break
        
        if not question_text:
            continue
            
        # Clean up question text by removing prefixes
        original_question = question_text
        
        # Remove numbering and prefixes
        question_text = re.sub(r'^\d+[.:]?\s*', '', question_text)      # Remove numbering
        question_text = re.sub(r'^T/F:\s*', '', question_text)          # Remove T/F: prefix
        question_text = re.sub(r'^\(T/F\)\s*', '', question_text)       # Remove (T/F) prefix
        question_text = re.sub(r'^MCQ:\s*', '', question_text)          # Remove MCQ: prefix
        question_text = re.sub(r'^\(MCQ\)\s*', '', question_text)       # Remove (MCQ) prefix
        question_text = re.sub(r'^\(Short Answer\)\s*', '', question_text)  # Remove (Short Answer) prefix
        question_text = re.sub(r'^Q:\s*', '', question_text)            # Remove Q: prefix
        
        # Determine question type from the original text if not already set by section
        if ('T/F:' in original_question or '(T/F)' in original_question or 
            (current_section_type == 'true_false_question')):
            current_question_type = 'true_false_question'
        elif ('MCQ:' in original_question or '(MCQ)' in original_question or 
              (current_section_type == 'multiple_choice_question')):
            current_question_type = 'multiple_choice_question'
        elif ('Q:' in original_question or '(Short Answer)' in original_question or 
              (current_section_type == 'essay_question')):
            current_question_type = 'essay_question'
        else:
            current_question_type = current_section_type
        
        if current_question_type == 'true_false_question':
            # Find the answer
            correct_answer = None
            for line in lines[question_line_idx + 1:]:
                if line.startswith('Answer:') or line.startswith('**Answer:**'):
                    answer_text = line.replace('Answer:', '').replace('**Answer:**', '').strip()
                    correct_answer = answer_text.lower() in ['true', 't', '1', 'yes']
                    break
            
            if correct_answer is not None:
                answers = [
                    {"answer_text": "True", "weight": 100 if correct_answer else 0},
                    {"answer_text": "False", "weight": 0 if correct_answer else 100}
                ]
                
                questions.append({
                    "question_text": question_text,
                    "question_type": "true_false_question",
                    "points_possible": current_points,
                    "answers": answers
                })
        
        elif current_question_type == 'multiple_choice_question':
            # Collect answer options
            answer_options = []
            correct_answer_text = None
            
            for line in lines[question_line_idx + 1:]:
                # Check for answer options: A), B), C), D) or a), b), c), d)
                if re.match(r'^[a-dA-D]\)', line):
                    answer_options.append(line[2:].strip())
                elif line.startswith('Answer:') or line.startswith('**Answer:**'):
                    correct_answer_text = line.replace('Answer:', '').replace('**Answer:**', '').strip()
                    break
            
            if answer_options and correct_answer_text:
                # Parse the correct answer to find which option is correct
                correct_option_letter = None
                if correct_answer_text and len(correct_answer_text) > 0:
                    # Handle formats like "B) Option text", "b) Option text", "B", or "b"
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
                
                questions.append({
                    "question_text": question_text,
                    "question_type": "multiple_choice_question",
                    "answers": canvas_answers,
                    "points_possible": current_points
                })
        
        elif current_question_type == 'essay_question':  # Updated from short_answer_question
            # For essay questions, collect only the question text, not the answer
            full_question_text = question_text
            
            # Collect all lines until we hit the answer or next section
            for line in lines[question_line_idx + 1:]:
                # Stop if we hit an answer line, new section header, or another question
                if (line.startswith('Answer:') or line.startswith('**Answer:**') or
                    line.startswith('⸻') or 
                    re.match(r'^\d*\.?\s*T/F:', line) or
                    re.match(r'^\d*\.?\s*\(T/F\)', line) or
                    re.match(r'^\d*\.?\s*MCQ:', line) or
                    re.match(r'^\d*\.?\s*\(MCQ\)', line) or
                    re.match(r'^\d*\.?\s*\(Short Answer\)', line) or
                    re.match(r'^Q:', line) or
                    (re.match(r'^\s*$', line) and len(full_question_text.strip()) > 50)):  # Stop at empty line if we have enough content
                    break
                
                # Skip empty lines at the beginning but include them later
                if line.strip() or len(full_question_text.strip()) > len(question_text.strip()):
                    full_question_text += "\n" + line
            
            questions.append({
                "question_text": full_question_text.strip(),
                "question_type": "essay_question",  # Changed from short_answer_question to essay_question
                "points_possible": current_points
            })
    
    # Convert math equations to Canvas format before returning
    questions = batch_convert_questions(questions)
    
    return questions, section_metadata