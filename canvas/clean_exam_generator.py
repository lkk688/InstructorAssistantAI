#!/usr/bin/env python3
"""
Exam Question Cleaner

This script converts exam questions with answers and explanations into a clean exam format
suitable for students, removing answers and explanations while preserving structure.

Usage:
    python clean_exam_generator.py input_file.md output_file.md
"""

import re
import sys
from pathlib import Path
from question_parsers import parse_questions_cmpe_format


def replace_unicode_with_latex(text):
    """
    Replace Unicode symbols with LaTeX macros.
    
    Args:
        text (str): Text containing Unicode symbols
        
    Returns:
        str: Text with Unicode symbols replaced by LaTeX macros
    """
    # Dictionary of Unicode to LaTeX replacements
    unicode_to_latex = {
        'ρ': r'$\rho$',
        '∞': r'$\infty$',
        'ᵢ': r'$_i$',
        'ⱼ': r'$_j$',
        '₁': r'$_1$',
        '₂': r'$_2$',
        '₃': r'$_3$',
        '₄': r'$_4$',
        '₅': r'$_5$',
        '₆': r'$_6$',
        '₇': r'$_7$',
        '₈': r'$_8$',
        '₉': r'$_9$',
        '₀': r'$_0$',
        'ₙ': r'$_n$',
        'α': r'$\alpha$',
        'β': r'$\beta$',
        'γ': r'$\gamma$',
        'δ': r'$\delta$',
        'ε': r'$\epsilon$',
        'θ': r'$\theta$',
        'λ': r'$\lambda$',
        'μ': r'$\mu$',
        'σ': r'$\sigma$',
        'τ': r'$\tau$',
        'φ': r'$\phi$',
        'χ': r'$\chi$',
        'ψ': r'$\psi$',
        'ω': r'$\omega$',
        '≤': r'$\leq$',
        '≥': r'$\geq$',
        '≠': r'$\neq$',
        '≈': r'$\approx$',
        '∈': r'$\in$',
        '∉': r'$\notin$',
        '∪': r'$\cup$',
        '∩': r'$\cap$',
        '⊆': r'$\subseteq$',
        '⊇': r'$\supseteq$',
        '∅': r'$\emptyset$',
        '∇': r'$\nabla$',
        '∂': r'$\partial$',
        '∫': r'$\int$',
        '∑': r'$\sum$',
        '∏': r'$\prod$',
        '√': r'$\sqrt$',
        '±': r'$\pm$',
        '×': r'$\times$',
        '÷': r'$\div$',
        '°': r'$^\circ$',
        'π': r'$\pi$'
    }
    
    result = text
    for unicode_char, latex_macro in unicode_to_latex.items():
        result = result.replace(unicode_char, latex_macro)
    
    return result


def clean_exam_questions(input_file):
    """
    Clean exam questions by removing answers and explanations using question parsers.
    
    Args:
        input_file (str): Path to the original exam file with answers
        
    Returns:
        str: Cleaned exam content without answers
    """
    # Parse questions using the CMPE format parser
    questions, sections = parse_questions_cmpe_format(input_file)
    
    cleaned_lines = []
    
    # Add header and instructions
    cleaned_lines.extend([
        '# CMPE 258-02 Fa2025 Deep Learning - Quiz1 Questions',
        '',
        '**Name:** ________________________ **Student ID:** ________________________',
        '',
        '**Date:** ________________________ **Time Allowed:** ________________________',
        '',
        '---',
        '',
        '## Instructions',
        '- The exam is closed book and closed notes',
        '- Answer all questions clearly and concisely',
        '- For True/False questions (2 pts per question), circle T or F',
        '- For Multiple Choice questions (3 pts per question), circle the correct answer',
        '- For Short Answer questions (4 pts per question), use the space provided',
        '',
        '---',
        ''
    ])
    
    # Group questions by section
    current_section = None
    question_counter = 0
    
    for question in questions:
        # Check if we need to add a section header
        if question.get('section') != current_section:
            current_section = question.get('section')
            if current_section:
                cleaned_lines.append(f"## {current_section}")
                cleaned_lines.append('')
        
        question_counter += 1
        question_type = question['question_type']
        question_text = question['question_text']
        
        if question_type == 'true_false_question':
            # Format True/False question
            cleaned_lines.append(f"**{question_counter}. T/F: {question_text}**")
            cleaned_lines.append('')
            cleaned_lines.append('**T** / **F**')
            cleaned_lines.append('')
            cleaned_lines.append('---')
            cleaned_lines.append('')
            
        elif question_type == 'multiple_choice_question':
            # Format Multiple Choice question
            cleaned_lines.append(f"**{question_counter}. {question_text}**")
            cleaned_lines.append('')
            
            # Add answer choices - each on independent line
            for i, answer in enumerate(question.get('answers', [])):
                choice_letter = chr(ord('a') + i)
                cleaned_lines.append(f"**{choice_letter})** {answer['answer_text']}")
                cleaned_lines.append('')
            
            cleaned_lines.append('**Answer:** _______')
            cleaned_lines.append('')
            cleaned_lines.append('---')
            cleaned_lines.append('')
            
        elif question_type == 'essay_question':
            # Format Essay question (previously short_answer_question)
            cleaned_lines.append(f"**{question_counter}. {question_text}**")
            cleaned_lines.append('')
            # Add answer lines for essay questions
            for _ in range(10):  # More lines for essay questions
                cleaned_lines.append('___________________________________________________________________________')
                cleaned_lines.append('')
            cleaned_lines.append('---')
            cleaned_lines.append('')
    
    # Clean up multiple consecutive empty lines
    result = []
    prev_empty = False
    for line in cleaned_lines:
        if line == '':
            if not prev_empty:
                result.append(line)
            prev_empty = True
        else:
            result.append(line)
            prev_empty = False
    
    # Apply Unicode to LaTeX conversion to the final result
    final_content = '\n'.join(result)
    final_content = replace_unicode_with_latex(final_content)
            
    return final_content


def main():
    """
    Main function to process command line arguments and clean exam file.
    """
    if len(sys.argv) != 3:
        print("Usage: python clean_exam_generator.py input_file.md output_file.md")
        print("Example: python clean_exam_generator.py cmpe257_exam_questions.md cmpe257_exam_questions_clean.md")
        sys.exit(1)
        
    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    if not input_file.exists():
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
        
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Clean the content
        cleaned_content = clean_exam_questions(input_file)
        
        # Write output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
            
        print(f"Successfully created clean exam file: {output_file}")
        print(f"Original file: {len(content.split())} words")
        print(f"Clean file: {len(cleaned_content.split())} words")
        
    except Exception as e:
        print(f"Error processing files: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()