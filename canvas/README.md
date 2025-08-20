# Canvas Quiz API Integration

This module provides secure Canvas API integration for creating and managing quizzes programmatically. It includes both a command-line interface and a modern React web application for easy quiz management.

## Features

### Core API Features
- **Secure Token Management**: Uses environment variables to store sensitive Canvas API credentials
- **Course Discovery**: List all available courses with their IDs and names (supports pagination for >100 courses)
- **Course Filtering**: Filter courses by prefix (e.g., "SP25" for Spring 2025 courses)
- **Automatic Pagination**: Handles Canvas API pagination to fetch all courses (no 100-course limit)
- **Quiz Creation**: Automatically create quizzes from text files
- **Multi-Question Type Support**: Support for multiple choice, true/false, short answer, and essay questions
- **Question Parsing**: Flexible parsing with automatic question type detection
- **Error Handling**: Comprehensive error handling for API failures and network issues

### Web Application Features
- **Modern React Frontend**: User-friendly web interface for quiz management
- **Real-time Course Loading**: Dynamic course selection with filtering capabilities
- **File Upload Interface**: Drag-and-drop file upload with progress tracking
- **Quiz Configuration**: Set quiz title, time limit, and publish status
- **Progress Tracking**: Visual progress bar during quiz upload
- **Responsive Design**: Works on desktop and mobile devices

## Security Features

- **Environment Variables**: All sensitive credentials are stored in environment variables
- **No Hardcoded Tokens**: API tokens are never stored in source code
- **Git-Safe**: `.env` files are automatically ignored by git

## Setup Instructions

### Option 1: Web Application (Recommended)

For the full web interface experience:

#### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Option 2: Command Line Only

For command-line usage only:

```bash
cd canvas
pip install -r requirements.txt
```

### 2. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your Canvas credentials:
   ```bash
   # Your Canvas domain
   CANVAS_API_URL=https://yourschool.instructure.com/api/v1
   
   # Your Canvas API access token
   CANVAS_ACCESS_TOKEN=your_actual_token_here
   
   # Course ID (optional - can be set after testing)
   CANVAS_COURSE_ID=12345
   ```

### 3. Generate Canvas API Token

1. Log into your Canvas account
2. Go to **Account** → **Settings**
3. Scroll down to **Approved Integrations**
4. Click **+ New Access Token**
5. Enter a purpose (e.g., "Quiz API Integration")
6. Click **Generate Token**
7. Copy the token and paste it into your `.env` file

⚠️ **Important**: Save the token immediately - Canvas will only show it once!

## Running the Application

### Web Application

To run the full web application with both backend and frontend:

#### 1. Start the Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at: `http://localhost:8000`

#### 2. Start the Frontend Server

In a new terminal:

```bash
cd frontend
npm run dev
```

The web application will be available at: `http://localhost:5173`

#### 3. Access the Application

Open your browser and navigate to `http://localhost:5173` to use the web interface.

### API Endpoints

The backend provides the following REST API endpoints:

- `GET /courses` - Get filtered Canvas courses
- `GET /test-api` - Test Canvas API connection
- `POST /upload-quiz` - Upload quiz from file

## Usage

### Command Line Interface

#### Test Canvas API Connection
```bash
python canvasquiz.py
```

This will:
- Verify your API credentials
- Display your user profile
- List all available courses with their IDs
- Show course names and codes in a formatted table

#### Upload Quiz from File
```bash
# Upload from text file
python canvasquiz.py upload sample_mixed_questions.txt "My Quiz" 60

# Upload from Markdown file
python canvasquiz.py upload cmpe257_exam_questions.md "CMPE257 Exam" 90

# Basic upload (uses default title and 30-minute time limit)
python canvasquiz.py upload questions.txt
```

### Python API

#### Test Canvas API Connection
```python
from canvasquiz import test_canvas_api

# Test API and list all courses (automatically handles pagination for >100 courses)
test_canvas_api()

# Filter courses by prefix (e.g., Spring 2025 courses)
test_canvas_api(course_prefix="SP25")
```

#### Get Courses Programmatically
```python
from canvasquiz import get_filtered_courses

# Get all courses (handles pagination automatically)
all_courses = get_filtered_courses()
print(f"Total courses: {len(all_courses)}")

# Get filtered courses
sp25_courses = get_filtered_courses("SP25")
for course in sp25_courses:
    print(f"Course: {course['name']} (ID: {course['id']})")
```

#### Use in Your Code

```python
from canvasquiz import test_canvas_api, upload_quiz_from_file

# Test API connection
success = test_canvas_api()
if success:
    print("Ready to create quizzes!")
```

