"""Isolate test storage from user datasets, including when pytest runs on Windows."""
import os,tempfile
_TESTDIR=tempfile.TemporaryDirectory(prefix='mdf_test_')
os.environ['MDF_DATA_DIR']=_TESTDIR.name+'/data'
os.environ['MDF_ARTIFACT_DIR']=_TESTDIR.name+'/artifacts'
os.environ['MDF_NO_AUTOWORKER']='1'
