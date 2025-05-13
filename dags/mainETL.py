from airflow import DAG
from datetime import datetime, timedelta
import pytz
from airflow.operators.python import PythonOperator
import praw
import os
import urllib.request
from airflow.decorators import task
from minio import Minio
from urllib.parse import urlsplit
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.hooks.base import BaseHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import tempfile


with DAG(
    dag_id="reddit_test",
    start_date=datetime(2023, 1, 1),
    schedule=None,  # manual run
    catchup=False,
    tags=["example"]
) as dag:

    @task()
    def fetch_reddit_posts():
        reddit = praw.Reddit(
        client_id=os.environ.get('REDDIT_CLIENT_ID'),
        client_secret=os.environ.get('REDDIT_CLIENT_SECRET'),
        user_agent=os.environ.get('REDDIT_USER')
        )
        
        utc = pytz.UTC
        now = datetime.now(utc)
        one_day_ago = now - timedelta(days=1)

        posts = []
        for subredit in ["ProgrammerHumor", "programminghumor", "programmingmemes", "DataScienceMemes"]:
            for submission in reddit.subreddit(subredit).new():
                post_time = datetime.fromtimestamp(submission.created_utc, tz=utc)
                
                if one_day_ago <= post_time:
                    if submission.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        posts.append({
                            "id": submission.id,
                            "url": submission.url,
                            "title": submission.title,
                            "score": submission.score,
                            "created_utc": submission.created_utc,
                            "author": submission.author.name if submission.author else "Unknown",
                            "num_comments": submission.num_comments,
                            "post_time_iso": post_time.isoformat()  # Convert datetime to string
                        })
        return posts
    

    @task
    def transform_posts(posts):
        transformed_posts = []
        for post in posts:
            if post["score"] > 50:
                transformed_posts.append(post)

        return transformed_posts


    @task()
    def donload_img_fromurl(posts):        

        miniio_hook = S3Hook(aws_conn_id="minio_conn_s3")

        for submission in posts:
            try:
                url = submission["url"]
                path = urlsplit(url).path
                extension = os.path.splitext(path)[1][1:]  # Extracts "jpg" from "/path/image.jpg"
                filename = f"memes/{submission['id']}.{extension}"
                with urllib.request.urlopen(submission["url"]) as response:
                    with tempfile.NamedTemporaryFile() as tmp:
                        tmp.write(response.read())
                        miniio_hook.load_file(
                            filename=tmp.name,
                            key=filename,
                            bucket_name='memes',
                            replace=True
                        )

            except Exception as e:
                print(f"Failed to download: {e}\n")
                raise

    
    @task()
    def load_memes_to_DB(posts):
        pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memes_test(
                id VARCHAR PRIMARY KEY,
                url TEXT,
                title TEXT,
                score INT
            );
            """)
        

        for post in posts:
            cursor.execute("""
            INSERT INTO memes_test (id, url, title, score)
            VALUES (%s, %s, %s, %s)
            """,(
                post["id"],
                post["url"],
                post["title"],
                post["score"],
            ))
        
        conn.commit()
        cursor.close()


    posts = fetch_reddit_posts()
    transf_posts = transform_posts(posts)
    donload_img_fromurl(transf_posts)
    load_memes_to_DB(transf_posts)



    # ...: client = tweepy.Client(
    # ...:     bearer_token="AAAAAAAAAAAAAAAAAAAAAK7Y1AEAAAAASxGU3vCcHKpqTz6vQ0hwa72aSyk%3DXK2CafDshSRKpTiiS1d1p20gVpasZ0Pr9L
    # ...: RAHxWnGbr0jWyxbR",
    # ...:     consumer_key="Rh1PxqS3G3nuEyTXp3JhzrrBH",
    # ...:     consumer_secret="uigV9aiLBcLc757mE5iyaJbTHbe3AzuCUwMenqQsDTk1FefvFQ",
    # ...:     access_token="1921856203052781569-vrMs995p51B51rgqkbbQ4zr7iPBFz3",
    # ...:     access_token_secret="6lGc09lVcu2ITJ34O80PTuR28rIFtHOqee8ysJkk5KYXk"
    # ...: )
