"""
Will Nearn 
4 March 2024
Assignment Problem Example
based off of example in https://developers.google.com/optimization/assignment/assignment_example, but modified for my understanding
"""
import pandas as pd
from ortools.linear_solver import pywraplp

def print_preference_sums(preferences):
    """Prints sum of rows if a row sums to anything but 1"""
    rownum = 0
    for row in preferences:
        if abs(sum(row) - 1) > 0.005: #floating point error
            print("Row "+str(rownum)+"'s sum is "+str(sum(row))+": "+str(row))
        rownum += 1


def main():
    worker_names = ["Amber", "Nearn", "Rob", "Elinor", "Mariam"] #Need to pair this with the input data and extract it
    job_names = ["Konalani", "Hilltop Opener", "Hilltop Closer", "Field"] #Best to pair this with the input data and extract it
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] #I'm fine with this one staying hard-coded
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
        print_preference_sums(day)
    
    num_days = len(week_preferences)
    num_workers = len(week_preferences[0])
    num_jobs = len(week_preferences[0][0])
    num_days_off_per_week = 3 #CONFIGUREABLE

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP") #Not sure what SCIP is

    if not solver:
        return
    
    # assignment_matrix[d, w, j] is an array of 0-1 variables, which will be 1
    # if worker w is assigned to task j on day d.
    assignment_matrix = {}
    for d in range(num_days):
        for w in range(num_workers):
            for j in range(num_jobs):
                assignment_matrix[d, w, j] = solver.IntVar(0, 1, "") #Initialization
    
    # Constraint: Each worker is assigned to at most 1 task per day.
    for d in range(num_days):
        for w in range(num_workers):
            solver.Add(solver.Sum([assignment_matrix[d, w, j] for j in range(num_jobs)]) <= 1)

    # Constraint: Each task is assigned to at most one worker per day.
    for d in range(num_days):
        for j in range(num_jobs):
            sol = [assignment_matrix[d, w, j] for w in range(num_workers)]
            print(sol)
            solver.Add(solver.Sum([assignment_matrix[d, w, j] for w in range(num_workers)]) <= 1)
    
    # Constraint: Each worker only works for num_days - num_days_off_per_week
    for w in range(num_workers):
        solver.Add(solver.Sum([assignment_matrix[d, w, j] for d in range(num_days) for j in range(num_jobs)]) <= (num_days - num_days_off_per_week))

    # Objective function -- a combination of the (double)preference matrix and the (<ortools.linear_solver.pywraplp.Variable>)assignment matrix
    objective_terms = []
    for d in range(num_days):
        for w in range(num_workers):
            for j in range(num_jobs):
                objective_terms.append(week_preferences[d][w][j] * assignment_matrix[d, w, j])
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
            print(f"\n\t---- Day {d} ----")
            day_assignments = {day_names[d] : ["NOBODY" for _ in range(num_jobs)]}
            for w in range(num_workers):
                assigned = False
                for j in range(num_jobs):
                    # Test if assignment_matrix[d,w,j] is 1 (with tolerance for floating point arithmetic).
                    if assignment_matrix[d, w, j].solution_value() > 0.5:
                        print(f"Worker {w} assigned to task {j}." + f" Happiness: {week_preferences[d][w][j]}")
                        day_assignments[day_names[d]][j] = worker_names[w]
                        assigned = True
                if not assigned:
                    print(f"Worker {w} unassigned.")
            data[day_names[d]] = day_assignments[day_names[d]]
        df = pd.DataFrame(data, index=job_names)
        df.to_csv("output.csv", index=True)
    else:
        print("No solution found.")



if __name__ == "__main__":
    main()