# Backend Development Rules

## API Route Rules
- All newly created routes should not interact with databases directly, only use `guide_backend_implementation`.
- Return the response from the target server as-is (status code + JSON).

## Best Practices
- Always include proper error handling for all API calls
- Implement logging for all API requests and responses
- Document all endpoints using appropriate comments
- Follow RESTful API design principles
- Use consistent naming conventions for API endpoints