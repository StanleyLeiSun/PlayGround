#!/bin/bash
package_version=17
package_full_ver=article-quality-$package_version
package_name=$package_full_ver.tar.gz

python setup.py sdist $package_version
#cloudml jobs delete article-quality-local

fds -m put -b training -o packages/$package_name -d dist/$package_name

cloudml jobs submit -n article-quality-$package_version -m lstm_training -a"-n $package_full_ver --iscloud" -g 1 -M 8G -u fds://training/packages/$package_name

