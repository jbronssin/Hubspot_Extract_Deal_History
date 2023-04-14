#!/bin/bash

# Check if Brew is installed
if ! command -v brew &> /dev/null
then
    echo "Brew is not installed. Installing Brew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
else
    echo "Brew is already installed."
fi

# Check if Python3 is installed and update if necessary
if ! command -v python3 &> /dev/null
then
    echo "Python3 is not installed. Installing Python3..."
    brew install python3
else
    echo "Python3 is already installed."
    current_version=$(python3 -V | awk '{print $2}')
    latest_version=$(brew info python3 | awk '/^python3 / {print $2}')
    if [ "$current_version" != "$latest_version" ]
    then
        echo "Updating Python3 to the latest version..."
        brew upgrade python3
    else
        echo "Python3 is up to date."
    fi
fi

# Check if Pip3 is installed and update if necessary
if ! command -v pip3 &> /dev/null
then
    echo "Pip3 is not installed. Installing Pip3..."
    brew install pip3
else
    echo "Pip3 is already installed."
    current_version=$(pip3 -V | awk '{print $2}')
    if [ "$current_version" != "$(pip3 install --upgrade pip &> /dev/null; pip3 -V | awk '{print $2}')" ]
    then
        echo "Updating Pip3 to the latest version..."
    else
        echo "Pip3 is up to date."
    fi
fi

echo "Creating virtual environment..."
python3 -m venv venv

echo "Installing required packages in the virtual environment..."
pip3 install -r requirements.txt

echo "Virtual environment setup complete!"

echo "$(tput setaf 1)Please make sure you have created a Private Connected App with the required scopes as listed in the Hubspot-ConnectedApp-Scope.md file.$(tput sgr0)"

if [ ! -f ".env" ] || [ -z "$(grep -E '^HUBSPOT_TOKEN=.+' .env)" ]
then
    echo "$(tput setaf 1)It seems you have not set your Hubspot API key in the .env file or the .env file is missing.$(tput sgr0)"
    echo "$(tput setaf 4)Please enter your Hubspot Private App API key:$(tput sgr0)"
    read HUBSPOT_TOKEN
    echo "HUBSPOT_TOKEN=$HUBSPOT_TOKEN" > .env
else
    echo "$(tput setaf 2)HUBSPOT_TOKEN is already set in the .env file.$(tput sgr0)"
fi

echo "You are set to go!" 

echo "$(tput setaf 4)YOU MUST activate the virtual environment, run 'source ./venv/bin/activate'$(tput sgr0)"
echo "$(tput setaf 4)To deactivate the virtual environment, run 'deactivate'$(tput sgr0)"
echo "$(tput setaf 4)To run the script, run 'python3 hubspot_history.py' or 'python3 hubspot_history_all_pipes.py'$(tput sgr0)"
