#!/bin/bash

# LaTeX Beamer Presentation Compilation Script
# This script compiles the presentation.tex file into a PDF

echo "Compiling LaTeX Beamer presentation..."

# Check if pdflatex is available
if ! command -v pdflatex &> /dev/null; then
    echo "Error: pdflatex is not installed or not in PATH"
    echo "Please install a LaTeX distribution like MacTeX, TeX Live, or MiKTeX"
    echo "For macOS: brew install --cask mactex"
    exit 1
fi

# Compile the presentation (run twice for proper references)
echo "First compilation pass..."
pdflatex -interaction=nonstopmode presentation.tex

if [ $? -eq 0 ]; then
    echo "Second compilation pass..."
    pdflatex -interaction=nonstopmode presentation.tex
    
    if [ $? -eq 0 ]; then
        echo "✅ Compilation successful!"
        echo "📄 Output: presentation.pdf"
        
        # Clean up auxiliary files
        echo "Cleaning up auxiliary files..."
        rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb *.fls *.fdb_latexmk *.synctex.gz
        
        # Open the PDF if on macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "Opening presentation.pdf..."
            open presentation.pdf
        fi
    else
        echo "❌ Second compilation failed. Check the LaTeX log for errors."
        exit 1
    fi
else
    echo "❌ First compilation failed. Check the LaTeX log for errors."
    exit 1
fi

echo "Done!"