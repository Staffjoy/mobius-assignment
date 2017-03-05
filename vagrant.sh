#!/bin/bash
set -e

cd /vagrant/build
bash ubuntu-install.sh
cd ..

# Virtual Env
sudo pip install virtualenv
echo "source /vagrant/vagrant-venv/bin/activate" >> $HOME/.bashrc
echo 'echo "export PYTHONPATH=\"/vagrant/\"" >> /etc/profile' | sudo sh

rm -rf vagrant-venv && virtualenv vagrant-venv

# Now install gurobi within the virtualenv
source /etc/profile
source /vagrant/vagrant-venv/bin/activate
cd $GUROBI_HOME
python setup.py install
cd /vagrant/
make dependencies
