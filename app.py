import os
import json
import datetime
from flask import Flask
from loguru import logger
from src.blueprints.routemanager import routemanager

# Load settings from appsettings.json
with open("appsettings.json", "r", encoding="utf-8") as settings_file:
    settings = json.load(settings_file)

# Configure log directory
log_directory = settings.get("log_directory", "static/logs")
os.makedirs(log_directory, exist_ok=True)
log_file_path = os.path.join(
    log_directory, f"application_{datetime.datetime.today().strftime('%Y-%m-%d')}.log"
)

# Configure Loguru
logger.add(
    log_file_path,
    rotation="10 MB",
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<cyan>{module}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{level}</level> | <level>{message}</level>",
)

# Create Flask app
app = Flask(__name__)
app.register_blueprint(routemanager, url_prefix="")


def main():
    logger.info("Starting application")
    port = settings.get("port", 8000)
    logger.info(f"Application running on port {port}")
    app.run(debug=True, port=port)


if __name__ == "__main__":
    main()
