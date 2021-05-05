FROM python:3.7

RUN mkdir /cardinal
WORKDIR /cardinal
ADD . /cardinal/
RUN pip install -r requirements.txt

# fill out with appropriate information
ENV PORT=5000
ENV CLOUD_PROVIDER="EKS"
#ENV PROJECT="curia-test"
ENV REGION="us-east-1"

CMD ["python", "/cardinal/wsgi.py"]
