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
from src.routes.resource_routes import create_resource_routes
from src.routes.path_routes import create_path_routes
from src.routes.plan_routes import create_plan_routes
from src.routes.encounter_routes import create_encounter_routes
from src.routes.event_routes import create_event_routes
from src.routes.profile_routes import create_profile_routes
# Register route blueprints
# Register explorer routes with template's docs directory
docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
app.register_blueprint(create_explorer_routes(docs_dir), url_prefix='/docs')
app.register_blueprint(create_config_routes(), url_prefix='/api/config')
app.register_blueprint(create_resource_routes(), url_prefix='/api/resource')
app.register_blueprint(create_path_routes(), url_prefix='/api/path')
app.register_blueprint(create_plan_routes(), url_prefix='/api/plan')
app.register_blueprint(create_encounter_routes(), url_prefix='/api/encounter')
app.register_blueprint(create_event_routes(), url_prefix='/api/event')
app.register_blueprint(create_profile_routes(), url_prefix='/api/profile')
metrics = create_metric_routes(app)  # This exposes /metrics endpoint

logger.info("============= Routes Registered ===============")
logger.info("  /api/config - Configuration endpoint")
logger.info("  /api/resource - Resource domain endpoints")
logger.info("  /api/path - Path domain endpoints")
logger.info("  /api/plan - Plan domain endpoints")
logger.info("  /api/encounter - Encounter domain endpoints")
logger.info("  /api/event - Event domain endpoints")
logger.info("  /api/profile - Profile domain endpoints")
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
    api_port = config.MENTOR_API_PORT
    logger.info(f"Starting Flask server on port {api_port}")
    app.run(host="0.0.0.0", port=api_port, debug=False)