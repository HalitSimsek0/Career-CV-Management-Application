from models.planned_company import PlannedCompany
from repositories.planned_company_repository import PlannedCompanyRepository
from typing import List


class PlannedCompanyService:
    def __init__(self):
        self._repo = PlannedCompanyRepository()

    def create(self, company_name: str, check_exists: bool = True) -> PlannedCompany:
        if not company_name or not company_name.strip():
            raise ValueError("Şirket adı boş olamaz.")

        from utils.string_utils import turkish_upper, search_normalize
        
        if check_exists:
            norm_new_name = search_normalize(company_name.strip())
            existing = self.get_all()
            for comp in existing:
                if comp.company_name and search_normalize(comp.company_name) == norm_new_name:
                    raise ValueError(f"'{comp.company_name}' şirketi zaten planlananlar listesinde var.")

        company = PlannedCompany(
            company_name=turkish_upper(company_name.strip()),
        )
        company.id = self._repo.save(company)
        return company

    def get_or_create(self, company_name: str) -> PlannedCompany:
        if not company_name or not company_name.strip():
            return None

        from utils.string_utils import turkish_upper, search_normalize
        norm_new_name = search_normalize(company_name.strip())
        
        existing = self.get_all()
        for comp in existing:
            if comp.company_name and search_normalize(comp.company_name) == norm_new_name:
                return comp

        company = PlannedCompany(
            company_name=turkish_upper(company_name.strip()),
        )
        company.id = self._repo.save(company)
        return company

    def delete(self, company_id: int) -> bool:
        return self._repo.delete(company_id)

    def update(self, company: PlannedCompany) -> None:
        self._repo.update(company)

    def get_all(self) -> List[PlannedCompany]:
        return self._repo.get_all()

    def search(self, query: str) -> List[PlannedCompany]:
        return self._repo.search(query)

    def get_count(self) -> int:
        return self._repo.count()
