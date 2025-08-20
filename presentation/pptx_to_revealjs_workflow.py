#!/usr/bin/env python3
"""
Complete PPTX to reveal.js Workflow

This script provides a complete workflow for converting PowerPoint presentations
to reveal.js presentations by:
1. Analyzing PPTX structure and generating optimized pandoc config
2. Extracting content from PPTX files to markdown
3. Generating reveal.js presentation with pandoc
4. Optionally serving the presentation

Usage:
    python pptx_to_revealjs_workflow.py <input_folder> [options]

Requirements:
    pip install python-pptx pyyaml
    pandoc (system installation required)
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

# Import our custom modules
try:
    from analyze_pptx_structure import PPTXStructureAnalyzer, find_pptx_files
    from extract_pptx_to_markdown import PPTXExtractor, create_combined_markdown
except ImportError:
    print("Error: Required modules not found.")
    print("Make sure analyze_pptx_structure.py and extract_pptx_to_markdown.py are in the same directory.")
    sys.exit(1)


class PPTXToRevealJSWorkflow:
    """Complete workflow for PPTX to reveal.js conversion"""
    
    def __init__(self, input_folder: str, output_dir: str = "output"):
        self.input_folder = Path(input_folder)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Output file paths
        self.config_file = self.output_dir / "pandoc_config.yaml"
        self.markdown_file = self.output_dir / "presentation_content.md"
        self.html_file = self.output_dir / "presentation.html"
        
        self.pptx_files = []
        self.analyzer = None
        self.extractor = None
    
    def validate_requirements(self) -> bool:
        """Check if all required tools are available"""
        print("🔍 Checking requirements...")
        
        # Check if pandoc is installed
        try:
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, check=True)
            pandoc_version = result.stdout.split('\n')[0]
            print(f"   ✅ {pandoc_version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   ❌ Pandoc not found. Please install pandoc from https://pandoc.org/")
            return False
        
        # Check Python libraries
        try:
            import pptx
            print("   ✅ python-pptx library found")
        except ImportError:
            print("   ❌ python-pptx not found. Install with: pip install python-pptx")
            return False
        
        try:
            import yaml
            print("   ✅ PyYAML library found")
        except ImportError:
            print("   ❌ PyYAML not found. Install with: pip install pyyaml")
            return False
        
        return True
    
    def find_presentations(self) -> bool:
        """Find and validate PPTX files"""
        print(f"\n📁 Searching for PPTX files in: {self.input_folder}")
        
        if not self.input_folder.exists():
            print(f"❌ Input folder does not exist: {self.input_folder}")
            return False
        
        self.pptx_files = find_pptx_files(str(self.input_folder))
        
        if not self.pptx_files:
            print("❌ No PPTX files found")
            return False
        
        print(f"✅ Found {len(self.pptx_files)} PPTX files:")
        for i, file in enumerate(self.pptx_files, 1):
            print(f"   {i}. {Path(file).name}")
        
        return True
    
    def analyze_structure(self) -> bool:
        """Analyze PPTX structure and generate config"""
        print(f"\n🔬 Analyzing PPTX structure...")
        
        self.analyzer = PPTXStructureAnalyzer()
        
        for pptx_file in self.pptx_files:
            print(f"   📖 Analyzing: {Path(pptx_file).name}")
            analysis = self.analyzer.analyze_presentation(pptx_file)
            
            if analysis:
                self.analyzer.presentations.append(analysis)
                print(f"      ✅ {analysis['slide_count']} slides analyzed")
            else:
                print(f"      ❌ Failed to analyze")
        
        if not self.analyzer.presentations:
            print("❌ No presentations successfully analyzed")
            return False
        
        # Generate pandoc configuration
        print(f"\n⚙️  Generating pandoc configuration: {self.config_file}")
        self.analyzer.generate_pandoc_config(str(self.config_file))
        
        return True
    
    def extract_content(self) -> bool:
        """Extract content from PPTX files to markdown"""
        print(f"\n📝 Extracting content to markdown...")
        
        self.extractor = PPTXExtractor()
        presentations = []
        
        for pptx_file in self.pptx_files:
            print(f"   📖 Processing: {Path(pptx_file).name}")
            presentation_data = self.extractor.extract_presentation(pptx_file)
            
            if presentation_data:
                presentations.append(presentation_data)
                print(f"      ✅ {presentation_data['slide_count']} slides extracted")
            else:
                print(f"      ❌ Failed to extract")
        
        if not presentations:
            print("❌ No content extracted")
            return False
        
        # Create combined markdown
        print(f"\n📄 Creating combined markdown: {self.markdown_file}")
        create_combined_markdown(presentations, str(self.markdown_file))
        
        return True
    
    def enhance_markdown_for_revealjs(self) -> bool:
        """Enhance markdown with reveal.js specific features"""
        print(f"\n✨ Enhancing markdown for reveal.js...")
        
        try:
            with open(self.markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add reveal.js specific enhancements
            enhanced_content = self._add_revealjs_features(content)
            
            with open(self.markdown_file, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)
            
            print("   ✅ Markdown enhanced with reveal.js features")
            return True
            
        except Exception as e:
            print(f"   ❌ Error enhancing markdown: {str(e)}")
            return False
    
    def _add_revealjs_features(self, content: str) -> str:
        """Add reveal.js specific features to markdown content"""
        lines = content.split('\n')
        enhanced_lines = []
        
        for line in lines:
            # Convert speaker notes format
            if line.startswith('**Speaker Notes:**'):
                enhanced_lines.append('')
                enhanced_lines.append('<div class="notes">')
                continue
            elif line.startswith('**Speaker Notes:**') or (enhanced_lines and enhanced_lines[-1] == '<div class="notes">' and line.strip() == ''):
                if line.strip() == '' and len(enhanced_lines) > 0 and not enhanced_lines[-1].endswith('</div>'):
                    enhanced_lines.append('</div>')
                    enhanced_lines.append('')
                continue
            
            # Add fragment classes for bullet points (optional)
            if line.strip().startswith('- ') and 'fragment' not in line:
                # Uncomment next line to add fragment animation to bullet points
                # line = line.replace('- ', '- {.fragment} ')
                pass
            
            # Convert [Image] placeholders to actual image syntax
            if '[Image]' in line:
                line = line.replace('[Image]', '![Image Placeholder](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y4ZjlmYSIgc3Ryb2tlPSIjZGVlMmU2IiBzdHJva2Utd2lkdGg9IjIiLz48dGV4dCB4PSIxNTAiIHk9IjEwMCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjg3MDc2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2UgUGxhY2Vob2xkZXI8L3RleHQ+PC9zdmc+) {.center-image}')
            
            enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def generate_presentation(self) -> bool:
        """Generate reveal.js presentation using pandoc"""
        print(f"\n🎬 Generating reveal.js presentation...")
        
        try:
            # Build pandoc command
            cmd = [
                'pandoc',
                str(self.markdown_file),
                '-t', 'revealjs',
                '-s',  # standalone
                '--defaults', str(self.config_file),
                '-o', str(self.html_file)
            ]
            
            print(f"   Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                print(f"   ✅ Presentation generated: {self.html_file}")
                return True
            else:
                print(f"   ❌ Pandoc failed with return code: {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Pandoc command failed: {e}")
            if e.stderr:
                print(f"   Error output: {e.stderr}")
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
            return False
    
    def serve_presentation(self, port: int = 8000) -> bool:
        """Serve the presentation using the existing serve script"""
        print(f"\n🚀 Starting presentation server...")
        
        serve_script = Path(__file__).parent / "serve_presentation.py"
        
        if not serve_script.exists():
            print(f"   ❌ Serve script not found: {serve_script}")
            return False
        
        try:
            # Change to output directory and serve
            os.chdir(self.output_dir)
            
            cmd = ['python3', str(serve_script), self.html_file.name]
            print(f"   Running: {' '.join(cmd)}")
            
            # This will run the server (blocking)
            subprocess.run(cmd)
            return True
            
        except KeyboardInterrupt:
            print("\n   ⏹️  Server stopped by user")
            return True
        except Exception as e:
            print(f"   ❌ Error starting server: {str(e)}")
            return False
    
    def run_complete_workflow(self, serve: bool = False) -> bool:
        """Run the complete workflow"""
        print("🎯 Starting PPTX to reveal.js conversion workflow")
        print("=" * 60)
        
        # Step 1: Validate requirements
        if not self.validate_requirements():
            return False
        
        # Step 2: Find presentations
        if not self.find_presentations():
            return False
        
        # Step 3: Analyze structure
        if not self.analyze_structure():
            return False
        
        # Step 4: Extract content
        if not self.extract_content():
            return False
        
        # Step 5: Enhance markdown
        if not self.enhance_markdown_for_revealjs():
            return False
        
        # Step 6: Generate presentation
        if not self.generate_presentation():
            return False
        
        # Success summary
        print("\n" + "=" * 60)
        print("🎉 Workflow completed successfully!")
        print("\n📊 Generated files:")
        print(f"   - Configuration: {self.config_file}")
        print(f"   - Markdown: {self.markdown_file}")
        print(f"   - Presentation: {self.html_file}")
        
        # Step 7: Optionally serve presentation
        if serve:
            print("\n🌐 Starting presentation server...")
            self.serve_presentation()
        else:
            print("\n💡 To view the presentation:")
            print(f"   python3 serve_presentation.py {self.html_file}")
            print(f"   # or open {self.html_file} in your browser")
        
        return True


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Convert PowerPoint presentations to reveal.js presentations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pptx_to_revealjs_workflow.py ./presentations
  python pptx_to_revealjs_workflow.py ./presentations --output ./output --serve
  python pptx_to_revealjs_workflow.py ./presentations --output ./my_presentation

This tool will:
1. Analyze your PPTX files to understand their structure
2. Generate an optimized pandoc configuration
3. Extract all content to markdown format
4. Generate a reveal.js presentation
5. Optionally serve the presentation locally
        """
    )
    
    parser.add_argument(
        'input_folder',
        help='Path to folder containing PPTX files'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output directory for generated files (default: output)'
    )
    
    parser.add_argument(
        '--serve', '-s',
        action='store_true',
        help='Start local server after generating presentation'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='Port for local server (default: 8000)'
    )
    
    args = parser.parse_args()
    
    # Create and run workflow
    workflow = PPTXToRevealJSWorkflow(args.input_folder, args.output)
    
    success = workflow.run_complete_workflow(serve=args.serve)
    
    if not success:
        print("\n❌ Workflow failed. Please check the errors above.")
        sys.exit(1)
    
    print("\n✨ All done! Enjoy your presentation!")


if __name__ == "__main__":
    main()