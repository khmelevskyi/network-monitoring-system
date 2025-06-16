from apscheduler.schedulers.background import BackgroundScheduler

from src.ip_details_enrichment import enrich_ips
from src.anomaly_detectors import check_all_anomalies
from src.api_endpoints import update_routers_and_devices


scheduler = BackgroundScheduler()

def start_scheduler(app):
	"""Here are all scheduled jobs, running within app context."""

	def wrap_with_context(func):
		def wrapped():
			with app.app_context():
				func()
		return wrapped

	scheduler.add_job(
		func=wrap_with_context(enrich_ips),
		trigger="interval",
		minutes=1,
		id="enrich_ips_with_data",
		replace_existing=True
	)

	scheduler.add_job(
		func=wrap_with_context(check_all_anomalies),
		trigger="interval",
		minutes=1,
		id="check_all_anomalies",
		replace_existing=True
	)

	scheduler.add_job(
		func=wrap_with_context(update_routers_and_devices),
		trigger="interval",
		minutes=1,
		id="update_routers_and_devices",
		replace_existing=True
	)

	scheduler.start()
