# Start from a minimal Go image for building
FROM golang:1.20-alpine AS builder

# Install CA certificates and sqlite3 build tools
RUN apk --no-cache add gcc musl-dev sqlite-dev

WORKDIR /app

# Copy go.mod and go.sum first, for caching dependencies
COPY src/go.mod src/go.sum ./
RUN go mod download

# Copy the rest of the application source code
COPY src/* .

# Build the Go app statically
RUN CGO_ENABLED=1 go build -o server main.go

# Final runtime image
FROM alpine:latest

# Install CA certificates and sqlite3 runtime
RUN apk --no-cache add ca-certificates sqlite-libs

WORKDIR /app

# Copy the built binary and any required files
COPY --from=builder /app/server .

# Expose the service port
EXPOSE 8000

# Set environment variables as needed, or use docker run -e
# ENV AWS_ACCESS_KEY_ID=...
# ENV AWS_SECRET_ACCESS_KEY=...
# ENV AWS_REGION=...
# ENV S3_BUCKET=...
# ENV JWT_SECRET=...

# Run the server
CMD ["./server"]
