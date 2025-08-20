#!/usr/bin/env python3
"""
Preprocess Markdown for reveal.js slides
Optimizes the Physical AI document for better slide presentation
"""

import re
import sys
from pathlib import Path

def preprocess_markdown_for_slides(input_file, output_file):
    """Convert markdown to slide-friendly format"""
    
    if not Path(input_file).exists():
        print(f"Error: Input file {input_file} not found")
        sys.exit(1)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Convert ## headers to slide breaks
    content = re.sub(r'^## (.+)$', r'\n---\n\n## \1', content, flags=re.MULTILINE)
    
    # Convert ### headers to slide breaks with smaller titles
    content = re.sub(r'^### (.+)$', r'\n---\n\n### \1', content, flags=re.MULTILINE)
    
    # Ensure proper spacing around slide breaks
    content = re.sub(r'\n---\n\n', '\n\n---\n\n', content)
    
    # Remove excessive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Preprocessed {input_file} -> {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 preprocess_for_slides.py <input_file> <output_file>")
        sys.exit(1)
    
    preprocess_markdown_for_slides(sys.argv[1], sys.argv[2])

def preprocess_markdown(content):
    """
    Preprocess markdown content for better slide presentation
    """
    lines = content.split('\n')
    processed_lines = []
    
    # Track current section for better slide organization
    in_code_block = False
    
    for i, line in enumerate(lines):
        # Track code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
        
        # Skip processing inside code blocks
        if in_code_block:
            processed_lines.append(line)
            continue
            
        # Convert level 1 headers to slide separators
        if line.startswith('# ') and not line.startswith('## '):
            # Add slide separator before major sections
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append('')
                processed_lines.append('---')
                processed_lines.append('')
            processed_lines.append(line)
            
        # Convert level 2 headers to new slides
        elif line.startswith('## '):
            # Add slide separator
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append('')
                processed_lines.append('---')
                processed_lines.append('')
            processed_lines.append(line)
            
        # Convert level 3 headers to slide content
        elif line.startswith('### '):
            processed_lines.append(line)
            
        # Handle special markdown elements
        elif line.strip().startswith('!!! '):
            # Convert admonitions to blockquotes
            admonition_type = line.strip().split()[1]
            title = line.strip().split('"')[1] if '"' in line else admonition_type.title()
            processed_lines.append(f'> **{title}**')
            processed_lines.append('>')
            
        # Handle tables - make them smaller for slides
        elif '|' in line and line.strip().startswith('|'):
            # Add class for smaller tables
            if i > 0 and not lines[i-1].strip().startswith('<div'):
                processed_lines.append('<div class="small-text">')
            processed_lines.append(line)
            # Check if this is the last table row
            if i < len(lines) - 1 and not lines[i+1].strip().startswith('|'):
                processed_lines.append('</div>')
                
        # Handle long paragraphs - split them for better readability
        elif len(line.strip()) > 200 and not line.startswith(('- ', '* ', '1. ')):
            # Split long paragraphs into bullet points if they contain multiple sentences
            sentences = re.split(r'(?<=[.!?])\s+', line.strip())
            if len(sentences) > 2:
                for sentence in sentences:
                    if sentence.strip():
                        processed_lines.append(f'- {sentence.strip()}')
            else:
                processed_lines.append(line)
                
        # Handle image references
        elif line.strip().startswith('!['):
            # Add center class to images
            img_match = re.match(r'!\[([^\]]*)\]\(([^\)]+)\)', line.strip())
            if img_match:
                alt_text, img_path = img_match.groups()
                processed_lines.append(f'<img src="{img_path}" alt="{alt_text}" class="center-image" />')
            else:
                processed_lines.append(line)
                
        # Handle mermaid diagrams
        elif line.strip().startswith('```mermaid'):
            processed_lines.append('```mermaid')
            processed_lines.append('%%{init: {"theme":"dark", "themeVariables": {"primaryColor":"#42A5F5"}}}%%')
            
        # Regular lines
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)

def add_title_slide(content):
    """
    Add a proper title slide at the beginning
    """
    title_slide = '''---
title: "Physical AI and Large Language Models in Autonomous Driving"
author: "AI Research Team"
date: "2024"
---

# Physical AI and Large Language Models in Autonomous Driving

## A Comprehensive Overview

**AI Research Team**  
*2024*

---

## Presentation Overview

- **Introduction**: The Convergence of Physical AI and LLMs
- **Importance**: Why Physical AI & LLMs are Crucial
- **Current Solutions**: Traditional and Modern Approaches
- **Case Study**: Tesla's Latest Architecture
- **Technical Deep Dive**: Vision, Planning, and Control
- **Future Directions**: Research and Development

---

'''
    
    # Find the first main heading and insert title slide before it
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('# ') and not line.startswith('## '):
            lines.insert(i, title_slide)
            break
    
    return '\n'.join(lines)

def main():
    input_file = Path('docs/physical_ai_autonomous_driving.md')
    output_file = Path('physical_ai_slides.md')
    
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)
    
    print(f"Preprocessing {input_file} for slides...")
    
    # Read the original file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Preprocess the content
    processed_content = preprocess_markdown(content)
    processed_content = add_title_slide(processed_content)
    
    # Write the processed file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(processed_content)
    
    print(f"✅ Preprocessed file saved as {output_file}")
    print("Ready for pandoc conversion to reveal.js")

if __name__ == '__main__':
    main()