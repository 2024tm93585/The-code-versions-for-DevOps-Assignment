# ACEest Fitness & Gym — DevOps Assignment 2

A Flask-based fitness management system with a full DevOps pipeline: CI/CD via Jenkins, code quality via SonarQube, containerisation via Docker, and multi-strategy Kubernetes deployments.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ACEest Fitness                           │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Flask   │    │  SQLite  │    │  Docker  │    │   k8s    │  │
│  │   App    │───▶│    DB    │    │ Container│───▶│ Cluster  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │                               ▲                         │
│       │          ┌────────────────────┘                         │
│       ▼          │                                              │
│  ┌──────────┐    │   ┌──────────────┐    ┌──────────────────┐  │
│  │ Pytest   │    │   │   Jenkins    │    │   SonarQube      │  │
│  │  Tests   │────┘   │  Pipeline   │───▶│  Code Quality    │  │
│  └──────────┘        └──────────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

CI/CD Flow:
  Git Push → Jenkins → Flake8 → Pytest → SonarQube → Docker Build
           → Docker Push → kubectl apply → Smoke Test
           → (on failure) kubectl rollout undo
```

---

## Project Structure

```
DevOps-Assignment2/
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── app.py               # Entry point
│   ├── models.py            # SQLite helpers & business logic
│   ├── routes.py            # Flask Blueprint routes
│   └── templates/
│       ├── base.html        # Bootstrap 5 dark theme base
│       ├── index.html       # Dashboard
│       ├── clients.html     # Client list
│       ├── add_client.html  # Add client form
│       └── programs.html    # Programs overview
├── tests/
│   ├── test_app.py          # Integration tests
│   ├── test_models.py       # Unit tests for models
│   └── test_routes.py       # Route-level tests
├── k8s/
│   ├── deployment.yaml      # Standard deployment
│   ├── service.yaml         # NodePort service
│   ├── blue-green/          # Blue-Green strategy
│   ├── canary/              # Canary strategy
│   ├── shadow/              # Shadow strategy
│   ├── ab-testing/          # A/B Testing strategy
│   └── rolling/             # Rolling update strategy
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── sonar-project.properties
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- kubectl (configured for your cluster)
- Jenkins with plugins: Pipeline, SonarQube Scanner, Docker Pipeline, HTML Publisher
- SonarQube server (or use the included docker-compose service)

---

## Local Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd DevOps-Assignment2

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app/app.py
# App available at http://localhost:5000
```

---

## Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=html --cov-report=xml

# Run a specific test file
pytest tests/test_models.py -v

# Run linting
flake8 app/ tests/ --max-line-length=120 --statistics
```

---

## Docker

### Build and run locally

```bash
# Build the image
docker build -t aceest-fitness:latest .

# Run the container
docker run -p 5000:5000 aceest-fitness:latest

# App available at http://localhost:5000
```

### Docker Compose (App + SonarQube)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f aceest-app

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

Services:
- **aceest-app**: http://localhost:5000
- **SonarQube**: http://localhost:9000 (admin/admin on first login)

---

## Kubernetes Deployment

### Standard Deployment

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl rollout status deployment/aceest-fitness
```

Access via NodePort: `http://<node-ip>:30080`

---

## Deployment Strategies

### Blue-Green Deployment

Zero-downtime deployment by switching traffic between two identical environments.

```bash
# Deploy both environments
kubectl apply -f k8s/blue-green/blue-deployment.yaml
kubectl apply -f k8s/blue-green/green-deployment.yaml
kubectl apply -f k8s/blue-green/service.yaml

# Service currently routes to BLUE
# To cut over to GREEN:
kubectl patch service aceest-fitness-service \
  -p '{"spec":{"selector":{"version":"green"}}}'

# To roll back to BLUE:
kubectl patch service aceest-fitness-service \
  -p '{"spec":{"selector":{"version":"blue"}}}'
```

### Canary Deployment

Gradually shift traffic to a new version by controlling replica counts.

```bash
kubectl apply -f k8s/canary/stable-deployment.yaml   # 9 replicas
kubectl apply -f k8s/canary/canary-deployment.yaml   # 1 replica (~10% traffic)
kubectl apply -f k8s/canary/service.yaml

# Monitor canary, then promote by scaling:
kubectl scale deployment aceest-fitness-canary --replicas=5
kubectl scale deployment aceest-fitness-stable --replicas=5

# Full promotion:
kubectl scale deployment aceest-fitness-canary --replicas=10
kubectl scale deployment aceest-fitness-stable --replicas=0
```

### Shadow Deployment

Mirror production traffic to a shadow environment without affecting users.

```bash
kubectl apply -f k8s/shadow/production-deployment.yaml
kubectl apply -f k8s/shadow/shadow-deployment.yaml
kubectl apply -f k8s/shadow/service.yaml

# Configure Istio or nginx-ingress to mirror traffic to shadow service
# (see annotations in shadow/service.yaml for examples)
```

### A/B Testing

Route different user segments to different application variants.

