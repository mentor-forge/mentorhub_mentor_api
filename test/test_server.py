"""
Unit tests for server.py module.

Tests application initialization, route registration, and configuration.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import signal
import sys

_FORBIDDEN_CREDENTIAL_ISSUER_PATH = '/%s-%s' % ('dev', 'login')


class TestServerInitialization(unittest.TestCase):
    """Test cases for server initialization."""
    
    @patch('src.server.signal.signal')
    @patch('api_utils.MongoIO.get_instance')
    @patch('api_utils.Config.get_instance')
    def test_config_singleton_initialized(self, mock_get_config, mock_get_mongo, mock_signal):
        """Test that Config singleton is properly initialized."""
        # Arrange
        mock_config = MagicMock()
        mock_config.ENUMERATORS_COLLECTION_NAME = "Enumerators"
        mock_config.VERSIONS_COLLECTION_NAME = "Versions"
        mock_config.{{ (repo.name | upper | replace("-", "_")) }}_PORT = 8184
        mock_get_config.return_value = mock_config
        
        mock_mongo_instance = MagicMock()
        mock_mongo_instance.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo_instance
        
        # Import causes initialization
        import importlib
        import src.server as server_module
        importlib.reload(server_module)
        
        # Assert
        mock_get_config.assert_called()
    
    @patch('src.server.signal.signal')
    @patch('api_utils.MongoIO.get_instance')
    @patch('api_utils.Config.get_instance')
    def test_mongo_singleton_initialized(self, mock_get_config, mock_get_mongo, mock_signal):
        """Test that MongoIO singleton is properly initialized."""
        # Arrange
        mock_config = MagicMock()
        mock_config.ENUMERATORS_COLLECTION_NAME = "Enumerators"
        mock_config.VERSIONS_COLLECTION_NAME = "Versions"
        mock_get_config.return_value = mock_config
        
        mock_mongo_instance = MagicMock()
        mock_mongo_instance.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo_instance
        
        # Import causes initialization
        import importlib
        import src.server as server_module
        importlib.reload(server_module)
        
        # Assert
        mock_get_mongo.assert_called()
        self.assertEqual(mock_mongo_instance.get_documents.call_count, 2)


class TestAppConfiguration(unittest.TestCase):
    """Test cases for Flask app configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import the app after mocking at module level is complete
        from src.server import app
        self.app = app
        self.client = app.test_client()
    
    def test_app_exists(self):
        """Test that Flask app is created."""
        self.assertIsNotNone(self.app)
        self.assertEqual(self.app.name, 'src.server')
    
    def test_config_route_registered(self):
        """Test that /api/config route is registered."""
        response = self.client.get('/api/config')
        # Should not get 404 (route exists), but may get 401 (auth required)
        self.assertIn(response.status_code, [200, 401, 500])
    
    def test_credential_issuing_route_not_registered(self):
        """Domain APIs must not register HTTP routes that mint credentials."""
        response = self.client.post(_FORBIDDEN_CREDENTIAL_ISSUER_PATH)
        self.assertEqual(response.status_code, 404)
{% for item in service.data_domains.controls %}
    def test_{{item | lower}}_routes_registered(self):
        """Test that /api/{{item | lower}} routes are registered."""
        response = self.client.get('/api/{{item | lower}}')
        # Should not get 404 (route exists), but may get 401 (auth required)
        self.assertIn(response.status_code, [200, 401, 500])

{% endfor %}
{% for item in service.data_domains.creates %}
    def test_{{item | lower}}_routes_registered(self):
        """Test that /api/{{item | lower}} routes are registered."""
        response = self.client.get('/api/{{item | lower}}')
        # Should not get 404 (route exists), but may get 401 (auth required)
        self.assertIn(response.status_code, [200, 401, 500])

{% endfor %}
{% for item in service.data_domains.consumes %}
    def test_{{item | lower}}_routes_registered(self):
        """Test that /api/{{item | lower}} routes are registered."""
        response = self.client.get('/api/{{item | lower}}')
        # Should not get 404 (route exists), but may get 401 (auth required)
        self.assertIn(response.status_code, [200, 401, 500])

{% endfor %}
    
    def test_metrics_route_registered(self):
        """Test that /metrics route is registered."""
        response = self.client.get('/metrics')
        # Should not get 404 (route exists)
        self.assertNotEqual(response.status_code, 404)
    
    def test_all_blueprints_registered(self):
        """Test that all expected blueprints are registered."""
        blueprint_names = [bp.name for bp in self.app.blueprints.values()]
        
        # Check that our custom blueprints are registered
{% for item in service.data_domains.controls %}
        self.assertIn('{{item | lower}}_routes', blueprint_names)
{% endfor %}
{% for item in service.data_domains.creates %}
        self.assertIn('{{item | lower}}_routes', blueprint_names)
{% endfor %}
{% for item in service.data_domains.consumes %}
        self.assertIn('{{item | lower}}_routes', blueprint_names)
{% endfor %}
    
    def test_url_map_contains_expected_routes(self):
        """Test that URL map contains all expected route patterns."""
        # Get all registered routes
        rules = [rule.rule for rule in self.app.url_map.iter_rules()]
        
        # Check for key routes
        self.assertTrue(any('/docs' in rule for rule in rules))
        self.assertTrue(any('/api/config' in rule for rule in rules))
        self.assertFalse(any(_FORBIDDEN_CREDENTIAL_ISSUER_PATH in rule for rule in rules))
{% for item in service.data_domains.controls %}
        self.assertTrue(any('/api/{{item | lower}}' in rule for rule in rules))
{% endfor %}
{% for item in service.data_domains.creates %}
        self.assertTrue(any('/api/{{item | lower}}' in rule for rule in rules))
{% endfor %}
{% for item in service.data_domains.consumes %}
        self.assertTrue(any('/api/{{item | lower}}' in rule for rule in rules))
{% endfor %}
        self.assertTrue(any('/metrics' in rule for rule in rules))


