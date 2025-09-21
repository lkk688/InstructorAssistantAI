#!/usr/bin/env python3
"""
AI-powered Question Guidance and Instruction Generation Tool

This tool reads math problems from various file formats (Markdown, TXT, Word documents)
and generates comprehensive educational content including:
- Detailed explanations and solutions
- Common mistakes and misconceptions
- Practice problems
- Slide-ready presentations

Features:
- Multi-format input support (MD, TXT, DOCX)
- Enhanced error handling and logging
- Output validation and quality scoring
- Multiple export formats (HTML, PDF-ready Markdown)
- Summary reporting

Usage:
    python questionguide.py --input problems.md --output results/
    python questionguide.py --input problems.txt --export-html --create-summary
"""

from __future__ import annotations
import argparse
import json
import logging
import os
import re
import sys
import textwrap
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextIteratorStreamer,
)

# Optional sympy for mathematical validation
try:
    import sympy as sp
except Exception:  # pragma: no cover
    sp = None

# Optional manim for animation generation
try:
    from manim import *
    MANIM_AVAILABLE = True
except Exception:  # pragma: no cover
    MANIM_AVAILABLE = False
    # Create a mock Scene class for testing when Manim is not available
    class Scene:
        pass

def setup_logging(log_level: str, output_dir: str) -> None:
    """Setup comprehensive logging with file and console handlers."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure logging level
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Clear any existing handlers
        logging.getLogger().handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        
        # File handler
        log_file = os.path.join(output_dir, 'questionguide.log')
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        logging.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
        
    except Exception as e:
        print(f"Failed to setup logging: {str(e)}")
        # Fallback to basic logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class Problem:
    title: str
    content: str
    index: int

def read_problems(file_path: str) -> List[Problem]:
    """Read problems from various file formats (markdown, txt, docx) with enhanced parsing."""
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        logging.info(f"Reading problems from: {file_path}")
        
        # Determine file type and read content
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.docx':
            content = read_docx_content(file_path)
        elif file_extension in ['.md', '.markdown']:
            content = read_markdown_content(file_path)
        elif file_extension == '.txt':
            content = read_text_content(file_path)
        else:
            # Try to read as plain text
            logging.warning(f"Unknown file extension {file_extension}, treating as plain text")
            content = read_text_content(file_path)
        
        # Parse problems from content
        problems = parse_problems_from_content(content)
        
        logging.info(f"Successfully parsed {len(problems)} problems from {file_path}")
        return problems
        
    except Exception as e:
        logging.error(f"Failed to read problems from {file_path}: {str(e)}")
        logging.error(traceback.format_exc())
        return []

def read_docx_content(file_path: Path) -> str:
    """Read content from a Word document (.docx)."""
    try:
        # Try to import python-docx
        try:
            from docx import Document
        except ImportError:
            logging.error("python-docx not installed. Install with: pip install python-docx")
            raise ImportError("python-docx package required for .docx files")
        
        doc = Document(file_path)
        content_parts = []
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                # Preserve heading styles
                if paragraph.style.name.startswith('Heading'):
                    level = paragraph.style.name.replace('Heading ', '')
                    if level.isdigit():
                        content_parts.append('#' * int(level) + ' ' + text)
                    else:
                        content_parts.append('## ' + text)
                else:
                    content_parts.append(text)
        
        return '\n\n'.join(content_parts)
        
    except Exception as e:
        logging.error(f"Failed to read .docx file: {str(e)}")
        raise

def read_markdown_content(file_path: Path) -> str:
    """Read content from a Markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Failed to read markdown file: {str(e)}")
        raise

def read_text_content(file_path: Path) -> str:
    """Read content from a plain text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to detect if it's structured content
        lines = content.split('\n')
        structured_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                structured_content.append('')
                continue
            
            # Convert numbered items to headings
            if re.match(r'^\d+\.\s+', line):
                problem_text = re.sub(r'^\d+\.\s+', '', line)
                structured_content.append(f'## {problem_text}')
            # Convert lines that look like titles to headings
            elif len(line) < 100 and not line.endswith('.') and not line.endswith(':'):
                structured_content.append(f'## {line}')
            else:
                structured_content.append(line)
        
        return '\n'.join(structured_content)
        
    except Exception as e:
        logging.error(f"Failed to read text file: {str(e)}")
        raise

def parse_problems_from_content(content: str) -> List[Problem]:
    """Parse problems from content using multiple detection methods."""
    try:
        problems = []
        
        # Method 1: Try markdown-style parsing (## headings)
        markdown_problems = parse_markdown_problems(content)
        if markdown_problems:
            return markdown_problems
        
        # Method 2: Try fenced code blocks
        fenced_problems = parse_fenced_problems(content)
        if fenced_problems:
            return fenced_problems
        
        # Method 3: Try paragraph-based parsing
        paragraph_problems = parse_paragraph_problems(content)
        if paragraph_problems:
            return paragraph_problems
        
        # Method 4: Fallback - treat entire content as one problem
        if content.strip():
            problems.append(Problem(
                title='Problem 1',
                content=content.strip(),
                index=1
            ))
        
        return problems
        
    except Exception as e:
        logging.error(f"Failed to parse problems from content: {str(e)}")
        return []

def parse_markdown_problems(content: str) -> List[Problem]:
    """Parse problems using markdown heading structure."""
    problems = []
    lines = content.splitlines()
    current_problem = None
    current_content = []
    
    for line in lines:
        # Check for heading (## or #)
        heading_match = re.match(r'^(#{1,6})\s+(.+)', line)
        if heading_match:
            # Save previous problem if exists
            if current_problem:
                problems.append(Problem(
                    title=current_problem,
                    content='\n'.join(current_content).strip(),
                    index=len(problems) + 1
                ))
            
            # Start new problem
            current_problem = heading_match.group(2).strip()
            current_content = []
        else:
            if current_problem:
                current_content.append(line)
    
    # Add last problem
    if current_problem:
        problems.append(Problem(
            title=current_problem,
            content='\n'.join(current_content).strip(),
            index=len(problems) + 1
        ))
    
    return problems

def parse_fenced_problems(content: str) -> List[Problem]:
    """Parse problems using fenced code blocks."""
    problems = []
    lines = content.splitlines()
    in_fence = False
    current_content = []
    fence_type = None
    
    for line in lines:
        if re.match(r'^```(problem|math|question)', line, re.IGNORECASE):
            in_fence = True
            fence_type = re.match(r'^```(\w+)', line).group(1)
            current_content = []
        elif line.strip() == '```' and in_fence:
            in_fence = False
            if current_content:
                content_text = '\n'.join(current_content).strip()
                problems.append(Problem(
                    title=f'{fence_type.title()} {len(problems) + 1}',
                    content=content_text,
                    index=len(problems) + 1
                ))
            current_content = []
        elif in_fence:
            current_content.append(line)
    
    return problems

def parse_paragraph_problems(content: str) -> List[Problem]:
    """Parse problems by splitting on double newlines."""
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    if len(paragraphs) <= 1:
        return []
    
    problems = []
    for i, paragraph in enumerate(paragraphs):
        # Use first line or first few words as title
        lines = paragraph.split('\n')
        first_line = lines[0].strip()
        
        if len(first_line) > 100:
            title = f"Problem {i + 1}"
        else:
            title = first_line[:50] + "..." if len(first_line) > 50 else first_line
        
        problems.append(Problem(
            title=title,
            content=paragraph,
            index=i + 1
        ))
    
    return problems

def build_model_and_tokenizer(model_name: str, device: str = "auto") -> Tuple[Any, Any]:
    """Build and return model and tokenizer with enhanced error handling."""
    try:
        logging.info(f"Loading model: {model_name}")
        
        # Determine device
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
                logging.info("Using CUDA device")
            else:
                device = "cpu"
                logging.info("Using CPU device")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map=device if device != "cpu" else None,
            trust_remote_code=True
        )
        
        if device == "cpu":
            model = model.to(device)
        
        model.eval()
        logging.info(f"Model loaded successfully on {device}")
        
        return model, tokenizer
    
    except Exception as e:
        logging.error(f"Failed to load model {model_name}: {str(e)}")
        logging.error(traceback.format_exc())
        raise

def chat_completion(model, tokenizer, messages: List[Dict[str, str]],
                    max_new_tokens: int = 512, temperature: float = 0.2, top_p: float = 0.9) -> str:
    """Generate chat completion using Qwen2.5-Math-7B-Instruct format."""
    try:
        # Use Qwen's chat template for proper formatting
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize the formatted text
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        # Generate
        with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        # Extract only the generated tokens (excluding input)
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        # Decode response using batch_decode as recommended by Qwen
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Debug information
        logging.debug(f"Input length: {model_inputs.input_ids.shape[1]}")
        logging.debug(f"Generated tokens length: {len(generated_ids[0])}")
        logging.debug(f"Generated token IDs: {generated_ids[0].tolist()}")
        logging.debug(f"Response: '{response}'")
        
        if not response.strip():
            logging.warning("Empty response generated by the model")
            return "No response generated"
        
        return response.strip()
    
    except Exception as e:
        logging.error(f"Error in chat completion: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error generating response: {str(e)}"

def explanation_prompt(problem_text: str, grade_level: str = "middle school") -> List[Dict[str, str]]:
    """Create enhanced prompt for generating comprehensive explanations tailored to grade level."""
    
    # Define grade-specific language and complexity
    grade_configs = {
        "elementary": {
            "language": "simple, concrete language with everyday examples",
            "complexity": "basic concepts with visual aids and step-by-step guidance",
            "examples": "real-world situations kids can relate to",
            "vocabulary": "age-appropriate mathematical terms with explanations"
        },
        "middle school": {
            "language": "clear, accessible language with some mathematical terminology",
            "complexity": "moderate complexity with logical reasoning",
            "examples": "practical applications and problem-solving strategies",
            "vocabulary": "standard mathematical vocabulary with context"
        },
        "high school": {
            "language": "precise mathematical language with formal reasoning",
            "complexity": "advanced concepts with rigorous explanations",
            "examples": "abstract applications and theoretical connections",
            "vocabulary": "formal mathematical terminology and notation"
        }
    }
    
    # Get configuration for the specified grade level
    config = grade_configs.get(grade_level.lower(), grade_configs["middle school"])
    
    system_prompt = f"""You are an expert mathematics educator specializing in {grade_level} instruction with deep expertise in:
