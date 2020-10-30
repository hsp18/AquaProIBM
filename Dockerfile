FROM python:3.666666 
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT [ "python" ] 
CMD ["run.py" ]



