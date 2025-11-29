# AegisSecure Backend - Object Design Document

## 1. Introduction
This document outlines the object-oriented design and architecture of the AegisSecure Backend. The system is built using FastAPI and follows a layered architecture to ensure separation of concerns, maintainability, and scalability. The design encompasses configuration management, error handling, database interactions, security validation, middleware processing, and route handling.

## 2. Architecture Overview
The backend is structured into distinct layers:
- **Configuration Layer**: Manages application settings and environment variables.
- **Error Handling Layer**: Defines a hierarchy of custom exceptions for consistent error reporting.
- **Database Layer**: Handles MongoDB connections and CRUD operations using the Motor async driver.
- **Validation & Security Layer**: Provides utilities for input validation, sanitization, and security checks.
- **Middleware Layer**: Intercepts requests for rate limiting, logging, and security header injection.
- **Data Models**: Defines Pydantic models for request/response schemas.
- **Route Handlers**: Groups API endpoints by functionality (Auth, Gmail, SMS, etc.).
- **Application Core**: The central FastAPI application instance that orchestrates all components.

## 3. Class Design

### 3.1 Configuration Layer
Responsible for loading and validating environment variables and constants.

#### `Settings`
Central configuration class.
- **Attributes**:
  - `APP_NAME`, `APP_VERSION`, `DEBUG`: General app info.
  - `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_HOURS`: JWT security settings.
  - `MONGO_URI`, `DB_NAME`: Database connection strings.
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: OAuth credentials.
  - `OTP_EXPIRE_MINUTES`, `OTP_LENGTH`: OTP security parameters.
  - `RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE`: Rate limiting controls.
- **Methods**:
  - `validate()`: Checks for missing required environment variables.
  - `print_config_summary()`: Logs the current configuration state on startup.

#### `StatusMessages`
Constants for standardized API response messages.
- **Attributes**: `SUCCESS_LOGIN`, `ERROR_INVALID_CREDENTIALS`, `ERROR_USER_NOT_FOUND`, etc.

#### `ValidationPatterns`
Regex patterns for input validation.
- **Attributes**: `EMAIL_PATTERN`, `PHONE_PATTERN`, `URL_PATTERN`.

### 3.2 Error Handling Layer
A robust exception hierarchy ensures that all errors are caught and transformed into appropriate HTTP responses.

#### `AegisException` (Abstract Base Class)
Base class for all application-specific exceptions.
- **Attributes**: `message`, `status_code`, `details`.
- **Methods**: `to_dict()` returns a dictionary representation for JSON responses.

#### Concrete Exceptions
- **`AuthenticationError`**: 401 Unauthorized (Login failures).
- **`AuthorizationError`**: 403 Forbidden (Permission issues).
- **`ValidationError`**: 400 Bad Request (Invalid input).
- **`ResourceNotFoundError`**: 404 Not Found.
- **`DuplicateResourceError`**: 409 Conflict (e.g., email already registered).
- **`DatabaseError`**: 500 Internal Server Error (DB connection/query failures).
- **`ExternalAPIError`**: 502 Bad Gateway (Failures in ML model or Google API calls).
- **`RateLimitError`**: 429 Too Many Requests.

### 3.3 Database Layer
Manages asynchronous interactions with MongoDB.

#### `DatabaseManager`
Singleton class for managing the database connection lifecycle.
- **Attributes**: `client` (AsyncIOMotorClient), `connected` (bool).
- **Methods**:
  - `connect()`: Establishes connection to MongoDB.
  - `disconnect()`: Closes the connection.
  - `ping()`: Verifies connection health.

#### `DatabaseHelper`
Static utility class for common CRUD operations.
- **Methods**:
  - `find_one()`, `find_many()`: Retrieval with projection and sorting.
  - `insert_one()`: Document creation with timestamp injection.
  - `update_one()`: Atomic updates.
  - `delete_one()`, `delete_many()`: Removal operations.
  - `count_documents()`: Aggregation helper.

#### Decorators
- **`@with_retry`**: Automatically retries database operations on transient failures.
- **`@log_operation`**: Logs the execution time and result of database queries.

### 3.4 Validation & Security Layer
Ensures data integrity and security before processing.

