set -e

cd /vagrant/ 
echo "building" 
sudo docker build -t dev .  
echo "Running server" 
sudo docker run -p 80:80 -i -t dev /bin/bash