#### Upload Quiz from File
```python
from canvasquiz import upload_quiz_from_file

# Upload quiz with default settings
result = upload_quiz_from_file('quiz_questions.txt')

# Upload with custom settings
result = upload_quiz_from_file(
    questions_file='my_quiz.txt',
    quiz_title='Midterm Exam',
    course_id='12345',
    time_limit=60,
    published=True
)

# Upload from Markdown file
result = upload_quiz_from_file("exam_questions.md", "Final Exam")

if result:
    print(f"Quiz created successfully! Quiz ID: {result['quiz_id']}")
    print(f"Quiz URL: {result['quiz_url']}")
```

## Question Format Support

The system supports multiple question types with automatic detection:

### Multiple Choice Questions
```
Q: What is the capital of France?
A) London
B) Berlin
C) Paris
D) Madrid
Answer: C
```

### True/False Questions
```
Q: Python is an interpreted programming language.
Type: true_false
Answer: True
```

### Short Answer Questions
```
Q: What are the main benefits of version control?
Type: short_answer
Answer: Track changes, collaborate, maintain history
```

### Essay Questions
```
Q: Explain machine learning and its applications.
Type: essay
Answer: Machine learning enables computers to learn from data...
```

**Notes:**
- Multiple choice questions are detected automatically (no Type: needed)
- For true/false, short answer, and essay questions, specify `Type:` 
- Sample answers for short answer/essay questions are optional
- Questions should be separated by blank lines

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `CANVAS_API_URL` | Yes | Your Canvas API base URL | `https://school.instructure.com/api/v1` |
| `CANVAS_ACCESS_TOKEN` | Yes | Your Canvas API access token | `1234~abcd...` |
| `CANVAS_COURSE_ID` | No | Default course ID for operations | `12345` |

## Security Best Practices

1. **Never commit `.env` files** - They're automatically ignored by git
2. **Use different tokens for different environments** (dev, staging, prod)
3. **Regularly rotate your API tokens**
4. **Limit token permissions** to only what's needed
5. **Store tokens securely** in production (use secrets management)

## Technical Details

### Pagination Implementation

The Canvas API limits responses to 100 items per page. This module automatically handles pagination by:

1. Making initial request with `per_page=100`
2. Parsing the `Link` header for pagination URLs
3. Following `rel="next"` links until all courses are fetched
4. Combining results from all pages

This ensures you get **all** your courses, regardless of how many you have (100, 500, 1000+).

```python
# Example: Institution with 250 courses
all_courses = get_filtered_courses()  # Fetches all 250 courses automatically
print(f"Total courses: {len(all_courses)}")  # Output: Total courses: 250
```

## Prompt
```
You are an expert educator and course designer. I want you to create in-depth, graduate-level exam questions based on the following content.

Requirements:
1. Output the markdown format. Generate questions for each important topics. Each question should test deep understanding, not just surface recall.
2. Choose any of the three question types, surround the questions via **, followed by **Answer:** paragraph and **Explanation:** paragraph:
   - True/False Questions (T/F)
   - Multiple Choice Questions (MCQ)
   - Short Answer Questions
3. Group question types in sections

content: 
```

## Troubleshooting

### Common Issues

1. **"CANVAS_ACCESS_TOKEN environment variable is required"**
   - Make sure your `.env` file exists and contains the token
   - Check that the token is not wrapped in quotes

2. **"API connection failed. Status code: 401"**
   - Your access token is invalid or expired
   - Generate a new token from Canvas settings

3. **"API connection failed. Status code: 403"**
   - Your token doesn't have sufficient permissions
   - Contact your Canvas administrator

4. **"Failed to fetch courses"**
   - Check your Canvas domain URL
   - Ensure you have access to courses

5. **Large Number of Courses (>100)**
   - Issue: Only seeing first 100 courses
   - Solution: This is now automatically handled by pagination - you'll see all courses

### Getting Help

If you encounter issues:
1. Run `python canvasquiz.py` to test your setup
2. Check the error messages for specific guidance
3. Verify your Canvas permissions with your administrator

## File Structure

```
InstructorAssistantAI/
├── backend/
│   ├── app/
│   │   └── main.py        # FastAPI backend server
│   └── requirements.txt   # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   ├── App.css        # Application styles
│   │   ├── main.tsx       # React entry point
│   │   └── index.css      # Global styles
│   ├── index.html         # HTML entry point
│   ├── package.json       # Frontend dependencies
│   ├── tsconfig.json      # TypeScript configuration
│   └── vite.config.ts     # Vite build configuration
├── canvas/
│   ├── canvasquiz.py      # Core Canvas API integration
│   ├── requirements.txt   # Canvas module dependencies
│   ├── .env.example       # Template for environment variables
│   ├── .env               # Your actual credentials (git-ignored)
│   └── README.md          # This documentation
└── docs/                  # Additional documentation
```