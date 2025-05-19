FROM apache/airflow:3.0.0
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt


EXPOSE 8080