- Mathematical problem-solving appropriate for {grade_level} students
- Common misconceptions and learning challenges at the {grade_level} level
- Effective instructional design for {grade_level} learners
- Creating engaging educational content suitable for {grade_level} students

Your role is to analyze mathematical problems and create comprehensive educational materials that help {grade_level} students understand both the solution process and underlying concepts using {config['language']}."""

    user_prompt = f"""Please analyze this mathematical problem and provide a comprehensive educational response in markdown format, specifically tailored for {grade_level} students:

**Problem:**
{problem_text}

**Required Markdown Structure:**

## Overview
Provide a brief description of the mathematical topics and concepts covered in this problem, explaining why these topics are important for {grade_level} students and how they connect to their mathematical learning journey.

## Solution
Step-by-step solution with clear explanations appropriate for {grade_level} students. Use {config['language']} and explain each step with {config['complexity']}. Include proper mathematical notation suitable for this grade level and explain the reasoning behind each step.

## Final Answer
The final numerical or algebraic answer, clearly stated

## Common Mistakes
- 🚫 **Common mistake:** Detailed description of typical errors for {grade_level} students and why they occur, with prevention strategies

## Practice Problems
- 📝 **Practice Problem 1:** Similar problem with significant variations but same mathematical topic
- 📝 **Practice Problem 2:** Problem that builds on the concept with major changes in context or numbers
- 📝 **Practice Problem 3:** Application to a completely different scenario but using the same mathematical principles

**Guidelines for {grade_level} level:**
- Use {config['language']} throughout your explanation
- Provide {config['complexity']} in your mathematical reasoning
- Include {config['examples']} where helpful
- Use {config['vocabulary']} appropriately
- Focus on building conceptual understanding suitable for {grade_level} students
- Ensure practice problems have major variations while maintaining the same core mathematical concepts
- Make the overview focus on topic descriptions rather than learning objectives

Please respond using the exact markdown structure above, ensuring all content is appropriate for {grade_level} students."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

def create_tape_diagram(problem_text: str, solution: str = "") -> str:
    """
    Create Singapore Math tape/bar diagram visualization using CSS and HTML.
    Analyzes the problem to identify quantities and relationships for visual representation.
    """
    
    def render_latex_math(text: str) -> str:
        """Convert content inside [ ] brackets to LaTeX math notation."""
        import re
        # Replace [content] with $content$ for inline math
        text = re.sub(r'\[([^\]]+)\]', r'$\1$', text)
        return text
    
    # Apply LaTeX rendering to input text
    problem_text = render_latex_math(problem_text)
    solution = render_latex_math(solution)
    
    # Extract numbers and relationships from problem text
    import re
    numbers = re.findall(r'\b\d+\b', problem_text)
    
    # Common Singapore Math problem patterns
    tape_diagram = ""
    
    # Check for addition/subtraction problems
    if any(word in problem_text.lower() for word in ['total', 'altogether', 'sum', 'more', 'less', 'difference']):
        tape_diagram = f"""
<div class="tape-diagram">
<h4>📊 Tape Diagram Visualization</h4>

<div class="tape-container">
  <div class="tape-section">
    <div class="tape-bar known" style="width: 150px;">
      <span class="tape-label">Known Quantity</span>
      <span class="tape-value">{numbers[0] if numbers else '?'}</span>
    </div>
  </div>
  
  <div class="tape-section">
    <div class="tape-bar unknown" style="width: 100px;">
      <span class="tape-label">Unknown</span>
      <span class="tape-value">?</span>
    </div>
  </div>
  
  <div class="tape-total">
    <div class="tape-bar total" style="width: 250px;">
      <span class="tape-label">Total</span>
      <span class="tape-value">{numbers[1] if len(numbers) > 1 else '?'}</span>
    </div>
  </div>
</div>

<div class="tape-explanation">
<strong>Visual Strategy:</strong>
- Draw bars to represent quantities
- Use the relationship to find the unknown
- Check your answer by substituting back
</div>
</div>
"""
    
    # Check for multiplication/division problems
    elif any(word in problem_text.lower() for word in ['times', 'groups', 'each', 'per', 'rate', 'equal']):
        tape_diagram = f"""
<div class="tape-diagram">
<h4>📊 Tape Diagram Visualization</h4>

<div class="tape-container">
  <div class="tape-groups">
    <div class="tape-group">
      <div class="tape-bar group" style="width: 80px;">
        <span class="tape-value">{numbers[0] if numbers else '?'}</span>
      </div>
    </div>
    <div class="tape-group">
      <div class="tape-bar group" style="width: 80px;">
        <span class="tape-value">{numbers[0] if numbers else '?'}</span>
      </div>
    </div>
    <div class="tape-group">
      <div class="tape-bar group" style="width: 80px;">
        <span class="tape-value">{numbers[0] if numbers else '?'}</span>
      </div>
    </div>
  </div>
  
  <div class="tape-total">
    <div class="tape-bar total" style="width: 250px;">
      <span class="tape-label">Total: {len(numbers) > 1 and numbers[1] or '?'}</span>
    </div>
  </div>
</div>

<div class="tape-explanation">
<strong>Visual Strategy:</strong>
- Draw equal groups/parts
- Identify the relationship (× or ÷)
- Use the pattern to solve
</div>
</div>
"""
    
    # Check for fraction/ratio problems
    elif any(word in problem_text.lower() for word in ['fraction', 'part', 'ratio', 'proportion', 'percent']):
        tape_diagram = f"""
<div class="tape-diagram">
<h4>📊 Tape Diagram Visualization</h4>

<div class="tape-container">
  <div class="tape-whole">
    <div class="tape-bar whole" style="width: 300px;">
      <div class="tape-part known" style="width: 60%;">
        <span class="tape-label">Known Part</span>
      </div>
      <div class="tape-part unknown" style="width: 40%;">
        <span class="tape-label">Unknown Part</span>
      </div>
    </div>
  </div>
  
  <div class="tape-labels">
    <span class="whole-label">Whole = {numbers[0] if numbers else '?'}</span>
  </div>
</div>

<div class="tape-explanation">
<strong>Visual Strategy:</strong>
- Draw the whole as one bar
- Divide into parts based on the ratio
- Use proportional reasoning
</div>
</div>
"""
    
    # Default generic tape diagram
    else:
        tape_diagram = f"""
<div class="tape-diagram">
<h4>📊 Tape Diagram Visualization</h4>

<div class="tape-container">
  <div class="tape-section">
    <div class="tape-bar generic" style="width: 200px;">
      <span class="tape-label">Given Information</span>
      <span class="tape-value">{', '.join(numbers[:2]) if numbers else 'Given values'}</span>
    </div>
  </div>
  
  <div class="tape-section">
    <div class="tape-bar unknown" style="width: 100px;">
      <span class="tape-label">Find</span>
      <span class="tape-value">?</span>
    </div>
  </div>
</div>

<div class="tape-explanation">
<strong>Visual Strategy:</strong>
- Identify what you know and what you need to find
- Draw bars to represent the relationships
- Use the visual model to guide your solution
</div>
</div>
"""
    
    return tape_diagram