#### `PasswordValidator`
- **Methods**:
  - `validate(password)`: Checks length, complexity (uppercase, lowercase, digits, special chars).
  - `validate_or_raise(password)`: Raises `ValidationError` if invalid.

#### `EmailValidator`
- **Methods**:
  - `validate(email)`: Checks format using regex.

#### `URLValidator`
- **Methods**:
  - `is_safe_url(url)`: Checks against known malicious patterns or blocklists.

#### `OTPValidator`
- **Methods**:
  - `validate(otp)`: Verifies OTP format and expiration.

#### `TextSanitizer`
- **Methods**:
  - `sanitize(text)`: Removes potential XSS scripts and dangerous characters.
  - `sanitize_html()`, `sanitize_sql()`: Specific sanitization for different contexts.

### 3.5 Middleware Layer
Interceptors that process requests globally.

#### `RateLimiter`
In-memory rate limiting logic (can be extended to Redis).
- **Methods**:
  - `is_rate_limited(identifier, max_requests, window)`: Checks if a user/IP has exceeded limits.
  - `_cleanup_old_requests()`: Garbage collection for request history.

#### Middleware Classes
- **`RateLimitMiddleware`**: Uses `RateLimiter` to block abusive traffic.
- **`SecurityHeadersMiddleware`**: Adds headers like `X-Content-Type-Options`, `X-Frame-Options`.
- **`RequestValidationMiddleware`**: Pre-validates request bodies.
- **`RequestLoggingMiddleware`**: Logs incoming requests and outgoing responses for audit trails.
- **`ErrorHandlerMiddleware`**: Global catch-all for unhandled exceptions.

### 3.6 Data Models
Pydantic models defining the schema for API payloads.

#### Auth Models
- **`RegisterRequest`**: `name`, `email`, `password`.
- **`LoginRequest`**: `email`, `password`.
- **`LoginResponse`**: `token`, `verified`.
- **`UserResponse`**: `name`, `email`, `user_id`.
- **`SendOTPRequest`**, **`VerifyOTPRequest`**.

#### Message Models
- **`SmsMessage`**: `address`, `body`, `date_ms`, `type`.
- **`SmsSyncRequest`**: List of `SmsMessage`.
- **`SpamRequest`**: `sender`, `subject`, `text` (for ML analysis).

### 3.7 Route Handlers
Controllers that map HTTP endpoints to business logic.

#### `AuthRouter`
Handles user authentication and profile management.
- **Endpoints**: `/register`, `/login`, `/verify-otp`, `/reset-password`, `/me`.
- **Dependencies**: `PasswordValidator`, `DatabaseHelper`.

#### `GmailRouter`
Manages Gmail integration via OAuth.
- **Endpoints**: `/get-emails`, `/connected-accounts`, `/delete-email`.
- **Responsibilities**: Fetches emails, manages OAuth tokens.

#### `SmsRouter`
Handles SMS synchronization and analysis.
- **Endpoints**: `/sync-sms`, `/get-all-sms`.
- **Responsibilities**: Syncs local SMS data, triggers spam detection.

#### `OAuthRouter`
Handles Google OAuth flow.
- **Endpoints**: `/google/authorize`, `/google/callback`.
- **Responsibilities**: Exchanges auth codes for access/refresh tokens.

#### `NotificationRouter`
Integrates with the ML model for spam detection.
- **Endpoints**: `/check-spam`, `/analyze-batch`.
- **Responsibilities**: Calls external ML API to classify content.

#### `DashboardRouter`
Provides aggregated statistics for the frontend.
- **Endpoints**: `/stats`, `/ai-fact`.

### 3.8 Application Core

#### `FastAPIApp`
The main application class.
- **Methods**:
  - `lifespan()`: Manages startup (DB connect) and shutdown (DB disconnect) events.
  - `root()`: Health check endpoint.
- **Integrations**: Includes all Routers and adds all Middleware.

## 4. Key Relationships
- **FastAPIApp** aggregates **Settings**, **DatabaseManager**, and all **Routers**.
- **Routers** depend on **DatabaseHelper** for data access and **Validators** for input checking.
- **RateLimitMiddleware** uses **RateLimiter** to enforce policies defined in **Settings**.
- **NotificationRouter** depends on external ML services, encapsulating failures in **ExternalAPIError**.
- **AuthRouter** uses **PasswordValidator** and **EmailValidator** to ensure credential security.
