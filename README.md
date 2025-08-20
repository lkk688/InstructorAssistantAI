# InstructorAssistantAI
A full-stack AI assistant to automate instructors' tasks and integrated with Canvas LMS.

## Features
- 📤 Upload local question files (.txt)
- 🔧 Auto-create quizzes using Canvas REST API
- 🌐 Web UI built with React + Vite
- ⚡ FastAPI backend
- 📚 MkDocs for documentation

## Quickstart

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Documentation
```bash
pip install mkdocs-material
mkdocs serve
```

## License
MIT
