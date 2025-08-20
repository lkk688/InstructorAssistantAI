# PDF Conversion Guide for Exam Papers

This guide explains how to convert the clean exam markdown file to PDF format using various methods.

## Files Created

1. `cmpe257_exam_questions_clean.md` - Clean exam questions without answers
2. `cmpe257_exam_questions_clean.html` - HTML version with print styling
3. `exam_print_style.css` - CSS stylesheet for print formatting

## Method 1: Browser Print to PDF (Recommended)

**This is the easiest method and works on any system:**

1. Open `cmpe257_exam_questions_clean.html` in your web browser
2. Press `Cmd+P` (Mac) or `Ctrl+P` (Windows/Linux) to open print dialog
3. Select "Save as PDF" as the destination
4. In print settings:
   - Set margins to "Minimum" or "Custom" (0.5 inch)
   - Enable "Background graphics" if available
   - Choose "More settings" and ensure "Headers and footers" is unchecked
5. Click "Save" and choose your desired location

## Method 2: Using Pandoc with LaTeX (Requires Installation)

**If you have LaTeX installed:**

```bash
# Install LaTeX (choose one):
# macOS: brew install --cask mactex
# Ubuntu: sudo apt-get install texlive-latex-extra
# Windows: Download MiKTeX from https://miktex.org/

# Convert to PDF
pandoc testout4.md -o testout4_clean.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V linestretch=1.2

brew install librsvg homebrew/cask/basictex
echo 'export PATH="/Library/TeX/texbin:$PATH"' >> ~/.zshrc
source ~/.zshrc
pandoc testout_latex_fixed.md -o testout4_clean.pdf \
  --pdf-engine=pdflatex \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V linestretch=1.2
```

## Method 3: Using wkhtmltopdf

**Install wkhtmltopdf first:**

```bash
# macOS
brew install wkhtmltopdf

# Ubuntu
sudo apt-get install wkhtmltopdf

# Windows: Download from https://wkhtmltopdf.org/downloads.html
```

**Then convert:**

```bash
pandoc cmpe257_exam_questions_clean.md -o cmpe257_exam_questions_clean.pdf \
  --pdf-engine=wkhtmltopdf \
  -V margin-top=1in \
  -V margin-bottom=1in \
  -V margin-left=1in \
  -V margin-right=1in
```

## Method 4: Online Conversion Tools

1. **Pandoc Try**: https://pandoc.org/try/
   - Paste your markdown content
   - Select "PDF" as output format
   - Download the result

2. **Markdown to PDF converters**:
   - https://www.markdowntopdf.com/
   - https://md2pdf.netlify.app/

## Method 5: Using LibreOffice/Word

1. Open the HTML file in LibreOffice Writer or Microsoft Word
2. Adjust formatting as needed
3. Export/Save as PDF

## Formatting Features Included

- **Clean layout**: Removed all answers and explanations
- **Answer spaces**: 
  - T/F questions have T/F options to circle
  - MCQ questions have blank answer lines
  - Short answer questions have multiple lined spaces
- **Print optimization**: 
  - Proper margins and font sizes
  - Page break handling
  - Professional exam formatting
- **Header section**: Space for name, student ID, date, and time

## Customization

To modify the formatting:

1. **Edit CSS**: Modify `exam_print_style.css` for styling changes
2. **Edit Markdown**: Modify `cmpe257_exam_questions_clean.md` for content changes
3. **Regenerate HTML**: Run the pandoc command again after changes

```bash
pandoc cmpe257_exam_questions_clean.md -o cmpe257_exam_questions_clean.html \
  --standalone --css=exam_print_style.css
```

## Tips for Best Results

1. **Use Method 1 (Browser Print)** for the most reliable results
2. **Check page breaks** in print preview before saving
3. **Adjust margins** if content is cut off
4. **Test print** on paper first to ensure proper formatting
5. **Keep backup** of the original markdown file for future edits

## Troubleshooting

- **Content cut off**: Reduce margins or font size in CSS
- **Poor formatting**: Try different browsers for Method 1
- **Missing styling**: Ensure CSS file is in the same directory
- **LaTeX errors**: Install full LaTeX distribution, not minimal version

The HTML version with CSS styling should provide excellent print quality when using the browser's "Print to PDF" function.