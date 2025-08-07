# Camera Monitoring System

## Overview

This is a Flask-based camera monitoring system that provides real-time surveillance camera management and monitoring capabilities. The application allows users to manage multiple security cameras, monitor their status, view live feeds, and receive alerts when cameras go offline or encounter errors. It features a modern web interface with user authentication through Replit Auth and supports RTSP camera streams.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with a component-based approach using template inheritance
- **UI Framework**: Bootstrap 5 with custom CSS for responsive dark-themed interface
- **JavaScript**: Vanilla JavaScript for real-time updates, sidebar navigation, and interactive features
- **Layout Pattern**: Fixed sidebar navigation with main content area for authenticated users, landing page for anonymous users

### Backend Architecture
- **Web Framework**: Flask with modular route organization
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy integration using DeclarativeBase pattern
- **Authentication**: Flask-Login with Replit OAuth integration for user session management
- **Application Structure**: 
  - `app.py`: Core Flask application setup and database configuration
  - `routes.py`: Request handling and business logic
  - `models.py`: Database schema definitions
  - `replit_auth.py`: Authentication and authorization logic

### Data Storage Solutions
- **Primary Database**: Configurable via DATABASE_URL environment variable (designed for PostgreSQL)
- **Connection Management**: SQLAlchemy with connection pooling, pool recycling (300s), and pre-ping health checks
- **Schema Design**: 
  - User management with OAuth token storage
  - Camera entities with connection details and status tracking
  - Alert system for monitoring events
  - System health metrics storage

### Authentication and Authorization
- **Authentication Provider**: Replit OAuth2 integration
- **Session Management**: Flask-Login with permanent sessions
- **Access Control**: Decorator-based route protection (`@require_login`)
- **Security Features**: JWT token handling, session key management, and CSRF protection via secret keys

### Camera Management System
- **Camera Types**: IP cameras with RTSP stream support
- **Status Monitoring**: Real-time status tracking (online/offline/error states)
- **Connection Details**: IP address, port, credentials, and custom stream URL storage
- **User Isolation**: Each user manages their own camera collection

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework with SQLAlchemy ORM integration
- **Flask-Login**: User session management and authentication state
- **Flask-Dance**: OAuth2 consumer implementation for Replit authentication
- **Werkzeug**: WSGI utilities including ProxyFix for HTTPS URL generation

### Frontend Dependencies
- **Bootstrap 5**: CSS framework for responsive UI components
- **Font Awesome 6**: Icon library for consistent iconography throughout the interface
- **Custom CSS**: Dark theme implementation with camera monitoring specific styling

### Database and Security
- **SQLAlchemy**: Database abstraction layer with declarative model definitions
- **PyJWT**: JSON Web Token handling for OAuth authentication flows
- **Environment Variables**: Configuration management for database URLs and session secrets

### Development and Deployment
- **Logging**: Python logging module for application debugging and monitoring
- **Environment Configuration**: Database URL and session secret management through environment variables
- **WSGI Configuration**: ProxyFix middleware for proper HTTPS handling in production environments