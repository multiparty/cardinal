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
ENV INFRA="AWS"
ENV REGION="us-east-1"
ENV CONGREGATION="docker.io/hicsail/congregation-jiff:debug"
ENV CHAMBERLAIN=""

# profile flag - set to "true" to receive profiling timestamps with each workflow
ENV PROFILE="false"

# Information for curia
ENV AWS_REGION=""
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""
ENV DESTINATION_BUCKET=""


CMD ["python", "/cardinal/wsgi.py"]
