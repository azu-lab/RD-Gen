#!/bin/bash


### echo usage
function show_usage () {
    echo "Usage: $0 [-h]"
    echo "          [-c or --chain]"
    echo "          [--config_yaml_name <file name>]"
    echo "          [-d <path of dir> or --dest_dir <path of dir>]"
    exit 0;
}


### initialize option variables
USE_CHAIN=""
CONFIG_YAML_NAME=""
CONFIG_YAML_PATH=""
DEST_DIR="${PWD}/DAGs"
PYTHON_SCRIPT_DIR="$(dirname $0)/src"


### parse command options
OPT=`getopt -o hcd: -l help,chain,config_yaml_name:,dest_dir: -- "$@"`


if [ $? != 0 ] ; then
    echo "[Error] Option parsing processing is failed." 1>&2
    show_usage
    exit 1
fi

eval set -- "$OPT"

while true
do
    case $1 in
    -h | --help)
        show_usage;
        shift
        ;;
    -c | --chain)
        USE_CHAIN="--use_chain"
        shift
        ;;
    --config_yaml_name)
        CONFIG_YAML_NAME="$2"
        shift 2
        ;;
    -d | --dest-dir)
        DEST_DIR="$2/DAGs"
        shift 2
        ;;
    --)
        shift
        break
        ;;
    esac
done

# check config yaml file
if [ -z "${CONFIG_YAML_NAME}" ]; then
    echo "[Error] '--config_yaml_name' should be specified." 1>&2
    exit 1
elif [ ${USE_CHAIN} ]; then
    CONFIG_YAML_PATH="$(dirname $0)/config/chain/${CONFIG_YAML_NAME}"
    if [ ! -f "${CONFIG_YAML_PATH}" ]; then
        echo "[Error] ${CONFIG_YAML_NAME} not found." 1>&2
        exit 1
    fi
else
    CONFIG_YAML_PATH="$(dirname $0)/config/normal/${CONFIG_YAML_NAME}"
    if [ ! -f  "${CONFIG_YAML_PATH}" ]; then
        echo "[Error] ${CONFIG_YAML_NAME} not found." 1>&2
        exit 1
    fi
fi

# check dest dir exist
if [ -e "${DEST_DIR}" ]; then
    echo "The following directory is already existing. Do you overwrite?"
    echo "DIRECTORY: ${DEST_DIR}"
    while :
    do
        read -p "[Y]es / [N]o? >> " INP
        if [[ ${INP} =~ [yYnN] ]]; then
            break
        fi
        echo "[Error] Input again [Y]es or [N]o."
    done
    if [[ ${INP} =~ [yY] ]]; then
        rm -r ${DEST_DIR}
        if [ $? -ne 0 ]; then
            echo "[Error] Cannot overwrite the destination directory: ${DEST_DIR}." 1>&2
            exit 1
        fi
    elif [[ ${INP} =~ [nN] ]]; then
        exit 1
    fi
fi


### make destination directory
if [[ ! -e "${DEST_DIR}" || ${INP} =~ [yY] ]]; then
    mkdir -p ${DEST_DIR}
    if [ $? -ne 0 ]; then
        echo "[Error] Cannot make the destination directory: ${DEST_DIR}." 1>&2
        exit 1
    fi
fi


### generate DAGs
if [ ${USE_CHAIN} ]; then
    python3 ${PYTHON_SCRIPT_DIR}/chain_based_generate.py --config_yaml_path "${CONFIG_YAML_PATH}" --dest_dir "${DEST_DIR}"
else
    python3 ${PYTHON_SCRIPT_DIR}/normal_generate.py --config_yaml_path "${CONFIG_YAML_PATH}" --dest_dir "${DEST_DIR}"
fi

if [ $? -ne 0 ]; then
    echo "$0 is Failed. Please fix [Error] in the log."
else
    cp ${CONFIG_YAML_PATH} ${DEST_DIR}
    echo "$0 is successfully completed." 1>&2
fi


# EOF
