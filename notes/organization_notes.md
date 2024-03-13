# Job Scheduling
## Goal
- Automate scheduling for a small-to-medium business to minimize the time scheduling
  
## Problem Statement
- Score schedule "goodness" as a function of manager preferences and worker preferences
- Don't assign workers to jobs for which they're unfit
- Each worker has a default of 2 days off (changeable)
- Each worker can only do 1 job per day
  
### Getting a little more mathematically formalized:
- `w` workers need to be scheduled
- `j` jobs need to be filled on any given day
- `f` free days are allotted per employee per week
- 3D "goodness" matrix of dimensions `j`x`d`x`w` represents the value of the "goodness" function if that worker is at that job on that day
- Constraint: for each `j`x`d`, only choose 1 `w`
- Constraint: "goodness" must be 0 or negative for workers unfit for jobs
- Constraint: "goodness" must be positive for workers fit for a job
- Constraint: 2 days off per worker per M-Sa
- Constraint: each worker can only do one job in a day
- Maximize goodness for the week's schedule
- Avoid using brute force methods (time complexity is something like a factorial on another factorial I think)

## Current State
### Complete
- Input manager happiness and worker happiness separately + combine them into a "happiness table"
- Given a `d`x`w`x`j` "happiness table" and the number of days that each worker has off per week, it'll generate the optimal schedule with the following constraints:
  - No more than one worker per job per day (if you want multiple in a day, you can do something like Field1, Field2, Field3 are all separate jobs
  - No more than one job per worker per day
  - Workers have a default number of days off per week, but this can be adjusted by populating their name and the number of days off that they get in manager_preferences.xlsx's `days_off` page
  - Workers can specify that they want to be off with someone / don't want to be off with someone
    - This can over-define the problem very quickly. It's recommended that workers accomplish this on their preferences (by e.g. setting both folks's Tuesday preferences down to the lowest setting in order to get the day off together) instead of making this a hard constraint whenever possible
- Output decisions onto a schedule in a .csv
- Feature: Allow workers to specify days that they want off -- This will be solved by the preference table:
  - For approved requests, management will put in 0s for that worker for that day
  - For unapproved requests, workers can just put in low values for those days
- Tested with more complete data
- Write instructions

  
### TODO
- Test with real-life data
- Look into/address potential bug adding people to the schedule with a score of 0


## Brett Meeting Notes
- Catch case for people requesting off days way into the future ==> Make a Preferences spreadsheet for each week, and just update it as you get requests
- Tracking training is helpful ==> Can do this in the manager_preferences.xlsx spreadsheet. Start off with 0s everywhere, and as they get training, fill it out with non-zero numbers
- When switching shifts, don't switch into a training shift ==> Company culture + the Scheduling groupme will take care of this
- Bunch people together in field ==> Done on the manager_preferences.xlsx file. The default that I gave it bunches people together on Tuesday, or potentially Wednesday
- Friday and Saturday off in the field ==> Done on the manager_preferences.xlsx file. You just put 0s for everyone those days
- Make worker end dates ==> This is handled in the week-to-week manager_preferences.xlsx file. If someone ends mid-week next week,
  1. Make a new manager_preferences spreadsheet for that week
  2. Put 0s for the days that they won't be in town
  3. Adjust their days off for that week by adding their name to manager_preferences.xlsx's `days_off` page

## Notes
- Helpful:
  - [Google OR-Tools](https://developers.google.com/optimization/introduction/python)
  - [Assignment Problem](https://developers.google.com/optimization/assignment)
  - [Assignment Example](https://developers.google.com/optimization/assignment/assignment_example)
  - [Google OR-Tools Docs](https://or-tools.github.io/docs/python/classortools_1_1linear__solver_1_1pywraplp_1_1Solver.html)
