#!/usr/bin/env bash

python.exe -m pip install --upgrade pip

VENV_DIR="./data_extraction_workflow/.venv"
VENV_ACTIVATE="$VENV_DIR/Scripts/activate"

# Check if the virtual environment exists; if not, create it
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating a new .venv..."
    python -m venv "$VENV_DIR"
    echo "Virtual environment created successfully."
fi

echo "Activating the Virtual Environment..."
source "$VENV_ACTIVATE"

echo Installing the requirements and upgrading statsbombpy incase of a newer version
pip install -r requirements.txt
pip install statsbombpy --upgrade

cd data_extraction_workflow

echo Running the Workflow
python main.py