import asyncio
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from src.scrapping.scrapping_page import scrapping_page

def run_scrapping():
    asyncio.run(scrapping_page())

def start_scheduler():
    scheduler: BackgroundScheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scrapping,
        CronTrigger(hour=22, minute=28),
        id='daily_scraping',
        name='Ejecutar scraping diario',
        replace_existing=True
    )
    scheduler.start()
    return scheduler