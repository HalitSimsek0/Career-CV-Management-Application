# CV Manager

A desktop application for managing your entire career journey — CV parsing, PDF editing, job application tracking, and analytics. Built with Python and PyQt6.

## Features

### CV Management
- Upload CVs in **PDF** and **DOCX** formats
- Auto-extract contact info, skills, experience, education, projects, certifications, languages, and references
- **Turkish and English** CV support with automatic language detection
- CV history stored in local database

### PDF Editor
- Edit PDF files directly within the app
- Add **text blocks** with font, size, color, and alignment options
- Insert **images** with drag-and-drop positioning and crop support
- Draw **lines and shapes** — rectangles, circles, arrows, freehand
- Multi-page navigation
- Full **undo/redo** support
- Save edited PDFs

### Job Application Tracker
- Log applications with company, position, date, source, salary range
- Track status: **Applied → Interview → Accepted / Rejected**
- Store contact info, job URLs, and custom notes per application
- Search, filter, sort, and calendar-based date filtering
- Automatic **TXT backup** of application data

### Statistics Dashboard
- Total applications, interviews, acceptances, and rejections
- Response rate, success rate, rejection rate, interview rate
- Monthly trend bar charts
- Top applied companies
- Status distribution breakdown

### Job Listing Analysis
- Paste a job listing → get instant analysis
- **Skill matching** against your CV
- Missing skill detection with improvement suggestions
- Keyword extraction from job descriptions
- **Cover letter draft** generation
- Experience and education requirement parsing
- Optional Turkish ↔ English translation via `deep-translator`

### Planned Companies
- Track companies you plan to apply to
- Bulk add via comma-separated list
- Mark application status (Applied / Not Applied)
- Search, filter, and auto-sync with application records

---

## Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| Language | Python 3.10+ | Core development language |
| GUI | PyQt6 | Desktop UI framework |
| PDF Processing | PyMuPDF (fitz) | PDF reading, text extraction, editing |
| DOCX Processing | python-docx | Word document text extraction |
| Database | SQLite3 | Local data storage with versioned migrations |
| Packaging | PyInstaller | Single-file .exe distribution |
| Translation | deep-translator | Optional translation for job analysis |

---

## Architecture

The app follows a **layered architecture** pattern:

```
UI Layer  →  Service Layer  →  Repository Layer  →  Database Layer
(PyQt6)      (Business logic)   (Data access)       (SQLite)
```

- Clean separation of concerns across layers
- Versioned database migrations for schema management
- Lazy loading for heavy pages (PDF Editor, Job Analysis)

---
