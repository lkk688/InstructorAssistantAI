import requests
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_URL = os.getenv('CANVAS_API_URL', 'https://<your-canvas-domain>/api/v1')
ACCESS_TOKEN = os.getenv('CANVAS_ACCESS_TOKEN')
#COURSE_ID = os.getenv('CANVAS_COURSE_ID')

# 1612885      FA25: CMPE-214 Sec 01 - GPU Arch and Prog          FA25: CMPE-214 Se...
# 1614455      FA25: CMPE-249 Sec 01 - IA Systems                 FA25: CMPE-249 Se...
# 1614936      FA25: CMPE-249 Sec 33 - IA Systems                 FA25: CMPE-249 Se...
# 1609258      FA25: CMPE-258 Sec 02 - Deep Learning              FA25: CMPE-258 S

# === Configuration ===
API_KEY = os.getenv('CANVAS_ACCESS_TOKEN')
COURSE_ID = "1614455"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# === 1. Create the Assignment ===
assignment_payload = {
    "assignment": {
        "name": "Project Proposal",
        "description": """
<h2>📝 Project Proposal – Autonomous Driving</h2>
<p><strong>Due Date</strong>: <em>TBD</em><br>
<strong>Team Size</strong>: 2–4 students<br>
<strong>Submission Format</strong>: PDF file (2–4 pages) via Canvas<br>
<strong>Submission Type</strong>: File Upload (.pdf only)</p>

<h3>📌 Objective</h3>
<p>Outline your autonomous driving project, define the problem, select your approach (apply vs. train), and plan implementation and evaluation.</p>

<h3>✅ Required Sections</h3>
<ol>
<li><strong>Team and Project Info</strong></li>
<li><strong>Project Option</strong></li>
<li><strong>Motivation</strong></li>
<li><strong>Model & Dataset</strong></li>
<li><strong>Technical Plan</strong></li>
<li><strong>Evaluation Plan</strong></li>
<li><strong>Timeline</strong></li>
<li><strong>Risk Analysis</strong></li>
</ol>

<h3>💯 Grading Rubric</h3>
<table>
<thead><tr><th>Criterion</th><th>Points</th></tr></thead>
<tbody>
<tr><td>Clarity and Structure</td><td>2</td></tr>
<tr><td>Technical Feasibility</td><td>2</td></tr>
<tr><td>Relevance and Motivation</td><td>2</td></tr>
<tr><td>Evaluation Plan and Metrics</td><td>2</td></tr>
<tr><td>Timeline and Risk Management</td><td>2</td></tr>
</tbody>
</table>
""",
        "submission_types": ["online_upload"],
        "allowed_extensions": ["pdf"],
        "points_possible": 10,
        "published": False,  # Do not publish
    }
}
#<Response [201]>
assignment_response = requests.post(
    f"{API_URL}/courses/{COURSE_ID}/assignments",
    headers=headers,
    json=assignment_payload
)

if assignment_response.status_code != 201:
    print(f"❌ Failed to create assignment: {assignment_response.status_code}")
    print(assignment_response.json())
    exit()

assignment = assignment_response.json()
assignment_id = assignment["id"]
print(f"✅ Assignment created: ID {assignment_id}")

