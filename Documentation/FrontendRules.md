# Frontend Development Guidelines

## Core Technologies
- Use **Vue 2 Option API** style (not Composition API)
- Use **Vite** as the build tool for all frontend projects
- Use native HTML elements (no external component libraries)

## Build Configuration
- Use the standard Vite configuration for Vue projects
- Optimize builds with proper code splitting
- Configure environment variables following Vite's `.env` file conventions
- Use ESBuild for transpilation and minification

## Development Workflow
- Use Vite's hot module replacement (HMR) during development
- Follow the component-based architecture pattern
- Implement lazy loading for routes using dynamic imports

## Testing
- Use Vitest for unit testing components
- Aim for at least 80% test coverage on business logic
- Use Vue Test Utils for component testing

## Performance Optimization
- Use code splitting for all routes
- Lazy load components when appropriate
- Implement proper caching strategies
- Use modern image formats and optimize assets