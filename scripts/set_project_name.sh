#!/bin/sh
#
# set the project name - once for python and in every apache conf file

read -p "Enter project name: " project_name
project_name_upper=`echo ${project_name} | tr '[:lower:]' '[:upper:]'`

read -p "You entered ${project_name}, is that right? [y/n]: " continue

case ${continue} in
  [yY][eE][sS]|[yY]) 
    ;;
  *)
    exit 1
    ;;
esac

proj_basedir=`dirname $0`/..

# set the project name for apache conf files
for file in ${proj_basedir}/apache/*.conf ; do
  sed -i "s/project_name/${project_name}/" ${file}
done

# set the project name for python - imported elsewhere
for file in ${proj_basedir}/deploy/project_settings.py ; do
  sed -i "s/insert_project_name_here/${project_name}/" ${file}
done

