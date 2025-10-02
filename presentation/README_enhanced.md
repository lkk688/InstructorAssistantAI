# Enhanced PowerPoint to Markdown Converter

A comprehensive tool for extracting content from PowerPoint presentations with advanced features including layout preservation, image extraction, OCR capabilities, and equation detection.

## Features

### Core Functionality
- **Layout Preservation**: Extracts position, size, rotation, and z-order information for all shapes
- **Image Extraction**: Saves images to organized folder structure with proper linking
- **OCR Integration**: Uses EasyOCR for text extraction from images
- **Equation Detection**: Converts mathematical equations to LaTeX using Pix2Tex
- **Presentation-Ready Output**: Generates markdown suitable for presentation generation

### Advanced Capabilities
- **Multi-format Support**: Handles text, images, tables, and grouped shapes
- **Text Formatting**: Preserves font information, colors, and styling
- **Error Handling**: Comprehensive logging and graceful error recovery
- **Batch Processing**: Process multiple PPTX files in a directory
- **Flexible Output**: Choose between layout-aware and simplified markdown

## Installation

### Basic Requirements
```bash
pip install python-pptx pillow numpy opencv-python
```

### Full Installation (with OCR)
```bash
pip install -r requirements_enhanced.txt
```

### Dependencies Breakdown
- **python-pptx**: Core PowerPoint processing
- **pillow**: Image processing and manipulation
- **numpy**: Numerical operations for image processing
- **opencv-python**: Advanced image processing
- **easyocr**: Text extraction from images (optional)
- **pix2tex**: LaTeX equation conversion (optional)
- **torch/torchvision**: Required for OCR models

## Usage

### Command Line Interface
```bash
# Extract single presentation
python enhanced_pptx_extractor.py presentation.pptx

# Extract all presentations in a folder
python enhanced_pptx_extractor.py /path/to/presentations/

# Specify output directory
python enhanced_pptx_extractor.py presentation.pptx --output-dir ./extracted/

# Include layout information
python enhanced_pptx_extractor.py presentation.pptx --include-layout

# Enable verbose logging
python enhanced_pptx_extractor.py presentation.pptx --verbose
```

### Python API
```python
from enhanced_pptx_extractor import EnhancedPPTXExtractor

# Initialize extractor
extractor = EnhancedPPTXExtractor(output_dir="my_extractions")

# Extract presentation
result = extractor.extract_presentation("presentation.pptx")

# Access extracted data
for slide_data in result['slides']:
    print(f"Slide {slide_data['slide_number']}: {slide_data['title']}")
    for shape in slide_data['shapes']:
        print(f"  - {shape.shape_type}: {shape.content}")
```

## Output Structure

```
extracted_presentations/
├── images/
│   ├── slide_1_shape_1.png
│   ├── slide_1_shape_2.jpg
│   └── ...
├── presentation_name.md
├── presentation_name.json
└── extraction.log
```

### Markdown Output Format

The generated markdown includes:

1. **Presentation Metadata**
   - Title, slide count, extraction timestamp
   - OCR and equation detection status

2. **Slide Content**
   - Slide titles and numbers
   - Shape-by-shape content with layout information
   - Image references with proper linking
   - OCR-extracted text from images
   - LaTeX equations from mathematical content

3. **Layout Information** (optional)
   - CSS-style positioning data
   - Size and rotation information
   - Z-order for layering

### Example Output
```markdown
# Presentation: Machine Learning Basics

**Extracted on:** 2024-01-15 10:30:00  
**Total Slides:** 25  
**OCR Enabled:** Yes  
**Equation Detection:** Yes  

---

## Slide 1: Introduction to ML

### Text Content
**Machine Learning Overview**
- Supervised Learning
- Unsupervised Learning  
- Reinforcement Learning

### Images
![Slide 1 - ML Diagram](images/slide_1_shape_3.png)

**OCR Text from Image:**
"Classification vs Regression
- Classification: Discrete outputs
- Regression: Continuous outputs"

**Detected Equations:**
$$y = mx + b$$
$$\sigma(x) = \frac{1}{1 + e^{-x}}$$

### Layout Information
```css
.shape_1 { left: 100px; top: 50px; width: 400px; height: 200px; }
.shape_2 { left: 150px; top: 300px; width: 300px; height: 150px; }
```
```

## Testing

### Run Tests
```bash
# Basic functionality test
python test_enhanced_extractor.py

# Test with sample file (place a .pptx file in the directory first)
python test_enhanced_extractor.py
```

### Test Results
The test script will verify:
- ✅ Import and initialization
- ✅ OCR model availability
- ✅ File processing capabilities
- ✅ Output generation
- ✅ Image extraction
- ✅ Markdown formatting

## Configuration

### OCR Settings
- **EasyOCR**: Automatically detects if available
- **Pix2Tex**: Requires additional setup for equation detection
- **Language Support**: Currently configured for English ('en')

### Output Options
- **Include Layout**: Add CSS positioning information
- **Image Quality**: Configurable image compression
- **Logging Level**: Control verbosity of output

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements_enhanced.txt
   ```

2. **OCR Not Working**
   - Install torch: `pip install torch torchvision`
   - For M1 Macs: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`

3. **Equation Detection Failing**
   - Install pix2tex: `pip install pix2tex[gui]`
   - May require additional system dependencies

4. **Memory Issues with Large Files**
   - Process files individually
   - Reduce image quality settings
   - Close other applications

### Performance Tips
- **Batch Processing**: Process multiple files in sequence
- **Image Optimization**: Use appropriate compression settings
- **OCR Selective**: Disable OCR for text-only presentations
- **Layout Minimal**: Skip layout info for simple extractions

## Contributing

### Development Setup
```bash
git clone <repository>
cd enhanced-pptx-extractor
pip install -r requirements_enhanced.txt
python test_enhanced_extractor.py
```

### Adding Features
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v2.0.0 (Enhanced Version)
- ✅ Added layout preservation
- ✅ Implemented image extraction
- ✅ Integrated OCR capabilities
- ✅ Added equation detection
- ✅ Enhanced markdown output
- ✅ Comprehensive error handling
- ✅ Added test suite

### v1.0.0 (Original Version)
- Basic text extraction
- Simple markdown output