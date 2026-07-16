Career & CV Management Application
A desktop application for managing your entire career journey — CV parsing, PDF editing, job tracking, and analytics. Built with Python and PyQt6.

✨ Features
CV Management — Upload & auto-parse CVs (PDF/DOCX), extract skills, experience, education, contact info
PDF Editor — Edit PDFs with text, images, lines, shapes. Full formatting, undo/redo, multi-page support
Job Tracker — Log applications, track statuses, search, filter, sort, calendar-based date filtering
Statistics — Dashboard with response/success/rejection rates, monthly trends, top companies
Job Analysis — Paste a job listing → get skill matching, cover letter draft, and improvement suggestions
Planned Companies — Track companies you plan to apply to with completion status

🛠️ Tech Stack
Python 3.10+ · PyQt6 · PyMuPDF · python-docx · SQLite3 · PyInstaller

📁 Project Structure

├── main.py              # Entry point
├── config.py            # Config & logging
├── database/            # SQLite connection & migrations
├── models/              # Data models (CV, Application, Company)
├── repositories/        # Data access layer
├── services/            # Business logic (parsing, analysis, stats)
├── ui/                  # PyQt6 interface (pages & widgets)
└── utils/               # Helpers (skill dictionary, language detection)
