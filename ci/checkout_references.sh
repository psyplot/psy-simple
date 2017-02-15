#!/bin/bash
set -ex
# Checkout the correct reference figures branch

REF_REPO=https://github.com/Chilipp/psy-simple-references.git

REFDIR=`python tests/get_ref_dir.py`

set +e
git submodule init ${REFDIR}
SUCCES=$?
set -e

if [[ ${SUCCES} != 0 ]]; then
    BRANCH=`python tests/get_ref_dir.py -b`
    set +e
    git submodule add -b ${BRANCH} ${REF_REPO} ${REFDIR}
    SUCCES=$?
    set -e
    if [[ ${SUCCES} != 0 ]]; then
        git clone ${REF_REPO}
        cd psy-simple-references
        git branch ${BRANCH}
        git push origin ${BRANCH}
        cd ../
        rm -rf psy-simple-references
        git submodule add -b ${BRANCH} ${REF_REPO} ${REFDIR}
    fi
fi
git submodule update ${REFDIR}
