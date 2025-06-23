FROM python:3.9
WORKDIR /app
RUN apt-get update && apt-get install -y git
RUN git clone --branch master https://github.com/nalamv/mlops_finalassignment.git
WORKDIR /app/mlops_finalassignment
RUN echo "Listing files in repo:" && ls -la
RUN echo "flask\nscikit-learn\npandas" > requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install scikit-optimize
EXPOSE 5000
RUN pip install pandas
CMD ["python", "main.py"]
