#!/bin/sh
# This script makes it easy to run the fuzzy match by double-clicking.

# Get the absolute directory where this script is located to run from anywhere
DIR="$( cd "$( dirname "$0" )" && pwd )"

# The name of the Excel tool file
EXCEL_FILE="FuzzyMatch_Tool.xlsm"
FULL_EXCEL_PATH="$DIR/$EXCEL_FILE"

# Check if the Excel file exists
if [ ! -f "$FULL_EXCEL_PATH" ]; then
    echo "ERROR: Could not find the Excel file."
    echo "Please make sure '$EXCEL_FILE' is in the same folder as this script."
    echo ""
    echo "Press Enter to close this window."
    read
    exit 1
fi

echo "Starting the fuzzy matching process..."
echo "This may take a few minutes. Please wait."
echo "----------------------------------------"

# Run the main shell script, which handles the python environment
sh "$DIR/run.sh" "$FULL_EXCEL_PATH"

echo "----------------------------------------"
echo "Matching process complete!"
echo "You can now open '$EXCEL_FILE' to see the results on the 'Match_Results' sheet."
echo ""
echo "This window will close automatically."
sleep 5 