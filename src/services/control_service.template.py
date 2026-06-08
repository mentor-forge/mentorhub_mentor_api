"""
{{item}} service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for {{item}} domain.
"""
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from api_utils.mongo_utils import execute_infinite_scroll_query
import logging

logger = logging.getLogger(__name__)

# Allowed sort fields for {{item}} domain
ALLOWED_SORT_FIELDS = ['name', 'description', 'status', 'created.at_time', 'saved.at_time']


class {{item}}Service:
    """
    Service class for {{item}} domain operations.
    
    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for {{item}} domain
    """
    
    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create', 'update')
        
        Raises:
            HTTPForbidden: If user doesn't have required permission
            
        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).
        
        Example RBAC implementation:
            if operation == 'update':
                # Update requires admin role
                if 'admin' not in token.get('roles', []):
                    raise HTTPForbidden("Admin role required to update {{item | lower}} documents")
            elif operation == 'create':
                # Create requires staff or admin role
                if not any(role in token.get('roles', []) for role in ['staff', 'admin']):
                    raise HTTPForbidden("Staff or admin role required to create {{item | lower}} documents")
            elif operation == 'read':
                # Read requires any authenticated user (no additional check needed)
                pass
        """
        pass
    
    @staticmethod
    def _validate_update_data(data):
        """
        Validate update data to prevent security issues.
        
        Args:
            data: Dictionary of fields to update
            
        Raises:
            HTTPForbidden: If update data contains restricted fields
        """
        # Prevent updates to _id and system-managed fields
        restricted_fields = ['_id', 'created', 'saved']
        for field in restricted_fields:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")
    
    @staticmethod
    def create_{{item | lower}}(data, token, breadcrumb):
        """
        Create a new {{item | lower}} document.
        
        Args:
            data: Dictionary containing {{item | lower}} data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)
            
        Returns:
            str: The ID of the created {{item | lower}} document
        """
        try:
            {{item}}Service._check_permission(token, 'create')
            
            # Remove _id if present (MongoDB will generate it)
            if '_id' in data:
                del data['_id']
            
            # Automatically populate required fields: created and saved
            # These are system-managed and should not be provided by the client
            # Use breadcrumb directly as it already has the correct structure
            data['created'] = breadcrumb
            data['saved'] = breadcrumb
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            {{item | lower}}_id = mongo.create_document(config.{{ (item | upper) }}_COLLECTION_NAME, data)
            logger.info(f"Created {{item | lower}} { {{item | lower}}_id} for user {token.get('user_id')}")
            return {{item | lower}}_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating {{item | lower}}: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create {{item | lower}}: {error_msg}")
    
    @staticmethod
    def get_{{item | lower}}s(token, breadcrumb, name=None, after_id=None, limit=10, sort_by='name', order='asc'):
        """
        Get infinite scroll batch of sorted, filtered {{item | lower}} documents.
        
        Args:
            token: Authentication token
            breadcrumb: Audit breadcrumb
            name: Optional name filter (simple search)
            after_id: Cursor (ID of last item from previous batch, None for first request)
            limit: Items per batch
            sort_by: Field to sort by
            order: Sort order ('asc' or 'desc')
        
        Returns:
            dict: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None  # ID of last item, or None if no more
            }
        
        Raises:
            HTTPBadRequest: If invalid parameters provided
        """
        try:
            {{item}}Service._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(config.{{ (item | upper) }}_COLLECTION_NAME)
            result = execute_infinite_scroll_query(
                collection,
                name=name,
                after_id=after_id,
                limit=limit,
                sort_by=sort_by,
                order=order,
                allowed_sort_fields=ALLOWED_SORT_FIELDS,
            )
            logger.info(
                f"Retrieved {len(result['items'])} {{item | lower}}s (has_more={result['has_more']}) "
                f"for user {token.get('user_id')}"
            )
            return result
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(f"Error retrieving {{item | lower}}s: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve {{item | lower}}s")
    
    @staticmethod
    def get_{{item | lower}}({{item | lower}}_id, token, breadcrumb):
        """
        Retrieve a specific {{item | lower}} document by ID.
        
        Args:
            {{item | lower}}_id: The {{item | lower}} ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The {{item | lower}} document
            
        Raises:
            HTTPNotFound: If {{item | lower}} is not found
        """
        try:
            {{item}}Service._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            {{item | lower}} = mongo.get_document(config.{{ (item | upper) }}_COLLECTION_NAME, {{item | lower}}_id)
            if {{item | lower}} is None:
                raise HTTPNotFound(f"{{item}} { {{item | lower}}_id} not found")
            
            logger.info(f"Retrieved {{item | lower}} { {{item | lower}}_id} for user {token.get('user_id')}")
            return {{item | lower}}
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving {{item | lower}} { {{item | lower}}_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve {{item | lower}} { {{item | lower}}_id}")
    
    @staticmethod
    def update_{{item | lower}}({{item | lower}}_id, data, token, breadcrumb):
        """
        Update a {{item | lower}} document.
        
        Args:
            {{item | lower}}_id: The {{item | lower}} ID to update
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The updated {{item | lower}} document
            
        Raises:
            HTTPNotFound: If {{item | lower}} is not found
        """
        try:
            {{item}}Service._check_permission(token, 'update')
            {{item}}Service._validate_update_data(data)
            
            # Build update data with $set operator (excluding restricted fields)
            restricted_fields = ['_id', 'created', 'saved']
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}
            
            # Automatically update the 'saved' field with current breadcrumb (system-managed)
            # Use breadcrumb directly as it already has the correct structure
            set_data['saved'] = breadcrumb
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.{{ (item | upper) }}_COLLECTION_NAME,
                document_id={{item | lower}}_id,
                set_data=set_data
            )
            
            if updated is None:
                raise HTTPNotFound(f"{{item}} { {{item | lower}}_id} not found")
            
            logger.info(f"Updated {{item | lower}} { {{item | lower}}_id} for user {token.get('user_id')}")
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating {{item | lower}} { {{item | lower}}_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update {{item | lower}} { {{item | lower}}_id}")
