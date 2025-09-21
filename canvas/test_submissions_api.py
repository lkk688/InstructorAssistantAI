#!/usr/bin/env python3

import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Canvas API configuration
API_URL = os.getenv('CANVAS_API_URL', 'https://sjsu.instructure.com/api/v1')
ACCESS_TOKEN = os.getenv('CANVAS_ACCESS_TOKEN')

if not ACCESS_TOKEN:
    print("Error: CANVAS_ACCESS_TOKEN not found in environment variables")
    exit(1)

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

course_id = '1615883'
quiz_id = '1869206'

print("Testing Submissions API approach...")

# First get quiz to find assignment_id
quiz_response = requests.get(f"{API_URL}/courses/{course_id}/quizzes/{quiz_id}", headers=headers)
if quiz_response.status_code != 200:
    print(f"Error fetching quiz: {quiz_response.status_code}")
    exit(1)

quiz_data = quiz_response.json()
assignment_id = quiz_data.get('assignment_id')
print(f"Assignment ID: {assignment_id}")

if not assignment_id:
    print("No assignment_id found")
    exit(1)

# Get submissions with submission_history
params = {
    'include': ['submission_history'],
    'per_page': 5  # Just get first 5 for testing
}

print(f"\nFetching submissions from: {API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions")
submissions_response = requests.get(f"{API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions", headers=headers, params=params)

if submissions_response.status_code != 200:
    print(f"Error fetching submissions: {submissions_response.status_code}")
    print(f"Response: {submissions_response.text}")
    exit(1)

submissions = submissions_response.json()
print(f"\nFound {len(submissions)} submissions")
print(f"Request URL: {API_URL}/courses/{course_id}/assignments/{assignment_id}/submissions")
print(f"Request params: {params}")

if submissions:
    first_submission = submissions[0]
    print(f"\nFirst submission keys: {list(first_submission.keys())}")
    
    if 'submission_history' in first_submission:
        history = first_submission['submission_history']
        print(f"Submission history length: {len(history)}")
        
        if history:
            print(f"First history entry keys: {list(history[0].keys())}")
            
            if 'submission_data' in history[0]:
                submission_data = history[0]['submission_data']
                print(f"Submission data length: {len(submission_data)}")
                
                if submission_data:
                    print(f"First submission data keys: {list(submission_data[0].keys())}")
                    print(f"First submission data: {json.dumps(submission_data[0], indent=2)}")
            else:
                print("No submission_data in history[0]")
        else:
            print("Empty submission history")
    else:
        print("No submission_history in submission")
        
    # Also check if there's submission_data directly in the submission
    if 'submission_data' in first_submission:
        print(f"\nDirect submission_data length: {len(first_submission['submission_data'])}")
    else:
        print("\nNo direct submission_data in submission")
else:
    print("No submissions found")