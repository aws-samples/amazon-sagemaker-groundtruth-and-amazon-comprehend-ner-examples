#!/usr/bin/env bash

if [[ $(uname) != 'Linux' ]]; then
    echo "This script should run in Linux. Exiting..." >&2
    exit 1
fi

# Install Lambda's python-3.8
mkdir -p /tmp/layer
curl https://lambci.s3.amazonaws.com/fs/python3.8.tgz | tar -zx -C /tmp/layer
export PATH=/tmp/layer/var/lang/bin:$PATH
export LD_LIBRARY_PATH=/tmp/layer/var/lang/lib:$LD_LIBRARY_PATH

# Install packages
python -m pip --version
python -m pip install -t /tmp/python spacy s3fs
find /tmp/python -name '*.so' | xargs -n1 strip --strip-unneeded
find /tmp/python -name tests -type d | xargs rm -fr

# Confirm the final uncompressed size
echo 'Checking uncompressed size...'
UNCOMPRESSED_SIZE=$(du -sb /tmp/python/ | cut -d$'\t' -f1)
if [[ $UNCOMPRESSED_SIZE -ge 262144000 ]]; then
    echo 'Uncompressed size >= 262,144,000 bytes'
    exit 1
fi

# Compress packages
(cd /tmp && zip -9qr lambda-layer-spacy-p38.zip python/)

# Testing
echo 'Test layer locally...'
PYTHONPATH=/tmp/python:$PYTHONPATH python -c "import sys, s3fs, spacy; print(sys.executable); print([f'{m.__name__}-{m.__version__}' for m in  (s3fs, spacy)])"
if [[ $? -eq 1 ]]; then
    echo "Failed to import the newly installed python modules"
    exit 1
fi

# Final reminder to upload the zip file to S3.
echo "Final reminder: upload lambda-layer-spacy-p38.zip to S3"
echo "After the zipped layer lands in S3, go to the Lambda console and create your layer."
