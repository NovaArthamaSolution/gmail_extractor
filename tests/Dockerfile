FROM google/cloud-sdk:latest AS gmail2bq-base

ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS="ignore"
ENV PYTHONDONTWRITEBYTECODE="dont"
ENV PYTHONPYCACHEPREFIX=/tmp/

WORKDIR /tmp
COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install -qr /tmp/requirements.txt

#RUN rm -rf ./tmp/


WORKDIR /data/in 
#COPY data/in/* /data/in/
#RUN rm -rf ./data/

# FROM gmail2bq-base

WORKDIR /opt/gmail2bq
ADD . /opt/gmail2bq

ENTRYPOINT [ "/opt/gmail2bq/bin/gmail2bq" ]
