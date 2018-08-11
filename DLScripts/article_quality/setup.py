import sys
import setuptools

name = sys.argv[2]
ver = sys.argv[3]
sys.argv.remove(ver)
sys.argv.remove(name)

setuptools.setup(name=name, version=ver, packages=[''], author='stansun')