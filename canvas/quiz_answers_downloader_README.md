# Quiz Answers Downloader

This tool downloads all student quiz answers from Canvas LMS and generates a markdown file suitable for AI automatic grading.

## Features

- Downloads all student submissions for a specific quiz
- Formats answers in a structured markdown format
- Includes question text, options, and student responses
- Organizes answers by student for easy review
- Preserves question types (multiple choice, true/false, essay, etc.)
- Handles pagination for courses with many students

## Prerequisites

1. Python 3.6 or higher
2. Canvas LMS API access token with appropriate permissions
3. Required Python packages: `requests`, `python-dotenv`

## Installation

1. Ensure you have the required Python packages:

```bash
pip install requests python-dotenv
```

2. Create a `.env` file in the same directory as the script with the following variables:

```
CANVAS_API_URL=https://your-canvas-domain/api/v1
CANVAS_ACCESS_TOKEN=your_access_token_here
CANVAS_COURSE_ID=your_default_course_id_here  # Optional
```

## Usage

### List Available Quizzes

To see all available quizzes for a course:

```bash
python quiz_answers_downloader.py --list
```

Or specify a different course ID:

```bash
python quiz_answers_downloader.py --list --course 12345
```

### Download Quiz Answers

To download all student answers for a specific quiz:

```bash
python quiz_answers_downloader.py --quiz 67890
```

You can also specify the output file path:

```bash
python quiz_answers_downloader.py --quiz 67890 --output my_quiz_answers.md
```

And use a different course ID than the default:

```bash
python quiz_answers_downloader.py --course 12345 --quiz 67890
```

## Output Format

The generated markdown file includes:

1. Quiz metadata (title, course ID, quiz ID, submission count)
2. Quiz questions section with:
   - Question text
   - Question type
   - Answer options (for multiple choice and true/false)
3. Student answers section with:
   - Student name and ID
   - Score
   - Submission timestamp
   - Answers to each question

This format is designed to be easily parsed by AI grading systems while remaining human-readable.

## Example Output

```markdown
# Midterm Exam - Student Answers

Generated on: 2023-10-15 14:30:45

Course ID: 12345

Quiz ID: 67890

Total Submissions: 25

## Quiz Questions

### Question 1: What is machine learning?

**Type**: essay_question

**Text**: Explain in your own words what machine learning is and give an example.

### Question 2: Supervised vs Unsupervised Learning

**Type**: multiple_choice_question

**Text**: Which of the following is NOT a characteristic of supervised learning?

**Options**:

- 7890: It requires labeled training data
- 7891: It involves a teacher signal (Correct)
- 7892: It discovers hidden patterns without labels
- 7893: It makes predictions based on past examples

## Student Answers

### Jane Doe (ID: 1122334)

**Score**: 18 / 20

**Submitted**: 2023-10-10T15:45:30Z

#### Answers

**Question 1**: 
```
Machine learning is a subset of artificial intelligence that allows computers to learn from data without being explicitly programmed. For example, email spam filters use machine learning to identify unwanted emails based on patterns from previously labeled spam.
```

**Question 2**: Selected option ID: 7892
```

## AI Grading Integration

The markdown format is designed to be easily processed by AI grading systems. The structured format allows AI to:

1. Identify question types and expected answer formats
2. Extract student responses for each question
3. Compare responses to correct answers or rubrics
4. Generate feedback and scores

## Troubleshooting

- **API Rate Limiting**: If you encounter rate limiting issues, the script will pause and retry automatically.
- **Large Courses**: For courses with many students, the script may take some time to complete due to API pagination.
- **HTML Content**: The script attempts to strip HTML tags from question and answer text, but complex formatting may require additional processing.

## License

This tool is part of the InstructorAssistantAI project and is subject to its licensing terms.