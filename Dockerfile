# FROM apache/airflow:3.0.0
# COPY requirements.txt /requirements.txt
# RUN pip install --upgrade pip
# RUN pip install --no-cache-dir -r /requirements.txt


FROM apache/airflow:3.0.0
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt


EXPOSE 8080

# RUN export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/dags \
#     export AIRFLOW__CORE__LOAD_EXAMPLES=False \
#     export AIRFLOW__CORE__PLUGINS_FOLDER=$(pwd)/plugins \
#     export REDDIT_CLIENT_ID='x8EPb0JZK4Fv4PxNBthO6Q' \
#     export REDDIT_CLIENT_SECRET='T4OpRH6JCAfSrDdp86iOytW1uAGHLA' \
#     export REDDIT_USER='my user agent'

# RUN airflow connections add postgres_default \
#         --conn-type postgres \
#         --conn-host localhost \    
#         --conn-login airflow \  
#         --conn-password airflow \
#         --conn-port 5432 \
#         --conn-schema memes_db

# RUN airflow connections add minio_conn_s3 \
#         --conn-type aws \
#         --conn-extra '{ \
#             "endpoint_url": "http://127.0.0.1:9000", \
#             "aws_access_key_id": "minioadmin", \
#             "aws_secret_access_key": "minioadmin" \
#         }'
