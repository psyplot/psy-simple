"""Get the right branch for the psy-simple reference figures"""
import sys
import os.path as osp


def get_ref_branch():
    import matplotlib as mpl
    return '_'.join([sys.platform,
                     'py' + '.'.join(map(str, sys.version_info[:2])),
                     'mpl' + mpl.__version__.rsplit('.', 1)[0]])


if __name__ == '__main__':
    print(get_ref_branch())
