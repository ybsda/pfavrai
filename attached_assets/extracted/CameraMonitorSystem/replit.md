# Overview

This is a Flask-based camera monitoring system designed to track and manage security equipment (cameras, DVRs) for multiple clients. The application provides real-time monitoring, alerting, and historical tracking of equipment status through ping-based connectivity checks.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Flask Templates**: Jinja2 templating with Bootstrap dark theme for responsive UI
- **Static Assets**: CSS customization for dark theme with Font Awesome icons
- **JavaScript**: Chart.js for data visualization and Bootstrap components for modals
- **Multi-language Support**: French interface with translation capability

## Backend Architecture
- **Flask Web Framework**: Main application server with blueprint-style route organization
- **SQLAlchemy ORM**: Database abstraction layer with model definitions
- **Background Scheduling**: APScheduler for periodic equipment health checks
- **Logging**: Structured logging throughout the application
- **WSGI**: ProxyFix middleware for deployment compatibility

## Database Schema
- **Client Model**: Stores client information (name, address, contact details)
- **Equipment Model**: Tracks individual devices (cameras, DVRs) with IP addresses and status
- **Alert Model**: Records system alerts for offline equipment (referenced but not fully implemented)
- **Ping History Model**: Logs connectivity check results (referenced but not fully implemented)

## Monitoring System
- **Ping-based Monitoring**: Periodic connectivity checks to equipment endpoints
- **Alert Generation**: Automated offline detection with configurable timeout thresholds
- **Status Tracking**: Real-time equipment online/offline status calculation
- **Historical Data**: Ping response time and connectivity history storage

## API Design
- **REST Endpoints**: JSON API for equipment ping reporting
- **Status Endpoints**: Real-time equipment status queries
- **Dashboard Data**: Aggregated statistics for management interface

## Database Configuration
- **SQLite Development**: Local file-based database for development
- **PostgreSQL Production**: Environment-variable configured for deployment
- **Connection Pooling**: Configured with health checks and recycling

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: Database ORM and connection management
- **Werkzeug**: WSGI utilities and middleware

## Scheduling and Background Tasks
- **APScheduler**: Background task scheduling for equipment monitoring
- **IntervalTrigger**: Periodic execution of health checks

## Frontend Libraries
- **Bootstrap**: UI framework with dark theme (via Replit CDN)
- **Font Awesome**: Icon library for UI elements
- **Chart.js**: JavaScript charting library for data visualization

## Development and Testing Tools
- **Requests Library**: HTTP client for testing and simulation scripts
- **Logging**: Python standard library for application logging

## Database Support
- **SQLite**: Default development database
- **PostgreSQL**: Production database support (configurable via environment variables)

## Environment Configuration
- **Environment Variables**: DATABASE_URL for database configuration, SESSION_SECRET for security
- **Development Mode**: Debug mode with auto-reload capabilities