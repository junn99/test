"""Background job scheduler for automated tasks."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..sync.daily_sync import run_daily_sync
from ..utils.config import settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class JobScheduler:
    """Manages scheduled background jobs."""

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=settings.sync_timezone)
        self.is_running = False

    def add_daily_sync_job(self):
        """Add daily synchronization job."""
        trigger = CronTrigger(
            hour=settings.sync_hour,
            minute=0,
            timezone=settings.sync_timezone
        )

        self.scheduler.add_job(
            func=self._run_daily_sync_job,
            trigger=trigger,
            id="daily_sync",
            name="Daily Notion Sync",
            replace_existing=True
        )

        logger.info(
            f"Daily sync job scheduled for {settings.sync_hour}:00 {settings.sync_timezone}"
        )

    def _run_daily_sync_job(self):
        """Execute daily sync job."""
        logger.info("Executing scheduled daily sync")
        try:
            result = run_daily_sync(days=1)
            logger.info(f"Daily sync completed: {result}")
        except Exception as e:
            logger.error(f"Daily sync job failed: {e}")

    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.add_daily_sync_job()
            self.scheduler.start()
            self.is_running = True
            logger.info("Job scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Job scheduler stopped")

    def list_jobs(self):
        """List all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in jobs
        ]


# Global scheduler instance
_scheduler = None


def get_scheduler() -> JobScheduler:
    """Get or create global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler
