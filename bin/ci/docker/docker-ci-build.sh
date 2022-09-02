#!/bin/bash

#set -x
set -eo pipefail

DIR_SANDBOX=$(cd $(dirname $0); pwd)
REPO_ROOT=${DIR_SANDBOX}/../../../

cd ${DIR_SANDBOX}

cp $REPO_ROOT/requirements.txt $DIR_SANDBOX/requirements.txt

echo "Build asia.gcr.io/bi-gojek/gmail2bq-base image for CI..."
docker build -t asia.gcr.io/bi-gojek/gmail2bq-base -f ./Dockerfile .

echo "Login to asia.gcr.io..."
docker login --username oauth2accesstoken --password $(gcloud auth application-default print-access-token) https://asia.gcr.io

echo "Push Images to asia.gcr.io/bi-gojek/gmail2bq-base ..."
docker push asia.gcr.io/bi-gojek/gmail2bq-base

rm $DIR_SANDBOX/requirements.txt

echo "Building and Pushing Docker Image is finished."
