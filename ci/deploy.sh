#!/bin/bash
set -e # Exit with nonzero exit code if anything fails
set -x

SRC_DIR=$1
shift
TARGET_BRANCH=$1
shift
WHAT=$@

cd $SRC_DIR

SSH_REPO=${REPO/https:\/\/github.com\//git@github.com:}
SHA=`git rev-parse --verify HEAD`

# Now let's go have some fun with the cloned repo
git config user.name "Travis"
git config user.email "$COMMIT_AUTHOR_EMAIL"

# If there are no changes to the compiled out (e.g. this is a README update) then just bail.
if [ -z `git diff --exit-code` ]; then
    echo "No changes to the output on this push; exiting."
    exit 0
fi

# Commit the "changes", i.e. the new version.
# The delta will show diffs between new and old versions.
git add $WHAT
git commit -m "Deploy from Travis: ${SHA} [skip ci]"

# Now that we're all set up, we can push.
git push $SSH_REPO $TARGET_BRANCH
