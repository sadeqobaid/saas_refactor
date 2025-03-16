# Services Layer

The services layer contains the business logic of the application, separated from the route handlers. This separation of concerns makes the code more maintainable, testable, and readable.

## User Service

The user service (`user_service.py`) handles user-related operations:

- User registration
- Authentication and token generation
- Password reset requests
- Password reset completion

## Tenant Service

The tenant service (`tenant_service.py`) handles tenant-related operations:

- Tenant creation and updates
- Tenant configuration management
- Access control for tenant resources

## Statistics Service

The statistics service (`stats_service.py`) handles analytics and reporting:

- Monthly Active Users (MAU) statistics
- Usage statistics by activity type
- User activity history
- Tenant statistics
- Global MAU statistics across all tenants

## Usage

Services should be used by route handlers to implement business logic. For example:

```python
@router.post("/register")
def register_user(
    request: Request, 
    user_data: UserRegister, 
    tenant: Tenant = Depends(get_tenant_from_db),
    db: Session = Depends(get_db)
):
    # Use the service to handle business logic
    user_service.register_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        tenant_id=tenant.id,
        request=request
    )
    
    return {"message": "User registered successfully"}
```

This approach keeps route handlers focused on HTTP concerns while delegating business logic to the service layer.
