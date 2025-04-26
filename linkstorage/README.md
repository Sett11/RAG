# LinkStorage API

API for storing and managing user links and collections.

## Features

- User registration and authentication
- Password reset and change
- Link management (create, read, update, delete)
- Collection management (create, read, update, delete)
- Automatic link metadata extraction

## Requirements

- Docker
- Docker Compose

## Installation

1. Clone the repository
2. Run `docker-compose up --build`
3. The API will be available at `http://localhost:8000`
4. Access Swagger documentation at `http://localhost:8000/docs`

## API Endpoints

- POST /register - User registration
- POST /login - User authentication
- GET /users/me - Get current user info
- PUT /users/me/password - Change password
- POST /password-reset - Request password reset
- POST /password-reset/confirm - Confirm password reset
- GET /links/ - Get user links
- POST /links/ - Create new link
- PUT /links/{link_id} - Update link
- DELETE /links/{link_id} - Delete link
- GET /collections/ - Get user collections
- POST /collections/ - Create new collection
- PUT /collections/{collection_id} - Update collection
- DELETE /collections/{collection_id} - Delete collection