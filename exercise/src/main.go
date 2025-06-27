package main

import (
	"database/sql"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	_ "github.com/mattn/go-sqlite3"
)

// The keys should be set as env vars for security reasons. Setting hardcoded for the sake of testing.
var (
	AWS_ACCESS_KEY = "AKIATKOFBMPZ5EVIUWES"
	AWS_SECRET_KEY = "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"
	AWS_REGION = "sa-east-1"
	S3_BUCKET = "cristiano-sap-test"
	JWT_SECRET = []byte("very-secret-key")
	DB_PATH = "users.db"
)

type User struct {
	ID       int    `json:"id"`
	Username string `json:"username"`
	Password string `json:"password"`
	Roles    []string `json:"roles"`
}

type Claims struct {
	UserID   int    `json:"user_id"`
	Username string `json:"username"`
	Roles    []string `json:"roles"`
	jwt.RegisteredClaims
}

// ----------- SQLite User Auth ------------
func initDB() (created bool, err error) {
	created = false
	if _, err := os.Stat(DB_PATH); os.IsNotExist(err) {
		created = true
	}
	db, err := sql.Open("sqlite3", DB_PATH)
	if err != nil {
		return created, err
	}
	defer db.Close()
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT UNIQUE NOT NULL,
			password TEXT NOT NULL,
			roles TEXT NOT NULL
		);
	`)
	return created, err
}


func getUserByUsername(username string) (*User, error) {
	db, err := sql.Open("sqlite3", DB_PATH)
	if err != nil {
		return nil, err
	}
	defer db.Close()
	row := db.QueryRow("SELECT id, username, password, roles FROM users WHERE username = ?", username)
	var user User
	var roles string
	if err := row.Scan(&user.ID, &user.Username, &user.Password, &roles); err != nil {
		return nil, err
	}
	user.Roles = strings.Split(roles, ",")
	return &user, nil
}

func addUser(username, password string, roles []string) error {
	db, err := sql.Open("sqlite3", DB_PATH)
	if err != nil {
		return err
	}
	defer db.Close()
	rolesStr := strings.Join(roles, ",")
	_, err = db.Exec("INSERT INTO users (username, password, roles) VALUES (?, ?, ?)", username, password, rolesStr)
	return err
}

func userExists(username string) bool {
	db, err := sql.Open("sqlite3", DB_PATH)
	if err != nil {
		return false
	}
	defer db.Close()
	row := db.QueryRow("SELECT id FROM users WHERE username = ?", username)
	var id int
	return row.Scan(&id) == nil
}

// ------------- JWT helpers ------------
func generateToken(user *User) (string, error) {
	claims := &Claims{
		UserID:   user.ID,
		Username: user.Username,
		Roles:    user.Roles,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(JWT_SECRET)
}

func validateToken(tokenStr string) (*Claims, error) {
	claims := &Claims{}
	token, err := jwt.ParseWithClaims(tokenStr, claims, func(token *jwt.Token) (interface{}, error) {
		return JWT_SECRET, nil
	})
	if err != nil || !token.Valid {
		return nil, err
	}
	return claims, nil
}

func AuthRequired() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if !strings.HasPrefix(authHeader, "Bearer ") {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Missing or invalid token"})
			c.Abort()
			return
		}
		tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
		claims, err := validateToken(tokenStr)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid or expired token"})
			c.Abort()
			return
		}
		c.Set("user_id", claims.UserID)
		c.Set("username", claims.Username)
		c.Set("roles", claims.Roles)
		c.Next()
	}
}

// RoleBasedAuth returns a middleware that allows access only to users with specified roles
func RoleBasedAuth(allowedRoles ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		val, exists := c.Get("roles")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			c.Abort()
			return
		}
		userRoles, ok := val.([]string)
		if !ok {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			c.Abort()
			return
		}
		for _, urole := range userRoles {
			for _, arole := range allowedRoles {
				if urole == arole {
					c.Next()
					return
				}
			}
		}
		c.JSON(http.StatusForbidden, gin.H{"error": "Permission denied"})
		c.Abort()
	}
}

// ------------- AWS S3 Logic ------------
func getS3Client() *s3.S3 {
	sess := session.Must(session.NewSession(&aws.Config{
		Region:      aws.String(AWS_REGION),
		Credentials: credentials.NewStaticCredentials(AWS_ACCESS_KEY, AWS_SECRET_KEY, ""),
	}))
	return s3.New(sess)
}

func listFilesHandler(c *gin.Context) {
	client := getS3Client()

	var files []string

	err := client.ListObjectsV2Pages(&s3.ListObjectsV2Input{
		Bucket: aws.String(S3_BUCKET),
	}, func(page *s3.ListObjectsV2Output, last bool) bool {
		for _, obj := range page.Contents {
			files = append(files, *obj.Key)
		}
		return true
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "fail", "message": "Failed to list files"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success", "files": files})
}

func getFileHandler(c *gin.Context) {
	fileName := c.Query("file")
	if fileName == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "fail", "message": "Missing file parameter"})
		return
	}
	client := getS3Client()
	obj, err := client.GetObject(&s3.GetObjectInput{
		Bucket: aws.String(S3_BUCKET),
		Key:    aws.String(fileName),
	})
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"status": "fail", "message": "File not found"})
		return
	}
	defer obj.Body.Close()
	c.Header("Content-Disposition", "attachment; filename="+fileName)
	c.DataFromReader(http.StatusOK, *obj.ContentLength, *obj.ContentType, obj.Body, nil)
}

func getPresignedURLHandler(c *gin.Context) {
	fileName := c.Query("file")

	if fileName == "" {
		c.JSON(http.StatusBadRequest, gin.H{"status": "fail", "message": "Missing file parameter"})
		return
	}

	client := getS3Client()
	req, _ := client.GetObjectRequest(&s3.GetObjectInput{
		Bucket: aws.String(S3_BUCKET),
		Key:    aws.String(fileName),
	})

	urlStr, err := req.Presign(3600)
	log.Println(urlStr)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"status": "fail", "message": "Failed to generate presigned URL"})
		return
	}
	c.String(http.StatusOK, urlStr)
}

// ------------- Auth Endpoints ------------
func registerHandler(c *gin.Context) {
	var req struct {
		Username string   `json:"username"`
		Password string   `json:"password"`
		Roles    []string `json:"roles"`
	}
	if err := c.ShouldBindJSON(&req); err != nil || req.Username == "" || req.Password == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Username and password required"})
		return
	}
	if len(req.Roles) == 0 {
		req.Roles = []string{"user"}
	}
	if err := addUser(req.Username, req.Password, req.Roles); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "User already exists"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "success"})
}

func loginHandler(c *gin.Context) {
	var req struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Username and password required"})
		return
	}
	user, err := getUserByUsername(req.Username)
	if err != nil || user.Password != req.Password {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}
	token, _ := generateToken(user)
	c.JSON(http.StatusOK, gin.H{"status": "success", "token": token})
}

func ensureDefaultUsers() {
	if !userExists("admin") {
		_ = addUser("admin", "adminpass", []string{"admin", "user"})
	}
	if !userExists("user") {
		_ = addUser("user", "userpass", []string{"user"})
	}
}

// ------------- Main ------------
func main() {
	// Read AWS credentials from environment variables
	if v := os.Getenv("AWS_ACCESS_KEY_ID"); v != "" {
		AWS_ACCESS_KEY = v
	}
	if v := os.Getenv("AWS_SECRET_ACCESS_KEY"); v != "" {
		AWS_SECRET_KEY = v
	}
	if v := os.Getenv("AWS_REGION"); v != "" {
		AWS_REGION = v
	}
	if v := os.Getenv("S3_BUCKET"); v != "" {
		S3_BUCKET = v
	}

	dbCreated, err := initDB()
	if err != nil {
		log.Fatal("Failed to init DB:", err)
	}
	if dbCreated {
		ensureDefaultUsers()
	}

	r := gin.Default()

	// Set routes
	r.POST("/register", AuthRequired(), RoleBasedAuth("admin", "user"), registerHandler)
	r.POST("/login", loginHandler)

	// Only users with "admin" role can list files
	r.GET("/list", AuthRequired(), listFilesHandler)
	r.GET("/get", AuthRequired(), getFileHandler)
	r.GET("/get_presigned", AuthRequired(), getPresignedURLHandler)

	log.Println("Server running at http://0.0.0.0:8080/")
	if err := r.Run("0.0.0.0:8000"); err != nil {
		log.Fatal(err)
	}
}
