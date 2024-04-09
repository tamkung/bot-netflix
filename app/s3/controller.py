import json
import os
import boto3
import io
from botocore.exceptions import ClientError

from minio import Minio

from config import CONFIG as ENV_CONFIG

def uploadFileToS3(filename, message_id):
    session = boto3.session.Session()
    s3_client = session.client(
        service_name="s3",
        aws_access_key_id=ENV_CONFIG.S3_ACCESS_KEY,
        aws_secret_access_key=ENV_CONFIG.S3_SECRET_KEY,
        endpoint_url=ENV_CONFIG.S3_ENDPOINT,
        verify=False
    )
    # response_bucket = s3_client.list_buckets()

    # # Output the bucket names
    # print('Existing buckets:')
    # for bucket in response_bucket['Buckets']:
    #     print(str(bucket["Name"]))
    filename_output = "tmp/"+message_id+"/"+filename["name_file"]
    try:
        response_upload_file = s3_client.upload_file("tmp/"+filename["name_file"], ENV_CONFIG.S3_BUCKET_NAME, filename_output, ExtraArgs={'ContentType': filename["content_type"]})
        if os.path.exists("tmp/"+filename["name_file"]):
            os.remove("tmp/"+filename["name_file"])
        else:
            print("The file does not exist")
    except ClientError as e:
        print(str(e))
        return False
    # print(str(response_upload_file))
    return filename_output

def uploadContentImageToS3(filename, message_id):
    session = boto3.session.Session()

    s3_client = session.client(
        service_name="s3",
        aws_access_key_id=ENV_CONFIG.S3_ACCESS_KEY,
        aws_secret_access_key=ENV_CONFIG.S3_SECRET_KEY,
        endpoint_url=ENV_CONFIG.S3_ENDPOINT,
        verify=False
    )
    # response_bucket = s3_client.list_buckets()

    # # Output the bucket names
    # print('Existing buckets:')
    # for bucket in response_bucket['Buckets']:
    #     print(str(bucket["Name"]))
    filename_output = "content/"+message_id+"/"+filename["name_file"]
    try:
        response_upload_file = s3_client.upload_file("tmp/"+filename["name_file"], ENV_CONFIG.S3_BUCKET_NAME, filename_output, ExtraArgs={'ContentType': filename["content_type"]})
        if os.path.exists("tmp/"+filename["name_file"]):
            os.remove("tmp/"+filename["name_file"])
        else:
            print("The file does not exist")
    except ClientError as e :
        print(str(e))
        return False
    # print(str(response_upload_file))
    return filename_output
