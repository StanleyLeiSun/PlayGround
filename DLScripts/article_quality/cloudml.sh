#!/bin/bash
package_version=9
package_name=article-quality-$package_version.tar.gz

python setup.py sdist $package_version
#cloudml jobs delete article-quality-local
echo $package_name

fds -m put -b training -o packages/$package_name -d dist/$package_name

cloudml jobs submit -n article-quality-$package_version -m lstm_training -g 1 -M 8G -u fds://training/packages/$package_name

