#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask import Flask, jsonify, request, abort
from aws_utils import *
from authentication import *

app = Flask(__name__)

AWS_ACCESS_KEY = "AKIATKOFBMPZ5EVIUWES"
AWS_SECRET_KEY = "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"
AWS_REGION = "sa-east-1"


@app.route('/register', methods=['POST'])
@token_required
@requires_role('admin')
def register():
	data = request.get_json()
	username = data.get('username')
	password = data.get('password')
	roles = data.get('roles', ['user'])

	if not username or not password:
		abort(400, description="Username and password required")

	if add_user(username, password, roles):
		return jsonify({"message": "User registered!"})
	else:
		abort(400, description="User already exists")


@app.route('/login', methods=['POST'])
def login():
	data = request.get_json()
	username = data.get('username')
	password = data.get('password')
	user = get_user(username)

	if user and user['password'] == password:
		token = generate_token(user['id'], user['roles'])
		return jsonify({'token': token})

	else:
		abort(401, description="Invalid credentials")


@app.route('/list', methods=['GET'])
@token_required
def list_files():

	# Accept query parameters
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
	# Accept query parameters
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

	app.run(debug=True, port=8000)
