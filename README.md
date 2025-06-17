# Interview Exercise: Cloud Log Access Service
## Background
Your team is building a backend-for-frontend (BFF) service that provides secure, controlled access to log files stored in object storage across multiple cloud providers (AWS S3, GCP GCS, Azure Blob Storage). The service must support authentication, authorization, and basic self-service features.

## Task
Build a minimal backend service that exposes RESTful endpoints to:
1. List log files in a specified bucket/container for a given cloud provider.
2. Download a specific log file from the bucket/container.
3. (Bonus) Allow a user to request a temporary access link (pre-signed URL) to download a file.

## Requirements
- The service must support at least one cloud provider (AWS, GCP, or Azure). Supporting more is a bonus.
- Implement authentication and authorization for the endpoints. You may use a simple token-based approach, OAuth2/OIDC, or any method you are comfortable with.
- The service should be containerized (e.g., Docker) and runnable locally.
- Provide clear setup instructions and sample requests in a README.
- (Bonus) Infrastructure as Code (e.g., Terraform) for provisioning a test bucket/container.
- (Bonus) Implement a basic CI workflow (e.g., GitHub Actions) to lint and test your code.

## Deliverables
- Source code in a new branch of this repository (i.e.: `exercise/your-branch`).
- A README with:
    - Setup and run instructions.
    - Example API requests and responses.
    - Brief explanation of your design decisions.
- (Bonus) Infrastructure as Code and/or CI workflow files.

## Evaluation Criteria
- Code clarity, structure, and documentation.
- Repository organization and use of version control.
- Correctness and completeness of the required features.
- Security and robustness of authentication/authorization.
- Use of best practices for cloud interaction and containerization.
- Bonus: Infrastructure as Code and CI/CD pipeline.

> [!NOTE]
> Estimated time to complete: 3–4 hours. You may use any programming language and frameworks you are comfortable with.
