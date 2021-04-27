FROM python:3.7

RUN mkdir /cardinal
WORKDIR /cardinal
ADD . /cardinal/
RUN pip install -r requirements.txt

# fill out with appropriate information
#ENV PORT={{PORT}}
#ENV CLOUD_PROVIDER={{CLOUD_PROVIDER}}
#ENV PROJECT={{PROJECT}}
#ENV REGION={{REGION}}

CMD ["python", "/cardinal/wsgi.py"]
