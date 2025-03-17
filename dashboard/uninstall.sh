#################################
# Uninstall nodejs and npm
sudo apt remove -y nodejs npm libnode-dev
sudo apt autoremove -y
sudo apt clean
sudo dpkg --remove --force-all libnode-dev
sudo apt remove -y nodejs npm
