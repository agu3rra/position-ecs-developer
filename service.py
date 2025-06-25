#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask import Flask, jsonify, request, abort
from aws_utils import *
from authentication import *

app = Flask(__name__)

SERVER_PORT = 8000

AWS_ACCESS_KEY = "AKIATKOFBMPZ5EVIUWES"
AWS_SECRET_KEY = "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"
AWS_REGION = "sa-east-1"


@app.route('/register', methods=['POST'])
@token_required
@requires_role('admin')
def register():
	"""
	Register a new user with password and roles
	Parameters (GET):
		- username: str, username for new user
		- password: str, password for new user
		- roles: list, password for new user
	Returns:
		- JSON success message if successful, http code 400 otherwise
	"""

	data = request.get_json()
	username = data.get('username')
	password = data.get('password')
	roles = data.get('roles', ['user'])

	if not username or not password:
		abort(400, description="Username and password required")

	if add_user(username, password, roles):
		return jsonify({
			'status': 'success',
			'message': 'New user registered'
		})

	else:
		abort(400, description="User already exists")


@app.route('/login', methods=['POST'])
def login():
	"""
	User login
	Parameters (GET):
		- username: str, username for new user
		- password: str, password for new user
	Returns:
		- JSON success message containing a valid token if successful, http code 401 otherwise
	"""

	data = request.get_json()
	username = data.get('username')
	password = data.get('password')
	user = get_user(username)

	if user and user['password'] == password:
		token = generate_token(user['id'], user['roles'])
		return jsonify({
			'status': 'success',
			'token': token
		})

	else:
		abort(401, description="Invalid credentials")


@app.route('/list', methods=['GET'])
@token_required
def list_files():
	"""
	List log files in cloud service storage
	Parameters (GET):
		- provider: str, cloud service provider name
	Returns:
		- JSON success message containing th list of files on the log storage if successful, fail JSON message otherwise
	"""

	cloud_provider = request.args.get('provider', default="AWS")

	# handle provider
	if cloud_provider == "AWS":
		files = list_s3_files("cristiano-sap-test", prefix='', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)

	else:
		return jsonify({
			'status': 'fail',
			'message': 'unsupported provider',
			'provider': cloud_provider,
			'files': []
		})


	return jsonify({
		'status': 'success',
		'provider': cloud_provider,
		'files': files
	})


@app.route('/get', methods=['GET'])
@token_required
def get_file():
	"""
	Get specific file from cloud service storage
	Parameters (GET):
		- provider: str, cloud service provider name
		- file: str, name of the file to download
	Returns:
		- file content as bytes if successful, fail JSON message otherwise
	"""

	cloud_provider = request.args.get('provider', default="AWS")
	file_name = request.args.get('file', default=None)

	if file_name is None:
		return jsonify({
			'status': 'fail',
			'message': 'no file name',
			'provider': cloud_provider,
			'file': None
		})

	# handle provider
	if cloud_provider == "AWS":
		file_object = get_s3_file("cristiano-sap-test", key=file_name, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)

		if file_object is not None:
			return file_object
		else:
			return jsonify({
				'status': 'fail',
				'message': 'file not found',
				'provider': cloud_provider,
				'file': file_name
			})

	else:
		return jsonify({
			'status': 'fail',
			'message': 'unsupported provider',
			'provider': cloud_provider,
			'file': file_name
		})


@app.route('/get_presigned', methods=['GET'])
@token_required
def get_file_presigned_url():
	"""
	Get a temporary access link to download a specific file from cloud service storage
	Parameters (GET):
		- provider: str, cloud service provider name
		- file: str, name of the file to download
	Returns:
		-  if a pre-signed URL to the file successful, fail JSON message otherwise
	"""

	cloud_provider = request.args.get('provider', default="AWS")
	file_name = request.args.get('file', default=None)

	if file_name is None:
		return jsonify({
			'status': 'fail',
			'message': 'no file name',
			'provider': cloud_provider,
			'file': None
		})

	# handle provider
	if cloud_provider == "AWS":
		file_url = get_presigned_url("cristiano-sap-test", key=file_name, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)

		if file_url is not None:
			return file_url

		else:
			return jsonify({
				'status': 'fail',
				'message': 'file not found',
				'provider': cloud_provider,
				'file': file_name
			})

	else:
		return jsonify({
			'status': 'fail',
			'message': 'unsupported provider',
			'provider': cloud_provider,
			'file': file_name
		})


if __name__ == '__main__':

	# Check if SQLite db exists. Create it otherwise
	if not os.path.exists(DATABASE):
		init_db()
		add_user('admin', 'adminpass', ['admin', 'user'])
		add_user('user', 'userpass', ['user'])

	app.run(debug=True, port=SERVER_PORT)
