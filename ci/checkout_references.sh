#!/bin/bash
set -ex
# Checkout the correct reference figures branch

REF_REPO=https://github.com/Chilipp/psy-simple-references.git

REFDIR=`python tests/get_ref_dir.py`

git submodule update --init ${REFDIR}
