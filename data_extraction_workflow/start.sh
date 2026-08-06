#!/usr/bin/env bash

echo Activating the Virtual Environment
source /c/Users/ellio/Documents/baller-automation-and-dashboarding-project/.venv/Scripts/activate

echo Installing the requirements and upgrading statsbombpy incase of a newer version
pip install -r requirements.txt
pip install statsbombpy --upgrade

echo Running the Workflow
python ./data_extraction_workflow/main.py