#!/usr/bin/env bash

# Utility function to get script's directory (deal with Mac OSX quirkiness).
get_bin_dir() {
    local READLINK=readlink
    if [[ $(uname) == 'Darwin' ]]; then
        READLINK=greadlink
        if [ $(which greadlink) == '' ]; then
            echo '[ERROR] Mac OSX requires greadlink. Install with "brew install greadlink"' >&2
            exit 1
        fi
    fi

    local BIN_DIR=$(dirname "$($READLINK -f ${BASH_SOURCE[0]})")
    echo -n ${BIN_DIR}
}

# Deploy stack
STACK_NAME=samtest
sam deploy --region ap-southeast-1 deploy --stack-name ${STACK_NAME} --guided

# Epilogue...
cat << EOF
All resources created. Next steps:
- Create a private work team, and enroll your email address
- Create a NER labeling job for the sample corpus
- Work on the labeling
- Once labeling job completes, start working in the notebook instance.
EOF
