# Wepgen.tf Frontend

## Overview

This project is the frontend component of a Team Fortress 2 (TF2) loadout management application. It is built using **Flask** and provides a graphical user interface (GUI) for interacting with the backend API.

The frontend communicates with a separate FastAPI backend to handle user authentication, account management, weapon database queries, and loadout operations.

**Redis** is integrated into the application to temporarily store JSON Web Tokens (JWT), allowing authentication information to persist between requests. The application and Redis are containerized using Docker and orchestrated through Docker Compose.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application programming language |
| Flask | Web application framework |
| HTML | Frontend page structure |
| CSS | Frontend styling |
| Redis | JWT caching |
| Requests | HTTP communication with the backend API |
| Docker | Application containerization |
| Docker Compose | Container orchestration |
| FastAPI | Backend API integration |

## Project Structure

```text
├── app
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src
│       ├── app.py
│       ├── helper.py
│       ├── static
│       │   ├── style.css
│       │   └── wepgen.png
│       └── templates
│           ├── edit_loadout.html
│           ├── loadouts.html
│           └── main.html
├── docker-compose.yml
└── README.md
```

### Directory Breakdown

**Application (`app/src/`)**

Contains the primary Flask application and supporting functionality.

- `app.py` – Initializes the Flask application, defines application routes, handles backend API communication, and manages authentication.
- `helper.py` – Contains shared helper functions, including email validation, password validation, and Flask secret key management.

**Static Resources (`app/src/static/`)**

Contains resources served directly by Flask.

- `style.css` – Defines the application's visual styling.
- `wepgen.png` – Application graphic/logo.

**HTML Templates (`app/src/templates/`)**

Contains the HTML templates rendered by Flask.

- `main.html` – Main application page, including registration and login interfaces.
- `loadouts.html` – Displays the authenticated user's existing loadouts.
- `edit_loadout.html` – Provides the interface for editing existing loadouts.

**Application Configuration**

- `Dockerfile` – Defines the Flask application container.
- `requirements.txt` – Contains Python dependencies.
- `docker-compose.yml` – Defines and orchestrates the Flask and Redis services.
- `.secret-key` – Stores the Flask application's secret key. Generated or loaded through the `load_secret_key()` helper function.

## Application Functionality

### 1. User Registration and Authentication

The frontend provides registration and login functionality.

**Registration:**
- Accepts a username, email address, and password.
- Validates password confirmation.
- Validates password security requirements.
- Validates email formatting.
- Sends registration information to the FastAPI backend.

**Authentication:**
- Accepts user credentials through the login interface.
- Sends credentials to the FastAPI authentication endpoint.
- Receives a JWT upon successful authentication.
- Stores the JWT in Redis for subsequent authenticated requests.

### 2. JWT Authentication and Redis

Redis provides temporary storage for authentication tokens.

The authentication workflow is as follows:

1. A user submits their login credentials through Flask.
2. Flask forwards the credentials to the FastAPI backend.
3. FastAPI validates the credentials and generates a JWT.
4. Flask receives the JWT and stores it in Redis.
5. The token is retrieved from Redis when making authenticated backend requests.
6. The JWT is automatically removed from Redis after its configured expiration time.

The current implementation configures a **20-minute expiration period** for cached authentication tokens.

If a token cannot be retrieved, the frontend informs the user that they are not currently logged in.

### 3. Loadout Generation

The frontend provides an interface for generating TF2 loadouts based on user preferences.

Users select two primary preferences:

**Game Goal**
- Win – Prioritizes weapon reliability and competitive effectiveness.
- Fun – Prioritizes experimentation and less conventional weapon choices.
- Both – Balances competitive effectiveness and enjoyment.

**Individual Goal**
- Team Player – Prioritizes utility and defensive capabilities.
- Top Frag – Prioritizes offensive capabilities and damage output.

The frontend retrieves weapon information from the FastAPI backend and evaluates available weapons using their assigned characteristics.

The weapon evaluation considers six traits:

- Damage
- Utility
- Range
- Offense
- Defense
- Reliability

Each weapon receives a compatibility score based on how closely its characteristics align with the user's selected preferences.

The highest-scoring weapon is selected for each applicable weapon slot.

The resulting loadout and associated preferences are submitted to the backend and stored in PostgreSQL.

### 4. Loadout Management

The frontend provides an interface for managing previously generated loadouts.

Available functionality includes:

- Viewing existing loadouts.
- Retrieving individual loadouts.
- Editing primary, secondary, and melee weapons.
- Editing PDA selections when applicable.
- Deleting existing loadouts.

