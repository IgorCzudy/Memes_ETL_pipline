#!/bin/bash
airflow db reset --yes

airflow db migrate

# Initialize database (idempotent)
# airflow db upgrade

# Create admin user (only if not exists)
# airflow users create \
#   --username admin \
#   --password admin \
#   --firstname Admin \
#   --lastname User \
#   --role Admin \
#   --email admin@example.com || true


airflow connections add 'minio_conn_s3' \
  --conn-type 'aws' \
  --conn-extra '{"endpoint_url": "http://minio:9000", "aws_access_key_id": "minioadmin", "aws_secret_access_key": "minioadmin"}'


airflow connections add 'postgres_default' --conn-uri 'postgresql://airflow:airflow@postgres:5432/memes_db'

airflow standalone
