from minio import Minio
import os
client = Minio(
os.getenv('MINIO_ENDPOINT'),
access_key=os.getenv('MINIO_ACCESS_KEY'),
secret_key=os.getenv('MINIO_SECRET_KEY'),
secure=os.getenv('MINIO_SECURE','false').lower()=='true')
BUCKET = os.getenv('MINIO_BUCKET','data-warehouse-videos')
if not client.bucket_exists(BUCKET):
client.make_bucket(BUCKET)