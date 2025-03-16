"""
API Documentation module for the SaaS Platform.

This module enhances the OpenAPI documentation with additional information.
"""

def enhance_openapi_docs(app):
    """
    Enhance OpenAPI documentation with additional information.
    
    This function adds security schemes, global security requirements,
    and tenant header parameters to all operations in the OpenAPI schema.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        dict: Enhanced OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = app.openapi()
    
    # Add security schemes
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    openapi_schema["components"]["securitySchemes"]["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter JWT token with 'Bearer ' prefix"
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    # Add tenant header parameter to all operations
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "parameters" not in operation:
                operation["parameters"] = []
            
            # Add tenant header parameter
            tenant_header_exists = any(
                param.get("name") == "X-Tenant-ID" and param.get("in") == "header" 
                for param in operation["parameters"]
            )
            
            if not tenant_header_exists:
                operation["parameters"].append({
                    "name": "X-Tenant-ID",
                    "in": "header",
                    "description": "Tenant identifier (slug)",
                    "required": False,
                    "schema": {
                        "type": "string"
                    }
                })
            
            # Add tenant query parameter
            tenant_query_exists = any(
                param.get("name") == "tenant" and param.get("in") == "query" 
                for param in operation["parameters"]
            )
            
            if not tenant_query_exists:
                operation["parameters"].append({
                    "name": "tenant",
                    "in": "query",
                    "description": "Tenant identifier (slug)",
                    "required": False,
                    "schema": {
                        "type": "string"
                    }
                })
    
    # Add additional information to the schema
    if "info" in openapi_schema:
        if "description" not in openapi_schema["info"]:
            openapi_schema["info"]["description"] = ""
        
        openapi_schema["info"]["description"] += """
## Multi-tenant SaaS Platform API

This API provides authentication, tenant management, and usage statistics for a multi-tenant SaaS platform.

### Authentication

All protected endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

Tokens can be obtained using the `/token` endpoint with valid credentials.

### Multi-tenancy

All requests must include a tenant identifier, either:
- As an `X-Tenant-ID` header
- As a `tenant` query parameter

Example:
```
GET /users?tenant=example-tenant
```

Or:
```
GET /users
X-Tenant-ID: example-tenant
```
"""
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
