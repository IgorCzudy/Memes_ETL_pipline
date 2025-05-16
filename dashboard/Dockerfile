FROM python:3.8-slim

WORKDIR /dashboard

COPY . .

RUN pip install -r requirements.txt --no-cache

EXPOSE 8501
# http://localhost:8501/
CMD ["streamlit", "run", "dashboard.py"]
