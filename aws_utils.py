import boto3
from botocore.exceptions import ClientError


def get_s3_file(bucket_name, key, aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
	"""
	Download a file from AWS S3 and return its content as bytes.
	Parameters:
		- bucket_name: str, S3 bucket name
		- key: str, S3 object key (path to the file within the bucket)
		- aws_access_key_id: str, AWS Access Key ID (optional, uses default credentials if not provided)
		- aws_secret_access_key: str, AWS Secret Access Key (optional, uses default credentials if not provided)
		- region_name: str, AWS region (optional)
	Returns:
		- file content as bytes if successful, None otherwise
	Raises:
		- Exception on error
	"""
	try:
		session = boto3.Session(
			aws_access_key_id=aws_access_key_id,
			aws_secret_access_key=aws_secret_access_key,
			region_name=region_name
		)
		s3 = session.client('s3')
		response = s3.get_object(Bucket=bucket_name, Key=key)
		return response['Body'].read()

	except ClientError as e:
		print(f"Error downloading {key} from bucket {bucket_name}: {e}")
		return None


def list_s3_files(bucket_name, prefix='', aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
	"""
	List all files in an AWS S3 bucket (optionally within a prefix).
	Parameters:
		- bucket_name: str, S3 bucket name
		- prefix: str, optional, prefix (directory) to filter files
		- aws_access_key_id: str, AWS Access Key ID (optional, uses default credentials if not provided)
		- aws_secret_access_key: str, AWS Secret Access Key (optional, uses default credentials if not provided)
		- region_name: str, AWS region (optional)
	Returns:
		- List of file keys (str) if successful, empty list otherwise
	"""
	try:
		session = boto3.Session(
			aws_access_key_id=aws_access_key_id,
			aws_secret_access_key=aws_secret_access_key,
			region_name=region_name
		)
		s3 = session.client('s3')
		paginator = s3.get_paginator('list_objects_v2')
		page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

		files = []
		for page in page_iterator:
			contents = page.get('Contents')
			if contents:
				for obj in contents:
					files.append(obj['Key'])
		return files

	except ClientError as e:
		print(f"Error listing files in bucket {bucket_name}: {e}")
		return []


def get_presigned_url(bucket_name, key, expiration=3600, aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
	"""
	Generate a presigned URL to share an S3 object

	Parameters:
		- bucket_name: str, S3 bucket name
		- key: str, S3 object key (path to the file within the bucket)
		- expiration: int, Time in seconds for the presigned URL to remain valid (default: 3600)
		- aws_access_key_id: str, AWS Access Key ID (optional, uses default credentials if not provided)
		- aws_secret_access_key: str, AWS Secret Access Key (optional, uses default credentials if not provided)
		- region_name: str, AWS region (optional)
	Returns:
		- The presigned URL as a string if successful, None otherwise
	"""
	try:
		session = boto3.Session(
			aws_access_key_id=aws_access_key_id,
			aws_secret_access_key=aws_secret_access_key,
			region_name=region_name
		)

		s3_client = session.client('s3')
		url = s3_client.generate_presigned_url(
			'get_object',
			Params={'Bucket': bucket_name, 'Key': key},
			ExpiresIn=expiration
		)
		return url

	except ClientError as e:
		print(f"Error generating presigned URL for {key} in bucket {bucket_name}: {e}")
		return None
