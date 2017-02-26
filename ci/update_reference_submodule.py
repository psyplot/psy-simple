#!/usr/bin/env python
from utils import get_ref_dir, get_ref_branch, repo
import subprocess as spr
import shutil
from deploy import deploy

ref_branch = get_ref_branch()
ref_dir = get_ref_dir()

deploy_dir = 'deploy'

spr.check_call(['git', 'clone', '-b', ref_branch,
                repo.replace('psy-simple', 'psy-simple-references'),
                deploy_dir])

spr.check_call(['git branch TRAVIS_DEPLOY'.split()])

spr.check_call(['git checkout TRAVIS_DEPLOY'.split()])

shutil.copytree(ref_dir, deploy_dir)

deploy(deploy_dir, ref_branch, '.')

shutil.rmtree(deploy_dir)
