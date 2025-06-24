#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request, abort
from aws_utils import *

app = Flask(__name__)


# Hardcoded token for demonstration purposes
API_TOKEN = "TOKEN"

ACCESS_KEY = "AKIATKOFBMPZ5EVIUWES"
SECRET_KEY = "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"
REGION = "sa-east-1"

def token_required(f):
	def decorated_function(*args, **kwargs):
		token = request.headers.get("Authorization")
		if not token or token != f"Bearer {API_TOKEN}":
			abort(401, description="Unauthorized: Invalid or missing token")
		return f(*args, **kwargs)
	decorated_function.__name__ = f.__name__
	return decorated_function


@app.route('/list', methods=['GET'])
#@token_required
def list_files():

	# Accept query parameters
	cloud_provider = request.args.get('provider', default="AWS")

	# handle provider
	if cloud_provider == "AWS":
		files = list_s3_files("cristiano-sap-test", prefix='', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=REGION)

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
#@token_required
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
		file_object = get_s3_file("cristiano-sap-test", key=file_name, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=REGION)

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
#@token_required
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
		file_url = get_presigned_url("cristiano-sap-test", key=file_name, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=REGION)

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
	app.run(debug=True, port=8000)
