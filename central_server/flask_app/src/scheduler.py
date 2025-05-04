from apscheduler.schedulers.background import BackgroundScheduler

from src.geoip_traceroute import enrich_ips
from src.anomaly_detectors import check_entropy_anomaly


scheduler = BackgroundScheduler()

def start_scheduler(app):
    """Here are all scheduled jobs, running within app context."""

    def wrap_with_context(func):
        def wrapped():
            with app.app_context():
                func()
        return wrapped

    scheduler.add_job(
        func=wrap_with_context(check_entropy_anomaly),
        trigger="interval",
        minutes=1,
        id="check_entropy_anomaly",
        replace_existing=True
    )

    scheduler.add_job(
        func=wrap_with_context(enrich_ips),
        trigger="interval",
        minutes=1,
        id="enrich_ips_with_data",
        replace_existing=True
    )

    scheduler.start()
