#!/usr/bin/env python3
"""
Auto Max Score Uploader for Canvas Quiz Short Answer Questions

This script automatically assigns maximum scores to all students' short answer questions
by downloading quiz data, generating full-score assignments, and uploading to Canvas.

Usage:
    python auto_max_score_uploader.py --course COURSE_ID --quiz QUIZ_ID

Example:
    python auto_max_score_uploader.py --course 1615883 --quiz 1869206
"""

import json
import argparse
import os
import sys
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
    """
    print(f"Loading quiz data from {quiz_data_file}...")
    
    with open(quiz_data_file, 'r', encoding='utf-8') as f:
        quiz_data = json.load(f)
    
    # Create scores structure
    scores_data = {
        "submissions": []
    }
    
    print(f"Processing {len(quiz_data['submissions'])} submissions...")
    
    for submission in quiz_data['submissions']:
        submission_scores = {
            "user_id": submission['user_id'],
            "student_name": submission['student_name'],
            "submission_id": submission['submission_id'],
            "quiz_submission_id": submission['quiz_submission_id'],
            "attempt": submission['attempt'],
            "answers": []
        }
        
        # Assign maximum score to each short answer question
        for answer in submission['answers']:
            if answer['question_type'] in ['short_answer_question', 'essay_question']:
                answer_score = {
                    "question_id": answer['question_id'],
                    "score": answer['points_possible']  # Maximum score
                }
                submission_scores['answers'].append(answer_score)
        
        if submission_scores['answers']:  # Only add if there are short answer questions
            scores_data['submissions'].append(submission_scores)
    
    # Write scores file
    with open(output_scores_file, 'w', encoding='utf-8') as f:
        json.dump(scores_data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated scores file: {output_scores_file}")
    print(f"Total submissions with short answer questions: {len(scores_data['submissions'])}")
    
    # Calculate total questions and points
    total_questions = sum(len(sub['answers']) for sub in scores_data['submissions'])
    total_points = sum(sum(ans['score'] for ans in sub['answers']) for sub in scores_data['submissions'])
    
    print(f"Total short answer questions to score: {total_questions}")
    print(f"Total points to be awarded: {total_points}")
    
    return scores_data

def main():
    parser = argparse.ArgumentParser(
        description='Automatically assign maximum scores to all students\' short answer questions'
    )
    parser.add_argument('--course', type=str, required=True, help='Canvas course ID')
    parser.add_argument('--quiz', type=str, required=True, help='Canvas quiz ID')
    parser.add_argument('--dry-run', action='store_true', help='Generate scores file but do not upload to Canvas')
    parser.add_argument('--temp-dir', type=str, default='.', help='Directory for temporary files')
    
    args = parser.parse_args()
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # File paths
    quiz_data_file = os.path.join(args.temp_dir, f'quiz_data_{args.quiz}_{timestamp}.json')
    scores_file = os.path.join(args.temp_dir, f'max_scores_{args.quiz}_{timestamp}.json')
    
    try:
        print("=== Step 1: Downloading Quiz Data ===")
        print(f"Downloading short answer questions for quiz {args.quiz}...")
        
        # Download quiz data with short answer filter
        generate_quiz_answers_json(
            course_id=args.course,
            quiz_id=args.quiz,
            output_file=quiz_data_file,
            short_answer_only=True
        )
        
        print("\n=== Step 2: Generating Maximum Scores ===")
        scores_data = generate_max_scores_file(quiz_data_file, scores_file)
        
        if not scores_data['submissions']:
            print("No short answer questions found in this quiz.")
            return
        
        if args.dry_run:
            print("\n=== DRY RUN MODE ===")
            print(f"Scores file generated: {scores_file}")
            print("Use --upload flag to actually upload scores to Canvas.")
            return
        
        print("\n=== Step 3: Uploading Scores to Canvas ===")
        
        # Confirm before uploading
        response = input(f"\nReady to upload maximum scores for {len(scores_data['submissions'])} students. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Upload cancelled.")
            return
        
        # Upload scores to Canvas
        update_quiz_scores(args.course, args.quiz, scores_file)
        
        print("\n=== Upload Complete ===")
        print("All students have been awarded maximum scores for short answer questions.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    finally:
        # Clean up temporary files
        for temp_file in [quiz_data_file, scores_file]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"Cleaned up temporary file: {temp_file}")
                except:
                    pass

if __name__ == "__main__":
    main()