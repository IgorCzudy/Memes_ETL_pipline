import streamlit as st
from minio import Minio
import tempfile
import plotly.express as px


conn = st.connection("postgresql", type="sql")

query="""
select execution_time 
from memes 
ORDER BY execution_time DESC 
LIMIT 1;
"""
etl_process_time = conn.query(query, ttl="10m")
st.title("Memes dashboard")
st.write("Last updating time of ELT process:") 
st.write(etl_process_time.values[0][0].strftime("%Y-%m-%d %H:%M:%S"))


hour_counts_query = """
WITH hours AS (
    SELECT generate_series(0, 23) AS hour
)
SELECT 
    hours.hour,
    COUNT(memes.id) AS count
FROM hours
LEFT JOIN memes ON hours.hour = EXTRACT(HOUR FROM memes.created_utc AT TIME ZONE 'UTC')
GROUP BY hours.hour
ORDER BY hours.hour;
"""
hour_counts = conn.query(hour_counts_query, ttl="10m")
st.header("Hours of memes posting distribution")
st.bar_chart(hour_counts.set_index('hour'))


best_authors_query = """
select memes.author, SUM(memes.score) 
from memes 
GROUP BY author 
ORDER BY SUM(memes.score) DESC
LIMIT 5;
"""
best_authors = conn.query(best_authors_query, ttl="10m")
st.header("Best authors:")
st.bar_chart(
    best_authors.set_index('author')['sum'],
    use_container_width=True,
)
best_authors = best_authors.reset_index()



st.header("The most voted memes!")
most_popular_memes_query="""
SELECT s3_url, score
FROM memes 
ORDER BY score DESC
LIMIT 3;
"""
most_popular_memes_minioURL = conn.query(most_popular_memes_query, ttl="10m")

client = Minio("minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)
for s3_url, score in zip(most_popular_memes_minioURL.s3_url, most_popular_memes_minioURL.score):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        client.fget_object("memes", s3_url, tmp.name)
        st.write(f"This meme got {score} votes")
        st.image(tmp.name)




st.header("The most commented meme!")
most_commented_meme_query="""
SELECT s3_url, num_comments 
from memes 
WHERE 
num_comments=
    (SELECT MAX(num_comments) 
    FROM memes);
"""

most_commented_meme = conn.query(most_commented_meme_query, ttl="10m")
st.write(f"This meme got {most_commented_meme['num_comments'].values[0]} comments")
with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
    client.fget_object("memes", most_commented_meme['s3_url'].values[0], tmp.name)
    st.image(tmp.name)


conn.session.close()
