#!/usr/bin/env python3
"""
Test script for the enhanced PPTX extractor
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

from enhanced_pptx_extractor import EnhancedPPTXExtractor

def test_enhanced_extractor():
    """Test the enhanced PPTX extractor with a sample file"""
    
    # Initialize the extractor
    extractor = EnhancedPPTXExtractor()
    
    # Look for sample PPTX files in the current directory
    current_dir = Path(__file__).parent
    pptx_files = list(current_dir.glob("*.pptx"))
    
    if not pptx_files:
        print("No PPTX files found in the current directory.")
        print("Please add a sample PPTX file to test the extractor.")
        return False
    
    # Test with the first PPTX file found
    test_file = pptx_files[0]
    print(f"Testing with file: {test_file}")
    
    try:
        # Extract content
        result = extractor.extract_presentation(str(test_file))
        
        if result:
            print("✅ Extraction successful!")
            print(f"Output directory: {result}")
            
            # Check if markdown file was created
            markdown_file = Path(result) / f"{test_file.stem}.md"
            if markdown_file.exists():
                print(f"✅ Markdown file created: {markdown_file}")
                
                # Show first few lines of the markdown
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:20]
                    print("\n📄 First 20 lines of generated markdown:")
                    print("=" * 50)
                    for i, line in enumerate(lines, 1):
                        print(f"{i:2d}: {line.rstrip()}")
                    print("=" * 50)
            
            # Check if images were extracted
            images_dir = Path(result) / "images"
            if images_dir.exists():
                image_files = list(images_dir.glob("*"))
                print(f"✅ Images extracted: {len(image_files)} files")
                for img in image_files[:5]:  # Show first 5 images
                    print(f"   - {img.name}")
                if len(image_files) > 5:
                    print(f"   ... and {len(image_files) - 5} more")
            
            return True
        else:
            print("❌ Extraction failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_test():
    """Create a simple test to verify the extractor can be imported"""
    try:
        from enhanced_pptx_extractor import EnhancedPPTXExtractor
        extractor = EnhancedPPTXExtractor()
        print("✅ Enhanced PPTX Extractor imported successfully!")
        print(f"✅ OCR reader available: {extractor.ocr_reader is not None}")
        print(f"✅ LaTeX OCR available: {extractor.latex_ocr is not None}")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install required dependencies:")
        print("pip install -r requirements_enhanced.txt")
        return False
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Enhanced PPTX Extractor")
    print("=" * 40)
    
    # First test: Import and initialization
    print("\n1. Testing import and initialization...")
    if not create_sample_test():
        sys.exit(1)
    
    # Second test: Full extraction (if PPTX files available)
    print("\n2. Testing full extraction...")
    success = test_enhanced_extractor()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")