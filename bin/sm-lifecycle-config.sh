#!/usr/bin/env bash
# A lifecycle configuration for SageMaker notebook instances. Can be used for
# "on-create" or "on-start". The later is useful to ensure S3 has pristine
# sample corpus every time the notebook instance starts.

set -e

# On-create: default git repo not cloned yet, so source directly from origin.
# On-start: source from origin to ensure S3 has pristine copies.
ORIGIN=aws-samples/amazon-sagemaker-groundtruth-dev
BUCKET=amazon-sagemaker-groundtruth-ner
for i in doc-00.txt doc-01.txt doc-02.txt
do
    curl --silent --location https://raw.githubusercontent.com/$ORIGIN/master/refdata/$i \
        | aws s3 cp - s3://$BUCKET/sampleraw/$i
done