All loadout modifications are communicated to the FastAPI backend, which handles the corresponding database operations.

### 5. Account Management

Authenticated users can delete their own accounts through the frontend.

The request is forwarded to the FastAPI backend, which handles account deletion. Upon successful deletion, the cached JWT is removed from Redis.

## Flask Routes

The following routes are defined in `app.py`.

| HTTP Method | Route | Description |
|---|---|---|
| GET, POST | `/` | Displays the main application page. |
| POST | `/register` | Registers a new user account. |
| POST | `/login` | Authenticates a user and stores their JWT in Redis. |
| POST | `/generate` | Generates a loadout based on selected preferences. |
| GET | `/loadouts` | Retrieves and displays the user's loadouts. |
| GET, POST | `/edit_loadout/<loadout_id>` | Retrieves and updates a specific loadout. |
| POST | `/delete_loadout` | Deletes a selected loadout. |
| POST | `/delete_account` | Deletes the authenticated user's account. |

## Docker Architecture

The frontend uses Docker Compose to orchestrate two primary services.

**1. Flask Application**

- Builds from the Dockerfile located in `app/`.
- Hosts the graphical user interface.
- Handles browser requests and form submissions.
- Communicates with the FastAPI backend.
- Retrieves and stores JWTs through Redis.

**2. Redis**

- Provides in-memory data storage.
- Temporarily stores JWT authentication tokens.
- Automatically expires cached tokens after 20 minutes.

The Flask and Redis containers communicate through the Docker Compose network.

The FastAPI backend operates separately and must be accessible to the Flask application over the network.

## Installation and Deployment

### Prerequisites

The following software is required:

- Docker Engine or Docker Desktop.
- Docker Compose.

Python does not need to be installed separately when running the application through Docker.

### 1. Installing Docker

If Docker is not already installed, follow the appropriate instructions for your operating system.

**Windows and macOS**

Install Docker Desktop, which includes Docker Engine, Docker CLI, and Docker Compose.

https://docs.docker.com/get-started/get-docker/

**Linux**

Docker Engine can be installed through Docker's official package repository.

Installation instructions are available for Ubuntu, Debian, Fedora, and other supported distributions.

https://docs.docker.com/engine/install/

For Linux installations, ensure that the Docker Compose plugin is installed:

https://docs.docker.com/compose/install/linux/

### 2. Verify Docker Installation

After installing Docker, open a terminal and execute:

```bash
docker --version
docker compose version
```

Both commands should return their respective installed versions.

Ensure the Docker service or Docker Desktop is running before proceeding.

### 3. Clone the Repository

Clone the frontend repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

Ensure that `docker-compose.yml` is located in the current working directory.

### 4. Configure the Flask Secret Key

The application uses a `.secret-key` file to manage Flask's secret key.

The `load_secret_key()` helper function is responsible for loading or generating the key.

Ensure that the application has permission to access the file and that the key remains consistent between application restarts.

**Important:** The `.secret-key` file should not be committed to a public repository. It should be excluded through `.gitignore`.

### 5. Build and Start the Application

From the directory containing `docker-compose.yml`, execute:

```bash
docker compose up --build -d
```

This command builds the Flask application image and starts the Flask and Redis services in the background.

### 6. Verify Container Status

Check whether the containers are running:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f
```

### 7. Access the Application

The Flask application listens on port `5000`.

If Docker Compose publishes the application port using `5000:5000`, the frontend can be accessed through:

```text
http://localhost:5000
```

If accessing the application from another device, replace `localhost` with the host machine's IP address, provided the port is reachable.

### 8. Stop the Application

To stop the containers:

```bash
docker compose down
```

This stops and removes the containers while preserving data stored in persistent volumes.

## Security Considerations

Several security mechanisms are incorporated into the frontend:

- **JWT Authentication:** Uses tokens generated by the FastAPI backend to authenticate requests.
- **Token Expiration:** Cached JWTs expire after 20 minutes.
- **Secret Key Management:** Uses a separate secret key file for Flask application security.
- **Input Validation:** Validates registration information before forwarding requests to the backend.
- **Backend Authorization:** Relies on the FastAPI backend to enforce authentication and authorization requirements.

## Development Notes

The frontend follows a relatively simple application structure:

- **Flask:** Handles HTTP requests, application routing, and backend communication.
- **HTML Templates:** Define the structure of the graphical interface.
- **CSS:** Controls the application's appearance.
- **Redis:** Provides temporary storage for authentication tokens.
- **FastAPI:** Processes backend operations and manages application data.

The frontend and backend are maintained as separate components, allowing the graphical interface and API functionality to be developed independently.
