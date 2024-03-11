"""
Will Nearn 
4 March 2024
Assignment Problem Example
based off of example in https://developers.google.com/optimization/assignment/assignment_example, but modified for my use
"""
import os
import pandas as pd
import numpy as np
import warnings
from ortools.linear_solver import pywraplp


def cleanPreferenceFiles(worker_file_name,
                    cleaned_file_name, 
                    manager_file_name, 
                    unable_score,
                    high_score,
                    low_reset_score):
    # Take in the names of the messy worker file, clean it up (partly based on the manager file), and save the cleaned version at `cleaned_file_name`.
    # PARAMS:
    # worker_file_name:
    #  - Is a downloaded Google Sheet, where everyone can only edit the page with their name on it
    #  - Should be filled out as "0" for jobs that the worker can't do 
    #  - Should contain (0,1] for jobs that the worker can do, where 1 means that they really want to do that job on that day
    # cleaned_file_name will be the location of the cleaned version of the file stored at `worker_file_name`
    # manager_file_name should be identical to the worker preferences file except the data points are made by the managers
    # unable_score is the score that indicates that a worker is unfit for a task (due to an exemption, lack of training, etc.)
    # high_score is the highest allowed preference score
    # low_reset_score is the preference score that workers get if they set their preference for a task too low. "Too low" is either of the following:
    #  - A number below unable_score
    #  - The value of unable_score if management says that the worker can do the given task
    # RETURNS:
    # void, but it writes to an .xlsx file
    
    worker_file = pd.read_excel(worker_file_name, sheet_name=None, index_col=0)
    manager_file = pd.read_excel(manager_file_name, sheet_name=None, index_col=0)

    for name in worker_file.keys():
        wdf = worker_file[name] #Extract <name>'s preferences page
        mdf = manager_file[name]
        if wdf.shape != mdf.shape or not wdf.columns.equals(mdf.columns) or not wdf.index.equals(mdf.index):
            print(f"There's an error on the formatting of {name}'s schedule in {worker_file_name} or {manager_file_name}, either with the row names or the column names -- go check it out")
            return False
        wdf.fillna(unable_score) # Fill NaNs with the unable score
        mdf.fillna(unable_score) 
        wdf = wdf.astype(int) # Floor worker scores to an integer number
        wdf[wdf<unable_score] = unable_score # Replace values less than unable_score with unable_score
        mdf[mdf<unable_score] = unable_score 
        mdf[mdf>high_score] = high_score # Replace values above the max with the max value
        wdf[wdf>high_score] = high_score

        #Find where workers put that they're unable to do jobs they're able to do and fix it
        mismatched_indices = wdf[(wdf==unable_score) & (mdf != unable_score)]  
        if not mismatched_indices.isnull().values.all():
            print(f"\n{name} screwed up and said that they couldn't work a job that they're trained to do. Resetting the values below that aren't 'NaN' to {low_reset_score}")
            print(mismatched_indices)
            with warnings.catch_warnings(): #It gives a warning that `low_reset_score` isn't the right data type?
                warnings.simplefilter("ignore", category=FutureWarning)
                wdf[mismatched_indices.notna()] = low_reset_score 
        
        worker_file[name] = wdf # Reassign corrected values to our excel spreadsheet
        manager_file[name] = mdf

    # Write to Excel
    with pd.ExcelWriter(cleaned_file_name, engine='xlsxwriter') as writer:
        for name, df in worker_file.items(): # Editing the isolated DataFrame objects earlier also edits the DataFrame objects inside worker_file
            df.to_excel(writer, sheet_name=name)
    with pd.ExcelWriter(manager_file_name, engine='xlsxwriter') as writer:
        for name, df in manager_file.items(): # Editing the isolated DataFrame objects earlier also edits the DataFrame objects inside worker_file
            df.to_excel(writer, sheet_name=name)
    return True


def read_in_off_day_requests(xlsx_dict, sheet_name, names):
    try:
        df = xlsx_dict[sheet_name]
        for index, row in df.iterrows():
            if index not in names:
                print(f"\nHold your horses there, buddy. The sheet {sheet_name} had an incorrect worker name in it. \nWrong Name: {index}\nAvailable Names: {names}. Skipping this guy")
                df.drop(index, inplace=True)
                continue
            if row.values[0] not in names:
                print(f"\nHold your horses there, buddy. The sheet {sheet_name} had an incorrect worker name in it. \nWrong Name: {row.values[0]}\nAvailable Names: {names}. Skipping this guy")
                df.drop(index, inplace=True)
                continue
        df.reset_index(inplace=True)
        return df
    except KeyError as e:
        return pd.DataFrame() # If it doesn't exist, just return an empty DataFrame

