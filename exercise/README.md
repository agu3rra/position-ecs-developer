# Interview Exercise: Cloud Log Access Service
## Setup and run instructions
- To run the server in localhost is necessary to have Python (the server was developed using version 3.9.22) and requirements installed.
- The easiest way To install requirements is using pip (e.g.: **pip install -r requirements.txt**)
- To run the server locally run: **python service.py**
- The Docker image can be built from the Dockerfile directory runing: **docker build -t backend .**
- To run the Docker image run: **docker container run -it -p 8000:8000 backend**
- By default server.py is using port 8000 which can be changed in the file (or redirected if running as a Docker container).
- For the sake of testing the system uses SQLite and starts with two users with different roles one admin and a non privileged user. The only endpoint forbidden for the non previlleged user is /register (create a new user).

## Example of API requests and responses
### 1. Login

Request:
```
    curl -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"adminpass"}' http://localhost:8000/login
```
Return:
```json
    {
        "status": "success",
        "token": "<your.jwt.token>"
    }
```

### 2. Get log files list

Request:
```
    curl -H "Authorization: Bearer <your.jwt.token>" http://localhost:8000/list

```
Return:
```json
{
  "files": [
    "log_file1",
    "log_file2",
    "log_file3"
  ],
  "provider": "AWS",
  "status": "success"
}
```

### 2. Get log file

Request:
```
    curl -H "Authorization: Bearer <your.jwt.token>" http://localhost:8000/get?provider='AWS'&file='log_file2 -o log_file2
```
Return:
```json
    Downloads log_file2 file
```

### 3. Get presigned url for log file

Request:
```
    curl -H "Authorization: Bearer <your.jwt.token>" http://localhost:8000/get_presigned?provider='AWS'&file='log_file2
```
Return:
```json
    https://cristiano-sap-test.s3.amazonaws.com/log_file2?AWSAccessKeyId=AABBCCDDEE&Signature=BweVpdd4OJ%2F4Pi7Oo%3D&Expires=1750824649
```

## Design decisions
The design prioritizes clarity, modularity, and extensibility, using widely adopted patterns and technologies that make it easy to maintain, scale, and upgrade for future needs.

1. Flask Web Framework
    - Is lightweight, easy to understand, and quick to set up for REST APIs.

2. SQLite Database
    - Easy to set up and migrate to more robust databases if needed.

3. JWT for Authentication
    - No need for server-side session storage, improving scalability and making the system stateless.
    - Is possible to store roles as claims in the JWT which enables easy and efficient access control.
    - Flexible and extendable for supporting more roles or permissions in the future.

5. Decorators for Route Protection
    - Decorators like @token_required and @requires_role keep route logic clean and reusable.
    - Centralizes authentication and authorization logic, reducing code duplication and potential errors.
