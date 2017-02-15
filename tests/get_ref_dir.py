"""Get the right branch for the psy-simple reference figures"""
import sys
import os.path as osp


def get_ref_dir():
    import matplotlib as mpl
    return osp.join(osp.dirname(__file__), 'reference_figures', sys.platform,
                    'py' + '.'.join(map(str, sys.version_info[:2])),
                    'mpl' + mpl.__version__.rsplit('.', 1)[0])


if __name__ == '__main__':
    print(get_ref_dir())