def main():
    # CONFIGUREABLE
    dirty_worker_preferences_file_name = "worker_preferences.xlsx" # Name of the file that contains each worker's preferences for each day/shift to work. Each column is a day, each row is a shift, and the values should be above `unable_score` for tasks that they're trained to do, and up to high_score for tasks that they really want to do. Non-integer values will be floored to the nearest integer, and values that are too low are brought back up to `low_reset_score`
    clean_worker_preferences_file_name = "cleaned_worker_preferences.xlsx" #Transition file that the program generates when it cleans the worker input data. It is deleted at the end of the program.
    manager_preferences_file_name = "manager_preferences.xlsx" # Excel workbook that has the manager preferences for each worker/day/shift combination, plus any extra sheets for other requirements
    not_off_together_page = "not_off_together" # This is the name of the sheet on the manager preferences workbook that contains the pairs of people that DO NOT WANT to be off together 
    off_together_page = "off_together" # This is the name of the sheet on the manager preferences workbook that contains the pairs of people that WANT to be off together 
    days_off_page = "days_off" # Page that contains who requested an unusual number of days off
    default_num_days_off_per_week = 2 # Number of days off that each worker has for M-Sa by default
    unable_score = 0 # If a worker gives this score, that indicates that they can't do the given task -- days off should be given in the manager preferences Excel worksheet
    high_score = 10 # Anything higher than this will be reset to this
    low_reset_score = np.int64(3) #Any score at or below unable_score for a task that a worker is able to do will be reset to this

    # Clean up data
    if not cleanPreferenceFiles(dirty_worker_preferences_file_name, 
                    clean_worker_preferences_file_name, 
                    manager_preferences_file_name, 
                    unable_score,
                    high_score,
                    low_reset_score):
        print("\nThere was an error in cleaning up the file. Please investigate. Exiting out of the program. Please re-run this program after fixing the data")
        return
    # Read in data
    worker_xlsx = pd.read_excel(clean_worker_preferences_file_name, sheet_name=None, index_col=0)
    manager_xlsx = pd.read_excel(manager_preferences_file_name, sheet_name=None, index_col=0)
    worker_names = list(worker_xlsx.keys()) # MAKE SURE THAT THE NAMES ARE THE SAME ON THE MANAGER PREFERENCE FILE AS THE WORKER PREFERENCE FILE !!!
    job_names = list(worker_xlsx[worker_names[0]].index)  # MAKE SURE THAT THE SAME JOB NAMES EXIST ON ALL SHEETS OF THE MANAGER PREFERENCE AND THE WORKER PREFERENCE FILE !!!
    day_names = list(worker_xlsx[worker_names[0]].head()) # MAKE SURE THAT THE SAME DAY NAMES EXIST ON ALL SHEETS OF THE MANAGER PREFERENCE AND THE WORKER PREFERENCE FILE !!!
    week_preferences = []
    for index in range(len(worker_names)):
        week_preferences.append(np.multiply(
            worker_xlsx[worker_names[index]].to_numpy(),
            manager_xlsx[worker_names[index]].to_numpy()
        ))    

    # Analysis
    num_workers = len(week_preferences)
    num_jobs = len(week_preferences[0])
    num_days = len(week_preferences[0][0])

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP") #Not sure what SCIP is

    if not solver:
        print("Solver not found. Exiting the program without solving.")
        return
    
    # assignment_matrix[w, j, d] is an array of 0-1 variables, which will be 1
    # if worker w is assigned to task j on day d when the solution is made.
    assignment_matrix = np.empty((num_workers, num_jobs, num_days), dtype=object)
    for w in range(num_workers): 
        for j in range(num_jobs):
            for d in range(num_days):
                assignment_matrix[w, j, d] = solver.IntVar(0, 1, "") #Initialization
    
    # Constraint: Each worker is assigned to at most 1 task per day.
    for d in range(num_days):
        for w in range(num_workers):
            solver.Add(solver.Sum([assignment_matrix[w, j, d] for j in range(num_jobs)]) <= 1)

    # Constraint: Each task is assigned to at most one worker per day.
    for d in range(num_days):
        for j in range(num_jobs):
            solver.Add(solver.Sum([assignment_matrix[w, j, d] for w in range(num_workers)]) <= 1)
    
    # Constraint: Each worker only works for num_days - num_days_off_per_week
    workers_to_days_off = {}
    for name in worker_names:
        workers_to_days_off[name] = default_num_days_off_per_week
    try:
        days_off_df = manager_xlsx[days_off_page] # Read in who requested a different number of days off than the default
        for name, row in days_off_df.iterrows():
            if name not in worker_names:
                print(f"\nHey, just a heads up-- you had {name} in here for {row.values[0]} days off on the sheet {days_off_page}, but they aren't in the list of worker names, so this program is ignoring them.\nNames: {worker_names}")
                continue
            try:
                num_days_off = int(row.values[0])
            except ValueError as e:
                print(f"\nHey, watch it there -- you put a non-number value ({row.values[0]}) as the number of days that {name} has off on the sheet {days_off_page}. We're gonna go ahead and skip it for that.")
            if num_days_off > num_days:
                print(f"\nYou listed {name} as having {num_days_off} days off this week on the sheet {days_off_page}, but there are only {num_days} in the week. I want their lifestyle! I'm gonna go ahead and set their days off this week back down to {num_days}")
                num_days_off = num_days
            workers_to_days_off[name] = num_days_off
    except KeyError as e:
        pass
    for w in range(num_workers):
        solver.Add(solver.Sum([assignment_matrix[w, j, d] for d in range(num_days) for j in range(num_jobs)]) <= (num_days - workers_to_days_off[worker_names[w]]))

    # Constraint: People who don't want to be off together won't be off together
    not_off_together_df = read_in_off_day_requests(manager_xlsx, not_off_together_page, worker_names)
    for index, row in not_off_together_df.iterrows():
        first_person = not_off_together_df.iloc[index, 0] #Get people's names
        second_person = not_off_together_df.iloc[index, 1]
        w1 = worker_names.index(first_person) # Convert people's names into indices
        w2 = worker_names.index(second_person)
        for d in range(num_days):
            solver.Add(  solver.Sum( assignment_matrix[w1, :, d]+assignment_matrix[w2, :, d] )  >= 1) # Constrain at least one of them to be on during a given day, therefore they aren't off together

    # Constraint: People who do want to be off together will always be off together
    off_together_df = read_in_off_day_requests(manager_xlsx, off_together_page, worker_names)
    for index, row in off_together_df.iterrows():
        first_person = off_together_df.iloc[index, 0] #Get people's names
        second_person = off_together_df.iloc[index, 1]
        w1 = worker_names.index(first_person) # Convert people's names into indices
        w2 = worker_names.index(second_person)
        for d in range(num_days):
            solver.Add(  solver.Sum( assignment_matrix[w1, :, d]-assignment_matrix[w2, :, d] )  >= 0) # Constrain not exactly one of them to be on during a given day, therefore they are always off together
            solver.Add(  solver.Sum( -assignment_matrix[w1, :, d]+assignment_matrix[w2, :, d] )  >= 0) # Constrain not exactly one of them to be on during a given day, therefore they are always off together


    # Objective function -- a combination of the (double)preference matrix and the (<ortools.linear_solver.pywraplp.Variable>)assignment matrix
    objective_terms = []
    for d in range(num_days):
        for w in range(num_workers):
            for j in range(num_jobs):
                objective_terms.append(week_preferences[w][j][d] * assignment_matrix[w, j, d])
    solver.Maximize(solver.Sum(objective_terms))
    
    #Solve
    print(f"Solving with {solver.SolverVersion()}")
    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        if status == pywraplp.Solver.OPTIMAL:
            print("Optimal solution found.")
        if status == pywraplp.Solver.FEASIBLE:
            print("Feasible solution found.")
        print(f"Total Happiness = {solver.Objective().Value()}\n")
        data = {} #For the output DataFrame
        for d in range(num_days):
            print(f"\n\t---- {day_names[d]} ----")
            day_assignments = {day_names[d] : [" " for _ in range(num_jobs)]}
            for w in range(num_workers):
                assigned = False
                for j in range(num_jobs):
                    # Test if assignment_matrix[w, j, d] is 1 (with tolerance for floating point arithmetic).
                    if assignment_matrix[w, j, d].solution_value() > 0.5:
                        print(f"{worker_names[w]} is assigned to {job_names[j]}." + f" Happiness: {week_preferences[w][j][d]}")
                        day_assignments[day_names[d]][j] = worker_names[w]
                        assigned = True
                if not assigned:
                    print(f"{worker_names[w]} is off.")
            data[day_names[d]] = day_assignments[day_names[d]]
        df = pd.DataFrame(data, index=job_names)
        df.to_csv("output.csv", index=True)
    else:
        print("\n\n\n\t\t**** ERROR: No solution found. ****")
        print("> That means that the problem is over-defined-- it has too many constriants. If you remove some constraints, you'll probably get a solution")
        print("  > This most cumbersome constraints are 'I wanna be off together with John Doe' or 'I don't wanna be off together with John Doe.' Try to get the workers just to set their own daily preferences on their preference sheet (e.g. both workers setting all their preferences on Tuesday to the lowest value in order to increase the likelihood that they'll have a day off together)")
        print("  > The next most cumbersome constraints are the days off. Hopefully, you shouldn't need to rearrange these too much, but obviously if we're overstaffed and everyone wants to work 6/6 days, we just aren't going to have enough jobs to go around. If you're wildly overstaffed, and there still aren't enough jobs to go around for everyone to work 4 days a week, you can add more jobs (rows) on the preferences sheets")
        print("  > Once you solve these two things, you should be good :)")
    os.remove(clean_worker_preferences_file_name) #Cleanup!



if __name__ == "__main__":
    main()