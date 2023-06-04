# labor_assignment

Constrained optimization algorithm using PuLP

Heavily inspired by
https://github.com/kimsk132/kims-playground/tree/master/employee_scheduling


# HOW TO USE:
To use this script you need 3 files: form_responses.csv, shift_overlaps.csv, shift_requirements.csv

### form_responses.csv:
1. First, gather responses on the Labor Preference/Availability Form. Use template which resides in the _shift_script folder (make sure to modify shifts, info, etc.)
2. Once responses are all gathered, go to Responses -> View In Sheets. This will open up Google Sheets.
3. Go over responses. Take a note of how many hours there are in total. 
4. IMPORTANT. Make sure that the column where members put in their name is named 'What is your first and last name?' and the column where members put their hours is named 'Required hours of labor'. The script relies on matching this text exactly. 
5. Download the sheet as a .csv file. 
6. Create a folder for the current term in the _shift_script folder and put the .csv file inside of it.

###shift_requirements.csv
1. Go to sampleData subfolder and open shift_requirements.csv Right Click -> Open With -> Google Sheets
3. Save a copy of this file in the folder for the current term.
2. Go to the form responses sheet. Copy the first row starting from the first shift (Monday [Morning Hobbit [8:00AM-9:00AM]]	Monday [Lunch Cook [10:00AM-12:00PM]], etc.) 
3. Place this row of shift names right after 'Shift Name' row as in the example.
4. Manually populate Required number of people, Shift Length columns for each shift. 

###shift_overlaps.csv
1. Copy the example in sampleData as in the previous steps for shift_requirements.csv
2. Enter shifts that overlap in the same row as in the example. 

# Start the script
1. Modify FORM_RESPONSES_PATH, SHIFT_OVERLAPS_PATH and SHIFT_REQUIREMENTS_PATH in the first lines of the script below. 
2. These are the paths to the 3 files you created earlier. make sure these paths are correct.  
3. (OPTIONAL) populate Constraint 5: Worker conflicts as described in the code below. 
4. Connect to a runtime if not connected already (check upper right corner)
5. Click Runtime -> Run All in the upper left corner menu
6. Pray to God. 
7. Check the output. If there are no errors you should see the schedule followed by the breakdown of assignement. Make sure hours and everything looks okay. I'd reccomend copying and saving this console output somewhere for easy reference in the future. 
8. Now you can use this output to populate the labor schedule! Congrats on reaching final step 🥳. 

