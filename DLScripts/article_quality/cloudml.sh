#!/bin/bash
package_version=regression2
package_name=article-quality
package_full_name=$package_name-$package_version
package_file_name=$package_full_name.tar.gz
model_name=lstm_training

#todo: read model_name and package_name from per folder config
python setup.py sdist $package_name $package_version

fds -m delete -b training -o packages/$package_file_name 
cloudml jobs delete $package_full_name
sleep 6

fds -m put -b training -o packages/$package_file_name -d dist/$package_file_name

cloudml jobs submit -n $package_full_name -m $model_name -a"-n $package_full_name --iscloud" -g 1 -M 2G -u fds://training/packages/$package_file_name

