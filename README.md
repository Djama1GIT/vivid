# Vivid

Vivid is a AI book generation project based on FastAPI.

## Installation and Setup <sup><sub>(tested on Linux)</sub></sup>

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

or<sup>* (it is assumed that you also have npm and Python installed)</sup>

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
Home page:

http://localhost:3000/ (Make)

or http://localhost/ (Docker)

## Technologies Used

- Python - The programming language used for the project.
- Websocket - WebSocket is a computer communications protocol, providing simultaneous two-way communication channels over a single Transmission Control Protocol connection.
- FastAPI - The Python framework used in the project to implement the REST API.
- PostgreSQL - A relational database used in the project for data storage.
- SQLAlchemy - An Object-Relational Mapping (ORM) used in the project for working with the database.
- Alembic - A database migration library used in the project to update the database structure when data models change.
- Docker - A platform used in the project for creating, deploying, and managing containers, allowing the application to run in an isolated environment.


## Contributors

<table>
  <tbody>
    <tr>
       <td align="center" valign="top" width="14.28%">
        <a href="https://github.com/Djama1GIT">
          <img src="https://avatars.githubusercontent.com/u/89941580?v=4?s=100" width="130px;" alt="Djama1GIT"/><br />
          <sub><b>Djama1GIT</b></sub>
        </a>
      </td>
      <td align="center" valign="top" width="14.28%">
        <a href="https://github.com/valuevichslava">
          <img src="https://avatars.githubusercontent.com/u/90149943?v=4?s=100" width="100px;" alt="valuevichslava"/><br />
          <sub><b>valuevichslava</b></sub>
        </a>
      </td>
      <td align="center" valign="top" width="14.28%">
        <a href="https://github.com/Baroisyidi">
          <img src="https://avatars.githubusercontent.com/u/96845788?v=4?s=100" width="100px;" alt="Baroisyidi"/><br />
          <sub><b>Baroisyidi</b></sub>
        </a>
      </td>
    </tr>
  </tbody>
</table>
