#!/bin/bash

# General Purpose Pandoc + reveal.js Presentation Generator
# Converts any markdown file to reveal.js presentation

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -i, --input FILE        Input markdown file (required)"
    echo "  -p, --preprocessed FILE Preprocessed markdown file name (optional)"
    echo "  -o, --output FILE       Output HTML file name (optional)"
    echo "  -t, --title TITLE       Presentation title (optional)"
    echo "  -a, --author AUTHOR     Presentation author (optional)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -i docs/my_document.md"
    echo "  $0 -i docs/my_document.md -p my_slides.md -o my_presentation.html"
    echo "  $0 -i docs/my_document.md -t \"My Presentation\" -a \"John Doe\""
}

# Default values
INPUT_FILE=""
PREPROCESSED_FILE=""
OUTPUT_FILE=""
PRESENTATION_TITLE=""
PRESENTATION_AUTHOR="AI Research Team"
CONFIG_FILE="pandoc_revealjs_config.yaml"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input)
            INPUT_FILE="$2"
            shift 2
            ;;
        -p|--preprocessed)
            PREPROCESSED_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -t|--title)
            PRESENTATION_TITLE="$2"
            shift 2
            ;;
        -a|--author)
            PRESENTATION_AUTHOR="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Error: Unknown option $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if input file is provided
if [ -z "$INPUT_FILE" ]; then
    echo "❌ Error: Input file is required"
    show_usage
    exit 1
fi

# Generate default file names if not provided
if [ -z "$PREPROCESSED_FILE" ]; then
    # Extract filename without extension and add _slides.md
    BASENAME=$(basename "$INPUT_FILE" .md)
    PREPROCESSED_FILE="${BASENAME}_slides.md"
fi

if [ -z "$OUTPUT_FILE" ]; then
    # Extract filename without extension and add _presentation.html
    BASENAME=$(basename "$INPUT_FILE" .md)
    OUTPUT_FILE="${BASENAME}_presentation.html"
fi

if [ -z "$PRESENTATION_TITLE" ]; then
    # Generate title from filename
    BASENAME=$(basename "$INPUT_FILE" .md)
    PRESENTATION_TITLE=$(echo "$BASENAME" | sed 's/_/ /g' | sed 's/\b\w/\u&/g')
fi

echo "🚀 Creating reveal.js presentation with Pandoc..."
echo "================================================"
echo "📄 Input file: $INPUT_FILE"
echo "📝 Preprocessed file: $PREPROCESSED_FILE"
echo "🎯 Output file: $OUTPUT_FILE"
echo "📋 Title: $PRESENTATION_TITLE"
echo "👤 Author: $PRESENTATION_AUTHOR"
echo ""

# Check dependencies
echo "Checking dependencies..."

if ! command -v pandoc &> /dev/null; then
    echo "❌ Error: pandoc is not installed"
    echo "Please install pandoc:"
    echo "  macOS: brew install pandoc"
    echo "  Linux: sudo apt-get install pandoc"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    exit 1
fi

echo "✅ Dependencies check passed"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Error: Input file $INPUT_FILE not found"
    exit 1
fi

# Step 1: Preprocess the markdown file
echo "📝 Step 1: Preprocessing markdown for slides..."

# Use external preprocessing script
python3 preprocess_for_slides.py "$INPUT_FILE" "$PREPROCESSED_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Preprocessing failed"
    exit 1
fi
echo "✅ Preprocessing completed"

# Step 2: Convert with pandoc using configuration file
echo "🔄 Step 2: Converting with Pandoc + reveal.js..."

pandoc "$PREPROCESSED_FILE" \
    $([ -f "$CONFIG_FILE" ] && echo "--defaults=$CONFIG_FILE") \
    -t revealjs \
    -s \
    -o "$OUTPUT_FILE" \
    --slide-level=2 \
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
    --variable hideAddressBar=true \
    --variable width=1280 \
    --variable height=720 \
    --metadata title="$PRESENTATION_TITLE" \
    --metadata author="$PRESENTATION_AUTHOR" \
    --metadata date="$(date +'%Y-%m-%d')"

if [ $? -eq 0 ]; then
    echo "✅ Pandoc conversion successful!"
else
    echo "❌ Pandoc conversion failed. Trying alternative approach..."
    
    # Fallback: simpler pandoc command
    pandoc "$PREPROCESSED_FILE" \
        -t revealjs \
        -s \
        -o "$OUTPUT_FILE" \
        --slide-level=2 \
        --theme=black \
        --transition=slide \
        --highlight-style=github \
        --mathjax \
        --variable revealjs-url=https://unpkg.com/reveal.js@4.3.1/
    
    if [ $? -ne 0 ]; then
        echo "❌ Conversion failed completely. Check error messages above."
        exit 1
    fi
fi

# Step 3: Use external server script
echo "🌐 Step 3: Using external server script..."

# Use external server script
SERVER_SCRIPT="serve_presentation.py"
echo "📝 Using server script: $SERVER_SCRIPT"

# Step 4: Display results
echo ""
echo "🎉 Presentation creation completed!"
echo "================================================"
echo "📄 Files created:"
echo "  - $PREPROCESSED_FILE (preprocessed markdown)"
echo "  - $OUTPUT_FILE (reveal.js presentation)"
echo ""
echo "🚀 To serve the presentation:"
echo "  python $SERVER_SCRIPT $OUTPUT_FILE"
echo ""
echo "🎮 Presentation features:"
echo "  - Responsive design optimized for different screen sizes"
echo "  - Dark theme with custom styling"
echo "  - Math equations support (MathJax)"
echo "  - Code syntax highlighting"
echo "  - Touch/swipe navigation for mobile devices"
echo "  - Speaker notes and overview mode"
echo ""
echo "📱 Navigation:"
echo "  - Arrow keys or swipe to navigate"
echo "  - Press 'f' for fullscreen"
echo "  - Press 's' for speaker notes"
echo "  - Press 'o' for overview mode"
echo "  - Press '?' for help"
echo ""
echo "💡 Usage examples for future runs:"
echo "  $0 -i docs/my_document.md"
echo "  $0 -i docs/my_document.md -t \"Custom Title\" -a \"Your Name\""
echo "  $0 -i docs/my_document.md -p custom_slides.md -o custom_presentation.html"

# Clean up intermediate file
if [ -f "$PREPROCESSED_FILE" ]; then
    echo "🧹 Cleaning up intermediate files..."
    # Keep the preprocessed file for debugging
    # rm "$PREPROCESSED_FILE"
fi

echo "✅ Done!"