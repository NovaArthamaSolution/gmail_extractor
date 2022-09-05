FROM google/cloud-sdk:latest AS gmail2bq-base



WORKDIR /tmp
ADD ./requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

COPY ./tmp/* /tmp/

WORKDIR /data/in
# COPY ./data/in /data/in/

WORKDIR /data/in 
COPY data/in/* /data/in/

FROM gmail2bq-base

WORKDIR /opt/gmail2bq
ADD . /opt/gmail2bq

WORKDIR /opt/gmail2bq

ENTRYPOINT ["/opt/gmail2bq/bin/gmail2bq-test" ]
