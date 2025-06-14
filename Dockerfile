FROM google/cloud-sdk:latest AS gmail2bq-base

# FROM gmail2bq-base as modules
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS="ignore"
ENV PYTHONDONTWRITEBYTECODE="dont"
ENV PYTHONPYCACHEPREFIX=/tmp/

WORKDIR /tmp
COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install -qr requirements.txt
# RUN pip3 install -q --upgrade google-api-python-client --ignore-installed six


#RUN rm -rf ./tmp/
#RUN rm -rf ./tests/

WORKDIR /data/in 
# ADD ./data/in/ /data/in/

FROM gmail2bq-base 

WORKDIR /opt/gmail2bq
COPY . /opt/gmail2bq

# FROM  modules as app

ENTRYPOINT [ "/opt/gmail2bq/bin/gmail2bq" ]
