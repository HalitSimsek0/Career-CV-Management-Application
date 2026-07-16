import os
import sys
import logging
from pathlib import Path


def get_project_root() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent

def get_app_data_dir() -> Path:
    base = get_project_root() / 'data'
    base.mkdir(parents=True, exist_ok=True)
    return base


APP_NAME = "CV Manager"
APP_VERSION = "1.1.0"
APP_DATA_DIR = get_app_data_dir()
DB_PATH = APP_DATA_DIR / "cv_manager.db"
BACKUP_DIR = APP_DATA_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
CV_STORAGE_DIR = APP_DATA_DIR / "cv_files"
CV_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# Setup structured logging for the application
def setup_logging():
    log_dir = APP_DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

# Initialize logging when config is loaded
setup_logging()
