#!/usr/bin/env python3
"""
Example script for uploading maximum scores to Canvas quiz short answer questions

This is a simple example showing how to use the auto_max_score_uploader.py script
to give all students full credit on short answer questions.

IMPORTANT: This will actually upload scores to Canvas. Use with caution!
"""

import subprocess
import sys

def upload_max_scores(course_id, quiz_id):
    """
    Upload maximum scores for all short answer questions in a quiz
    
    Args:
        course_id: Canvas course ID
        quiz_id: Canvas quiz ID
    """
    print(f"Uploading maximum scores for Course {course_id}, Quiz {quiz_id}")
    print("WARNING: This will give all students full credit on short answer questions!")
    
    # Confirm the action
    confirm = input("Are you sure you want to proceed? Type 'YES' to continue: ")
    if confirm != 'YES':
        print("Operation cancelled.")
        return False
    
    try:
        # Run the auto max score uploader
        cmd = [
            'python', 'canvas/auto_max_score_uploader.py',
            '--course', str(course_id),
            '--quiz', str(quiz_id)
        ]
        
        print("\nExecuting upload command...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Upload completed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Upload failed!")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running upload: {e}")
        return False

def main():
    # Example usage - modify these values for your quiz
    COURSE_ID = "1615883"  # Replace with your course ID
    QUIZ_ID = "1869206"    # Replace with your quiz ID
    
    print("Canvas Quiz Max Score Uploader")
    print("==============================")
    print(f"Course ID: {COURSE_ID}")
    print(f"Quiz ID: {QUIZ_ID}")
    print()
    
    # # First, run in dry-run mode to see what would happen
    # print("Step 1: Running dry-run to preview changes...")
    # try:
    #     cmd = [
    #         'python', 'auto_max_score_uploader.py',
    #         '--course', COURSE_ID,
    #         '--quiz', QUIZ_ID,
    #         '--dry-run'
    #     ]
        
    #     result = subprocess.run(cmd, capture_output=True, text=True)
    #     print(result.stdout)
        
    #     if result.returncode != 0:
    #         print("Error in dry-run:", result.stderr)
    #         return
            
    # except Exception as e:
    #     print(f"Error running dry-run: {e}")
    #     return
    
    # Ask if user wants to proceed with actual upload
    print("\nStep 2: Actual upload")
    proceed = input("Do you want to proceed with the actual upload? (y/N): ")
    
    if proceed.lower() == 'y':
        success = upload_max_scores(COURSE_ID, QUIZ_ID)
        if success:
            print("\n🎉 All students have been awarded maximum scores!")
        else:
            print("\n💥 Upload failed. Please check the error messages above.")
    else:
        print("Upload cancelled.")

if __name__ == "__main__":
    main()