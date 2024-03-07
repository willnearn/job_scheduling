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


def cleanWorkerFile(worker_file_name,
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


def main():
    # CONFIGUREABLE
    dirty_worker_preferences_file_name = "worker_preferences.xlsx"
    clean_worker_preferences_file_name = "cleaned_worker_preferences.xlsx"
    manager_preferences_file_name = "manager_preferences.xlsx"
    not_off_together_file = "not_off_together.csv"
    off_together_file = "off_together.csv"
    num_days_off_per_week = 2
    unable_score = 0 # If a worker gives this score, that indicates that they can't do the given task -- days off should be given in the manager preferences Excel worksheet
    high_score = 10 # Anything higher than this will be reset to this
    low_reset_score = np.int64(3) #Any score at or below unable_score for a task that a worker is able to do will be reset to this

    # Clean up data
    if not cleanWorkerFile(dirty_worker_preferences_file_name, 
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
    for w in range(num_workers):
        solver.Add(solver.Sum([assignment_matrix[w, j, d] for d in range(num_days) for j in range(num_jobs)]) <= (num_days - num_days_off_per_week))

    # Constraint: People who don't want to be off together won't be off together
    for index, row in not_off_together_df.iterrows():
        first_person = not_off_together_df.iloc[index, 0] #Get people's names
        second_person = not_off_together_df.iloc[index, 1]
        w1 = worker_names.index(first_person) # Convert people's names into indices
        w2 = worker_names.index(second_person)
        for d in range(num_days):
            solver.Add(  solver.Sum( assignment_matrix[w1, :, d]+assignment_matrix[w2, :, d] )  >= 1) # Constrain at least one of them to be on during a given day, therefore they aren't off together

    # Constraint: People who do want to be off together will always be off together
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
        print("No solution found.")



if __name__ == "__main__":
    main()