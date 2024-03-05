"""
Will Nearn
5 March 2024
This is a script to read a google form for scheduling and convert it to an .xlsx for processing
"""

import pandas as pd
import numpy as np
import warnings

# CONFIGUREABLE
unable_score = 0
high_score = 1 # Anything higher than this will be reset to this
low_reset_score = np.float64(0.3) #Any score at or below unable_score for a task that a worker is able to do will be reset to this
cleaned_file_name = "cleaned_worker_preferences.xlsx"

# EXECUTION
worker_file_name = "Test_google_sheets_input.xlsx"
# This file:
#  - Is a downloaded Google Sheet, where everyone can only edit the page with their name on it
#  - Should be filled out as "0" for jobs that the worker can't do 
#  - Should contain (0,1] for jobs that the worker can do, where 1 means that they really want to do that job on that day

# Read in worker preferences
worker_file = pd.read_excel(worker_file_name, sheet_name=None, index_col=0)

# Read in Manager Preferences
manager_file_name = "manager_preferences.xlsx" #This file should be identical to the worker preferences file except the data points are made by the managers
manager_file = pd.read_excel(manager_file_name, sheet_name=None, index_col=0)

for name in worker_file.keys():
    wdf = worker_file[name] #Extract <name>'s page
    mdf = manager_file[name]
    if wdf.shape != mdf.shape or not wdf.columns.equals(mdf.columns) or not wdf.index.equals(mdf.index):
        print(f"There's an error on the formatting of {name}'s schedule, either with the row names or the column names -- go check it out")
        continue
    wdf.fillna(0) # Fill NaNs with 0s
    mdf.fillna(0) 
    wdf[wdf<0] = 0 # Replace negative values with 0 
    mdf[mdf<0] = 0 

    #Find where workers put that they're unable to do jobs they're able to do and fix it
    mismatched_indices = wdf[(wdf==unable_score) & (mdf != unable_score)]  
    if not mismatched_indices.isnull().values.all():
        print(f"\n{name} screwed up and said that they couldn't work a job that they're trained to do. Resetting the values below that aren't 'NaN' to {low_reset_score}")
        print(mismatched_indices)
        with warnings.catch_warnings(): #It gives a warning that `low_reset_score` isn't the right data type?
            warnings.simplefilter("ignore", category=FutureWarning)
            wdf[mismatched_indices.notna()] = low_reset_score 
    
    # Find where workers put that they want to do a job with a higher preference than they're allowed
    mismatched_indices = wdf[wdf>high_score]
    if not mismatched_indices.isnull().values.all():
        print(f"\n{name} screwed up and said that they wanted to work a job more than the max limit. Resetting the values below that aren't 'NaN' to {high_score}")
        print(mismatched_indices)
        with warnings.catch_warnings(): #It gives a warning that `high_score` isn't the right data type?
            warnings.simplefilter("ignore", category=FutureWarning)
            wdf[mismatched_indices.notna()] = high_score
    a = 1
# Write to Excel
with pd.ExcelWriter(cleaned_file_name, engine='xlsxwriter') as writer:
    for name, df in worker_file.items():
        df.to_excel(writer, sheet_name=name)
