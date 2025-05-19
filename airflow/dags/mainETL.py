from airflow import DAG
from datetime import datetime, timedelta
import pytz
import praw
import os
import urllib.request
from airflow.decorators import task
from urllib.parse import urlsplit
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import tempfile


with DAG(
    dag_id="reddit_test",
    start_date=datetime(2025, 5, 12, 8, 0),
    schedule="@daily", 
    catchup=True,
    tags=["example"]
) as dag:

    @task()
    def fetch_reddit_posts(**kwargs):
        reddit = praw.Reddit(
        client_id=os.environ.get('REDDIT_CLIENT_ID'),
        client_secret=os.environ.get('REDDIT_CLIENT_SECRET'),
        user_agent=os.environ.get('REDDIT_USER')
        )
        utc = pytz.UTC
        context = kwargs
        execution_date = context["logical_date"]  # Start of interval (UTC)
        one_day_ago = execution_date - timedelta(days=1)

        posts = []
        for subredit in ["ProgrammerHumor", "programminghumor", "programmingmemes", "DataScienceMemes"]:
            for submission in reddit.subreddit(subredit).new():
                post_time = datetime.fromtimestamp(submission.created_utc, tz=utc)

                if one_day_ago <= post_time < execution_date :
                    if submission.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        posts.append({
                            "id": submission.id,
                            "url": submission.url,
                            "title": submission.title,
                            "score": submission.score,
                            "created_utc": post_time,
                            "author": submission.author.name if submission.author else "Unknown",
                            "num_comments": submission.num_comments,
                            "execution_time": execution_date
                        })
        return posts
    

    @task
    def transform_posts(posts):
        transformed_posts = []
        for post in posts:
            if post["score"] > 50:
                url = post["url"]
                path = urlsplit(url).path
                extension = os.path.splitext(path)[1][1:]
                s3_url = f"memes/{post['id']}.{extension}"
                post["s3_url"] = s3_url
                transformed_posts.append(post)
                

        return transformed_posts


    @task()
    def donload_img_fromurl(posts):        

        miniio_hook = S3Hook(aws_conn_id="minio_conn_s3")

        for post in posts:
            try:
                with urllib.request.urlopen(post["url"]) as response:
                    with tempfile.NamedTemporaryFile() as tmp:
                        tmp.write(response.read())
                        miniio_hook.load_file(
                            filename=tmp.name,
                            key=post["s3_url"],
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
        CREATE TABLE IF NOT EXISTS memes(
                    id SERIAL PRIMARY KEY,
                    meme_id TEXT,
                    title TEXT NOT NULL,
                    score INTEGER,
                    created_utc TIMESTAMP WITH TIME ZONE,
                    s3_url TEXT,
                    author VARCHAR(50),
                    num_comments INTEGER,
                    execution_time TIMESTAMP WITH TIME ZONE
            );
            """)

        for post in posts:

            cursor.execute("""
            INSERT INTO memes (meme_id, title, score, created_utc, s3_url, author, num_comments, execution_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,(
                post["id"],
                post["title"],
                post["score"],
                post["created_utc"],
                post["s3_url"],
                post["author"],
                post["num_comments"],
                post["execution_time"],
            ))
        
        conn.commit()
        cursor.close()


    posts = fetch_reddit_posts()
    transf_posts = transform_posts(posts)
    donload_img_fromurl(transf_posts)
    load_memes_to_DB(transf_posts)


