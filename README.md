# mc | mission-control

A cloud- and hosting-platform-agnostic tool for managing compute resources and deploying applications.

## Features

### Cloud & Application management

- Multi-cloud support: AWS, GCP, Azure, DigitalOcean, Linode, and more.
- Application deployment: Deploy applications with ease using pre-configured templates.
- Monitoring and alerts: Keep track of your applications and receive notifications for any issues.
- User management: Manage users and permissions with a robust authentication system.
- API-first design: Interact with the platform programmatically using a RESTful API.
- Extensible architecture: Easily extend the platform with plugins and custom integrations.
- Web-based UI: Intuitive and user-friendly interface for managing your applications and cloud resources.

### Orchestration

- Task queue: Background task processing using Celery.
- Workflow management: Define and manage complex workflows for application deployment and management.
- Scheduling: Schedule tasks and workflows to run at specific times or intervals.
- Retry mechanisms: Automatic retries for failed tasks to ensure reliability.
- Monitoring and logging: Track the status of tasks and workflows with detailed logs and metrics.


### DevOps features

- Infrastructure as Code: Define and manage your infrastructure using code.
- Continuous Integration/Continuous Deployment (CI/CD): Automate your build, test, and deployment processes.
- Configuration management: Manage application and system configurations across multiple environments.
- Containerization: Support for Docker and Kubernetes for containerized applications.
- Version control integration: Integrate with popular version control systems like Git.
- Security and compliance: Implement security best practices and ensure compliance with industry standards.
- Backup and recovery: Automated backup and recovery solutions for your applications and data.


### SecDevOps features

- Security scanning: Automated security scans for vulnerabilities in your applications and infrastructure.
- Compliance checks: Ensure your applications and infrastructure comply with industry standards and regulations.
- Access control: Granular access control for users and resources.
- Audit logging: Detailed logs of user actions and system events for auditing purposes.
- Incident response: Tools and workflows for managing security incidents.
- Secret management: Securely manage and store sensitive information like API keys and passwords.
- Threat detection: Monitor for potential security threats and anomalies in your applications and infrastructure.


## Development setup

### Run the server

Run the following command to start the server:

```bash
# from the project root directory
uv run uvicorn --app-dir ./src server:app

# for development with auto-reload
uv run uvicorn --app-dir ./src server:app --reload
```


### Run Orchestra

Orchestra is a lightweight task queue built on top of Celery. 

It is used to run background tasks and track their status.


#### Run celery worker

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
export DATA_DIR="/path/to/data"
celery -A celery_worker.celery worker --loglevel=INFO
```


### Local development stack with Docker

```bash
docker-compose -f docker-compose.dev.yml up -d
```