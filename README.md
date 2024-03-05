# Job Scheduling
## Goal
- Automate scheduling for a small-to-medium business to minimize the time scheduling
  
## Problem Statement
- Score schedule "goodness" as a function of manager preferences and worker preferences
- Don't assign workers to jobs for which they're unfit
- Each worker has a default of 2 days off (changeable)
- Each worker can only do 1 job per day
- Allow workers to switch with each other (pending manager approval?) after initial schedule is made
  
### Getting a little more mathematically formalized:
- `w` workers need to be scheduled
- `j` jobs need to be filled on any given day
- `f` free days are allotted per employee per week
- 3D "goodness" matrix of dimensions `j`x`d`x`w` represents the value of the "goodness" function if that worker is at that job on that day
- Constraint: for each `j`x`d`, only choose 1 `w`
- Constraint: "goodness" must be 0 or negative for workers unfit for jobs
- Constraint: "goodness" must be positive for workers fit for a job
- Constraint: No values in the final "goodness" matrix can be 0 or negative (indicating that an unfit worker was chosen for a job)
- Constraint: 2 days off per worker per M-Sa
- Constraint: each worker can only do one job in a day
- Maximize goodness for the week's schedule
- Avoid using brute force methods (time complexity is something like a factorial on another factorial)

## Current State
### Complete
- Input manager happiness and worker happiness separately + combine them into a "happiness table"
- Given a `d`x`w`x`j` "happiness table" and the number of days that each worker has off per week, it'll generate the optimal schedule with the following constraints:
  - No more than one worker per job per day (if you want multiple in a day, you can do something like Field1, Field2, Field3 are all separate jobs
  - No more than one job per worker per day
  - Workers have `num_days_off_per_week` days off per week
- Output decisions onto a schedule in a .csv

  
### TODO
- Test with more complete data
- Feature: Allow workers to specify days that they want off
- Feature: Allow workers to specify that they want to have a different number of days off
- Feature: Allow workers to specify that they want to be off together on certain days (TBD-- may be too complex)
- Take in data more smoothly
- Feature: allow workers to trade off which days they're working

## Notes
- [PuLP](https://coin-or.github.io/pulp/)
- [Google OR-Tools](https://developers.google.com/optimization/introduction/python)
