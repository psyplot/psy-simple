#!/bin/bash
set -e

WORK=`pwd`

if [ ! -f $WORK/deployed ]; then
    echo "No reference figures deployed, exiting..."
    exit 0
fi

echo "Cloning $TRAVIS_BRANCH from $REPO"
git clone -b $TRAVIS_BRANCH $REPO deploy
cd deploy

git branch TRAVIS_DEPLOY

git checkout TRAVIS_DEPLOY

# create backup of gitmodules
cp .gitmodules .gitmodules.bak

sed -i "s#https://#git://#" .gitmodules

echo "Initializing submodule $REFDIR"
git submodule update --init $REFDIR

# restore original gitmodules
mv .gitmodules.bak .gitmodules

echo "Pull from origin"
cd $REFDIR
git checkout $REFBRANCH
git pull

echo "deploying ..."
cd $WORK
bash ci/deploy.sh deploy $TRAVIS_BRANCH "$REFDIR" .gitmodules

rm -rf deploy
