# InstructorAssistantAI – Pending Changes Overview

This document summarizes the uncommitted updates currently present in the working tree so that stakeholders (e.g., Professor Pullareddy) can review what was touched and why before a commit goes in.

---

## Environment & Runtime Actions
- Confirmed Canvas API connectivity by running `python canvas/canvasquiz.py`; captured course roster for reference.
- Ensured Python dependencies were available via `pip install -r backend/requirements.txt`.
- Cleared blocked dev ports by terminating stray `uvicorn` (8000) and Vite/Node (5173) processes.

These runtime steps did not modify repository files but ensured the application was in a usable state during testing.

---

## Source Control Hygiene
- Added `.DS_Store` to `.gitignore` and removed the tracked file (`git rm --cached .DS_Store`). This stops macOS Finder metadata from reappearing in future diffs.

---

## Backend (FastAPI) Updates
- **`backend/requirements.txt`**  
  - Bumped framework/tooling versions to the latest verified stack: `fastapi 0.115.4`, `uvicorn[standard] 0.32.0`, `python-multipart 0.0.10`, `requests 2.32.3`, `python-dotenv 1.0.1`, and explicitly added `pydantic 2.10.4`. These align the backend with the versions used during local testing.
- **`backend/app/main.py`**  
  - Hardened file-type validation by lower-casing the uploaded filename before checking for `.md`/`.txt`, ensuring mixed-case extensions (e.g., `.MD`) are accepted.
  - Restored a trailing newline at EOF (formatting consistency).

_Impact_: Backend now reliably accepts markdown uploads regardless of filename casing and runs against the intended dependency set.

---

## Canvas Quiz Automation
- **`canvas/canvasquiz.py`**  
  - Made quiz creation payloads form-encoded (`quiz[title]`, etc.) to match Canvas’ expected format and expanded response handling to cope with Canvas returning wrapped objects or lists.
  - Added defensive checks for missing/renamed fields and improved logging when Canvas responses deviate from the ideal schema.
  - Enhanced question-group creation to tolerate both list and dict responses.
  - Treated HTTP 201 as a successful question creation response and corrected the fallback true/false answer schema to use Canvas’ `weight` key.
  - Ensured the closing status message still renders (newline reintroduced at EOF).

- **`canvas/question_parsers.py`**  
  - Rewrote `parse_questions` to support numbered “QUESTION n (Xpt)” blocks, mixed-case directives, optional inline type declarations, and both letter- or text-based correct-answer indicators.
  - Added graceful handling for missing answers (defaults to first option), reusable regex helpers, UTF-8 safe reading, and ensured math conversion runs on the finalized question list.
  - Preserved existing markdown/CMPE parsers while normalizing EOF formatting.

_Impact_: The Canvas automation pipeline is more resilient to Canvas’ varied API responses and can ingest a wider range of instructor-authored text files without manual cleanup.

---

## Frontend (React/Vite)
- **`frontend/src/App.tsx`**  
  - Introduced course sanitization to drop placeholder Canvas entries (`Unnamed Course` / `N/A`).
  - Added helper logic to default-select CMPE courses when present and to keep selections valid as filters change.
  - Implemented client-side filtering without round-tripping to the API, using normalized prefix matching across course codes and names.
  - Improved the rendered course labels to avoid duplicated `N/A` text and provide clearer dropdown entries.

_Impact_: The instructor-facing UI now presents cleaner course lists, auto-selects the most relevant option, and handles filtering more intuitively.

---

## Sample Content
- **`sample.txt`** (new file)  
  - Added a representative question bank covering multiple choice, true/false, short-answer, and essay formats using the new numbered layout. This was used to validate the reworked text parser and can serve as a testing artifact.

---

## Documentation
- **`docs/change_overview.md`** (this file) now captures the above adjustments for transparency prior to committing.

---

### Suggested Next Steps
1. Run the backend (`uvicorn app.main:app --reload`) and frontend (`npm run dev`) to sanity-check end-to-end quiz creation with the new parser.
2. Commit the pending changes once validated.
3. Optionally expand automated tests around the parsers to lock in coverage for the new question formats.
