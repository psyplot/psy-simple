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

REPO_NAME=$(basename `git config remote.origin.url`)
REPO_NAME=${REPO_NAME%.git}

# Now let's go have some fun with the cloned repo
git config user.name "Travis"
git config user.email "$COMMIT_AUTHOR_EMAIL"

git add -N $WHAT

# If there are no changes to the compiled out (e.g. this is a README update) then just bail.
if [[ -z `git diff --exit-code` ]]; then
    echo "No changes to the output on this push; exiting."
    exit 0
fi

# Commit the "changes", i.e. the new version.
# The delta will show diffs between new and old versions.
git commit -am "Deploy from Travis build $TRAVIS_BUILD_NUMBER: Commit ${SHA} [skip ci]"

# Now that we're all set up, we can push.
git push "https://${GH_REPO_TOKEN}@${REPO_NAME}" $TARGET_BRANCH
