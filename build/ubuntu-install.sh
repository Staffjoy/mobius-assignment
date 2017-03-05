#!/bin/bash
set -e

sudo apt-get update --yes --force-yes

# Sometimes ubuntuneeds these software-properties repos :-(
sudo apt-get install --yes --force-yes  build-essential libffi-dev libssl-dev cmake expect-dev \
    python python-dev curl python-setuptools python-software-properties

sudo easy_install -U pip

sudo apt-get update --yes --force-yes # Re-update

# Set env variable that we are in dev
echo "echo 'export env=\"dev\"' >> /etc/profile" | sudo bash

# Install gurobi
# First remove remnants
#rm -rf gurobi650
rm -rf gurobi605

# Unzip. Sometimes it throws a hard link error - hence the "or" statement
#tar xfz gurobi6.5.0_linux64.tar.gz || :
tar xfz gurobi6.0.5_linux64.tar.gz || :

#cd gurobi650/linux64
cd ./gurobi605/linux64/
sudo python setup.py install
cd ../..


# Set up environment variables
cwd=`pwd`

# Gurobi home
#gurobi_home="$cwd/gurobi650/linux64/"
gurobi_home="$cwd/gurobi605/linux64/"
echo "echo \"export GUROBI_HOME=$gurobi_home\" >> /etc/profile" | sudo bash
echo "echo \"export LD_LIBRARY_PATH=${gurobi_home}lib/\" >> /etc/profile" | sudo bash

# Gurobi binary and library
echo "echo 'export PATH=\"${PATH}:${gurobi_home}bin/\"' >> /etc/profile" | sudo bash

# Gurobi license:
# If you want prod - just override environment variable!
echo "echo 'export GRB_LICENSE_FILE=$cwd/licenses/default.lic' >> /etc/profile" | sudo bash

cd $gurobi_home
