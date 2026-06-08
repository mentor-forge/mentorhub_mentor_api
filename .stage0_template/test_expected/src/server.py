"""
Flask MongoDB API Server

This is a Flask + MongoDB API that for the sample service in the Mentor Hub system.
"""
import sys
import os
import signal
from flask import Flask, send_from_directory

# Initialize Config Singleton (doesn't require external services)
from api_utils import Config
config = Config.get_instance()

# Initialize logging (Config constructor configures logging)
import logging
logger = logging.getLogger(__name__)
logger.info("============= Starting Server ===============")

# Initialize MongoIO Singleton and set enumerators and versions
from api_utils import MongoIO
mongo = MongoIO.get_instance()
config.set_enumerators(mongo.get_documents(config.ENUMERATORS_COLLECTION_NAME))
config.set_versions(mongo.get_documents(config.VERSIONS_COLLECTION_NAME))

# Initialize Flask App
from api_utils import MongoJSONEncoder
app = Flask(__name__)
app.json = MongoJSONEncoder(app)

# Route registration (all grouped together)
from api_utils import (
    create_metric_routes,
    create_config_routes,
    create_explorer_routes
)
from src.routes.control_routes import create_control_routes
from src.routes.create_routes import create_create_routes
from src.routes.consume_routes import create_consume_routes
# Register route blueprints
# Register explorer routes with template's docs directory
docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
app.register_blueprint(create_explorer_routes(docs_dir), url_prefix='/docs')
app.register_blueprint(create_config_routes(), url_prefix='/api/config')
app.register_blueprint(create_control_routes(), url_prefix='/api/control')
app.register_blueprint(create_create_routes(), url_prefix='/api/create')
app.register_blueprint(create_consume_routes(), url_prefix='/api/consume')
metrics = create_metric_routes(app)  # This exposes /metrics endpoint

logger.info("============= Routes Registered ===============")
logger.info("  /api/config - Configuration endpoint")
logger.info("  /api/control - Control domain endpoints")
logger.info("  /api/create - Create domain endpoints")
logger.info("  /api/consume - Consume domain endpoints")
logger.info("  /docs - API Explorer")
logger.info("  /metrics - Prometheus metrics endpoint")

# Define a signal handler for SIGTERM and SIGINT
def handle_exit(signum, frame):
    """Handle graceful shutdown on SIGTERM/SIGINT."""
    global mongo
    logger.info(f"Received signal {signum}. Initiating shutdown...")
    
    # Disconnect from MongoDB if connected
    if mongo is not None:
        logger.info("Closing MongoDB connection.")
        try:
            mongo.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from MongoDB: {e}")
    
    logger.info("Shutdown complete.")
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# Expose app for Gunicorn or direct execution
if __name__ == "__main__":
    api_port = config.SAMPLE_API_PORT
    logger.info(f"Starting Flask server on port {api_port}")
    app.run(host="0.0.0.0", port=api_port, debug=False)