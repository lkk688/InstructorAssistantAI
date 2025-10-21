"""
Math equation converter and markdown formatter for Canvas LMS compatibility.

This module provides functions to convert LaTeX math equations from various formats
to Canvas-compatible MathJax format using \( \) for inline and $$ $$ for block equations.
It also handles markdown formatting conversion to HTML for proper display in Canvas.
"""

import re


def convert_markdown_to_html(text):
    """
    Convert basic markdown formatting to HTML for Canvas compatibility.
    
    Args:
        text (str): Text containing markdown formatting
        
    Returns:
        str: Text with markdown converted to HTML
    """
    if not text:
        return text
    
    # Convert **bold** to <strong>bold</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert *italic* to <em>italic</em> (but avoid conflicting with math)
    # Only convert single * if it's not part of math equations
    text = re.sub(r'(?<!\$)\*([^*$]+?)\*(?!\$)', r'<em>\1</em>', text)
    
    # Convert `code` to <code>code</code>
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    
    return text


def convert_math_to_canvas(text, use_block_format=False):
    """
    Convert LaTeX math equations from $ delimiters to Canvas-compatible MathJax format.
    
    Args:
        text (str): Text containing LaTeX math equations with $ delimiters
        use_block_format (bool): If True, use $$ $$ for block equations, otherwise \( \) for inline
        
    Returns:
        str: Text with math equations converted to Canvas format
    """
    if not text:
        return text
    
    # Convert inline math: $equation$ -> \(equation\) or $$equation$$
    def replace_math(match):
        math_content = match.group(1)
        if use_block_format:
            return f"$${math_content}$$"
        else:
            return f"\\({math_content}\\)"
    
    # Pattern to match $...$ but avoid matching things like $20,000 or $5.99
    # Look for $ followed by non-digit or digit followed by non-comma/period
    pattern = r'\$([^$]*?(?:[a-zA-Z_\\{}^]+|[0-9]+[a-zA-Z_\\{}^])[^$]*?)\$'
    
    converted_text = re.sub(pattern, replace_math, text)
    
    return converted_text


def convert_math_in_question_text(question_text: str, use_block_format=False) -> str:
    """
    Convert math equations in question text to Canvas format.
    
    Args:
        question_text: The question text that may contain math equations
        use_block_format: If True, use $$ $$ format instead of \( \)
        
    Returns:
        Question text with Canvas-compatible math format
    """
    return convert_math_to_canvas(question_text, use_block_format)


def convert_math_in_answer_text(answer_text: str, use_block_format=False) -> str:
    """
    Convert math equations in answer text to Canvas format.
    
    Args:
        answer_text: The answer text that may contain math equations
        use_block_format: If True, use $$ $$ format instead of \( \)
        
    Returns:
        Answer text with Canvas-compatible math format
    """
    return convert_math_to_canvas(answer_text, use_block_format)


def process_question_with_math(question_dict: dict) -> dict:
    """
    Process a question dictionary and convert all math equations to Canvas format
    and convert markdown formatting to HTML.
    
    Args:
        question_dict: Dictionary containing question data with potential math equations and markdown
        
    Returns:
        Updated question dictionary with Canvas-compatible math format and HTML formatting
    """
    # Create a copy to avoid modifying the original
    processed_question = question_dict.copy()
    
    # Convert math in question text
    if 'question_text' in processed_question:
        # First convert markdown to HTML, then convert math
        processed_question['question_text'] = convert_markdown_to_html(
            processed_question['question_text']
        )
        processed_question['question_text'] = convert_math_in_question_text(
            processed_question['question_text']
        )
    
    # Convert math and markdown in answers if they exist
    if 'answers' in processed_question and processed_question['answers']:
        processed_answers = []
        for answer in processed_question['answers']:
            if isinstance(answer, dict) and 'answer_text' in answer:
                processed_answer = answer.copy()
                # First convert markdown to HTML, then convert math
                processed_answer['answer_text'] = convert_markdown_to_html(
                    answer['answer_text']
                )
                processed_answer['answer_text'] = convert_math_in_answer_text(
                    processed_answer['answer_text']
                )
                processed_answers.append(processed_answer)
            else:
                processed_answers.append(answer)
        processed_question['answers'] = processed_answers
    
    # Convert math in sample answers or explanations if they exist
    for field in ['sample_answer', 'explanation', 'neutral_comments']:
        if field in processed_question and processed_question[field]:
            processed_question[field] = convert_math_to_canvas(
                processed_question[field]
            )
    
    return processed_question


def batch_convert_questions(questions_list: list) -> list:
    """
    Convert math equations in a list of questions to Canvas format.
    
    Args:
        questions_list: List of question dictionaries
        
    Returns:
        List of questions with Canvas-compatible math format
    """
    return [process_question_with_math(question) for question in questions_list]


# Example usage and test cases
if __name__ == "__main__":
    # Test cases for math conversion
    test_cases = [
        "The matrix $P^2_{rect}$ contains both intrinsic and extrinsic parameters.",
        "The coordinate terms $(x_{offset}, y_{offset}, h, w)$ represent offsets.",
        "The output tensor shape $N \\times N \\times [3 \\times (4 + 1 + 80)]$ is important.",
        "Regular text without math equations should remain unchanged.",
        "Multiple equations: $x^2 + y^2 = r^2$ and $E = mc^2$ in one sentence."
    ]

    print("Testing math conversion to Canvas format:")
    print("=" * 60)

    for i, test_text in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Original: {test_text}")
        print(f"Canvas:   {convert_math_to_canvas(test_text)}")
    
    # Test cases for markdown conversion
    markdown_test_cases = [
        "This is **bold text** and this is *italic text*.",
        "The **softmax** function is used in neural networks.",
        "Use `code` formatting for inline code.",
        "Mixed: **bold** with $math$ and *italic* text.",
        "**Multiple** **bold** words in one sentence."
    ]
    
    print("\n" + "=" * 60)
    print("Testing markdown to HTML conversion:")
    
    for i, test_text in enumerate(markdown_test_cases, 1):
        print(f"\nMarkdown Test {i}:")
        print(f"Original: {test_text}")
        print(f"HTML:     {convert_markdown_to_html(test_text)}")

    print("\n" + "=" * 60)
    print("Testing question processing:")

    sample_question = {
        'question_type': 'true_false_question',
        'question_text': 'The **matrix** $P^2_{rect}$ contains both intrinsic and extrinsic parameters.',
        'points_possible': 2,
        'answers': [
            {'answer_text': '**True**', 'answer_weight': 100},
            {'answer_text': '**False**', 'answer_weight': 0}
        ]
    }

    processed = process_question_with_math(sample_question)
    print(f"\nOriginal question text: {sample_question['question_text']}")
    print(f"Processed question text: {processed['question_text']}")
    print(f"Original answer 1: {sample_question['answers'][0]['answer_text']}")
    print(f"Processed answer 1: {processed['answers'][0]['answer_text']}")