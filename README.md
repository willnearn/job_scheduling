# Job Scheduling
## Goal
- Automate scheduling for a small-to-medium business to minimize the time scheduling
  
## Problem Statement
- Score schedule "goodness" as a function of manager preferences and worker preferences
- Don't assign workers to jobs for which they're unfit
- Each worker has a default of 2 days off (changeable)
- Allow workers to switch with each other (pending manager approval?) after initial schedule is made
- `w` workers need to be scheduled
- `j` jobs need to be filled on any given day
- `f` free days are allotted per employee per week
- Avoid using brute force methods (time complexity is something like a factorial on another factorial)

## Notes
- [PuLP](https://coin-or.github.io/pulp/)
