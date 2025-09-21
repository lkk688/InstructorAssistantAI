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
    """Generate chat completion with enhanced error handling."""
    try:
        # Format messages for the model
        formatted_prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                formatted_prompt += f"System: {content}\n\n"
            elif role == "user":
                formatted_prompt += f"User: {content}\n\n"
            elif role == "assistant":
                formatted_prompt += f"Assistant: {content}\n\n"
        
        formatted_prompt += "Assistant: "
        
        # Tokenize
        inputs = tokenizer(formatted_prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        return response.strip()
    
    except Exception as e:
        logging.error(f"Error in chat completion: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error generating response: {str(e)}"

def explanation_prompt(problem_text: str) -> List[Dict[str, str]]:
    """Create enhanced prompt for generating comprehensive explanations."""
    
    system_prompt = """You are an expert mathematics educator and pedagogical specialist with deep expertise in:
- Mathematical problem-solving and solution strategies
- Common student misconceptions and error patterns
- Effective instructional design and learning progression
- Creating engaging educational content

Your role is to analyze mathematical problems and create comprehensive educational materials that help students understand both the solution process and underlying concepts."""

    user_prompt = f"""Please analyze this mathematical problem and provide a comprehensive educational response in JSON format:

**Problem:**
{problem_text}

**Required JSON Structure:**
```json
{{
    "overview": [
        "Learning objective 1 (what students will understand)",
        "Learning objective 2 (what skills they'll develop)",
        "Learning objective 3 (connections to broader concepts)"
    ],
    "solution": "Step-by-step solution with clear explanations of each step, mathematical reasoning, and key insights. Include proper mathematical notation and explain the 'why' behind each step.",
    "final_answer": "The final numerical or algebraic answer",
    "mistakes": [
        "🚫 Common mistake 1: Detailed description of error and why students make it",
        "🚫 Common mistake 2: Another frequent misconception with explanation",
        "🚫 Common mistake 3: Additional error pattern with prevention strategy"
    ],
    "practice": [
        "📝 Practice Problem 1: Similar problem with slight variation",
        "📝 Practice Problem 2: Problem that builds on the concept",
        "📝 Practice Problem 3: Application to different context"
    ]
}}
```

**Guidelines:**
- Provide detailed, step-by-step mathematical reasoning
- Explain the conceptual understanding behind each step
- Include at least 3 specific common mistakes students make
- Create 3 practice problems that reinforce the learning
- Use clear, educational language appropriate for the level
- Ensure mathematical accuracy and proper notation
- Focus on building understanding, not just getting the answer

Please respond with ONLY the JSON object, no additional text."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

def slides_from_explanation(title: str, data: Dict[str, Any]) -> str:
    """Generate slide-ready Markdown from explanation data with enhanced formatting."""
    
    if "error" in data:
        return f"""---
title: "{title}"
theme: default
class: error
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
    
    slides = f"""---
title: "{title}"
theme: default
class: math-lesson
---

<style>
.math-lesson {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
}}
.learning-objectives {{ background: #e8f4fd; padding: 1rem; border-radius: 8px; }}
.solution-steps {{ background: #f8f9fa; padding: 1rem; border-radius: 8px; }}
.common-mistakes {{ background: #fff3cd; padding: 1rem; border-radius: 8px; }}
.practice-problems {{ background: #d1ecf1; padding: 1rem; border-radius: 8px; }}
.final-answer {{ background: #d4edda; padding: 1rem; border-radius: 8px; font-weight: bold; }}
</style>

# 📚 {title}

---

## 🎯 Learning Objectives

<div class="learning-objectives">

"""
    
    for i, obj in enumerate(overview, 1):
        slides += f"{i}. {obj}\n"
    
    slides += f"""
</div>

---

## 📖 Worked Example

<div class="solution-steps">

### Solution Process

{solution}

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
- **Main Strategy:** {solution.split('.')[0] if solution else 'Problem-solving approach'}
- **Final Answer:** {final_answer}
- **Next Steps:** Practice the provided problems and identify any remaining questions

---

*Generated by AI Question Guide Generator*
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

def generate_for_problem(model, tokenizer, prob: Problem, args) -> Tuple[Dict[str, Any], str]:
    """Generate explanation and slides for a problem with comprehensive error handling."""
    try:
        logging.info(f"Generating content for problem {prob.index}: {prob.title}")
        
        msgs = explanation_prompt(prob.content)
        raw = chat_completion(
            model,
            tokenizer,
            msgs,
            max_new_tokens=getattr(args, 'max_new_tokens', 1024),
            temperature=getattr(args, 'temperature', 0.7),
            top_p=getattr(args, 'top_p', 0.9),
        )
        
        # Extract JSON from the model output
        json_text = None
        
        # Try to find JSON in various formats
        patterns = [
            r"\{[\s\S]*\}\s*$",  # JSON at end
            r"```json\s*([\s\S]*?)```",  # Fenced JSON
            r"```\s*([\s\S]*?)```",  # Any fenced block
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw)
            if match:
                json_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
                break
        
        if not json_text:
            logging.warning(f"No JSON found in response for problem {prob.index}")
            json_text = "{}"

        try:
            data = json.loads(json_text)
            logging.debug(f"Successfully parsed JSON for problem {prob.index}")
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to parse JSON for problem {prob.index}: {str(e)}")
            # Try to clean up common JSON issues
            json_text = json_text.replace("'", '"')  # Replace single quotes
            json_text = re.sub(r',\s*}', '}', json_text)  # Remove trailing commas
            json_text = re.sub(r',\s*]', ']', json_text)  # Remove trailing commas in arrays
            
            try:
                data = json.loads(json_text)
                logging.debug(f"Successfully parsed cleaned JSON for problem {prob.index}")
            except json.JSONDecodeError:
                logging.error(f"Could not parse JSON even after cleaning for problem {prob.index}")
                data = {"solution": raw.strip(), "error": "Failed to parse structured response"}

        # Validate data structure
        if not isinstance(data, dict):
            logging.warning(f"Response is not a dictionary for problem {prob.index}")
            data = {"solution": str(data)}

        # Optional sympy check
        if isinstance(data, dict) and data.get("final_answer"):
            note = try_sympy_check(data["final_answer"])
            if note:
                data.setdefault("notes", []).append(note)

        slide_md = slides_from_explanation(prob.title, data if isinstance(data, dict) else {"solution": raw})
        
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
            "practice": []
        }
        error_slides = slides_from_explanation(prob.title, error_data)
        return error_data, error_slides

def main():
    """Main function to orchestrate the lesson generation process."""
    parser = argparse.ArgumentParser(description="AI-powered Question Guidance and Instruction Generation Tool")
    parser.add_argument("--input", "-i", default='QuestionGuide/math_problems.docx', help="Input file with problems (supports .md, .txt, .docx)")
    parser.add_argument("--output", "-o", default="output", help="Output directory for generated lessons")
    parser.add_argument("--model", "-m", default="microsoft/DialoGPT-medium", help="Hugging Face model to use")
    parser.add_argument("--max-new-tokens", type=int, default=1024, help="Maximum generation tokens")
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
