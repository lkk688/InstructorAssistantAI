# LaTeX Beamer Presentation: Physical AI and LLMs in Autonomous Driving

This directory contains a LaTeX Beamer presentation based on the comprehensive markdown document `docs/physical_ai_autonomous_driving.md`.

## Files Created

- `presentation.tex` - Main LaTeX Beamer presentation file
- `compile_presentation.sh` - Compilation script for easy PDF generation
- `PRESENTATION_README.md` - This instruction file

## Prerequisites

To compile the LaTeX presentation, you need a LaTeX distribution installed:

### macOS
```bash
# Install MacTeX (recommended)
brew install --cask mactex

# Or install BasicTeX (smaller)
brew install --cask basictex
# Then install additional packages:
sudo tlmgr install beamer pgfplots tikz listings xcolor booktabs multirow subcaption
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install texlive-full
# Or for a minimal installation:
sudo apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra
```

### Windows
- Download and install [MiKTeX](https://miktex.org/) or [TeX Live](https://www.tug.org/texlive/)

## Compilation

### Method 1: Using the provided script (Recommended)
```bash
./compile_presentation.sh
```

### Method 2: Manual compilation
```bash
# Run pdflatex twice for proper references
pdflatex presentation.tex
pdflatex presentation.tex

# Clean up auxiliary files
rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb
```

## Presentation Structure

The presentation is organized into the following sections:

1. **Introduction: The Convergence** - Overview of Physical AI and LLMs integration
2. **Why Physical AI & LLMs are Crucial** - 5 key advantages with detailed explanations
3. **Current Solutions in Autonomous Driving** - Traditional 4 Pillars architecture
4. **Tesla's Latest Model: A Case Study** - End-to-end learning approach
5. **Future Research Directions** - Emerging trends and challenges
6. **Conclusion** - Key takeaways and discussion

## Features

- **Professional Design**: Uses Madrid theme with custom colors
- **Technical Content**: Includes tables, diagrams, and code snippets
- **References**: Maintains academic citations from the original document
- **Visual Elements**: Custom TikZ diagrams and color-coded content
- **Structured Layout**: Clear section organization with navigation

## Customization

### Changing Theme
Modify the theme in `presentation.tex`:
```latex
\usetheme{Madrid}  % Change to: Berlin, Copenhagen, Warsaw, etc.
\usecolortheme{default}  % Change to: dolphin, rose, seagull, etc.
```

### Custom Colors
The presentation uses custom colors defined at the top:
```latex
\definecolor{teslaBlue}{RGB}{33, 150, 243}
\definecolor{aiGreen}{RGB}{76, 175, 80}
\definecolor{warningOrange}{RGB}{255, 152, 0}
\definecolor{errorRed}{RGB}{244, 67, 54}
```

### Adding Content
To add new slides, use the frame environment:
```latex
\begin{frame}{Slide Title}
    Your content here...
\end{frame}
```

## Troubleshooting

### Common Issues

1. **Missing packages**: Install required packages using your LaTeX package manager
2. **Image not found**: Ensure the `docs/figures/` directory contains the referenced images
3. **Compilation errors**: Check the `.log` file for detailed error messages

### Package Installation (if needed)
```bash
# For MacTeX/TeX Live
sudo tlmgr install beamer pgfplots tikz listings xcolor booktabs multirow subcaption

# For MiKTeX (Windows)
mpm --install beamer pgfplots tikz listings xcolor booktabs multirow subcaption
```

## Output

After successful compilation, you'll get:
- `presentation.pdf` - The final presentation file
- Auxiliary files will be automatically cleaned up by the script

## Usage Tips

1. **Presentation Mode**: Use a PDF viewer that supports presentation mode (Adobe Reader, Preview on macOS)
2. **Navigation**: Use arrow keys or click to navigate between slides
3. **Handouts**: Add `\documentclass[handout]{beamer}` for printable handouts
4. **Notes**: Add speaker notes using `\note{Your notes here}`

## References

This presentation is based on the comprehensive research document:
- `docs/physical_ai_autonomous_driving.md`
- Contains 33+ academic citations and references
- Covers cutting-edge research in autonomous driving and AI

For the most up-to-date content and detailed technical information, refer to the original markdown document.