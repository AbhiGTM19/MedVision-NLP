FROM python:3.9
WORKDIR /app
RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/nalamv/mlops_finalassignment.git
WORKDIR /app/mlops_finalassignment.git
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "main.py"]
