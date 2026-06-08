"""
Create service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Create domain.
"""
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from api_utils.mongo_utils import execute_infinite_scroll_query
import logging

logger = logging.getLogger(__name__)

# Allowed sort fields for Create domain
ALLOWED_SORT_FIELDS = ['name', 'description', 'created.at_time']


class CreateService:
    """
    Service class for Create domain operations.
    
    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for Create domain
    """
    
    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create')
        
        Raises:
            HTTPForbidden: If user doesn't have required permission
            
        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).
        
        Example RBAC implementation:
            if operation == 'create':
                # Create requires staff or admin role
                if not any(role in token.get('roles', []) for role in ['staff', 'admin']):
                    raise HTTPForbidden("Staff or admin role required to create create documents")
            elif operation == 'read':
                # Read requires any authenticated user (no additional check needed)
                pass
        """
        pass
    
    @staticmethod
    def create_create(data, token, breadcrumb):
        """
        Create a new create document.
        
        Args:
            data: Dictionary containing create data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)
            
        Returns:
            str: The ID of the created create document
        """
        try:
            CreateService._check_permission(token, 'create')
            
            # Remove _id if present (MongoDB will generate it)
            if '_id' in data:
                del data['_id']
            
            # Automatically populate required field: created
            # This is system-managed and should not be provided by the client
            # Use breadcrumb directly as it already has the correct structure
            data['created'] = breadcrumb
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            create_id = mongo.create_document(config.CREATE_COLLECTION_NAME, data)
            logger.info(f"Created create { create_id} for user {token.get('user_id')}")
            return create_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating create: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create create: {error_msg}")
    
    @staticmethod
    def get_creates(token, breadcrumb, name=None, after_id=None, limit=10, sort_by='name', order='asc'):
        """
        Get infinite scroll batch of sorted, filtered create documents.
        
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
            CreateService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(config.CREATE_COLLECTION_NAME)
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
                f"Retrieved {len(result['items'])} creates (has_more={result['has_more']}) "
                f"for user {token.get('user_id')}"
            )
            return result
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(f"Error retrieving creates: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve creates")
    
    @staticmethod
    def get_create(create_id, token, breadcrumb):
        """
        Retrieve a specific create document by ID.
        
        Args:
            create_id: The create ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The create document
            
        Raises:
            HTTPNotFound: If create is not found
        """
        try:
            CreateService._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            create = mongo.get_document(config.CREATE_COLLECTION_NAME, create_id)
            if create is None:
                raise HTTPNotFound(f"Create { create_id} not found")
            
            logger.info(f"Retrieved create { create_id} for user {token.get('user_id')}")
            return create
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving create { create_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve create { create_id}")