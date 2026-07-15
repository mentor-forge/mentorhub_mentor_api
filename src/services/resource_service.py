"""
Resource service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Resource domain.
"""
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from api_utils.mongo_utils import execute_infinite_scroll_query
import logging

logger = logging.getLogger(__name__)

# Allowed sort fields for Resource domain
ALLOWED_SORT_FIELDS = ['name', 'description', 'status', 'created.at_time', 'saved.at_time']


class ResourceService:
    """
    Service class for Resource domain operations.
    
    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for Resource domain
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
                    raise HTTPForbidden("Admin role required to update resource documents")
            elif operation == 'create':
                # Create requires staff or admin role
                if not any(role in token.get('roles', []) for role in ['staff', 'admin']):
                    raise HTTPForbidden("Staff or admin role required to create resource documents")
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
    def create_resource(data, token, breadcrumb):
        """
        Create a new resource document.
        
        Args:
            data: Dictionary containing resource data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)
            
        Returns:
            str: The ID of the created resource document
        """
        try:
            ResourceService._check_permission(token, 'create')
            
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
            resource_id = mongo.create_document(config.RESOURCE_COLLECTION_NAME, data)
            logger.info(f"Created resource { resource_id} for user {token.get('user_id')}")
            return resource_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating resource: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create resource: {error_msg}")
    
    @staticmethod
    def get_resources(token, breadcrumb, name=None, after_id=None, limit=10, sort_by='name', order='asc'):
        """
        Get infinite scroll batch of sorted, filtered resource documents.
        
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
            ResourceService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(config.RESOURCE_COLLECTION_NAME)
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
                f"Retrieved {len(result['items'])} resources (has_more={result['has_more']}) "
                f"for user {token.get('user_id')}"
            )
            return result
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(f"Error retrieving resources: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve resources")
    
    @staticmethod
    def get_resource(resource_id, token, breadcrumb):
        """
        Retrieve a specific resource document by ID.
        
        Args:
            resource_id: The resource ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The resource document
            
        Raises:
            HTTPNotFound: If resource is not found
        """
        try:
            ResourceService._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource = mongo.get_document(config.RESOURCE_COLLECTION_NAME, resource_id)
            if resource is None:
                raise HTTPNotFound(f"Resource { resource_id} not found")
            
            logger.info(f"Retrieved resource { resource_id} for user {token.get('user_id')}")
            return resource
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving resource { resource_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve resource { resource_id}")
    
    @staticmethod
    def update_resource(resource_id, data, token, breadcrumb):
        """
        Update a resource document.
        
        Args:
            resource_id: The resource ID to update
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The updated resource document
            
        Raises:
            HTTPNotFound: If resource is not found
        """
        try:
            ResourceService._check_permission(token, 'update')
            ResourceService._validate_update_data(data)
            
            # Build update data with $set operator (excluding restricted fields)
            restricted_fields = ['_id', 'created', 'saved']
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}
            
            # Automatically update the 'saved' field with current breadcrumb (system-managed)
            # Use breadcrumb directly as it already has the correct structure
            set_data['saved'] = breadcrumb
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.RESOURCE_COLLECTION_NAME,
                document_id=resource_id,
                set_data=set_data
            )
            
            if updated is None:
                raise HTTPNotFound(f"Resource { resource_id} not found")
            
            logger.info(f"Updated resource { resource_id} for user {token.get('user_id')}")
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating resource { resource_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update resource { resource_id}")