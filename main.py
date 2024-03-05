"""
Will Nearn 
4 March 2024
Assignment Problem Example
based off of example in https://developers.google.com/optimization/assignment/assignment_example, but modified for my understanding
"""
import pandas as pd
import numpy as np
import warnings
from ortools.linear_solver import pywraplp

def print_preference_sums(preferences):
    """Prints sum of rows if a row sums to anything but 1"""
    rownum = 0
    for row in preferences:
        if abs(sum(row) - 1) > 0.005: #floating point error
            print("Row "+str(rownum)+"'s sum is "+str(sum(row))+": "+str(row))
        rownum += 1


def cleanWorkerFile(worker_file_name, cleaned_file_name, manager_file_name):
    # worker_file_name:
    #  - Is a downloaded Google Sheet, where everyone can only edit the page with their name on it
    #  - Should be filled out as "0" for jobs that the worker can't do 
    #  - Should contain (0,1] for jobs that the worker can do, where 1 means that they really want to do that job on that day
    # cleaned_file_name will be the location of the cleaned version of the file stored at `worker_file_name`
    # manager_file_name should be identical to the worker preferences file except the data points are made by the managers

    # CONFIGUREABLE
    unable_score = 0
    high_score = 1 # Anything higher than this will be reset to this
    low_reset_score = np.float64(0.3) #Any score at or below unable_score for a task that a worker is able to do will be reset to this
    
    worker_file = pd.read_excel(worker_file_name, sheet_name=None, index_col=0)
    manager_file = pd.read_excel(manager_file_name, sheet_name=None, index_col=0)

    for name in worker_file.keys():
        wdf = worker_file[name] #Extract <name>'s page
        mdf = manager_file[name]
        if wdf.shape != mdf.shape or not wdf.columns.equals(mdf.columns) or not wdf.index.equals(mdf.index):
            print(f"There's an error on the formatting of {name}'s schedule in {worker_file_name}, either with the row names or the column names -- go check it out")
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
        for name, df in worker_file.items():
            df.to_excel(writer, sheet_name=name)
    return True
    

def main():
    dirty_worker_preferences_file_name = "worker_preferences.xlsx"
    clean_worker_preferences_file_name = "cleaned_worker_preferences.xlsx"
    manager_preferences_file_name = "manager_preferences.xlsx"
    if not cleanWorkerFile(dirty_worker_preferences_file_name, 
                    clean_worker_preferences_file_name, 
                    manager_preferences_file_name):
        print("\nThere was an error in cleaning up the file. Please investigate. Exiting out of the program. Please re-run this program after fixing the data")
        return
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
    """
    day_preferences = [  #Rows are workers, columns are jobs
        # KL, HTO, HTC, Field
        [0.6, 0.2, 0.1, 0.1], #Amber
        [0.0, 0.3, 0.3, 0.4], #Nearn
        [0.0, 0.1, 0.2, 0.7], #Rob
        [0.8, 0.1, 0.1, 0.0], #Elinor
        [0.1, 0.5, 0.3, 0.1], #Mariam
    ]
    sunday_preferences = [
        # KL, HTO, HTC, Field
        [0.0, 0.0, 0.0, 0.0], #Amber
        [0.0, 0.0, 0.0, 0.0], #Nearn
        [0.0, 0.0, 0.0, 0.0], #Rob
        [0.0, 0.0, 0.0, 0.0], #Elinor
        [0.0, 0.0, 0.0, 0.0], #Mariam
    ]

    week_preferences = [day_preferences, #EVERYTHING SHOULD BE BASED OFF OF week_preferences FROM HERE ON OUT. NO MENTIONING day_preferences OR sunday_preferences
                        day_preferences,
                        day_preferences,
                        day_preferences,
                        day_preferences,
                        day_preferences,
                        sunday_preferences]
    
    for day in week_preferences: #Check for errors
        print_preference_sums(day)"""
    
    num_workers = len(week_preferences)
    num_jobs = len(week_preferences[0])
    num_days = len(week_preferences[0][0])
    num_days_off_per_week = 3 #CONFIGUREABLE

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP") #Not sure what SCIP is

    if not solver:
        return
    
    # assignment_matrix[d, w, j] is an array of 0-1 variables, which will be 1
    # if worker w is assigned to task j on day d.
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
            sol = [assignment_matrix[w, j, d] for w in range(num_workers)]
            print(sol)
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
            print("Good solution found.")
        print(f"Total Happiness = {solver.Objective().Value()}\n")
        data = {} #For the output DataFrame
        for d in range(num_days):
            print(f"\n\t---- {day_names[d]} ----")
            day_assignments = {day_names[d] : ["NOBODY" for _ in range(num_jobs)]}
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