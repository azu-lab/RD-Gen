#!/bin/bash


### echo usage
function show_usage () {
    echo "Usage: $0 [-h]"
    echo "          [-c or --chain]"
    echo "          [-d <path of dir> or --dest-dir <path of dir>]"
    exit 0;
}


### initialize option variables
USE_CHAIN=""
DEST_DIR="${PWD}"
PYTHON_SCRIPT_DIR="$(dirname $0)/src"


### parse command options
OPT=`getopt -o hcd: -l help,chain,dest-dir: -- "$@"`


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
    -d | --dest-dir)
        DEST_DIR="$2"
        mkdir -p $2
        shift 2
        ;;
    --)
        shift
        break
        ;;
    esac
done

# check dest dir exist
if [ -e "${DEST_DIR}/DAGs" ]; then
    echo "The following directory is already existing. Do you overwrite?"
    echo "DIRECTORY: ${DEST_DIR}/DAGs"
    while :
    do
        read -p "[Y]es / [N]o? >> " INP
        if [[ ${INP} =~ [yYnN] ]]; then
            break
        fi
        echo "[Error] Input again [Y]es or [N]o."
    done
fi


### generate DAGs
# TODO: python ファイルを実行
python3 ${PYTHON_SCRIPT_DIR}/generate_dags.py ${USE_CHAIN} --dest_dir "${DEST_DIR}"


echo "$0 is successfully completed."


# EOF