import os.path as osp
import importlib.util as iutil

import subprocess as spr


spec = iutil.spec_from_file_location('get_ref_dir',
                                     osp.join('tests', 'get_ref_dir.py'))
gt = iutil.module_from_spec(spec)
spec.loader.exec_module(gt)

get_ref_dir = gt.get_ref_dir
get_ref_branch = gt.get_ref_branch


with spr.Popen(
        ('git -C %s config remote.origin.url' % osp.dirname(__file__)).split(),
        stdout=spr.PIPE) as p:
    repo = p.stdout.read()