# === 2. Create and Attach the Rubric ===
rubric_payload = {
    "rubric[title]": "Project Proposal Rubric",
    "rubric[free_form_criterion_comments]": True,
    "rubric[criteria][0][description]": "Clarity and Structure",
    "rubric[criteria][0][points]": 2,
    "rubric[criteria][0][long_description]": "Proposal is well-written, logically organized, and easy to follow.",
    "rubric[criteria][0][ratings][0][description]": "Excellent",
    "rubric[criteria][0][ratings][0][points]": 2,
    "rubric[criteria][0][ratings][1][description]": "Good",
    "rubric[criteria][0][ratings][1][points]": 1.5,
    "rubric[criteria][0][ratings][2][description]": "Needs Improvement",
    "rubric[criteria][0][ratings][2][points]": 1,
    "rubric[criteria][0][ratings][3][description]": "Poor",
    "rubric[criteria][0][ratings][3][points]": 0,
    
    "rubric[criteria][1][description]": "Technical Feasibility",
    "rubric[criteria][1][points]": 2,
    "rubric[criteria][1][long_description]": "The proposed work is achievable given the timeline and resources.",
    "rubric[criteria][1][ratings][0][description]": "Excellent",
    "rubric[criteria][1][ratings][0][points]": 2,
    "rubric[criteria][1][ratings][1][description]": "Good",
    "rubric[criteria][1][ratings][1][points]": 1.5,
    "rubric[criteria][1][ratings][2][description]": "Needs Improvement",
    "rubric[criteria][1][ratings][2][points]": 1,
    "rubric[criteria][1][ratings][3][description]": "Poor",
    "rubric[criteria][1][ratings][3][points]": 0,
    
    "rubric[criteria][2][description]": "Relevance and Motivation",
    "rubric[criteria][2][points]": 2,
    "rubric[criteria][2][long_description]": "The topic is clearly motivated and relevant to autonomous driving.",
    "rubric[criteria][2][ratings][0][description]": "Excellent",
    "rubric[criteria][2][ratings][0][points]": 2,
    "rubric[criteria][2][ratings][1][description]": "Good",
    "rubric[criteria][2][ratings][1][points]": 1.5,
    "rubric[criteria][2][ratings][2][description]": "Needs Improvement",
    "rubric[criteria][2][ratings][2][points]": 1,
    "rubric[criteria][2][ratings][3][description]": "Poor",
    "rubric[criteria][2][ratings][3][points]": 0,
    
    "rubric[criteria][3][description]": "Evaluation Plan and Metrics",
    "rubric[criteria][3][points]": 2,
    "rubric[criteria][3][long_description]": "Evaluation strategy is clear and includes appropriate performance metrics.",
    "rubric[criteria][3][ratings][0][description]": "Excellent",
    "rubric[criteria][3][ratings][0][points]": 2,
    "rubric[criteria][3][ratings][1][description]": "Good",
    "rubric[criteria][3][ratings][1][points]": 1.5,
    "rubric[criteria][3][ratings][2][description]": "Needs Improvement",
    "rubric[criteria][3][ratings][2][points]": 1,
    "rubric[criteria][3][ratings][3][description]": "Poor",
    "rubric[criteria][3][ratings][3][points]": 0,
    
    "rubric[criteria][4][description]": "Timeline and Risk Management",
    "rubric[criteria][4][points]": 2,
    "rubric[criteria][4][long_description]": "The team presents a reasonable schedule and has considered possible risks.",
    "rubric[criteria][4][ratings][0][description]": "Excellent",
    "rubric[criteria][4][ratings][0][points]": 2,
    "rubric[criteria][4][ratings][1][description]": "Good",
    "rubric[criteria][4][ratings][1][points]": 1.5,
    "rubric[criteria][4][ratings][2][description]": "Needs Improvement",
    "rubric[criteria][4][ratings][2][points]": 1,
    "rubric[criteria][4][ratings][3][description]": "Poor",
    "rubric[criteria][4][ratings][3][points]": 0,
    
    "rubric_association[association_type]": "Assignment",
    "rubric_association[association_id]": assignment_id,
    "rubric_association[use_for_grading]": True,
    "rubric_association[purpose]": "grading"
}

rubric_response = requests.post(
    f"{API_URL}/courses/{COURSE_ID}/rubrics",
    headers=headers,
    data=rubric_payload
)

if rubric_response.status_code == 200:
    rubric_data = rubric_response.json()
    rubric_id = rubric_data['rubric']['id']
    print(f"✅ Rubric successfully created and attached: ID {rubric_id}")
else:
    print(f"❌ Failed to attach rubric: {rubric_response.status_code}")
    print(rubric_response.json())