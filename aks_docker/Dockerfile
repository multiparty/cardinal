FROM python:3.7

RUN mkdir /cardinal
WORKDIR /cardinal
ADD .. /cardinal/
RUN pip install -r requirements.txt

# fill out with appropriate information
ENV PORT=5000
ENV CLOUD_PROVIDER="AKS"
ENV SUB_ID="0e3d178e-863d-43a9-9f3c-3bd689fea5b1"
ENV RESOURCE_GROUP_NAME="cardinal"

CMD ["python", "/cardinal/wsgi.py"]
