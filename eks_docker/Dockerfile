FROM python:3.7

RUN mkdir /cardinal
WORKDIR /cardinal
ADD . /cardinal/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

#------------------#
# CHANGE AS NEEDED #
#------------------#
# Environment information
ENV PORT=5000
ENV CLOUD_PROVIDER="EKS"
ENV REGION="us-east-1"

# Information for curia
ENV AWS_REGION=""
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""

ENV SOURCE_BUCKET=""
ENV SOURCE_KEY=""
ENV DESTINATION_BUCKET=""


CMD ["python", "/cardinal/wsgi.py"]
