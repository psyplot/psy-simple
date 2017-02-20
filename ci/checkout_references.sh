#!/bin/bash
set -ex
# Checkout the correct reference figures branch

REF_REPO=https://github.com/Chilipp/psy-simple-references.git

TEST_DIR=`dirname $0`
BRANCH=`python ci/get_ref_branch.py`

REF_DIR='tests/reference_figures'

mkdir $REF_DIR  && cd $REF_DIR

git clone ${REF_REPO} .
git checkout $BRANCH || git checkout --orphan $BRANCH
