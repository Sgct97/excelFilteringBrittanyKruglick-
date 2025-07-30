#!/bin/sh
# This script ensures the python script is run from the correct environment.

# Get the absolute directory where this script is located
# This allows the tool to be run from anywhere.
DIR="$( cd "$( dirname "$0" )" && pwd )"

# Activate the virtual environment using the script's directory
source "$DIR/venv/bin/activate"

# Run the python script, passing along the workbook path argument ($1)
# The workbook path is provided by the VBA macro.
python3 "$DIR/run_from_excel.py" "$1" 