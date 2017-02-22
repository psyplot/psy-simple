#!/bin/bash
set -e

WORK=`pwd`

echo "Cloning $TRAVIS_BRANCH from $REPO"
git clone -b $TRAVIS_BRANCH $REPO deploy
cd deploy

echo "Initializing submodule $REFDIR"
git submodule update --init $REFDIR

echo "Pull from origin"
cd $REFDIR
git checkout $REFBRANCH
git pull

echo "deploying ..."
cd $WORK
bash ci/deploy.sh deploy $TRAVIS_BRANCH $REFDIR

rm -rf deploy
