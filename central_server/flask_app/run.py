from src.app import create_app

app = create_app()

# Gracefully shuting down APScheduler when the app exits
import atexit
from src.scheduler import scheduler  # this imports the actual scheduler instance
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
