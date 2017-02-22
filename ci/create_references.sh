# This script can be used to create references on travis. It should export a
# CREATE_REFERENCES variable that, if executed via
# `bash -c ${CREATE_REFERENCES}` creates the reference figures. Set
# CREATE_REFERENCES="" if no references shall be created

export CREATE_REFERENCES='tests/test_plotters.py::CombinedSimplePlotterTest::ref_cmap'
