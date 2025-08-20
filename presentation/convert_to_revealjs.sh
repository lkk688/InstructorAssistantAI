#!/bin/bash

# Pandoc + reveal.js Presentation Converter
# Converts physical_ai_autonomous_driving.md to reveal.js presentation

echo "Converting Markdown to reveal.js presentation..."

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "Error: pandoc is not installed"
    echo "Please install pandoc:"
    echo "  macOS: brew install pandoc"
    echo "  Linux: sudo apt-get install pandoc"
    echo "  Windows: Download from https://pandoc.org/installing.html"
    exit 1
fi

# Input and output files
INPUT_FILE="docs/physical_ai_autonomous_driving.md"
OUTPUT_FILE="physical_ai_presentation.html"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE not found"
    exit 1
fi

echo "Converting $INPUT_FILE to $OUTPUT_FILE..."

# Convert using pandoc with reveal.js
pandoc "$INPUT_FILE" \
    -t revealjs \
    -s \
    -o "$OUTPUT_FILE" \
    --slide-level=2 \
    --theme=black \
    --transition=slide \
    --highlight-style=github \
    --mathjax \
    --variable revealjs-url=https://unpkg.com/reveal.js@4.3.1/ \
    --variable theme=black \
    --variable transition=slide \
    --variable backgroundTransition=fade \
    --variable hash=true \
    --variable controls=true \
    --variable progress=true \
    --variable center=true \
    --variable touch=true \
    --variable loop=false \
    --variable rtl=false \
    --variable navigationMode=default \
    --variable previewLinks=false \
    --variable hideAddressBar=true \
    --metadata title="Physical AI and LLMs in Autonomous Driving" \
    --metadata author="AI Research Team" \
    --metadata date="$(date +'%Y-%m-%d')"

if [ $? -eq 0 ]; then
    echo "✅ Conversion successful!"
    echo "📄 Output: $OUTPUT_FILE"
    echo "🌐 Open in browser to view the presentation"
    
    # Try to open in browser (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Opening presentation in browser..."
        open "$OUTPUT_FILE"
    fi
else
    echo "❌ Conversion failed. Check the error messages above."
    exit 1
fi

echo "Done!"
echo ""
echo "Presentation features:"
echo "  - Use arrow keys to navigate"
echo "  - Press 'f' for fullscreen"
echo "  - Press 's' for speaker notes"
echo "  - Press 'o' for overview mode"
echo "  - Press '?' for help"