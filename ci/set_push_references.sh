# Test whether there have been changes to the reference figures, and if yes
# enable the deploy to the remote github repositories for psy-simple and
# psy-simple-references
#
# Usage::
#
#     source ci/set_push_references.sh

WORK=`pwd`
if [[ $TRAVIS_PULL_REQUEST == "false" && $TRAVIS_REPO_SLUG == 'Chilipp/psy-simple' ]]; then
    cd $REFDIR
    git add -N .
    if [[ -z `git diff --exit-code` ]]; then
        echo "No changes to the reference figures on this push -- No deploy."
        export PUSH_REFERENCES="false"
    else
        echo "------------------------------"
        echo "ATTENTION! REFERENCES CHANGED!"
        echo "------------------------------"
        echo "Enabled the deploy to psy-simple-references"
        export PUSH_REFERENCES="true"
    fi
  fi
cd $WORK
