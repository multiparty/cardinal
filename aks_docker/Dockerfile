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
ENV CLOUD_PROVIDER="AKS"
ENV SUB_ID="0e3d178e-863d-43a9-9f3c-3bd689fea5b1"
ENV RESOURCE_GROUP_NAME="mc_cardinal_cardinal_eastus"
ENV LOCATION="eastus"

# profile flag - set to "true" to receive profiling timestamps with each workflow
ENV PROFILE="false"

# Information for curia
ENV AWS_REGION=""
ENV AWS_ACCESS_KEY_ID=""
ENV AWS_SECRET_ACCESS_KEY=""

ENV SOURCE_BUCKET=""
ENV SOURCE_KEY=""
ENV DESTINATION_BUCKET=""


CMD ["python", "/cardinal/wsgi.py"]
