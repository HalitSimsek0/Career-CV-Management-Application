import logging
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


def run_migrations():
    conn = DatabaseConnection().get_connection()
    cursor = conn.cursor()

    # Create migrations tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT DEFAULT (datetime('now'))
        )
    """)

    def has_run(version: int) -> bool:
        cursor.execute("SELECT 1 FROM schema_migrations WHERE version = ?", (version,))
        return cursor.fetchone() is not None

    def mark_run(version: int):
        cursor.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))

    try:
        # Base schema creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cv_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                linkedin_url TEXT,
                github_url TEXT,
                website_url TEXT,
                location TEXT,
                summary TEXT,
                skills TEXT,
                experiences TEXT,
                education TEXT,
                projects TEXT,
                languages TEXT,
                certifications TEXT,
                raw_text TEXT,
                original_filename TEXT,
                file_path TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Migration 1: Add new sections to cv_snapshots
        if not has_run(1):
            cursor.execute("PRAGMA table_info(cv_snapshots)")
            columns = [col[1] for col in cursor.fetchall()]
            if "volunteer" not in columns:
                cursor.execute("ALTER TABLE cv_snapshots ADD COLUMN volunteer TEXT")
            if "references" not in columns:
                cursor.execute('ALTER TABLE cv_snapshots ADD COLUMN "references" TEXT')
            if "personal_info" not in columns:
                cursor.execute("ALTER TABLE cv_snapshots ADD COLUMN personal_info TEXT")
            mark_run(1)

        # Base schema for job applications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                position TEXT,
                status TEXT DEFAULT 'applied',
                application_date TEXT DEFAULT (date('now')),
                response_date TEXT,
                source TEXT,
                salary_range TEXT,
                contact_person TEXT,
                contact_email TEXT,
                job_url TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_applications_company
            ON job_applications(company_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_applications_status
            ON job_applications(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_applications_date
            ON job_applications(application_date)
        """)

        # Migration 2: Add notes to job_applications
        if not has_run(2):
            cursor.execute("PRAGMA table_info(job_applications)")
            app_columns = [col[1] for col in cursor.fetchall()]
            if "notes" not in app_columns:
                cursor.execute("ALTER TABLE job_applications ADD COLUMN notes TEXT")
            mark_run(2)

        # Migration 3: Create planned_companies table
        if not has_run(3):
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS planned_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_planned_companies_name
                ON planned_companies(company_name)
            """)
            mark_run(3)

        # Migration 4: Add is_applied to planned_companies
        if not has_run(4):
            cursor.execute("PRAGMA table_info(planned_companies)")
            cols = [col[1] for col in cursor.fetchall()]
            if "is_applied" not in cols:
                cursor.execute("ALTER TABLE planned_companies ADD COLUMN is_applied INTEGER DEFAULT NULL")
            mark_run(4)

        conn.commit()
        logger.info("Veritabanı migration'ları başarıyla tamamlandı.")
        
    except Exception as e:
        logger.exception("Migration sırasında hata oluştu: %s", e)
        conn.rollback()
        raise
