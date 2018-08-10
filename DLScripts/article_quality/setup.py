import sys
import setuptools

ver = sys.argv[2]
sys.argv.remove(ver)
print(ver)
setuptools.setup(name='article-quality', version=ver, packages=[''], author='stansun')