import jwt
import datetime
from functools import wraps
import sqlite3
from flask import request, abort

SECRET_KEY = "DJkHdu3y37r3fhkdjfhhzfkFKJH!34"  # Use a secure key in production!
DATABASE = "users.db"

# --- SQLite Setup ---
def init_db():
	"""Initialize the SQLite database and create users table if not exists."""
	conn = sqlite3.connect(DATABASE)
	c = conn.cursor()
	c.execute(
		"""
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT UNIQUE NOT NULL,
			password TEXT NOT NULL, -- In production, use hashed passwords!
			roles TEXT NOT NULL -- Comma-separated roles, e.g., "admin,user"
		)
		"""
	)
	conn.commit()
	conn.close()

def get_user(username):
	conn = sqlite3.connect(DATABASE)
	c = conn.cursor()
	c.execute("SELECT id, username, password, roles FROM users WHERE username = ?", (username,))
	row = c.fetchone()
	conn.close()

	if row:
		user_id, username, password, roles = row
		return {'id': user_id, 'username': username, 'password': password, 'roles': roles.split(',')}
	return None

def add_user(username, password, roles):
	try:
		conn = sqlite3.connect(DATABASE)
		c = conn.cursor()
		c.execute("INSERT INTO users (username, password, roles) VALUES (?, ?, ?)", (username, password, ",".join(roles)),)
		conn.commit()
		conn.close()
		return True

	except sqlite3.IntegrityError:
		return False

# --- JWT Helpers ---
def generate_token(user_id, roles, expires_in=3600):
	payload = {
		'user_id': user_id,
		'roles': roles,
		'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in),
		'iat': datetime.datetime.utcnow()
	}
	token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
	return token

def decode_token(token):
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
		return payload
	except jwt.ExpiredSignatureError:
		abort(401, description="Token expired")
	except jwt.InvalidTokenError:
		abort(401, description="Invalid token")

def token_required(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		auth_header = request.headers.get('Authorization', None)
		if not auth_header or not auth_header.startswith('Bearer '):
			abort(401, description="Missing or invalid token")
		token = auth_header.split(' ')[1]
		user = decode_token(token)
		request.user = user
		return f(*args, **kwargs)
	return wrapper

def requires_role(role):
	def decorator(f):
		@wraps(f)
		def wrapper(*args, **kwargs):
			user = getattr(request, 'user', {})
			if role not in user.get('roles', []):
				abort(403, description="Forbidden: insufficient permissions")
			return f(*args, **kwargs)
		return wrapper
	return decorator



