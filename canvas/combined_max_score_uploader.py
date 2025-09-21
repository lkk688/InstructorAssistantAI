#!/usr/bin/env python3
"""
Combined Canvas Quiz Max Score Uploader

This script combines the functionality of auto_max_score_uploader.py and upload_max_scores_example.py
into a single comprehensive tool that shows detailed progress for each student score update.

Features:
- Downloads quiz data and filters short answer questions
- Generates maximum scores for all students
- Shows detailed progress for each student update
- Provides dry-run mode for testing
- Interactive confirmation before uploading
- Comprehensive error handling and cleanup

Usage:
    python combined_max_score_uploader.py --course COURSE_ID --quiz QUIZ_ID [--dry-run]

Example:
    python combined_max_score_uploader.py --course 1615883 --quiz 1869206 --dry-run
    python combined_max_score_uploader.py --course 1615883 --quiz 1869206
"""

import json
import argparse
import os
import sys
import time
from datetime import datetime
from quiz_answers_downloader import (
    generate_quiz_answers_json,
    update_quiz_scores,
    get_quiz_questions
)

def generate_max_scores_file(quiz_data_file, output_scores_file):
    """
    Generate a scores file with maximum points for all short answer questions
    
    Args:
        quiz_data_file: Path to the JSON file containing quiz data
        output_scores_file: Path to output the scores JSON file
        
    Returns:
        dict: Generated scores data
    """
    print(f"📂 Loading quiz data from {quiz_data_file}...")
    
    with open(quiz_data_file, 'r', encoding='utf-8') as f:
        quiz_data = json.load(f)
    
    # Create scores structure
    scores_data = {
        "submissions": []
    }
    
    print(f"👥 Processing {len(quiz_data['submissions'])} submissions...")
    
    for i, submission in enumerate(quiz_data['submissions'], 1):
        submission_scores = {
            "user_id": submission['user_id'],
            "student_name": submission['student_name'],
            "submission_id": submission['submission_id'],
            "quiz_submission_id": submission['quiz_submission_id'],
            "attempt": submission['attempt'],
            "answers": []
        }
        
        # Count short answer questions for this student
        short_answer_count = 0
        total_points = 0
        
        # Assign maximum score to each short answer question
        for answer in submission['answers']:
            if answer['question_type'] in ['short_answer_question', 'essay_question']:
                answer_score = {
                    "question_id": answer['question_id'],
                    "score": answer['points_possible']  # Maximum score
                }
                submission_scores['answers'].append(answer_score)
                short_answer_count += 1
                total_points += answer['points_possible']
        
        if submission_scores['answers']:  # Only add if there are short answer questions
            scores_data['submissions'].append(submission_scores)
            print(f"  [{i:3d}] {submission['student_name']:<30} - {short_answer_count} questions, {total_points} points")
    
    # Write scores file
    with open(output_scores_file, 'w', encoding='utf-8') as f:
        json.dump(scores_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Generated scores file: {output_scores_file}")
    print(f"📊 Total submissions with short answer questions: {len(scores_data['submissions'])}")
    
    # Calculate total questions and points
    total_questions = sum(len(sub['answers']) for sub in scores_data['submissions'])
    total_points = sum(sum(ans['score'] for ans in sub['answers']) for sub in scores_data['submissions'])
    
    print(f"📝 Total short answer questions to score: {total_questions}")
    print(f"🎯 Total points to be awarded: {total_points}")
    
    return scores_data

def delete_comments_from_submissions(course_id, quiz_id):
    """
    Delete additional comments from already uploaded quiz submissions
    
    Args:
        course_id: Canvas course ID
        quiz_id: Canvas quiz ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n🗑️  Starting comment deletion for Course {course_id}, Quiz {quiz_id}")
    
    try:
        # Import here to avoid circular imports
        import requests
        import os
        
        # Get Canvas API token
        canvas_token = os.getenv('CANVAS_API_TOKEN')
        if not canvas_token:
            print(f"❌ Error: CANVAS_API_TOKEN environment variable not set")
            return False
        
        # Get all quiz submissions
        print(f"📥 Fetching quiz submissions...")
        submissions_url = f"https://canvas.instructure.com/api/v1/courses/{course_id}/quizzes/{quiz_id}/submissions"
        headers = {'Authorization': f'Bearer {canvas_token}'}
        
        response = requests.get(submissions_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error fetching submissions: {response.status_code}")
            return False
        
        submissions = response.json().get('quiz_submissions', [])
        print(f"📊 Found {len(submissions)} submissions")
        
        # Get quiz questions to identify short answer questions
        questions_url = f"https://canvas.instructure.com/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions"
        response = requests.get(questions_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error fetching questions: {response.status_code}")
            return False
        
        questions = response.json()
        short_answer_questions = [q for q in questions if q.get('question_type') in ['short_answer_question', 'essay_question']]
        
        if not short_answer_questions:
            print(f"⚠️  No short answer questions found in this quiz")
            return True
        
        print(f"📝 Found {len(short_answer_questions)} short answer questions")
        
        # Process each submission
        updated_count = 0
        for i, submission in enumerate(submissions, 1):
            submission_id = submission['id']
            user_id = submission['user_id']
            
            # Get submission details with answers
            submission_url = f"https://canvas.instructure.com/api/v1/quiz_submissions/{submission_id}/questions"
            response = requests.get(submission_url, headers=headers)
            
            if response.status_code != 200:
                print(f"  [{i:3d}] ❌ Error fetching submission {submission_id}: {response.status_code}")
                continue
            
            submission_questions = response.json().get('quiz_submission_questions', [])
            
            # Update each short answer question to remove comments
            submission_updated = False
            for question in submission_questions:
                question_id = question['id']
                
                # Check if this is a short answer question
                if any(q['id'] == question_id for q in short_answer_questions):
                    # Update the question score without comment
                    current_score = question.get('score', 0)
                    
                    update_url = f"https://canvas.instructure.com/api/v1/quiz_submissions/{submission_id}/questions/{question_id}"
                    update_data = {
                        'quiz_submissions': [{
                            'attempt': submission['attempt'],
                            'questions': {
                                str(question_id): {
                                    'score': current_score,
                                    'comment': ''  # Empty comment to remove existing ones
                                }
                            }
                        }]
                    }
                    
                    response = requests.put(update_url, headers=headers, json=update_data)
                    if response.status_code == 200:
                        submission_updated = True
            
            if submission_updated:
                updated_count += 1
                print(f"  [{i:3d}] ✅ Updated submission {submission_id} (User {user_id})")
            else:
                print(f"  [{i:3d}] ⏭️  No updates needed for submission {submission_id} (User {user_id})")
        
        print(f"\n✅ Comment deletion completed!")
        print(f"📊 Updated {updated_count} out of {len(submissions)} submissions")
        return True
        
    except Exception as e:
        print(f"\n❌ Comment deletion failed with error: {e}")
        return False

def upload_scores_with_progress(course_id, quiz_id, scores_file):
    """
    Upload scores to Canvas with detailed progress tracking for each student
    
    Args:
        course_id: Canvas course ID
        quiz_id: Canvas quiz ID
        scores_file: Path to the scores JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n🚀 Starting score upload for Course {course_id}, Quiz {quiz_id}")
    print(f"📄 Using scores file: {scores_file}")
    
    # Load scores data to show progress
    try:
        with open(scores_file, 'r', encoding='utf-8') as f:
            scores_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading scores file: {e}")
        return False
    
    total_students = len(scores_data['submissions'])
    total_questions = sum(len(sub['answers']) for sub in scores_data['submissions'])
    
    print(f"\n📋 Upload Summary:")
    print(f"   Students: {total_students}")
    print(f"   Questions: {total_questions}")
    print(f"   Total Points: {sum(sum(ans['score'] for ans in sub['answers']) for sub in scores_data['submissions'])}")
    
    # Show preview of students to be updated
    print(f"\n👥 Students to be updated:")
    for i, submission in enumerate(scores_data['submissions'][:10], 1):  # Show first 10
        question_count = len(submission['answers'])
        points = sum(ans['score'] for ans in submission['answers'])
        print(f"  [{i:2d}] {submission['student_name']:<30} - {question_count} questions ({points} pts)")
    
    if total_students > 10:
        print(f"  ... and {total_students - 10} more students")
    
    # Final confirmation
    print(f"\n⚠️  WARNING: This will upload scores to Canvas and affect student grades!")
    confirm = input(f"\n🤔 Are you absolutely sure you want to proceed? Type 'YES' to continue: ")
    if confirm != 'YES':
        print("❌ Operation cancelled by user.")
        return False
    
    print(f"\n🔄 Starting upload process...")
    print(f"{'='*60}")
    
    try:
        # Call the existing update_quiz_scores function
        # Note: This function handles the actual API calls internally
        update_quiz_scores(course_id, quiz_id, scores_file)
        
        print(f"\n✅ Upload completed successfully!")
        print(f"🎉 All {total_students} students have been awarded maximum scores!")
        return True
        
    except Exception as e:
        print(f"\n❌ Upload failed with error: {e}")
        return False

def show_dry_run_preview(scores_data):
    """
    Show a detailed preview of what would be uploaded in dry-run mode
    
    Args:
        scores_data: The generated scores data
    """
    print(f"\n🔍 DRY RUN PREVIEW")
    print(f"{'='*50}")
    
    total_students = len(scores_data['submissions'])
    total_questions = sum(len(sub['answers']) for sub in scores_data['submissions'])
    total_points = sum(sum(ans['score'] for ans in sub['answers']) for sub in scores_data['submissions'])
    
    print(f"📊 Summary:")
    print(f"   • Students with short answer questions: {total_students}")
    print(f"   • Total questions to be scored: {total_questions}")
    print(f"   • Total points to be awarded: {total_points}")
    
    print(f"\n👥 Student Details:")
    for i, submission in enumerate(scores_data['submissions'], 1):
        student_questions = len(submission['answers'])
        student_points = sum(ans['score'] for ans in submission['answers'])
        print(f"  [{i:3d}] {submission['student_name']:<30} - {student_questions:2d} questions, {student_points:4.1f} points")
        
        # Show question details for first few students
        if i <= 3:
            for j, answer in enumerate(submission['answers'], 1):
                print(f"       Q{j}: Question {answer['question_id']} → {answer['score']} points")
            if i < 3 and len(scores_data['submissions']) > 3:
                print()
    
    print(f"\n💡 To actually upload these scores, run without --dry-run flag")

def main():
    parser = argparse.ArgumentParser(
        description='Combined Canvas Quiz Max Score Uploader with detailed progress tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview what would be uploaded (recommended first step)
  python combined_max_score_uploader.py --course 1615883 --quiz 1869206 --dry-run
  
  # Actually upload maximum scores
  python combined_max_score_uploader.py --course 1615883 --quiz 1869206
  
  # Delete additional comments from already uploaded submissions
  python combined_max_score_uploader.py --course 1615883 --quiz 1869206 --delete-comments
        """
    )
    parser.add_argument('--course', type=str, required=True, help='Canvas course ID')
    parser.add_argument('--quiz', type=str, required=True, help='Canvas quiz ID')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without uploading to Canvas')
    parser.add_argument('--delete-comments', action='store_true', help='Delete additional comments from already uploaded submissions')
    parser.add_argument('--temp-dir', type=str, default='.', help='Directory for temporary files')
    
    args = parser.parse_args()
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # File paths
    quiz_data_file = os.path.join(args.temp_dir, f'quiz_data_{args.quiz}_{timestamp}.json')
    scores_file = os.path.join(args.temp_dir, f'max_scores_{args.quiz}_{timestamp}.json')
    
    print(f"🎯 Canvas Quiz Max Score Uploader")
    print(f"{'='*50}")
    print(f"📚 Course ID: {args.course}")
    print(f"📝 Quiz ID: {args.quiz}")
    print(f"🔧 Mode: {'DRY RUN' if args.dry_run else 'LIVE UPLOAD'}")
    print(f"📁 Temp Directory: {args.temp_dir}")
    
    try:
        print(f"\n🔄 Step 1: Downloading Quiz Data")
        print(f"{'-'*40}")
        print(f"📥 Downloading short answer questions for quiz {args.quiz}...")
        
        # Download quiz data with short answer filter
        generate_quiz_answers_json(
            course_id=args.course,
            quiz_id=args.quiz,
            output_file=quiz_data_file,
            short_answer_only=True
        )
        
        print(f"\n🔄 Step 2: Generating Maximum Scores")
        print(f"{'-'*40}")
        scores_data = generate_max_scores_file(quiz_data_file, scores_file)
        
        if not scores_data['submissions']:
            print(f"\n⚠️  No short answer questions found in this quiz.")
            print(f"💡 This script only works with quizzes that have short answer or essay questions.")
            return
        
        if args.delete_comments:
            print(f"\n🔄 Step 3: Deleting Comments from Submissions")
            print(f"{'-'*40}")
            
            success = delete_comments_from_submissions(args.course, args.quiz)
            
            if success:
                print(f"\n🎉 SUCCESS! Comments have been deleted from submissions!")
            else:
                print(f"\n💥 Comment deletion failed. Please check the error messages above.")
                sys.exit(1)
            return
        
        if args.dry_run:
            show_dry_run_preview(scores_data)
            print(f"\n📄 Scores file saved: {scores_file}")
            print(f"💡 Remove --dry-run flag to actually upload scores to Canvas.")
            return
        
        print(f"\n🔄 Step 3: Uploading Scores to Canvas")
        print(f"{'-'*40}")
        
        success = upload_scores_with_progress(args.course, args.quiz, scores_file)
        
        if success:
            print(f"\n🎉 SUCCESS! All students have been awarded maximum scores!")
            print(f"📊 Updated {len(scores_data['submissions'])} students")
            total_questions = sum(len(sub['answers']) for sub in scores_data['submissions'])
            print(f"📝 Scored {total_questions} questions")
        else:
            print(f"\n💥 Upload failed. Please check the error messages above.")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Operation cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    
    finally:
        # Clean up temporary files
        print(f"\n🧹 Cleaning up temporary files...")
        for temp_file in [quiz_data_file, scores_file]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"   ✅ Removed: {os.path.basename(temp_file)}")
                except Exception as e:
                    print(f"   ⚠️  Could not remove {os.path.basename(temp_file)}: {e}")

if __name__ == "__main__":
    main()