"""
Will Nearn 
4 March 2024
Assignment Problem Example
based off of example in https://developers.google.com/optimization/assignment/assignment_example, but modified for my use
"""
import pandas as pd
import numpy as np
import warnings
from ortools.linear_solver import pywraplp


def cleanWorkerFile(worker_file_name, cleaned_file_name, manager_file_name):
    # Take in the names of the messy worker file, clean it up (partly based on the manager file), and save the cleaned version at `cleaned_file_name`.
    # PARAMS:
    # worker_file_name:
    #  - Is a downloaded Google Sheet, where everyone can only edit the page with their name on it
    #  - Should be filled out as "0" for jobs that the worker can't do 
    #  - Should contain (0,1] for jobs that the worker can do, where 1 means that they really want to do that job on that day
    # cleaned_file_name will be the location of the cleaned version of the file stored at `worker_file_name`
    # manager_file_name should be identical to the worker preferences file except the data points are made by the managers
    # RETURNS:
    # void, but it writes to an .xlsx file

    # CONFIGUREABLE
    unable_score = 0 # If a worker gives this score, that indicates that they can't do the given task -- days off should be given in the manager preferences Excel worksheet
    high_score = 1 # Anything higher than this will be reset to this
    low_reset_score = np.float64(0.3) #Any score at or below unable_score for a task that a worker is able to do will be reset to this
    
    worker_file = pd.read_excel(worker_file_name, sheet_name=None, index_col=0)
    manager_file = pd.read_excel(manager_file_name, sheet_name=None, index_col=0)

    for name in worker_file.keys():
        wdf = worker_file[name] #Extract <name>'s preferences page
        mdf = manager_file[name]
        if wdf.shape != mdf.shape or not wdf.columns.equals(mdf.columns) or not wdf.index.equals(mdf.index):
            print(f"There's an error on the formatting of {name}'s schedule in {worker_file_name} or {manager_file_name}, either with the row names or the column names -- go check it out")
            return False
        wdf.fillna(0) # Fill NaNs with 0s
        mdf.fillna(0) 
        wdf[wdf<0] = 0 # Replace negative values with 0 
        mdf[mdf<0] = 0 
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
    
    # Write to Excel
    with pd.ExcelWriter(cleaned_file_name, engine='xlsxwriter') as writer:
        for name, df in worker_file.items(): # Editing the isolated DataFrame objects earlier also edits the DataFrame objects inside worker_file
            df.to_excel(writer, sheet_name=name)
    return True


def read_in_off_day_requests(file_name, names):
    # A convenience function to read in off together / not off together requests
    df = pd.DataFrame()
    if file_name is not None:
        df = pd.read_csv(file_name)
    for index, row in df.iterrows():
        for elem in row:
            if elem not in names:
                print(f"Hold your horses there, buddy. {file_name} had an incorrect worker name in it. \nWrong Name: {elem}\nAvailable Names: {names}. Skipping this guy")
                df.drop(index, inplace=True)
                break
    df.reset_index(drop=True, inplace=True)
    return df



def main(dirty_worker_preferences_file_name, 
         clean_worker_preferences_file_name, 
         manager_preferences_file_name, 
         num_days_off_per_week, 
         not_off_together_file=None,
         off_together_file=None):
    # Clean up data
    if not cleanWorkerFile(dirty_worker_preferences_file_name, 
                    clean_worker_preferences_file_name, 
                    manager_preferences_file_name):
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
    off_together_df = read_in_off_day_requests(off_together_file, worker_names)
    not_off_together_df = read_in_off_day_requests(not_off_together_file, worker_names)

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
    assignment_matrix = {}
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
    for w in range(num_workers):
        solver.Add(solver.Sum([assignment_matrix[w, j, d] for d in range(num_days) for j in range(num_jobs)]) <= (num_days - num_days_off_per_week))

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
        print("No solution found.")



if __name__ == "__main__":
    dirty_worker_preferences_file_name = "worker_preferences.xlsx"
    clean_worker_preferences_file_name = "cleaned_worker_preferences.xlsx"
    manager_preferences_file_name = "manager_preferences.xlsx"
    not_off_together_file = "not_off_together.csv"
    off_together_file = "off_together.csv"
    num_days_off_per_week = 2
    main(dirty_worker_preferences_file_name, 
         clean_worker_preferences_file_name, 
         manager_preferences_file_name, 
         num_days_off_per_week,
         not_off_together_file=not_off_together_file,
         off_together_file=off_together_file)