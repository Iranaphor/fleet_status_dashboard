cd dashboard

################################
# Install nodejs and npm
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install npm
sudo apt install nodejs


################################
# Check installation success
node -v  # Should show v20.x.x
npm -v   # Should show the latest npm version


################################
# Install node-red and modules
sudo npm install -g --unsafe-perm node-red
sudo npm install node-red-dashboard
sudo npm install node-red-node-ui-table
sudo npm install tabulator-tables --save


################################
# Launch node-red
#node-red


#################################
# Uninstall nodejs and npm
#sudo apt remove -y nodejs npm libnode-dev
#sudo apt autoremove -y
#sudo apt clean
#sudo dpkg --remove --force-all libnode-dev
#sudo apt remove -y nodejs npm
