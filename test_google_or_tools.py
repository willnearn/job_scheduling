"""
Will Nearn 
4 March 2024
Assignment Problem Example
based off of example in https://developers.google.com/optimization/assignment/assignment_example, but modified for my understanding
"""

from ortools.linear_solver import pywraplp

def print_preference_sums(preferences):
    """Prints sum of rows if a row sums to anything but 1"""
    rownum = 0
    for row in preferences:
        if abs(sum(row) - 1) > 0.005: #floating point error
            print("Row "+rownum+"'s sum is "+sum(row)+": "+row)
        rownum += 1


def main():
    preferences = [  #Rows are workers, columns are jobs
        # KL, HTO, HTC, Field
        [0.6, 0.2, 0.1, 0.1], #Amber
        [0.0, 0.3, 0.3, 0.4], #Nearn
        [0.0, 0.1, 0.2, 0.7], #Rob
        [0.8, 0.1, 0.1, 0.0], #Elinor
        [0.1, 0.5, 0.3, 0.1], #Mariam
    ]
    print_preference_sums(preferences)
    num_workers = len(preferences)
    num_jobs = len(preferences[0])

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP") #Not sure what SCIP is

    if not solver:
        return
    
    # assignment_matrix[i, j] is an array of 0-1 variables, which will be 1
    # if worker i is assigned to task j.
    assignment_matrix = {}
    for w in range(num_workers):
        for j in range(num_jobs):
            assignment_matrix[w, j] = solver.IntVar(0, 1, "")
    
    # Each worker is assigned to at most 1 task.
    for w in range(num_workers):
        solver.Add(solver.Sum([assignment_matrix[w, j] for j in range(num_jobs)]) <= 1)

    # Each task is assigned to at most one worker.
    for j in range(num_jobs):
        solver.Add(solver.Sum([assignment_matrix[w, j] for w in range(num_workers)]) <= 1)
    
    # Objective function. TODO: Change this to reflect my own objective function
    objective_terms = []
    for i in range(num_workers):
        for j in range(num_jobs):
            objective_terms.append(preferences[i][j] * assignment_matrix[i, j])
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
        for i in range(num_workers):
            for j in range(num_jobs):
                # Test if assignment_matrix[i,j] is 1 (with tolerance for floating point arithmetic).
                if assignment_matrix[i, j].solution_value() > 0.5:
                    print(f"Worker {i} assigned to task {j}." + f" Happiness: {preferences[i][j]}")
    else:
        print("No solution found.")



if __name__ == "__main__":
    main()