def create_step_diagram(step_text: str, step_number: int, problem_context: str = "") -> str:
    """
    Create a step-specific tape diagram for each solution step.
    Analyzes the step to create relevant visual representation.
    """
    import re
    
    def render_latex_math(text: str) -> str:
        """Convert content inside [ ] brackets to LaTeX math notation."""
        # Replace [content] with $content$ for inline math
        text = re.sub(r'\[([^\]]+)\]', r'$\1$', text)
        return text
    
    # Apply LaTeX rendering to input text
    step_text = render_latex_math(step_text)
    problem_context = render_latex_math(problem_context)
    
    # Extract numbers from the current step
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', step_text)
    
    # Clean and analyze step text
    step_lower = step_text.lower().strip()
    
    # Determine diagram type based on step content
    diagram_html = f"""
<div class="step-diagram" id="step-{step_number}">
<h5>📊 Step {step_number} Visualization</h5>

<div class="tape-container">
"""
    
    # Check for arithmetic operations in the step
    if any(op in step_lower for op in ['add', 'plus', '+', 'sum', 'total', 'combine']):
        # Addition diagram
        num1 = numbers[0] if len(numbers) >= 1 else "a"
        num2 = numbers[1] if len(numbers) >= 2 else "b"
        result = numbers[2] if len(numbers) >= 3 else str(int(num1) + int(num2)) if num1.isdigit() and num2.isdigit() else "?"
        
        diagram_html += f"""
  <div class="operation-visual addition">
    <div class="tape-bar operand known" style="width: 120px;">
      <span class="tape-label">First Number</span>
      <span class="tape-value">{num1}</span>
    </div>
    <span class="operation-symbol">+</span>
    <div class="tape-bar operand known" style="width: 120px;">
      <span class="tape-label">Second Number</span>
      <span class="tape-value">{num2}</span>
    </div>
    <span class="equals">=</span>
    <div class="tape-bar result" style="width: 150px;">
      <span class="tape-label">Sum</span>
      <span class="tape-value">{result}</span>
    </div>
  </div>
"""
    
    elif any(op in step_lower for op in ['subtract', 'minus', '-', 'difference', 'less', 'remove', 'take away']):
        # Subtraction diagram
        num1 = numbers[0] if len(numbers) >= 1 else "x"
        num2 = numbers[1] if len(numbers) >= 2 else "y"
        result = numbers[2] if len(numbers) >= 3 else str(int(num1) - int(num2)) if num1.isdigit() and num2.isdigit() else "?"
        
        diagram_html += f"""
  <div class="operation-visual subtraction">
    <div class="tape-bar minuend known" style="width: 150px;">
      <span class="tape-label">Start with</span>
      <span class="tape-value">{num1}</span>
    </div>
    <span class="operation-symbol">-</span>
    <div class="tape-bar subtrahend known" style="width: 100px;">
      <span class="tape-label">Remove</span>
      <span class="tape-value">{num2}</span>
    </div>
    <span class="equals">=</span>
    <div class="tape-bar result" style="width: 120px;">
      <span class="tape-label">Result</span>
      <span class="tape-value">{result}</span>
    </div>
  </div>
"""
    
    elif any(op in step_lower for op in ['multiply', 'times', '×', '*', 'groups', 'each', 'per']):
        # Multiplication diagram
        num1 = numbers[0] if len(numbers) >= 1 else "3"
        num2 = numbers[1] if len(numbers) >= 2 else "4"
        result = numbers[2] if len(numbers) >= 3 else str(int(num1) * int(num2)) if num1.isdigit() and num2.isdigit() else "?"
        
        groups = min(int(num1) if num1.isdigit() and int(num1) <= 6 else 3, 4)
        diagram_html += f"""
  <div class="operation-visual multiplication">
    <div class="multiplication-groups">
"""
        for i in range(groups):
            diagram_html += f"""
      <div class="tape-group">
        <div class="tape-bar group known" style="width: 60px;">
          <span class="tape-label">Group {i+1}</span>
          <span class="tape-value">{num2}</span>
        </div>
      </div>
"""
        diagram_html += f"""
    </div>
    <div class="multiplication-result">
      <div class="tape-bar total result" style="width: 200px;">
        <span class="tape-label">{num1} groups of {num2}</span>
        <span class="tape-value">= {result}</span>
      </div>
    </div>
  </div>
"""
    
    elif any(op in step_lower for op in ['divide', '÷', '/', 'split', 'share', 'equal parts']):
        # Division diagram
        num1 = numbers[0] if len(numbers) >= 1 else "12"
        num2 = numbers[1] if len(numbers) >= 2 else "3"
        result = numbers[2] if len(numbers) >= 3 else str(int(num1) // int(num2)) if num1.isdigit() and num2.isdigit() else "?"
        
        diagram_html += f"""
  <div class="operation-visual division">
    <div class="tape-bar dividend known" style="width: 240px;">
      <span class="tape-label">Total to divide</span>
      <span class="tape-value">{num1}</span>
    </div>
    <div class="division-groups">
"""
        groups = min(int(num2) if num2.isdigit() and int(num2) <= 6 else 3, 4)
        for i in range(groups):
            diagram_html += f"""
      <div class="tape-group">
        <div class="tape-bar group result" style="width: 50px;">
          <span class="tape-label">Part {i+1}</span>
          <span class="tape-value">{result}</span>
        </div>
      </div>
"""
        diagram_html += f"""
    </div>
  </div>
"""
    
    elif any(keyword in step_lower for keyword in ['equation', 'solve', 'find', 'calculate', 'determine']):
        # Problem-solving step diagram
        if numbers:
            diagram_html += f"""
  <div class="operation-visual generic">
    <div class="tape-bar step-info known" style="width: 250px;">
      <span class="tape-label">Step {step_number}: Working with</span>
      <span class="tape-value">{', '.join(numbers[:3])}</span>
    </div>
  </div>
"""
        else:
            diagram_html += f"""
  <div class="operation-visual generic">
    <div class="tape-bar step-info" style="width: 200px;">
      <span class="tape-label">Step {step_number}</span>
      <span class="tape-value">Analyzing...</span>
    </div>
  </div>
"""
    
    else:
        # Enhanced generic step diagram
        if numbers:
            diagram_html += f"""
  <div class="operation-visual generic">
    <div class="tape-bar step-info known" style="width: 200px;">
      <span class="tape-label">Step {step_number}</span>
      <span class="tape-value">Values: {', '.join(numbers[:2])}</span>
    </div>
  </div>
"""
        else:
            diagram_html += f"""
  <div class="operation-visual generic">
    <div class="tape-bar step-info" style="width: 200px;">
      <span class="tape-label">Step {step_number}</span>
      <span class="tape-value">Processing...</span>
    </div>
  </div>
"""
    
    # Truncate step text for display
    display_text = step_text[:150] + "..." if len(step_text) > 150 else step_text
    
    diagram_html += f"""
</div>

<div class="step-explanation">
<strong>This step:</strong> {display_text}
</div>
</div>

"""
    
    return diagram_html


def create_solution_with_diagrams(solution_text: str, problem_text: str = "") -> str:
    """
    Process the solution text and insert step-by-step diagrams.
    Breaks down the solution into steps and adds visual diagrams for each.
    """
    
    # Split solution into steps (look for numbered steps, bullet points, or line breaks)
    import re
    
    # Try to identify step patterns
    step_patterns = [
        r'(?:Step\s*\d+[:.]\s*)(.*?)(?=Step\s*\d+[:.]\s*|\Z)',  # "Step 1:", "Step 2:", etc.
        r'(?:\d+[.)]\s*)(.*?)(?=\d+[.)]\s*|\Z)',  # "1.", "2.", etc.
        r'(?:^\s*[-*]\s*)(.*?)(?=^\s*[-*]\s*|\Z)',  # Bullet points
    ]
    
    steps = []
    for pattern in step_patterns:
        matches = re.findall(pattern, solution_text, re.MULTILINE | re.DOTALL)
        if matches and len(matches) > 1:  # Found multiple steps
            steps = [match.strip() for match in matches if match.strip()]
            break
    
    # If no clear steps found, split by sentences or paragraphs
    if not steps:
        # Split by double line breaks (paragraphs)
        paragraphs = [p.strip() for p in solution_text.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            steps = paragraphs
        else:
            # Split by sentences
            sentences = [s.strip() for s in re.split(r'[.!?]+', solution_text) if s.strip()]
            if len(sentences) > 2:
                steps = sentences[:5]  # Limit to 5 steps for readability
            else:
                steps = [solution_text]  # Use entire solution as one step
    
    # Generate solution with integrated diagrams
    enhanced_solution = ""
    
    for i, step in enumerate(steps, 1):
        if not step.strip():
            continue
            
        # Add the step text
        enhanced_solution += f"""
### Step {i}

{step}

"""
        
        # Add step-specific diagram
        step_diagram = create_step_diagram(step, i, problem_text)
        enhanced_solution += step_diagram
        
        # Add separator between steps (except for the last one)
        if i < len(steps):
            enhanced_solution += "\n---\n"
    
    return enhanced_solution


def create_manim_equation_script(equation: str, problem_text: str = "") -> str:
    """
    Generate a Manim Python script to animate the given mathematical equation.
    
    Args:
        equation: The mathematical equation to animate (e.g., "2x + 5 = 15")
        problem_text: Optional context about the problem
        
    Returns:
        A complete Manim Python script as a string
    """
    # Clean and parse the equation
    equation = equation.strip()
    if not equation:
        return "# No equation provided"
    
    # Extract variable name (default to 'x')
    import re
    var_match = re.search(r'([a-zA-Z])', equation)
    variable = var_match.group(1) if var_match else 'x'
    
    # Generate class name from equation
    class_name = f"Equation_{hash(equation) % 10000}"
    
    # Create the Manim script
    script = f'''from manim import *

class {class_name}(Scene):
    def construct(self):
        # Title
        title = Text("Solving: {equation}", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Original equation
        eq1 = MathTex(r"{equation}")
        eq1.scale(1.5)
        self.play(Write(eq1))
        self.wait(2)
        
        # Step-by-step solution
        steps = self.solve_equation("{equation}")
        
        current_eq = eq1
        for i, step in enumerate(steps):
            # Move current equation up
            self.play(current_eq.animate.shift(UP * 1.5))
            
            # Show step explanation
            explanation = Text(step["explanation"], font_size=24)
            explanation.next_to(current_eq, DOWN, buff=0.5)
            self.play(Write(explanation))
            self.wait(1)
            
            # Show new equation
            new_eq = MathTex(step["equation"])
            new_eq.scale(1.5)
            new_eq.next_to(explanation, DOWN, buff=0.5)
            self.play(Write(new_eq))
            self.wait(2)
            
            # Clean up for next step
            if i < len(steps) - 1:
                self.play(FadeOut(explanation))
                current_eq = new_eq
            else:
                # Final answer highlight
                final_box = SurroundingRectangle(new_eq, color=GREEN, buff=0.2)
                self.play(Create(final_box))
                self.wait(2)
    
    def solve_equation(self, equation):
        """
        Parse and solve the equation step by step.
        Returns a list of steps with explanations.
        """
        steps = []
        
        # Simple linear equation solver for demonstration
        # This is a basic implementation - could be enhanced with sympy
        
        if "2x + 5 = 15" in equation:
            steps = [
                {{"explanation": "Subtract 5 from both sides", "equation": r"2x + 5 - 5 = 15 - 5"}},
                {{"explanation": "Simplify", "equation": r"2x = 10"}},
                {{"explanation": "Divide both sides by 2", "equation": r"\\\\frac{{2x}}{{2}} = \\\\frac{{10}}{{2}}"}},
                {{"explanation": "Solution", "equation": r"{variable} = 5"}}
            ]
        else:
            # Generic steps for other equations
            steps = [
                {{"explanation": "Isolate the variable term", "equation": equation}},
                {{"explanation": "Solve for {variable}", "equation": f"{variable} = ?"}}
            ]
        
        return steps

# To render this animation, run:
# manim -pql {class_name.lower()}.py {class_name}
'''
    
    return script


def extract_equations_from_text(text: str) -> List[str]:
    """
    Extract mathematical equations from text using various patterns.
    
    Args:
        text: Input text that may contain equations
        
    Returns:
        List of extracted equations
    """
    equations = []
    
    # Pattern 1: Equations with equals sign
    eq_pattern1 = r'([a-zA-Z0-9\s\+\-\*\/\(\)]+\s*=\s*[a-zA-Z0-9\s\+\-\*\/\(\)]+)'
    matches1 = re.findall(eq_pattern1, text)
    equations.extend(matches1)
    
    # Pattern 2: Equations in brackets or parentheses
    eq_pattern2 = r'[\[\(]([^[\]()]*=+[^[\]()]*?)[\]\)]'
    matches2 = re.findall(eq_pattern2, text)
    equations.extend(matches2)
    
    # Pattern 3: Mathematical expressions with variables
    eq_pattern3 = r'([a-zA-Z]\s*[\+\-\*\/]\s*\d+\s*=\s*\d+)'
    matches3 = re.findall(eq_pattern3, text)
    equations.extend(matches3)
    
    # Clean and deduplicate
    cleaned_equations = []
    for eq in equations:
        eq = eq.strip()
        if eq and eq not in cleaned_equations and '=' in eq:
            cleaned_equations.append(eq)
    
    return cleaned_equations


def slides_from_explanation(title: str, data: Dict[str, Any]) -> str:
    """Generate Marp-optimized slide-ready Markdown from explanation data with enhanced formatting."""
    
    def render_latex_math(text: str) -> str:
        """Convert content inside [ ] brackets to LaTeX math notation."""
        import re
        # Replace [content] with $content$ for inline math
        text = re.sub(r'\[([^\]]+)\]', r'$\1$', text)
        return text
    
    if "error" in data:
        return f"""---
marp: true
title: "{title}"
theme: default
size: 16:9
class: error
paginate: true
header: 'Math Problem Solver'
footer: 'Generated by AI Question Guide'
---

# ⚠️ Processing Error

## Problem: {title}

### Error Details
{data.get('error', 'Unknown error occurred')}

### Troubleshooting Steps
1. Check the problem format and content
2. Verify the model is working correctly  
3. Review the logs for detailed error information
4. Try simplifying the problem statement

---
"""
    
    # Extract data with defaults
    overview = data.get("overview", ["No overview available"])
    solution = data.get("solution", "No solution available")
    final_answer = data.get("final_answer", "No answer available")
    mistakes = data.get("mistakes", ["No common mistakes identified"])
    practice = data.get("practice", ["No practice problems available"])
    
    # Get the original problem text for tape diagram generation
    problem_text = data.get("problem_text", title)
    
    # Apply LaTeX math rendering to all text content
    title = render_latex_math(title)
    problem_text = render_latex_math(problem_text)
    overview = [render_latex_math(obj) for obj in overview]
    solution = render_latex_math(solution)
    final_answer = render_latex_math(final_answer)
    mistakes = [render_latex_math(mistake) for mistake in mistakes]
    practice = [render_latex_math(prob) for prob in practice]
    
    slides = f"""---
marp: true
title: "{title}"
theme: default
size: 16:9
class: math-lesson
paginate: true
header: 'Math Problem Solver'
footer: 'Generated by AI Question Guide'
math: mathjax
---

<style>
section {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    padding: 40px;
}}
.math-lesson {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}}
.learning-objectives {{ 
    background: rgba(232, 244, 253, 0.95); 
    padding: 1.5rem; 
    border-radius: 12px; 
    color: #333;
    margin: 1rem 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}
.solution-steps {{ 
    background: rgba(248, 249, 250, 0.95); 
    padding: 1.5rem; 
    border-radius: 12px; 
    color: #333;
    margin: 1rem 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}
.common-mistakes {{ 
    background: rgba(255, 243, 205, 0.95); 
    padding: 1.5rem; 
    border-radius: 12px; 
    color: #333;
    margin: 1rem 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}
.practice-problems {{ 
    background: rgba(209, 236, 241, 0.95); 
    padding: 1.5rem; 
    border-radius: 12px; 
    color: #333;
    margin: 1rem 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}
.final-answer {{ 
    background: rgba(212, 237, 218, 0.95); 
    padding: 1.5rem; 
    border-radius: 12px; 
    font-weight: bold; 
    color: #333;
    margin: 1rem 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    font-size: 1.2em;
}}

/* Marp-optimized Singapore Math Tape Diagram Styles */
.tape-diagram {{
    background: rgba(240, 248, 255, 0.95); 
    padding: 2rem; 
    border-radius: 16px; 
    margin: 2rem auto;
    border: 3px solid #4a90e2;
    max-width: 90%;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}}
.tape-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    margin: 1.5rem 0;
    min-height: 200px;
    justify-content: center;
}}
.tape-section, .tape-groups {{
    display: flex;
    gap: 15px;
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;
}}
.tape-bar {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 80px;
    min-width: 120px;
    border: 4px solid #333;
    border-radius: 12px;
    position: relative;
    font-weight: bold;
    text-align: center;
    font-size: 1.1em;
    padding: 10px;
}}
.tape-bar.known {{ background: #90EE90; }}
.tape-bar.unknown {{ background: #FFB6C1; }}
.tape-bar.total {{ background: #87CEEB; }}
.tape-bar.group {{ background: #DDA0DD; }}
.tape-bar.whole {{ background: #F0E68C; display: flex; flex-direction: row; }}
.tape-bar.generic {{ background: #D3D3D3; }}
.tape-part {{
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-right: 3px solid #333;
    font-size: 1em;
    padding: 5px;
}}
.tape-part:last-child {{ border-right: none; }}
.tape-part.known {{ background: #90EE90; }}
.tape-part.unknown {{ background: #FFB6C1; }}
.tape-label {{
    font-size: 0.9em;
    color: #333;
    margin-bottom: 5px;
    font-weight: 600;
}}
.tape-value {{
    font-size: 1.2em;
    font-weight: bold;
    color: #000;
}}
.tape-explanation {{
    background: rgba(255, 255, 255, 0.95);
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 6px solid #4a90e2;
    margin-top: 1.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}
.tape-total, .tape-labels {{
    margin-top: 15px;
    text-align: center;
    font-size: 1.1em;
}}
.whole-label {{
    font-weight: bold;
    color: #333;
    font-size: 1.1em;
}}

/* Marp-optimized Step Diagram Styles */
.step-diagram {{
    background: rgba(248, 249, 250, 0.95);
    padding: 2rem;
    border-radius: 16px;
    margin: 2rem auto;
    border: 3px solid #28a745;
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    max-width: 90%;
    min-height: 250px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}}
.step-diagram h5 {{
    color: #28a745;
    margin-bottom: 1.5rem;
    font-size: 1.4em;
    text-align: center;
}}
.operation-visual {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
    margin: 1.5rem 0;
    min-height: 100px;
}}
.operation-symbol, .equals {{
    font-size: 2em;
    font-weight: bold;
    color: #333;
    padding: 0 15px;
}}
.tape-bar.operand {{ background: #e3f2fd; border-color: #1976d2; }}
.tape-bar.result {{ background: #e8f5e8; border-color: #388e3c; }}
.tape-bar.minuend {{ background: #fff3e0; border-color: #f57c00; }}
.tape-bar.subtrahend {{ background: #ffebee; border-color: #d32f2f; }}
.tape-bar.dividend {{ background: #f3e5f5; border-color: #7b1fa2; }}
.tape-bar.step-info {{ background: #e1f5fe; border-color: #0277bd; }}
.multiplication-groups, .division-groups {{
    display: flex;
    gap: 12px;
    margin: 15px 0;
    flex-wrap: wrap;
    justify-content: center;
}}
.tape-group {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}}
.multiplication-result {{
    margin-top: 20px;
}}
.step-explanation {{
    background: rgba(255, 255, 255, 0.95);
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 6px solid #28a745;
    margin-top: 1.5rem;
    font-size: 1em;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}}

/* Marp slide-specific optimizations */
section.math-lesson h1 {{
    font-size: 2.5em;
    text-align: center;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}}
section.math-lesson h2 {{
    font-size: 2em;
    margin-bottom: 1rem;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}}
section.math-lesson h3 {{
    font-size: 1.5em;
    margin-bottom: 0.8rem;
}}
</style>

# 📚 {title}

---

## 🎯 Learning Objectives

<div class="learning-objectives">

"""
    
    for i, obj in enumerate(overview, 1):
        slides += f"{i}. {obj}\n"
    
    # Generate and include tape diagram
    tape_diagram = create_tape_diagram(problem_text, solution)
    
    slides += f"""
</div>

---

## 📊 Visual Problem Solving

{tape_diagram}

---

## 📖 Worked Example

<div class="solution-steps">

### Solution Process

{create_solution_with_diagrams(solution, problem_text)}

</div>

---

## ✅ Final Answer

<div class="final-answer">

**Answer:** {final_answer}

</div>

---

## ⚠️ Common Pitfalls

<div class="common-mistakes">

"""
    
    for mistake in mistakes:
        slides += f"- {mistake}\n"
    
    slides += f"""
</div>

---

## 🏃‍♂️ Practice Problems

<div class="practice-problems">

"""
    
    for i, prob in enumerate(practice, 1):
        slides += f"**Problem {i}:** {prob}\n\n"
    
    slides += f"""
</div>

---

## 📝 Summary

- **Key Concept:** {title}
- **Visual Strategy:** Use tape diagrams to represent relationships
- **Main Strategy:** {solution.split('.')[0] if solution else 'Problem-solving approach'}
- **Final Answer:** {final_answer}
- **Next Steps:** Practice the provided problems and identify any remaining questions

---

*Generated by AI Question Guide Generator with Singapore Math Visualization*
"""
    
    return slides

def try_sympy_check(expr_text: str) -> str | None:
    """Optional SymPy validation of mathematical expressions."""
    if sp is None:
        return None
    
    try:
        # Clean the expression
        cleaned = re.sub(r'[^\w\s\+\-\*/\(\)\^\.\=]', '', expr_text)
        if not cleaned.strip():
            return None
        
        # Try to parse and evaluate
        expr = sp.sympify(cleaned)
        simplified = sp.simplify(expr)
        
        if expr != simplified:
            return f"SymPy note: Expression can be simplified to {simplified}"
        
        return f"SymPy validation: Expression is valid"
    
    except Exception:
        return None

def parse_markdown_response(text: str, problem_text: str = "") -> Dict[str, Any]:
    """Parse markdown response into structured data."""
    
    # Initialize result dictionary
    result = {
        "overview": [],
        "solution": "",
        "final_answer": "",
        "mistakes": [],
        "practice": [],
        "problem_text": problem_text,  # Always preserve original problem text
        "manim_scripts": []  # Initialize empty Manim scripts array
    }
    
    # More robust section splitting to handle various formats:
    # - ## Header, ##_header, ## _header
    # - Numbered sections like "4. **Final Answer:**"
    # - Handle both with and without spaces/underscores
    
    # First, let's extract sections using a more comprehensive approach
    # Find all section headers and their positions
    # Support both ## and ### headers, including those with underscores
    section_pattern = r'^\s*(?:##|###)[\s_]*([^#\n]+)'
    sections_info = []
    
    for match in re.finditer(section_pattern, text, re.MULTILINE):
        start_pos = match.start()
        header = match.group(1).strip()
        sections_info.append((start_pos, header, match.group(0)))
    
    # Also look for numbered main sections like "4. **Final Answer:**" at the start of lines
    # but only if they appear to be main sections (not subsections within content)
    numbered_main_pattern = r'^(\d+)\.\s*\*\*([^*]+)\*\*:?\s*$'
    for match in re.finditer(numbered_main_pattern, text, re.MULTILINE):
        start_pos = match.start()
        header = match.group(2).strip()
        # Only add if it's likely a main section (check if it's not inside another section's content)
        is_main_section = True
        for existing_start, _, _ in sections_info:
            if existing_start < start_pos:
                # Check if this numbered item is too close to an existing section (likely a subsection)
                lines_between = text[existing_start:start_pos].count('\n')
                if lines_between < 10:  # Increased threshold - if less than 10 lines, likely a subsection
                    is_main_section = False
                    break
        
        # Additional check: if the header looks like a step in a solution, don't treat as main section
        step_keywords = ['define', 'set up', 'solve', 'substitute', 'calculate', 'find', 'determine']
        if any(keyword in header.lower() for keyword in step_keywords):
            is_main_section = False
        
        if is_main_section:
            sections_info.append((start_pos, header, match.group(0)))
    
    # Sort sections by position
    sections_info.sort(key=lambda x: x[0])
    
    # Extract content for each section
    for i, (start_pos, header, full_match) in enumerate(sections_info):
        # Find the end position (start of next section or end of text)
        if i + 1 < len(sections_info):
            end_pos = sections_info[i + 1][0]
            content = text[start_pos:end_pos]
        else:
            content = text[start_pos:]
        
        # Remove the header line from content
        content_lines = content.split('\n')[1:]  # Skip first line (header)
        content_text = '\n'.join(content_lines).strip()
        
        # Process based on header type
        header_clean = header.lower().strip().replace('_', ' ').replace(':', '').strip()
        
        if 'final answer' in header_clean or header_clean == 'answer' or header_clean == 'finalanswer':
            result["final_answer"] = content_text
        elif 'solution' in header_clean:
            result["solution"] = content_text
        elif 'common mistake' in header_clean or header_clean == 'mistakes' or header_clean == 'commonmistakes':
            # Parse mistakes content
            for line in content_text.split('\n'):
                line = line.strip()
                if line.startswith(('- ', '* ', '1. ', '2. ', '3. ')):
                    clean_line = re.sub(r'^[-*\d.]+\s*[🚫❌⚠️]*\s*', '', line).strip()
                    if clean_line:
                        result["mistakes"].append(clean_line)
                elif line and '**' in line and 'mistake' in line.lower():
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            clean_line = parts[1].strip()
                            if clean_line:
                                result["mistakes"].append(clean_line)
            
            # If no structured mistakes found, treat the whole content as one mistake
            if not result["mistakes"] and content_text:
                result["mistakes"].append(content_text)
        elif 'practice' in header_clean or header_clean == 'practiceproblems':
            # Parse practice problems content
            for line in content_text.split('\n'):
                line = line.strip()
                if line.startswith(('- ', '* ', '1. ', '2. ', '3. ')):
                    clean_line = re.sub(r'^[-*\d.]+\s*[📝✏️📋]*\s*', '', line).strip()
                    if clean_line:
                        result["practice"].append(clean_line)
                elif line and '**' in line:
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            clean_line = parts[1].strip()
                            if clean_line:
                                result["practice"].append(clean_line)
        elif 'overview' in header_clean:
            # Extract overview content
            if content_text:
                # Split by sentences for overview
                sentences = [s.strip() for s in content_text.split('.') if s.strip()]
                result["overview"] = [s + '.' for s in sentences if len(s) > 10]
    
    # Fallback: try regex-based extraction for missed sections
    if not result["final_answer"]:
        # Look for boxed answers at the end of content
        boxed_match = re.search(r'\boxed\{([^}]+)\}', text)
        if boxed_match:
            result["final_answer"] = boxed_match.group(1).strip()
        else:
            # Original fallback
            final_answer_match = re.search(r'(?:\d+\.\s*)?\*\*\s*Final Answer\s*\*\*:?\s*(.*?)(?=\n\s*(?:\d+\.\s*)?\*\*|\n\s*##|\Z)', text, re.DOTALL | re.IGNORECASE)
            if final_answer_match:
                result["final_answer"] = final_answer_match.group(1).strip()
    
    if not result["mistakes"]:
        mistakes_match = re.search(r'##_?common_?mistakes?\s*(.*?)(?=##|\Z)', text, re.DOTALL | re.IGNORECASE)
        if mistakes_match:
            mistakes_content = mistakes_match.group(1).strip()
            for line in mistakes_content.split('\n'):
                line = line.strip()
                if line.startswith(('- ', '* ')) and 'mistake' in line.lower():
                    clean_line = re.sub(r'^[-*]+\s*\*\*Common mistake:\*\*\s*', '', line).strip()
                    if clean_line:
                        result["mistakes"].append(clean_line)
    
    if not result["practice"]:
        practice_match = re.search(r'##_?practice_?problems?\s*(.*?)(?=##|\Z)', text, re.DOTALL | re.IGNORECASE)
        if practice_match:
            practice_content = practice_match.group(1).strip()
            for line in practice_content.split('\n'):
                line = line.strip()
                if line.startswith(('- ', '1. ', '2. ', '3. ', '* ')):
                    clean_line = re.sub(r'^[-*\d.]+\s*[📝✏️📋]*\s*', '', line).strip()
                    if clean_line:
                        result["practice"].append(clean_line)
    
    # Legacy section processing (keeping for compatibility)
    sections = re.split(r'^(?:##[\s_]+|\d+\.\s*\*\*)', text, flags=re.MULTILINE)
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Clean header by removing underscores and normalizing
        header = lines[0].lower().strip().replace('_', ' ')
        # Remove bold formatting from headers
        header = re.sub(r'\*\*([^*]*)\*\*', r'\1', header).strip()
        content_lines = lines[1:] if len(lines) > 1 else []
        
        if header == 'overview':
            # Extract content - handle both bullet points and paragraph text
            content_text = '\n'.join(content_lines).strip()
            if content_text:
                # Split by sentences or meaningful chunks for overview
                sentences = [s.strip() for s in content_text.split('.') if s.strip()]
                result["overview"] = [s + '.' for s in sentences if len(s) > 10]  # Filter out very short fragments
                    
        elif header == 'solution':
            # Join all content as solution text
            if not result["solution"]:  # Only set if not already extracted above
                result["solution"] = '\n'.join(content_lines).strip()
            
        elif header in ['final answer', 'answer']:
            # Join all content as final answer
            if not result["final_answer"]:  # Only set if not already extracted above
                result["final_answer"] = '\n'.join(content_lines).strip()
            
        elif header in ['common mistakes', 'mistakes']:
            # Extract mistakes - handle both bullet points and numbered items
            for line in content_lines:
                line = line.strip()
                if line.startswith(('- ', '1. ', '2. ', '3. ', '* ')):
                    # Remove bullet/number and emoji if present
                    clean_line = re.sub(r'^[-*\d.]+\s*[🚫❌⚠️]*\s*', '', line).strip()
                    if clean_line:
                        result["mistakes"].append(clean_line)
                elif line and not line.startswith('#') and '**' in line:
                    # Handle bold formatted mistakes - preserve content after colon
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            clean_line = parts[1].strip()
                            if clean_line:
                                result["mistakes"].append(clean_line)
                    else:
                        clean_line = re.sub(r'\*\*([^*]*)\*\*', r'\1', line).strip()
                        if clean_line:
                            result["mistakes"].append(clean_line)
                    
        elif header in ['practice problems', 'practice']:
            # Skip if already extracted above
            if not result["practice"]:
                # Extract practice problems - handle both bullet points and numbered items
                for line in content_lines:
                    line = line.strip()
                    if line.startswith(('- ', '1. ', '2. ', '3. ', '* ')):
                        # Remove bullet/number and emoji if present
                        clean_line = re.sub(r'^[-*\d.]+\s*[📝✏️📋]*\s*', '', line).strip()
                        if clean_line:
                            result["practice"].append(clean_line)
                    elif line and not line.startswith('#') and '**' in line:
                        # Handle bold formatted practice problems
                        if ':' in line:
                            parts = line.split(':', 1)
                            if len(parts) > 1:
                                clean_line = parts[1].strip()
                                if clean_line:
                                    result["practice"].append(clean_line)
                        else:
                            clean_line = re.sub(r'\*\*([^*]*)\*\*', r'\1', line).strip()
                            if clean_line and not clean_line.lower().startswith('practice'):
                                result["practice"].append(clean_line)
    
    # Clean up extracted content
    # Fix final_answer formatting
    if result["final_answer"]:
        # Remove leading bullet points and clean up
        result["final_answer"] = re.sub(r'^[-*•]\s*', '', result["final_answer"]).strip()
        # Fix escaped characters in LaTeX
        result["final_answer"] = result["final_answer"].replace('\\(', '\\(').replace('\\)', '\\)')
        result["final_answer"] = result["final_answer"].replace('\x08oxed', '\\boxed')
    
    # Clean up mistakes
    cleaned_mistakes = []
    for mistake in result["mistakes"]:
        # Remove "Common mistake:" prefix if present
        clean_mistake = re.sub(r'^\*\*Common mistake:\*\*\s*', '', mistake, flags=re.IGNORECASE).strip()
        clean_mistake = re.sub(r'^Common mistake:\s*', '', clean_mistake, flags=re.IGNORECASE).strip()
        if clean_mistake and clean_mistake not in cleaned_mistakes:
            cleaned_mistakes.append(clean_mistake)
    result["mistakes"] = cleaned_mistakes
    
    # Clean up practice problems
    cleaned_practice = []
    for practice in result["practice"]:
        clean_practice = practice.strip()
        if clean_practice and clean_practice not in cleaned_practice:
            cleaned_practice.append(clean_practice)
    result["practice"] = cleaned_practice
    
    return result


def extract_markdown_fallback(text: str, problem_text: str = "") -> Dict[str, Any]:
    """Fallback method to extract data from markdown text when structured parsing fails."""
    
    result = {
        "overview": [],
        "solution": "",
        "final_answer": "",
        "mistakes": [],
        "practice": [],
        "problem_text": problem_text,  # Always preserve original problem text
        "manim_scripts": []  # Initialize empty Manim scripts array
    }
    
    # Try to find overview section
    overview_match = re.search(r'(?:## Overview|Overview)(.*?)(?=##|\Z)', text, re.DOTALL | re.IGNORECASE)
    if overview_match:
        overview_text = overview_match.group(1)
        for line in overview_text.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                result["overview"].append(line[2:].strip())
    
    # Try to find solution section
    solution_match = re.search(r'(?:## Solution|Solution)(.*?)(?=##|\Z)', text, re.DOTALL | re.IGNORECASE)
    if solution_match:
        result["solution"] = solution_match.group(1).strip()
    
    # Try to find final answer section
    answer_match = re.search(r'(?:## Final Answer|Final Answer)(.*?)(?=##|\Z)', text, re.DOTALL | re.IGNORECASE)
    if answer_match:
        result["final_answer"] = answer_match.group(1).strip()
    
    # Try to find mistakes section
    mistakes_match = re.search(r'(?:## Common Mistakes|## Mistakes|Common Mistakes|Mistakes)(.*?)(?=##|\Z)', text, re.DOTALL | re.IGNORECASE)
    if mistakes_match:
        mistakes_text = mistakes_match.group(1)
        for line in mistakes_text.split('\n'):
            line = line.strip()
            if '🚫' in line:
                result["mistakes"].append(line.replace('- ', '').replace('🚫', '').strip())
    
    # Try to find practice section
    practice_match = re.search(r'(?:## Practice Problems|## Practice|Practice Problems|Practice)(.*?)(?=##|\Z)', text, re.DOTALL | re.IGNORECASE)
    if practice_match:
        practice_text = practice_match.group(1)
        for line in practice_text.split('\n'):
            line = line.strip()
            if '📝' in line:
                result["practice"].append(line.replace('- ', '').replace('📝', '').strip())
    
    return result


def clean_json_text(json_text: str) -> str:
    """Clean common JSON formatting issues."""
    try:
        # Replace single quotes with double quotes
        cleaned = json_text.replace("'", '"')
        
        # Remove trailing commas before closing braces/brackets
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        # Fix common escape issues
        cleaned = cleaned.replace('\n', '\\n').replace('\t', '\\t')
        
        # Remove any non-JSON content before the first brace
        first_brace = cleaned.find('{')
        if first_brace > 0:
            cleaned = cleaned[first_brace:]
        
        # Remove any non-JSON content after the last brace
        last_brace = cleaned.rfind('}')
        if last_brace > 0:
            cleaned = cleaned[:last_brace + 1]
        
        return cleaned
    except Exception as e:
        logging.error(f"Error cleaning JSON text: {str(e)}")
        return json_text

def extract_data_manually(text: str, problem_text: str = "") -> Dict[str, Any]:
    """Extract structured data manually when JSON parsing fails."""
    try:
        data = {
            "overview": ["Problem analysis and solution approach"],
            "solution": "",
            "final_answer": "",
            "mistakes": ["Review the solution for potential errors"],
            "practice": ["Create similar problems for practice"],
            "problem_text": problem_text,  # Always preserve original problem text
            "manim_scripts": []  # Initialize empty Manim scripts array
        }
        
        # Extract the main solution content
        # Look for step-by-step solution or main mathematical content
        solution_patterns = [
            r'\*\*Step-by-Step Solution:\*\*(.*?)(?=\*\*Final Answer|\*\*Common Mistakes|\*\*Practice|$)',
            r'Step-by-Step Solution:(.*?)(?=Final Answer|Common Mistakes|Practice|$)',
            r'Solution:(.*?)(?=Answer|Mistakes|Practice|$)',
        ]
        
        for pattern in solution_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                data["solution"] = match.group(1).strip()
                break
        
        # If no solution section found, use the main content up to final answer
        if not data["solution"]:
            # Take content before "Final Answer" or use all content
            final_answer_pos = text.lower().find('final answer')
            if final_answer_pos > 0:
                data["solution"] = text[:final_answer_pos].strip()
            else:
                data["solution"] = text.strip()
        
        # Extract final answer
        final_answer_patterns = [
            r'\\boxed\{([^}]+)\}',
            r'\*\*Final Answer:\*\*\s*\\?\[?\s*\\?boxed\{([^}]+)\}\s*\\?\]?',
            r'Final Answer:\s*([^\n\*]+)',
            r'Answer:\s*([^\n\*]+)',
            r'Therefore,?\s*([^\n\.]+)',
        ]
        
        for pattern in final_answer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data["final_answer"] = match.group(1).strip()
                break
        
        # Extract mistakes if present
        mistakes_match = re.search(r'\*\*Common Mistakes:\*\*(.*?)(?=\*\*Practice|\*\*$|$)', text, re.DOTALL | re.IGNORECASE)
        if mistakes_match:
            mistakes_text = mistakes_match.group(1)
            # Extract individual mistakes
            mistake_lines = [line.strip() for line in mistakes_text.split('\n') if line.strip() and ('mistake' in line.lower() or line.strip().startswith(('1.', '2.', '3.', '-', '*')))]
            if mistake_lines:
                data["mistakes"] = [f"🚫 {line}" for line in mistake_lines[:3]]  # Limit to 3 mistakes
        
        # Extract practice problems if present
        practice_match = re.search(r'\*\*Practice Problems?:\*\*(.*?)$', text, re.DOTALL | re.IGNORECASE)
        if practice_match:
            practice_text = practice_match.group(1)
            # Extract individual practice problems
            practice_lines = [line.strip() for line in practice_text.split('\n') if line.strip() and ('problem' in line.lower() or line.strip().startswith(('1.', '2.', '3.', '-', '*')))]
            if practice_lines:
                data["practice"] = [f"📝 {line}" for line in practice_lines[:3]]  # Limit to 3 practice problems
        
        return data
        
    except Exception as e:
        logging.error(f"Error extracting data manually: {str(e)}")
        return {
            "overview": ["Problem analysis needed"],
            "solution": text.strip() if text.strip() else "No solution provided",
            "final_answer": "Answer not clearly identified",
            "mistakes": ["Review the solution for potential errors"],
            "practice": ["Create similar problems for practice"]
        }

def construct_json_from_text(text: str) -> str:
    """Construct JSON from structured text when no JSON block is found."""
    try:
        # Initialize the structure
        result = {
            "overview": [],
            "solution": "",
            "final_answer": "",
            "mistakes": [],
            "practice": []
        }
        
        # Extract solution section
        solution_match = re.search(r'\*\*Step-by-Step Solution:\*\*(.*?)(?=\*\*|$)', text, re.DOTALL | re.IGNORECASE)
        if solution_match:
            result["solution"] = solution_match.group(1).strip()
        else:
            # If no explicit solution section, use the main content
            result["solution"] = text.strip()
        
        # Extract final answer (look for boxed answers or explicit final answer sections)
        final_answer_patterns = [
            r'\\boxed\{([^}]+)\}',
            r'\*\*Final Answer:\*\*\s*([^\n\*]+)',
            r'Final Answer:\s*([^\n\*]+)',
            r'Answer:\s*([^\n\*]+)',
        ]
        
        for pattern in final_answer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["final_answer"] = match.group(1).strip()
                break
        
        # Extract common mistakes
        mistakes_section = re.search(r'\*\*Common Mistakes:\*\*(.*?)(?=\*\*|$)', text, re.DOTALL | re.IGNORECASE)
        if mistakes_section:
            mistakes_text = mistakes_section.group(1)
            # Look for numbered or bulleted mistakes
            mistake_items = re.findall(r'(?:^\d+\.|^\*|^-|\*\*Mistake \d+:\*\*)(.*?)(?=(?:^\d+\.|^\*|^-|\*\*Mistake \d+:\*\*|$))', mistakes_text, re.MULTILINE | re.DOTALL)
            result["mistakes"] = [f"🚫 {item.strip()}" for item in mistake_items if item.strip()]
        
        # Extract practice problems
        practice_section = re.search(r'\*\*Practice Problems:\*\*(.*?)(?=\*\*|$)', text, re.DOTALL | re.IGNORECASE)
        if practice_section:
            practice_text = practice_section.group(1)
            # Look for numbered or bulleted practice problems
            practice_items = re.findall(r'(?:^\d+\.|^\*|^-|\*\*.*?Problem \d+:\*\*)(.*?)(?=(?:^\d+\.|^\*|^-|\*\*.*?Problem \d+:\*\*|$))', practice_text, re.MULTILINE | re.DOTALL)
            result["practice"] = [f"📝 {item.strip()}" for item in practice_items if item.strip()]
        
        # Generate overview based on content
        if result["solution"]:
            result["overview"] = [
                "Understand the problem setup and variables",
                "Apply systematic equation solving techniques", 
                "Verify the solution and interpret results"
            ]
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logging.error(f"Error constructing JSON from text: {str(e)}")
        return "{}"

def generate_for_problem(model, tokenizer, prob: Problem, args) -> Tuple[Dict[str, Any], str]:
    """Generate explanation and slides for a problem with comprehensive error handling."""
    try:
        logging.info(f"Generating content for problem {prob.index}: {prob.title}")
        
        msgs = explanation_prompt(prob.content, getattr(args, 'grade_level', 'middle school'))
        raw = chat_completion(
            model,
            tokenizer,
            msgs,
            max_new_tokens=getattr(args, 'max_new_tokens', 1024),
            temperature=getattr(args, 'temperature', 0.7),
            top_p=getattr(args, 'top_p', 0.9),
        )
        print(raw)
        
        # First try to parse as markdown (new approach)
        try:
            logging.info(f"Attempting to parse markdown response for problem {prob.index}")
            data = parse_markdown_response(raw, prob.content)
            
            # Check if we got meaningful data
            if (data.get("solution") or data.get("overview") or 
                data.get("final_answer") or data.get("mistakes") or data.get("practice")):
                logging.debug(f"Successfully parsed markdown for problem {prob.index}")
            else:
                # Try fallback markdown parsing
                logging.info(f"Primary markdown parsing yielded empty results, trying fallback for problem {prob.index}")
                data = extract_markdown_fallback(raw, prob.content)
                
        except Exception as e:
            logging.warning(f"Markdown parsing failed for problem {prob.index}: {str(e)}")
            # Try fallback markdown parsing
            data = extract_markdown_fallback(raw, prob.content)
        
        # If markdown parsing didn't work well, try JSON parsing as fallback
        if not any([data.get("solution"), data.get("overview"), data.get("final_answer")]):
            logging.info(f"Markdown parsing unsuccessful, attempting JSON fallback for problem {prob.index}")
            
            # Extract JSON from the model output with robust parsing
            json_text = None
            
            # Look for JSON patterns in order of preference
            patterns = [
                # Complete JSON object with proper braces
                r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
                # JSON in code blocks
                r'```json\s*([\s\S]*?)```',
                r'```\s*(\{[\s\S]*?\})\s*```',
                # JSON at the end of response
                r'\{[\s\S]*\}\s*$',
                # Any JSON-like structure
                r'\{[\s\S]*?\}',
            ]
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, raw, re.MULTILINE | re.DOTALL)
                if matches:
                    # Take the longest match (most likely to be complete)
                    json_text = max(matches, key=len) if isinstance(matches[0], str) else matches[0]
                    logging.debug(f"Found JSON using pattern {i+1}: {json_text[:100]}...")
                    break
            
            # If JSON found, try to parse it
            if json_text and json_text.strip() != "{}":
                try:
                    print(f"Attempting to parse JSON: {json_text[:200]}...")
                    json_data = json.loads(json_text)
                    logging.debug(f"Successfully parsed JSON for problem {prob.index}")
                    # Use JSON data if it's better than markdown data
                    if isinstance(json_data, dict) and json_data.get("solution"):
                        data = json_data
                except json.JSONDecodeError as e:
                    logging.warning(f"Failed to parse JSON for problem {prob.index}: {str(e)}")
                    # Try to clean up common JSON issues
                    cleaned_json = clean_json_text(json_text)
                    
                    try:
                        json_data = json.loads(cleaned_json)
                        logging.debug(f"Successfully parsed cleaned JSON for problem {prob.index}")
                        if isinstance(json_data, dict) and json_data.get("solution"):
                            data = json_data
                    except json.JSONDecodeError as e2:
                        logging.error(f"Could not parse JSON even after cleaning for problem {prob.index}: {str(e2)}")
        
        # Final fallback if no good data was extracted
        if not any([data.get("solution"), data.get("overview"), data.get("final_answer")]):
            logging.warning(f"No structured data found, creating fallback for problem {prob.index}")
            data = {
                "overview": ["Problem analysis and solution approach"],
                "solution": raw.strip() if raw.strip() else "No solution provided",
                "final_answer": "Answer not clearly identified",
                "mistakes": ["Review the solution for potential errors"],
                "practice": ["Create similar problems for practice"],
                "problem_text": prob.content  # Always preserve original problem text
            }

        # Validate data structure
        if not isinstance(data, dict):
            logging.warning(f"Response is not a dictionary for problem {prob.index}")
            data = {"solution": str(data)}

        # Optional sympy check
        if isinstance(data, dict) and data.get("final_answer"):
            note = try_sympy_check(data["final_answer"])
            if note:
                data.setdefault("notes", []).append(note)

        # Ensure problem_text is available for tape diagram generation
        if isinstance(data, dict):
            data["problem_text"] = prob.content
            
            # Generate Manim script for equations found in the problem
            try:
                equations = extract_equations_from_text(prob.content)
                if equations:
                    logging.info(f"Found {len(equations)} equations in problem {prob.index}: {equations}")
                    manim_scripts = []
                    for eq in equations:
                        script = create_manim_equation_script(eq, prob.content)
                        manim_scripts.append({
                            "equation": eq,
                            "script": script,
                            "filename": f"equation_{hash(eq) % 10000}.py"
                        })
                    data["manim_scripts"] = manim_scripts
                    logging.info(f"Generated {len(manim_scripts)} Manim scripts for problem {prob.index}")
                else:
                    logging.debug(f"No equations found in problem {prob.index}")
                    data["manim_scripts"] = []
            except Exception as e:
                logging.warning(f"Failed to generate Manim scripts for problem {prob.index}: {str(e)}")
                data["manim_scripts"] = []
        
        slide_md = slides_from_explanation(prob.title, data if isinstance(data, dict) else {"solution": raw, "problem_text": prob.content})
        
        logging.info(f"Successfully generated content for problem {prob.index}")
        return data, slide_md
    
    except Exception as e:
        logging.error(f"Error generating content for problem {prob.index}: {str(e)}")
        logging.error(traceback.format_exc())
        
        # Return error data
        error_data = {
            "error": str(e),
            "solution": f"Error occurred while processing this problem: {str(e)}",
            "final_answer": "Error",
            "overview": ["Error processing problem"],
            "mistakes": ["Check logs for details"],
            "practice": [],
            "problem_text": prob.content,
            "manim_scripts": []
        }
        error_slides = slides_from_explanation(prob.title, error_data)
        return error_data, error_slides

def main():
    """Main function to orchestrate the lesson generation process."""
    parser = argparse.ArgumentParser(description="AI-powered Question Guidance and Instruction Generation Tool")
    parser.add_argument("--input", "-i", default='QuestionGuide/math_problems.docx', help="Input file with problems (supports .md, .txt, .docx)")
    parser.add_argument("--output", "-o", default="output", help="Output directory for generated lessons")
    parser.add_argument("--model", "-m", default="Qwen/Qwen2.5-Math-7B-Instruct", help="Hugging Face model to use")
    parser.add_argument("--grade-level", "-g", default="elementary", choices=["elementary", "middle school", "high school"], help="Grade level for content adaptation")
    parser.add_argument("--max-new-tokens", type=int, default=2048, help="Maximum generation tokens 1024")
    parser.add_argument("--temperature", type=float, default=0.7, help="Generation temperature")
    parser.add_argument("--top-p", type=float, default=0.9, help="Top-p sampling parameter")
    parser.add_argument("--device", default="auto", help="Device to use (auto, cpu, cuda)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.output)
    
    try:
        logging.info("Starting AI Question Guidance Generator")
        logging.info(f"Input file: {args.input}")
        logging.info(f"Output directory: {args.output}")
        logging.info(f"Model: {args.model}")
        
        # Create output directory
        os.makedirs(args.output, exist_ok=True)
        
        # Read problems from input file
        problems = read_problems(args.input)
        if not problems:
            logging.error("No problems found in input file")
            return
        
        logging.info(f"Found {len(problems)} problems to process")
        
        # Build model and tokenizer
        model, tokenizer = build_model_and_tokenizer(args.model, args.device)
        
        # Process each problem
        all_results = []
        for i, problem in enumerate(problems):
            logging.info(f"Processing problem {i+1}/{len(problems)}: {problem.title}")
            
            try:
                # Generate content for the problem
                data, slides = generate_for_problem(model, tokenizer, problem, args)
                
                # Save individual outputs
                problem_output_dir = os.path.join(args.output, f"problem_{i+1:02d}")
                os.makedirs(problem_output_dir, exist_ok=True)
                
                # Save JSON
                json_path = os.path.join(problem_output_dir, "explanation.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Save slides
                slides_path = os.path.join(problem_output_dir, "slides.md")
                with open(slides_path, 'w', encoding='utf-8') as f:
                    f.write(slides)
                
                all_results.append({
                    'problem': problem,
                    'data': data,
                    'slides': slides
                })
                
                logging.info(f"Problem {i+1} completed successfully")
                
            except Exception as e:
                logging.error(f"Failed to process problem {i+1}: {str(e)}")
                logging.error(traceback.format_exc())
                continue
        
        # Create master README
        readme_content = f"""# AI Question Guidance Generator Results

Generated on: {time.strftime("%Y-%m-%d %H:%M:%S")}
Total problems processed: {len(all_results)}
Model used: {args.model}

## Generated Content

Each problem has been processed and saved in its own directory:

"""
        
        for i, result in enumerate(all_results):
            problem_title = result['problem'].title
            readme_content += f"- **Problem {i+1}**: {problem_title}\n"
            readme_content += f"  - Directory: `problem_{i+1:02d}/`\n"
            readme_content += f"  - Files: `explanation.json`, `slides.md`\n\n"
        
        readme_content += f"""
## Usage Instructions

1. **JSON Data**: Contains all generated content in structured format
2. **Slides**: Ready-to-use Markdown slides for presentations

## Model Configuration

- Model: {args.model}
- Max New Tokens: {args.max_new_tokens}
- Temperature: {args.temperature}
- Top-p: {args.top_p}
- Device: {args.device}

Generated by AI Question Guide Generator
"""
        
        readme_path = os.path.join(args.output, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logging.info(f"Generation completed successfully!")
        logging.info(f"Results saved to: {args.output}")
        logging.info(f"Total problems processed: {len(all_results)}")
        
    except Exception as e:
        logging.error(f"Fatal error in main execution: {str(e)}")
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
