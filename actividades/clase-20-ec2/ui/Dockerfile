FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt /code/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . /code/

EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
