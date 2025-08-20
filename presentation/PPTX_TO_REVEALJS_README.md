# PPTX to reveal.js Conversion Toolkit

This toolkit provides a comprehensive solution for analyzing existing PowerPoint presentations, learning their organization and templates, and converting them to beautiful reveal.js presentations with optimized configurations.

## 🎯 Overview

The toolkit consists of several interconnected tools:

1. **`extract_pptx_to_markdown.py`** - Extracts text and layout from PPTX files
2. **`analyze_pptx_structure.py`** - Analyzes PPTX organization and generates optimized pandoc configs
3. **`pandoc_revealjs_config_enhanced.yaml`** - Enhanced configuration template
4. **`pptx_to_revealjs_workflow.py`** - Complete automated workflow
5. **Supporting scripts** - Preprocessing, serving, and utilities

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install python-pptx pyyaml

# Install pandoc (system-wide)
# macOS:
brew install pandoc

# Ubuntu/Debian:
sudo apt-get install pandoc

# Windows:
# Download from https://pandoc.org/installing.html
```

### One-Command Conversion

```bash
# Convert all PPTX files in a folder to reveal.js presentation
python pptx_to_revealjs_workflow.py /path/to/pptx/folder --serve
```

This single command will:
- ✅ Analyze your PPTX files' structure and organization
- ✅ Generate an optimized pandoc configuration
- ✅ Extract all content to structured markdown
- ✅ Create a beautiful reveal.js presentation
- ✅ Start a local server to view the presentation

## 📋 Detailed Usage

### 1. Analyzing PPTX Structure

Learn from existing presentations to create optimized configurations:

```bash
# Analyze PPTX files and generate custom config
python analyze_pptx_structure.py /path/to/pptx/folder custom_config.yaml
```

**What it analyzes:**
- 📊 Slide counts and layouts
- 🎨 Color schemes and fonts
- 📝 Content types (tables, images, charts)
- 🗣️ Speaker notes presence
- 📐 Content density and organization patterns

**Generated configuration includes:**
- Optimal themes based on content type
- Appropriate transitions for presentation length
- Custom CSS for discovered patterns
- Font and styling preferences
- Layout optimizations

### 2. Extracting Content

Extract structured content from PPTX files:

```bash
# Extract content from all PPTX files in folder
python extract_pptx_to_markdown.py /path/to/pptx/folder output.md
```

**Features:**
- 📄 Preserves slide structure and hierarchy
- 📊 Converts tables to markdown format
- 🖼️ Handles images and placeholders
- 📝 Extracts speaker notes
- 🔢 Maintains slide numbering
- 📚 Creates table of contents

### 3. Using Enhanced Configuration

The `pandoc_revealjs_config_enhanced.yaml` provides:

```yaml
# Optimized for PPTX-extracted content
slide-level: 3  # Matches ### headers from extraction
speaker-notes: true  # Support for extracted notes

# Enhanced styling for PowerPoint-like content
css:
  - |
    /* Table styling for extracted tables */
    .reveal table th {
      background-color: #2E86AB;
      color: white;
    }
    
    /* Speaker notes styling */
    .reveal .speaker-notes {
      background: rgba(162, 59, 114, 0.2);
      border-left: 4px solid #A23B72;
    }
```

### 4. Complete Workflow

For maximum automation:

```bash
# Full workflow with custom output directory
python pptx_to_revealjs_workflow.py ./presentations --output ./my_presentation --serve

# Just generate without serving
python pptx_to_revealjs_workflow.py ./presentations --output ./output
```

**Workflow steps:**
1. 🔍 Validates requirements (pandoc, python libraries)
2. 📁 Finds and validates PPTX files
3. 🔬 Analyzes structure and generates config
4. 📝 Extracts content to markdown
5. ✨ Enhances markdown with reveal.js features
6. 🎬 Generates final presentation
7. 🚀 Optionally serves the presentation

## 📁 File Structure

After running the workflow, you'll have:

```
output/
├── pandoc_config.yaml          # Generated configuration
├── presentation_content.md     # Extracted markdown content
└── presentation.html          # Final reveal.js presentation
```

## 🎨 Customization

### Modifying Generated Configurations

The analyzer creates configurations based on your PPTX patterns, but you can customize:

```yaml
# Edit the generated pandoc_config.yaml
theme: "white"  # Change theme
transition: "fade"  # Change transitions
width: 1920  # Adjust dimensions
height: 1080