```bash
kubectl apply -f k8s/ab-testing/variant-a-deployment.yaml
kubectl apply -f k8s/ab-testing/variant-b-deployment.yaml
kubectl apply -f k8s/ab-testing/service.yaml

# Configure Ingress for traffic splitting (see service.yaml annotations)
# Example: 50/50 split, cookie-based, or header-based routing
```

### Rolling Update

Kubernetes default — incrementally replaces pods with zero downtime.

```bash
kubectl apply -f k8s/rolling/rolling-deployment.yaml

# Update image (triggers rolling update):
kubectl set image deployment/aceest-fitness aceest-fitness=aceest-fitness:v2

# Monitor rollout:
kubectl rollout status deployment/aceest-fitness

# Rollback if needed:
kubectl rollout undo deployment/aceest-fitness
```

---

## Deployment Strategies Comparison

| Strategy     | Downtime | Risk    | Rollback Speed | Traffic Control | Use Case                        |
|--------------|----------|---------|----------------|-----------------|----------------------------------|
| Rolling      | None     | Medium  | Slow           | None            | Standard updates                 |
| Blue-Green   | None     | Low     | Instant        | Full switch      | Critical releases                |
| Canary       | None     | Low     | Fast           | Gradual          | Feature validation               |
| Shadow       | None     | None    | N/A            | Mirror only      | Performance/behaviour testing    |
| A/B Testing  | None     | Low     | Fast           | Segment-based    | UX experiments, feature flags    |

---

## Jenkins Pipeline Setup

1. Install required Jenkins plugins:
   - Pipeline
   - Git
   - Docker Pipeline
   - SonarQube Scanner
   - HTML Publisher
   - Credentials Binding

2. Configure credentials in Jenkins:
   - `dockerhub-credentials` — Docker Hub username/password
   - `kubeconfig-credential` — kubeconfig file secret

3. Configure SonarQube server in Jenkins:
   - Manage Jenkins → Configure System → SonarQube servers
   - Name: `SonarQube`
   - URL: `http://localhost:9000` (or your SonarQube URL)

4. Set environment variables (optional, defaults provided):
   - `DOCKER_HUB_REPO` — e.g. `yourdockerhubuser/aceest-fitness`
   - `KUBECONFIG_CREDENTIAL_ID` — credential ID for kubeconfig

5. Create a Pipeline job pointing to this repository's `Jenkinsfile`.

---

## SonarQube Setup

```bash
# Start SonarQube via Docker Compose
docker-compose up -d sonarqube

# Wait for startup (~60 seconds), then open:
# http://localhost:9000
# Default credentials: admin / admin (change on first login)

# Create a project with key: aceest-fitness
# Generate a token and add it to Jenkins SonarQube configuration

# Run analysis manually (from project root):
sonar-scanner \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=<your-token>
```

---

## API Endpoints

| Method   | Endpoint            | Description                          | Response         |
|----------|---------------------|--------------------------------------|------------------|
| GET      | `/`                 | Dashboard (HTML)                     | 200 HTML         |
| GET      | `/health`           | Health check                         | 200 JSON         |
| GET      | `/clients`          | List all clients (HTML)              | 200 HTML         |
| GET      | `/clients/add`      | Add client form (HTML)               | 200 HTML         |
| POST     | `/clients/add`      | Create new client                    | 302 redirect     |
| GET      | `/clients/<name>`   | Get client by name                   | 200 JSON / 404   |
| DELETE   | `/clients/<name>`   | Delete client by name                | 200 JSON / 404   |
| GET      | `/programs`         | List all programs (HTML)             | 200 HTML         |
| GET      | `/api/clients`      | All clients as JSON                  | 200 JSON array   |
| GET      | `/api/programs`     | All programs as JSON                 | 200 JSON object  |

### Health Check Response

```json
{
  "status": "healthy",
  "service": "ACEest Fitness API"
}
```

### Client Object

```json
{
  "id": 1,
  "name": "John Smith",
  "age": 28,
  "height": 175.0,
  "weight": 80.0,
  "program": "Muscle Gain (MG) - PPL",
  "calories": 2800,
  "created_at": "2024-01-15 10:30:00"
}
```

---

## Training Programs

| Program                    | Factor | Description                          |
|----------------------------|--------|--------------------------------------|
| Fat Loss (FL) - 3 day      | × 22   | 3-day full-body fat loss             |
| Fat Loss (FL) - 5 day      | × 24   | 5-day split, higher volume fat loss  |
| Muscle Gain (MG) - PPL     | × 35   | Push/Pull/Legs hypertrophy           |
| Beginner (BG)              | × 26   | 3-day simple beginner full-body      |

**Calorie formula:** `Daily Calories = Body Weight (kg) × Program Factor`

---

## Version History

| Version | Description                                      |
|---------|--------------------------------------------------|
| 3.2.4   | DevOps pipeline, Docker, Kubernetes strategies   |
| 3.1.2   | Flask web interface, SQLite persistence          |
| 3.0.1   | Modular refactor, Blueprint architecture         |
| 2.x     | CLI-based client management                      |
| 1.x     | Initial prototype                                |

---

## License

ACEest Fitness & Gym — Academic project. All rights reserved © 2024.
