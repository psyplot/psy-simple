#!/bin/bash

set -e

WORK=`pwd`

git clone -b $REFBRANCH ${REPO/psy-simple/psy-simple-references} deploy

git branch TRAVIS_DEPLOY

git checkout TRAVIS_DEPLOY

cp -r $REFDIR/* deploy

bash ci/deploy.sh deploy $REFBRANCH .

rm -rf deploy
