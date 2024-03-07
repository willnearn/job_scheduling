# Job Scheduling
This repo will help automate the schedule-making process at Heavenly Hawaiian Coffee Farm
# Overview:
- Workers rate each of the jobs that they can work 1-10 for each day of the week
- Managers rate each of the workers on which jobs they want them to fill for each day of the week
- Workers can specify a different number of off days that they want
- Workers can also specify that they want to be off with someone / don't want to be off with someone during the week (although this is discouraged; it can overdefine the problem, which means that there's no solution)
- The user pops these preferences into the program, and the program pops out the best schedule possible
  - Unless the problem is overdefined, this will be the optimal solution. If it "doesn't look right," tweak the inputs to get a result that looks better for ya

# Setup -- Required Software
**TODO-- Write this down when getting Brett setup**

# Quickstart
TODO
### Default Values for Manager Preferences
TODO
### How to Get People Off Together / Not Off Together
TODO
### How to adjust an individual's days off per week
TODO
### Pitfalls and Standards
TODO
### How to run the program
TODO

# Getting More Technical
- This is a repo on GitHub under the user `willnearn` and the repo name `job_scheduling`
- The way that the program combines worker preference with management preference is simple multiplication, and it optimizes the product. So if Sally rates her preference of working in Konalani on Monday as a 7, and management rates Sally working in Konalani as a 9, the total "happiness" that happens if Sally works Konalani on Monday is 7*9=**63**. The algorithm optimizes the overall happiness for everyone for the week given the constraints (e.g. workers can't work multiple jobs in a day, workers need days off, workers are unavailable when they're out of town, etc.)
- Worker preferences will be "floored," meaning that a 5.9 actually comes out as a 5. Manager preferences, however, are not floored. This allows management to make some jobs certainly be filled by setting the management preference for a certain job as an order of magnitude or two higher than a less important job (think: if you *need* to fill jobA, and it would be nice to fill jobB only *after* jobA is filled, and filling jobC is a cherry on top that only should happen after jobA and jobB are filled, you can set the management preference for jobA at 10, the management preference for jobB as 0.99, and the management preference for jobC as 0.09
- TODO
