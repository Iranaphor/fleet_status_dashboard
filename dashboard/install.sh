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
cp ./package.json ~/.node-red/
cp ./package-lock.json ~/.node-red/
npm install --prefix ~/.node-red
