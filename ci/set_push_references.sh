WORK=`pwd`
if [[ $TRAVIS_PULL_REQUEST == "false" && $TRAVIS_REPO_SLUG == 'Chilipp/psy-simple' ]]; then
    cd $REFDIR
    git add -N $WHAT
    if [ -z `git diff --exit-code` ]; then
        echo "No changes to the output on this push; exiting."
    else
        echo "Pushing to psy-simple-references"
        export PUSH_REFERENCES="true"
    fi
  fi
cd $WORK
