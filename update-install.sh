#!/bin/bash

# this script install stuff on the guest account to have an updated version

if [[ $EUID -ne 0 ]];  then 
	echo "Please run as root"
  	exit 1
fi

echo "rsyncing dist directory"
rsync -av ./pnethack.dist ~guest/ --delete
if [[ $? -ne 0 ]] ; then
	echo "Failed"
	exit 1
fi

for dir in data info levels ; do
	echo "rsyncing dir $dir"
	rsync -av ./$dir ~guest/ --delete
	if [[ $? -ne 0 ]] ; then
		echo "Failed"
		exit 1
	fi
	done
	
for file in pnethack.ini play.sh ; do
	echo "rsyncing file $file"
	rsync -av ./$file ~guest/ 
	if [[ $? -ne 0 ]] ; then
		echo "Failed"
		exit 1
	fi
	done

# for some reason this scripts breaks rights of log dir
echo "Resetting log dir"
rm -fr ~guest/log
mkdir  ~guest/log
chown guest ~guest/log
chgrp guest ~guest/log

echo "guest directory is up to date"
exit 0