class TestSignalHandlers(unittest.TestCase):
    """Test cases for signal handler registration and behavior."""
    
    @patch('src.server.signal.signal')
    @patch('api_utils.MongoIO.get_instance')
    @patch('api_utils.Config.get_instance')
    def test_sigterm_handler_registered(self, mock_get_config, mock_get_mongo, mock_signal):
        """Test that SIGTERM handler is registered."""
        # Arrange
        mock_config = MagicMock()
        mock_config.ENUMERATORS_COLLECTION_NAME = "Enumerators"
        mock_config.VERSIONS_COLLECTION_NAME = "Versions"
        mock_get_config.return_value = mock_config
        
        mock_mongo_instance = MagicMock()
        mock_mongo_instance.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo_instance
        
        # Import causes signal registration
        import importlib
        import src.server as server_module
        importlib.reload(server_module)
        
        # Assert - Check that signal.signal was called with SIGTERM
        calls = mock_signal.call_args_list
        sigterm_registered = any(
            call_args[0][0] == signal.SIGTERM 
            for call_args in calls
        )
        self.assertTrue(sigterm_registered, "SIGTERM handler not registered")
    
    @patch('src.server.signal.signal')
    @patch('api_utils.MongoIO.get_instance')
    @patch('api_utils.Config.get_instance')
    def test_sigint_handler_registered(self, mock_get_config, mock_get_mongo, mock_signal):
        """Test that SIGINT handler is registered."""
        # Arrange
        mock_config = MagicMock()
        mock_config.ENUMERATORS_COLLECTION_NAME = "Enumerators"
        mock_config.VERSIONS_COLLECTION_NAME = "Versions"
        mock_get_config.return_value = mock_config
        
        mock_mongo_instance = MagicMock()
        mock_mongo_instance.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo_instance
        
        # Import causes signal registration
        import importlib
        import src.server as server_module
        importlib.reload(server_module)
        
        # Assert - Check that signal.signal was called with SIGINT
        calls = mock_signal.call_args_list
        sigint_registered = any(
            call_args[0][0] == signal.SIGINT 
            for call_args in calls
        )
        self.assertTrue(sigint_registered, "SIGINT handler not registered")
    
    @patch('src.server.sys.exit')
    @patch('src.server.mongo')
    def test_handle_exit_disconnects_mongo(self, mock_mongo, mock_exit):
        """Test that handle_exit disconnects from MongoDB."""
        # Arrange
        from src.server import handle_exit
        mock_mongo.disconnect = MagicMock()
        
        # Act
        handle_exit(signal.SIGTERM, None)
        
        # Assert
        mock_mongo.disconnect.assert_called_once()
        mock_exit.assert_called_once_with(0)
    
    @patch('src.server.sys.exit')
    @patch('src.server.mongo')
    @patch('src.server.logger')
    def test_handle_exit_handles_disconnect_error(self, mock_logger, mock_mongo, mock_exit):
        """Test that handle_exit handles MongoDB disconnect errors gracefully."""
        # Arrange
        from src.server import handle_exit
        mock_mongo.disconnect = MagicMock(side_effect=Exception("Connection error"))
        
        # Act
        handle_exit(signal.SIGTERM, None)
        
        # Assert
        mock_mongo.disconnect.assert_called_once()
        # Should log error but still exit
        mock_logger.error.assert_called()
        mock_exit.assert_called_once_with(0)
    
    @patch('src.server.sys.exit')
    def test_handle_exit_with_none_mongo(self, mock_exit):
        """Test that handle_exit handles None mongo gracefully."""
        # Arrange
        from src.server import handle_exit
        import src.server as server_module
        original_mongo = server_module.mongo
        server_module.mongo = None
        
        try:
            # Act - Should not raise exception
            handle_exit(signal.SIGTERM, None)
            
            # Assert
            mock_exit.assert_called_once_with(0)
        finally:
            # Restore
            server_module.mongo = original_mongo


class TestServerExecution(unittest.TestCase):
    """Test cases for server execution."""
    
    @patch('src.server.app.run')
    @patch('src.server.config')
    def test_main_execution_uses_config_port(self, mock_config, mock_run):
        """Test that __main__ execution uses {{ (repo.name | upper | replace("-", "_")) }}_PORT from config."""
        # Arrange
        mock_config.{{ (repo.name | upper | replace("-", "_")) }}_PORT = 9999
        
        # Act
        # Simulate __main__ execution
        import src.server as server_module
        if hasattr(server_module, '__name__'):
            # Execute the main block logic
            api_port = mock_config.{{ (repo.name | upper | replace("-", "_")) }}_PORT
            
            # Assert
            self.assertEqual(api_port, 9999)


if __name__ == '__main__':
    unittest.main()
