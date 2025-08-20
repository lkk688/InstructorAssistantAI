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


def clean_exam_questions(input_content):
    """
    Clean exam questions by removing answers and explanations.
    
    Args:
        input_content (str): The original exam content with answers
        
    Returns:
        str: Cleaned exam content without answers
    """
    lines = input_content.split('\n')
    cleaned_lines = []
    current_section = None
    question_counter = 0
    
    # Add header and instructions
    cleaned_lines.extend([
        '# CMPE 257 Machine Learning - Comprehensive Exam Questions',
        '',
        '**Name:** ________________________ **Student ID:** ________________________',
        '',
        '**Date:** ________________________ **Time Allowed:** ________________________',
        '',
        '---',
        '',
        '## Instructions',
        '- Answer all questions clearly and concisely',
        '- For True/False questions, circle T or F and provide brief justification if required',
        '- For Multiple Choice questions, circle the correct answer',
        '- For Short Answer questions, use the space provided',
        '- Show your work where applicable',
        '',
        '---',
        ''
    ])
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip the original title
        if line.startswith('# CMPE 257') and i == 0:
            i += 1
            continue
            
        # Handle section headers
        if line.startswith('### '):
            current_section = line
            cleaned_lines.append(line)
            cleaned_lines.append('')
            i += 1
            continue
            
        # Handle True/False questions
        if re.match(r'^\*\*\d+\. T/F:', line):
            question_counter += 1
            # Extract question text after "T/F:"
            question_text = re.sub(r'^\*\*\d+\. T/F:', f'**{question_counter}. T/F:', line)
            cleaned_lines.append(question_text)
            cleaned_lines.append('')
            cleaned_lines.append('**T** / **F**')
            cleaned_lines.append('')
            cleaned_lines.append('___________________________________________________________________________')
            cleaned_lines.append('')
            
            # Skip answer and explanation
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if (re.match(r'^\*\*\d+\. T/F:', next_line) or 
                    re.match(r'^\*\*\d+\. [^T]', next_line) or
                    re.match(r'^\d+\. \*\*', next_line) or
                    next_line.startswith('### ')):
                    break
                i += 1
            continue
            
        # Handle Multiple Choice questions
        if re.match(r'^\*\*\d+\. [^T]', line) and current_section and 'Multiple Choice' in current_section:
            question_counter += 1
            # Extract question text and renumber
            question_text = re.sub(r'^\*\*\d+\.', f'**{question_counter}.', line)
            cleaned_lines.append(question_text)
            cleaned_lines.append('')
            
            # Look ahead for options
            i += 1
            while i < len(lines):
                option_line = lines[i].strip()
                if re.match(r'^[a-dA-D][.)\)]', option_line):
                    # Standardize to lowercase a-d format with parentheses
                    standardized_option = re.sub(r'^([a-dA-D])[.)\)]', lambda m: m.group(1).lower() + ')', option_line)
                    cleaned_lines.append(standardized_option)
                    i += 1
                elif option_line.startswith('**Answer:**'):
                    break
                elif option_line == '':
                    i += 1
                else:
                    i += 1
                    
            cleaned_lines.append('')
            cleaned_lines.append('**Answer:** _______')
            cleaned_lines.append('')
            
            # Skip answer and explanation
            while i < len(lines):
                next_line = lines[i].strip()
                if (re.match(r'^\*\*\d+\. T/F:', next_line) or 
                    re.match(r'^\*\*\d+\. [^T]', next_line) or
                    re.match(r'^\d+\. \*\*', next_line) or
                    next_line.startswith('### ')):
                    break
                i += 1
            continue
            
        # Handle Short Answer questions
        if (re.match(r'^\d+\. \*\*', line) or re.match(r'^\*\*\d+\.', line)) and current_section and 'Short Answer' in current_section:
            question_counter += 1
            # Extract question text and renumber - standardize to "number. **text**" format
            if re.match(r'^\d+\. \*\*', line):
                question_text = re.sub(r'^\d+\.', f'{question_counter}.', line)
            else:
                # Convert "**number. text**" to "number. **text**" format
                question_text = re.sub(r'^\*\*\d+\.\s*', f'{question_counter}. **', line)
            cleaned_lines.append(question_text)
            cleaned_lines.append('')
            # Add answer lines
            for _ in range(8):
                cleaned_lines.append('___________________________________________________________________________')
                cleaned_lines.append('')
            
            # Skip answer and explanation
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if (re.match(r'^\d+\. \*\*', next_line) or 
                    re.match(r'^\*\*\d+\.', next_line) or
                    next_line.startswith('### ') or
                    next_line == '---'):
                    break
                i += 1
            continue
            
        # Handle section breaks
        if line == '---':
            cleaned_lines.append('---')
            cleaned_lines.append('')
            i += 1
            continue
            
        # Skip everything else (answers, explanations, etc.)
        i += 1
    
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
        cleaned_content = clean_exam_questions(content)
        
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