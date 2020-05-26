#!/usr/bin/env bash

# Sample usage:
#     ./sam-local.sh <ConverterFunction> [--debug or other sam local invoke parameters]

FUN=''
DRY_RUN=0
declare -a SAM_CLI_ARGS=()
PROFILE=''

usage() {
    echo "Usage: ${BASH_SOURCE[0]##*/} <ConverterFunction> [-h|--help] [-d|--dry-run] -- [other sam local invoke parameters]"
}

parse_profile() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
        --profile)
            echo -n "$1" "$2"
            return
            ;;
        *)
            shift
            ;;
        esac
    done
}

parse_args() {
    if [[ $# -lt 1 ]]; then
        echo $(usage) >&2
        exit -1
    fi

    FUN="$1"
    shift
    while [[ $# -gt 0 ]]; do
        case "$1" in
        -h|--help)
            echo $(usage)
            exit 0
            ;;
        -d|--dry-run)
            DRY_RUN=1
            shift
            ;;
        --)
            shift
            SAM_CLI_ARGS+=( "$@" )
            PROFILE=$(parse_profile "$@")
            break
            ;;
        *)
            echo 'Unknown option:' "$1"
            exit -1
        esac
    done
}

parse_args "$@"

ACCOUNT=$(aws ${PROFILE} sts get-caller-identity | jq -r '.Account')
REGION=$(aws ${PROFILE} configure get region)
declare -a PARAM=(--parameter-overrides
    ParameterKey=AccountId,ParameterValue=${ACCOUNT}
    ParameterKey=Layer,ParameterValue=spacy-p38-dev:1
)
cmd="sam local invoke ${PROFILE} --region ${REGION} ${PARAM[@]} --event events/${FUN}.json ${FUN} ${SAM_CLI_ARGS[@]}"
echo $cmd
[[ ${DRY_RUN} == 1 ]] && exit 0
eval $cmd
