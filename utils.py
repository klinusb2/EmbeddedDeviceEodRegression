import logging
import time

def get_build_number(buildVersion):
    '''
    extracts the build number from a build version string
    in the form n.n.n.b ==> returns 'b' as int
    '''
    return int(buildVersion.split('.')[-1])

def version_sort_key(build: str) -> float:
    total = 0.
    multiplier = 1.
    for i in build.split('.'):
        total += float(i) * multiplier
        multiplier /= 10000.
    return total

def second_build_is_newer(build1: str, build2: str) -> bool:
    '''
    compares build strings to determine if the second one is newer than
    first one
    build strings are in the form a.b.c.d, a'.b'.c'.d'
    this function compares each pair (a,a') (b,b')... numerically
    to determine version precedence
    '''
    b1 = build1.split('.')
    b2 = build2.split('.')
    # zipped pairs: ( (a,a'), (b,b'), ...) up to the shorter of b1, b2
    for p1,p2 in zip(b1,b2):
        if int(p1) > int(p2):
            return False
        if int(p1) < int(p2):
            return True
    # if we reach here, this means the build version strings are either identical,
    # or they are similar up to the shorter one, something like: a.b.c, a.b.c.d
    # in this case, the longer version string is the newer one
    if (len(b1) < len(b2)):
        return True
    return False


def poll_wait_while_true(condition, conditionFalseSeconds = 20, wait = 10):
    '''
    loop/poll on lambda boolean function condition()
    continue waiting while condition() is True,
    exit loop when condition() is False for consecutive conditionFalseSeconds
    
    default conditionFalseSeconds is 20s
    default time between polls is 5s

    WARNING: possible infinite loop if condition() never becomes False
    '''
    totalWait = 0
    while totalWait < conditionFalseSeconds:
        if condition():
            totalWait = 0
        else:
            logging.info(' waiting...')
            time.sleep(wait)
            totalWait += wait

def poll_wait_until(condition, maxWaitSeconds = 20, wait = 10) -> bool:
    '''
    loop/poll on lambda boolean function condition()
    continue until condition() is True,
    exit loop on timeout maxWaitSeconds (default 20s)
    default time between polls is 2s

    returns True/False depending on conditon() met or timed out
    '''
    totalWait = 0
    while totalWait < maxWaitSeconds:
        if condition():
            return True
        else:
            logging.info(' waiting...')
            time.sleep(wait)
            totalWait += wait
    logging.warn(f'Waiting timed out after {maxWaitSeconds} seconds')
    return False