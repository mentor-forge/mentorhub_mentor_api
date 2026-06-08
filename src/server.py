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
{% for item in service.data_domains.controls -%}
from src.routes.{{item | lower}}_routes import create_{{item | lower}}_routes
{% endfor -%}
{% for item in service.data_domains.creates -%}
from src.routes.{{item | lower}}_routes import create_{{item | lower}}_routes
{% endfor -%}
{% for item in service.data_domains.consumes -%}
from src.routes.{{item | lower}}_routes import create_{{item | lower}}_routes
{% endfor -%}

# Register route blueprints
# Register explorer routes with template's docs directory
docs_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
app.register_blueprint(create_explorer_routes(docs_dir), url_prefix='/docs')
app.register_blueprint(create_config_routes(), url_prefix='/api/config')
{% for item in service.data_domains.controls -%}
app.register_blueprint(create_{{item | lower}}_routes(), url_prefix='/api/{{item | lower}}')
{% endfor -%}
{% for item in service.data_domains.creates -%}
app.register_blueprint(create_{{item | lower}}_routes(), url_prefix='/api/{{item | lower}}')
{% endfor -%}
{% for item in service.data_domains.consumes -%}
app.register_blueprint(create_{{item | lower}}_routes(), url_prefix='/api/{{item | lower}}')
{% endfor -%}
metrics = create_metric_routes(app)  # This exposes /metrics endpoint

logger.info("============= Routes Registered ===============")
logger.info("  /api/config - Configuration endpoint")
{% for item in service.data_domains.controls -%}
logger.info("  /api/{{item | lower}} - {{item}} domain endpoints")
{% endfor -%}
{% for item in service.data_domains.creates -%}
logger.info("  /api/{{item | lower}} - {{item}} domain endpoints")
{% endfor -%}
{% for item in service.data_domains.consumes -%}
logger.info("  /api/{{item | lower}} - {{item}} domain endpoints")
{% endfor -%}
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
    api_port = config.{{ (repo.name | upper | replace("-", "_")) }}_PORT
    logger.info(f"Starting Flask server on port {api_port}")
    app.run(host="0.0.0.0", port=api_port, debug=False)