# Add custom CSS
css:
  - |
    .reveal h1 {
      color: #your-brand-color;
    }
```

### Adding Custom Styling

Create your own CSS enhancements:

```css
/* Custom branding */
.reveal .title-slide {
  background: linear-gradient(45deg, #your-color1, #your-color2);
}

/* Custom bullet points */
.reveal ul li::before {
  content: "🚀";
  margin-right: 0.5em;
}
```

## 🔧 Advanced Features

### Speaker Notes Integration

Extracted speaker notes are automatically formatted:

```markdown
### Slide Title

Slide content here...

<div class="notes">
These are speaker notes that were extracted from the PPTX file.
They'll appear in presenter mode.
</div>
```

### Table Handling

PowerPoint tables are converted to markdown tables:

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

### Image Placeholders

Images are handled with placeholders that can be replaced:

```markdown
![Image Placeholder](data:image/svg+xml;base64,...) {.center-image}
```

## 🎯 Best Practices

### For Optimal Results

1. **Organize PPTX files** with consistent naming (e.g., `01_intro.pptx`, `02_main.pptx`)
2. **Use consistent slide layouts** in your PowerPoint templates
3. **Include speaker notes** for richer extracted content
4. **Use clear slide titles** for better structure detection
5. **Minimize complex animations** that don't translate to web

### Recommended Workflow

1. **Analyze first**: Run structure analysis to understand your content
2. **Review config**: Check the generated configuration and customize if needed
3. **Extract content**: Generate markdown and review for accuracy
4. **Customize styling**: Adjust CSS for your brand/preferences
5. **Generate and iterate**: Create presentation and refine as needed

## 🛠️ Troubleshooting

### Common Issues

**Pandoc not found:**
```bash
# Install pandoc system-wide
brew install pandoc  # macOS
sudo apt-get install pandoc  # Ubuntu
```

**Python library missing:**
```bash
pip install python-pptx pyyaml
```

**Empty slides in output:**
- Check if PPTX files have text content
- Verify files aren't password protected
- Ensure files aren't corrupted

**Styling issues:**
- Review generated CSS in the config file
- Check browser developer tools for CSS conflicts
- Validate HTML output

### Debug Mode

For detailed debugging:

```bash
# Run with verbose pandoc output
pandoc presentation_content.md -t revealjs -s --defaults pandoc_config.yaml -o presentation.html --verbose
```

## 📚 Examples

### Example 1: Academic Presentation

```bash
# For academic presentations with lots of content
python analyze_pptx_structure.py ./academic_slides academic_config.yaml
# This will generate config optimized for:
# - Dense content (smaller margins)
# - Math support (if formulas detected)
# - Table-heavy layouts
# - Formal styling
```

### Example 2: Business Presentation

```bash
# For business presentations with charts and images
python pptx_to_revealjs_workflow.py ./business_slides --output ./quarterly_review
# Automatically detects and optimizes for:
# - Chart-friendly themes
# - Image-heavy layouts
# - Professional styling
# - Speaker notes integration
```

### Example 3: Training Materials

```bash
# For training materials with step-by-step content
python pptx_to_revealjs_workflow.py ./training --serve
# Optimizes for:
# - Incremental reveals
# - Interactive navigation
# - Clear progression
# - Note-taking friendly layouts
```

## 🔗 Integration with Existing Tools

This toolkit works seamlessly with the existing presentation tools:

- **`create_pandoc_presentation.sh`** - Can use generated configs
- **`serve_presentation.py`** - Serves generated presentations
- **`preprocess_for_slides.py`** - Can further process extracted markdown

## 🤝 Contributing

To extend the toolkit:

1. **Add new analyzers** in `analyze_pptx_structure.py`
2. **Enhance extraction** in `extract_pptx_to_markdown.py`
3. **Improve styling** in the enhanced config template
4. **Add workflow steps** in `pptx_to_revealjs_workflow.py`

## 📄 License

This toolkit is part of the larger project and follows the same license terms.

---

**Happy presenting! 🎉**

For questions or issues, please refer to the main project documentation or create an issue in the repository.