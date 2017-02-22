#!/bin/bash

set -e

WORK=`pwd`

git clone -b $REFBRANCH ${REPO/psy-simple/psy-simple-references} deploy

cp -r $REFDIR/* deploy

bash ci/deploy.sh $deploy $REFBRANCH .
