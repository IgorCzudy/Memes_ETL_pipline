from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator



def say_hello():
    print("Hello, World!")

with DAG(
    dag_id="hello_world",
    start_date=datetime(2023, 1, 1),
    schedule=None,  # manual run
    catchup=False,
    tags=["example"]
) as dag:
    hello_task = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello
    )

