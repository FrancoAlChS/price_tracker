import asyncio
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore
from src.scrapping.scrapping_page import scrapping_page

def run_scrapping():
    asyncio.run(scrapping_page())

def start_scheduler():
    scheduler: BackgroundScheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scrapping,
        IntervalTrigger(minutes=5),
        id='periodic_scraping',
        name='Ejecutar scraping cada 5 minutos',
        replace_existing=True
    )
    scheduler.start()
    return scheduler