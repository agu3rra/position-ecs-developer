FROM python:3.12
WORKDIR /usr/local/backend

# Copy source
COPY src/* .

# Install the application dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Setup an app user so the container doesn't run as the root user
RUN useradd app
USER app

CMD ["python", "service.py"]
