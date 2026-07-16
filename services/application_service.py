from models.job_application import JobApplication
from repositories.application_repository import ApplicationRepository
from typing import List, Optional


class ApplicationService:
    def __init__(self):
        self._repo = ApplicationRepository()

    def _sync_backup_txt(self):
        try:
            import os
            from config import get_project_root
            backup_path = get_project_root() / "basvurulan_sirketler.txt"
            
            apps = self._repo.get_all()
            lines = ["=== BAŞVURULAN ŞİRKETLER VE POZİSYONLAR YEDEĞİ ===", ""]
            for app in apps:
                company = app.company_name or "Bilinmeyen Şirket"
                position = app.position or "Bilinmeyen Pozisyon"
                status = app.status_display
                date_str = f" [{app.application_date}]" if app.application_date else ""
                lines.append(f"{company} - {position} | Durum: {status}{date_str}")
                
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Not defteri yedeği güncellenirken hata: %s", e)

    def create(self, company_name: str, position: str = "", status: str = "applied",
               application_date: str = "", source: str = "",
               salary_range: str = "", contact_person: str = "",
               contact_email: str = "", job_url: str = "",
               notes: str = "") -> JobApplication:
        # Validate required fields
        if not company_name or not company_name.strip():
            raise ValueError("Şirket adı boş olamaz.")
        if status not in JobApplication.VALID_STATUSES:
            raise ValueError(
                f"Geçersiz durum: '{status}'. "
                f"Geçerli durumlar: {', '.join(JobApplication.VALID_STATUSES)}"
            )

        app = JobApplication(
            company_name=company_name.strip(),
            position=position.strip(),
            status=status,
            application_date=application_date,
            source=source.strip(),
            salary_range=salary_range.strip(),
            contact_person=contact_person.strip(),
            contact_email=contact_email.strip(),
            job_url=job_url.strip(),
            notes=notes.strip(),
        )
        app.id = self._repo.save(app)
        
        # Auto-add to planned companies if not exists
        try:
            from services.planned_company_service import PlannedCompanyService
            plan_service = PlannedCompanyService()
            plan_service.get_or_create(company_name.strip())
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Planlanan şirketlere otomatik eklenirken hata: %s", e)
            
        self._sync_backup_txt()
        return app

    def update(self, app: JobApplication) -> bool:
        # Validate status before updating
        if app.status not in JobApplication.VALID_STATUSES:
            raise ValueError(
                f"Geçersiz durum: '{app.status}'. "
                f"Geçerli durumlar: {', '.join(JobApplication.VALID_STATUSES)}"
            )
        result = self._repo.update(app)
        self._sync_backup_txt()
        return result

    def delete(self, app_id: int) -> bool:
        result = self._repo.delete(app_id)
        self._sync_backup_txt()
        return result

    def get_by_id(self, app_id: int) -> Optional[JobApplication]:
        return self._repo.get_by_id(app_id)

    def get_all(self) -> List[JobApplication]:
        return self._repo.get_all()

    def search(self, query: str) -> List[JobApplication]:
        return self._repo.search(query)

    def filter_by_status(self, status: str) -> List[JobApplication]:
        return self._repo.filter_by_status(status)

    def get_stats(self) -> dict:
        return self._repo.get_stats()
