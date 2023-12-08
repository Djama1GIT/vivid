# Vivid

Vivid is a AI book generation project based on FastAPI.

## Installation and Setup

1. Install Docker and Docker Compose if they are not already installed on your system.

2. Clone the project repository:

```bash
git clone https://github.com/Djama1GIT/vivid.git
cd vivid
```
3. Start the project:

```bash
docker-compose up --build
```

or

```bash
make install
```
```bash
make frontend-run
```
```bash
make backend-run
```

## User Interface
Home page: http://localhost/

## Technologies Used

- Python - The programming language used for the project.
- Websocket - WebSocket is a computer communications protocol, providing simultaneous two-way communication channels over a single Transmission Control Protocol connection.
- FastAPI - The Python framework used in the project to implement the REST API.
- PostgreSQL - A relational database used in the project for data storage.
- SQLAlchemy - An Object-Relational Mapping (ORM) used in the project for working with the database.
- Alembic - A database migration library used in the project to update the database structure when data models change.
- Docker - A platform used in the project for creating, deploying, and managing containers, allowing the application to run in an isolated environment.