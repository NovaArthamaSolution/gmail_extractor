FROM google/cloud-sdk:latest AS gmail2bq-base



WORKDIR /tmp
ADD ./requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /data/in
# COPY ./data/in /data/in/

WORKDIR /data/out

FROM gmail2bq-base

WORKDIR /opt/gmail2bq
ADD . /opt/gmail2bq

WORKDIR /opt/gmail2bq/data/in

ENTRYPOINT ["/opt/gmail2bq/bin/gmail2bq-test" ]
