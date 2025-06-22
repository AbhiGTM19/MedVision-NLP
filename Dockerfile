FROM python:3.9
WORKDIR /app
RUN apt-get update && apt-get install -y git
RUN git clone --branch master https://github.com/nalamv/mlops_finalassignment.git
WORKDIR /app/mlops_finalassignment
RUN ls -la
RUN echo "flask\nscikit-learn" > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "main.py"]
