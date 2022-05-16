#!/bin/bash


### echo usage
function show_usage () {
    echo "Usage: $0 [-h]"
    echo "          [-c <path of config file> or --config_path <path of config file>]"
    echo "          [-d <path of dir> or --dest_dir <path of dir>]"
    exit 0;
}


### initialize option variables
CONFIG_PATH=""
DEST_DIR="${PWD}/DAGs"
PYTHON_SCRIPT_DIR="$(dirname $0)/src"


### parse command options
OPT=`getopt -o hc:d: -l help,config_path:,dest_dir: -- "$@"`


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
    -c | --config_path)
        CONFIG_PATH="$2"
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

# check config file
if [ -z "${CONFIG_PATH}" ]; then
    echo "[Error] '--config_path' should be specified." 1>&2
    exit 1
elif [ ! -f  "${CONFIG_PATH}" ]; then
        echo "[Error] ${CONFIG_PATH} not found." 1>&2
        exit 1
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
export PYTHONPATH="$(dirname $0)/"
python3 ${PYTHON_SCRIPT_DIR}/main.py --config_path "${CONFIG_PATH}" --dest_dir "${DEST_DIR}"


if [ $? -ne 0 ]; then
    echo "$0 is Failed. Please fix [Error]."
else
    cp ${CONFIG_PATH} ${DEST_DIR}
    echo "$0 is successfully completed." 1>&2
fi


# EOF
