#!/bin/bash
# Filename: checkProcesses.sh
# Usage:
#    To run this script, execute the following command
#    $ sh checkProcesses.sh
# Output:
#    This script checks running status of 
#    * containers as found in /usr/local/sbin/container-init
#    * processes as found in /usr/local/etc/init/*Init files
#    * processes listed in /usr/local/etc/config/ProcessRegistryConfig.xml
#
#######################################################

UL=/usr/local
UL_ETC="${UL}/etc/"
UL_SBIN="${UL}/sbin/"

# list of running containers
RUNNING_CONTAINERS=`lxc-ls`

NOCO='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
function red() {
    echo -e ${RED}$1${NOCO}
}
function green() {
    echo -e ${GREEN}$1${NOCO}
}

function containsElement () {
    local e match="$1"
    shift
    for e; do [[ "$e" == "$match" ]] && return 0; done
    return 1
}

# list of containers found in and should have been started by /usr/local/sbin/container-init
echo
cat /data/mender/device_type
grep constexpr /usr/local/etc/ProjectInfo.txt|cut -c19-
CONTAINER_INIT=${UL_SBIN}container-init
process_list=()
echo
echo "Expected running containers found in ${CONTAINER_INIT}"
echo
for container in `grep lxc-start ${CONTAINER_INIT} | awk '{print $6}'`; do
    echo "container: $container"
    INIT_FILE="${UL_ETC}init/${container}Init"
    # check if each container is running
    if [[ $RUNNING_CONTAINERS == *"$container"* ]]; then
        green " ...is running"
        # find container's init file and get the processes started in it
        if [ -f "$INIT_FILE" ]; then 
            green " ...container init file found: $INIT_FILE"
            echo  " .....expected processes found in container init file"
            for process in `grep '/usr/local/sbin/.*\s&\s*$' $INIT_FILE|awk '{print $1}'`; do
                process_list+=(${process})
                if lxc-attach -n $container -- pidof $process > /dev/null; then
                    green " ......process $process running"
                else
                    red " ......process $process NOT running"
                fi
            done
        else
            red " ...init file ${INIT_FILE} NOT FOUND!"
        fi
    else
        red " ...is NOT running"
    fi
done

# check all process found in /usr/local/etc/init/*Init, any that's not already found in the loop above
# belongs to core
echo
echo "CORE processes"
for process in `grep '/usr/local/sbin/.*\s&\s*$' ${UL_ETC}init/*Init|awk '{print $2}'`; do
    if ! containsElement $process "${process_list[@]}"; then
        if pidof $process > /dev/null; then
            green " ......process $process running"
        else
            red " ......process $process NOT running"
        fi
    fi
done

echo
PROCESS_REGISTRY_CONFIG=${UL_ETC}config/ProcessRegistryConfig.xml
echo "Checking ProcessRegistry (${PROCESS_REGISTRY_CONFIG})..."
for process in `grep '<ProcessRegistry ' ${PROCESS_REGISTRY_CONFIG}|cut -d'"' -f2`; do
    if pidof $process > /dev/null; then
        green "ProcessRegistry: ${process} is running"
    else
        red "ProcessRegistry: ${process} NOT found"
    fi
done
