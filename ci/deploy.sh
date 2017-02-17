#!/bin/bash
set -e # Exit with nonzero exit code if anything fails
set -x

SRC_DIR=$1
shift
TARGET_BRANCH=$1
shift
WHAT=$@

SHA=`git rev-parse --verify HEAD`

cd $SRC_DIR

REPO_NAME=`git config remote.origin.url`
REPO_NAME=${REPO_NAME#https://}

# Now let's go have some fun with the cloned repo
git config user.name "Travis"
git config user.email "$COMMIT_AUTHOR_EMAIL"

# Commit the "changes", i.e. the new version.
# The delta will show diffs between new and old versions.
git add $WHAT
git commit -m "Deploy from Travis build $TRAVIS_BUILD_NUMBER: Commit ${SHA} [skip ci]"

# Now that we're all set up, we can push.
git branch --list
set +ex
echo git push --force "https://<secure>@${REPO_NAME}" $TARGET_BRANCH
git push --force "https://${GH_REPO_TOKEN}@${REPO_NAME}" $TARGET_BRANCH  2>&1 | sed -e "s/${GH_REPO_TOKEN}/<secure>/g"
