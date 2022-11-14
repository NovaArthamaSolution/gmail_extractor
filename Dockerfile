FROM google/cloud-sdk:latest AS gmail2bq-base


WORKDIR /tmp
ADD ./requirements.txt /tmp/requirements.txt
RUN pip3 install -r requirements.txt
RUN pip install --upgrade google-api-python-client --ignore-installed six

COPY ./tmp/. /tmp/

WORKDIR /data/in 
ADD ./data/in/ /data/in/

FROM gmail2bq-base

WORKDIR /opt/gmail2bq
COPY . /opt/gmail2bq


ENTRYPOINT ["/opt/gmail2bq/bin/gmail2bq" ]
