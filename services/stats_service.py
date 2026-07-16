from repositories.application_repository import ApplicationRepository


class StatsService:
    def __init__(self):
        self._repo = ApplicationRepository()
        self._cached_stats = None

    def _get_stats(self) -> dict:
        """Return stats, using a per-call cache to avoid redundant DB hits."""
        if self._cached_stats is None:
            self._cached_stats = self._repo.get_stats()
        return self._cached_stats

    def invalidate_cache(self):
        """Clear cached stats so next access fetches fresh data."""
        self._cached_stats = None

    def get_overview(self) -> dict:
        self.invalidate_cache()
        return self._get_stats()

    @staticmethod
    def _calc_rate(numerator: int, total: int) -> float:
        """Safe percentage calculation — returns 0.0 when total is zero."""
        if total == 0:
            return 0.0
        return (numerator / total) * 100

    def get_response_rate(self) -> float:
        stats = self._get_stats()
        total = stats["total"]
        responded = (stats["by_status"].get("interview", 0) + 
                     stats["by_status"].get("rejected", 0) + 
                     stats["by_status"].get("accepted", 0))
        return self._calc_rate(responded, total)

    def get_success_rate(self) -> float:
        stats = self._get_stats()
        total = stats["total"]
        accepted = stats["by_status"].get("accepted", 0)
        return self._calc_rate(accepted, total)

    def get_rejection_rate(self) -> float:
        stats = self._get_stats()
        total = stats["total"]
        rejected = stats["by_status"].get("rejected", 0)
        return self._calc_rate(rejected, total)

    def get_interview_rate(self) -> float:
        stats = self._get_stats()
        total = stats["total"]
        interview = stats["by_status"].get("interview", 0)
        return self._calc_rate(interview, total)

    def get_all_rates(self) -> dict:
        """Return all rates in a single call with only one DB query."""
        self.invalidate_cache()
        return {
            "response_rate": self.get_response_rate(),
            "success_rate": self.get_success_rate(),
            "rejection_rate": self.get_rejection_rate(),
            "interview_rate": self.get_interview_rate(),
        }
