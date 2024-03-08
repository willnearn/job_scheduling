# Job Scheduling
This repo will help automate the schedule-making process at Heavenly Hawaiian Coffee Farm
# Overview:
- Workers rate each of the jobs that they can work 1 (worst) to 10 (best) for each day of the week
- Managers rate each of the workers on which jobs they want the workers to fill for each day of the week
- Workers can specify a different number of off days that they want
- Workers can also specify that they want to be off with someone / don't want to be off with someone during the week (although this is discouraged; it can overdefine the problem, which means that there's no solution)
- The user pops these preferences into the program, and the program pops out the best schedule possible as a file named "output.csv"
  - Unless the problem is overdefined, this will be the optimal solution. If it "doesn't look right," tweak the inputs to get a result that looks better for ya

# Setup -- Required Software
**TODO-- Write this down when getting Brett setup**

# Quickstart
### Default Values for Manager Preferences
I went ahead and set some default values for the manager preferences spreadsheet that I'm gonna hand off to Brett. Here's a list of what worked fairly well as a first cut -- edit it as you see fit. All values are for all people on all days unless noted otherwise
- Tier 1: Imperative
  - Hilltop Opener -- 10
  - Hilltop Closer -- 10
  - Konalani -- 10
  - Paniolos -- 10
  - Tour Guide -- 10
  - Brew Class -- 10
- Tier 2: Important
  - Landscaping -- 4
  - Hilltop Floater -- 5
- Cooper I still love you
  - Hilltop Floater #2 -- 1
  - Field #1, #2, and #3 -- 1 on M/R, 4 on Tuesday, 2.5 on Wednesday, and 0 on F/Sa
- Irregularities and Explanations
  - Field isn't regular because:
    - Brett specified that they're off on F/Sa
    - Brett specified that Hilltop is busy on Mondays, so it gets a low value
    - Brett specified that it's better to have a field *crew* than a field *person*, so I arbitrarily chose Tuesday to be the field crew day
  - Hilltop Floater 1 gets bumped up from a preference of 5 to 10 on M/Sa because Brett said it's busier then
  - Hilltop Floater 2 gets bumped up from a preference of 1 to 3 on M/Sa because Brett said it's busier then
### How to Get People Off Together 
- Open manager_preferences.xlsx
- Create a sheet named "off_together" if it doesn't already exist (this name is required)
- Write "Person1" in cell A1 and "Person2" in cell A2 (or whatever column headers make sense to you; it doesn't really matter as long as something's there)
- Write the names of the people that are gonna be off together in cells A2+B2, A3+B3, etc. until you get to the end of the list of pairs of people that wanna be off together
### How to Get People Not Off Together
- Open manager_preferences.xlsx
- Create a sheet named "not_off_together" if it doesn't already exist (this name is required)
- Write "Person1" in cell A1 and "Person2" in cell A2
- Write the names of the people that are gonna not be off together in cells A2+B2, A3+B3, etc. until you get to the end of the list of pairs of people that don't wanna be off together
### How to adjust an individual's days off per week
- Open manager_preferences.xlsx
- Create a sheet named "days_off" if it doesn't already exist (this name is required)
- Leave A1 empty, and name cell B1 "days off" or give it another name that floats your boat
- Name cell A2 after who wants a different number of days off, and put the different number of days off in cell B2
  - A2 must have the name of the person as it's listed on the name of their spreadsheet tab
### Miscellaneous Pitfalls and Standards
- The column (days) and row (jobs) names for all of the preference sheets on manager_preferences.xlsx *and* worker_preferences.xlsx **must be the same**
- The names of the worker tabs on each preference file **must be the same** (e.g. you can't name Robert's tab on the worker spreadsheet "Robert" and his tab on the management spreadsheet "robert")
- The manager preferences file must be named manager_preferences.xlsx, and it must live in the same folder as main.py
- The worker preferences file must be named worker_preferences.xlsx, and it must live in the same folder as main.py
### How to run the program
- First, make sure that you set up your installation of python as prescribed in the [Setup](https://github.com/willnearn/job_scheduling/blob/main/README.md#setup----required-software) section above
- Then, make sure that your manager_preferences.xlsx and worker_preferences.xlsx have values that fit your wants/needs
- Next, let's run it:
- On Windows:
  - Open up a file explorer
  - Navigate to the folder that holds `main.py`
  - On the bar at the top that holds the file path, click just to the right of the current folder. The whole file path should now be visible, and it should be highlighted in blue
  - Hit `backspace` to erase the file path that shows up there and type `cmd`
  - Hit enter. You are now in the command prompt at the location that holds `main.py`. You can confirm this by typing `dir` and hitting enter. This will show you what files are in the current folder, how much storage they take up, and other fun facts
  - Call python on main.py. Typically, this means typing `python main.py` in the command prompt and hitting `enter`, but sometimes you need to do `python3 main.py` and hit `enter`
- On Macs:
  - `cmd`+`space` to open up the search bar
  - Type in "Terminal" and select it
  - Now you are in a terminal. Navigate to the folder that holds `main.py`. Here are some helpers:
    - `pwd` shows the whole file path that you're at right now
    - `cd` lets you change the folder that you're in (you can do `cd ..` to go back up)
    - `ls` lets you see what all items are in the current folder
  - When you reach the folder that contains `main.py`, type `ls` and hit enter. If main.py shows up, you're there
  - Now call python on main.py. Typically, this means typing `python main.py` in the command prompt and hitting `enter`, but sometimes you need to do `python3 main.py` and hit `enter`

# Getting More Technical
### Going Under the Hood
- All of the required names here can be adjusted if you open up `main.py` in a text editor and search for `def main(`. The hard-coded definitions are below it. Adjust 'em or inspect 'em as you need to. They each have a description of what they're supposed to do by their assignment, so hopefully they're easy to navigate through
- The way that the program combines worker preference with management preference is simple multiplication, and it optimizes the product. So if Sally rates her preference of working in Konalani on Monday as a 7, and management rates Sally working in Konalani as a 9, the total "happiness" that happens if Sally works Konalani on Monday is 7*9=**63**. The algorithm optimizes the overall happiness for everyone over the entire week given the constraints (e.g. workers can't work multiple jobs in a day, workers need days off, workers are unavailable when they're out of town, etc.)
- Worker preferences will be "floored," meaning that a 5.9 actually comes out as a 5. Manager preferences, however, are not floored. This allows management to force some jobs to be filled by setting the management preference for a certain job as an order of magnitude or two higher than a less important job (think: if you *need* to fill jobA, and it would be nice to fill jobB only *after* jobA is filled, and filling jobC is a cherry on top that only should happen after jobA and jobB are filled, you can set the management preference for jobA at 10, the management preference for jobB as 0.99, and the management preference for jobC as 0.09. That way, even if someone rates jobB as 10 and jobA as 1, the "happiness" on jobB (9.9 in this case) will never exceed the "happiness" on jobA (10 in this case)
- Management can keep someone out of a given task/day by rating them as a 0 for that task/day. If you do this like crazy, though, you'll start to see some folks be assigned to things that they've been banned from, though
### What Happens to the Rule-Breakers?
- If a worker or manager puts that their preference for a task is more than the upper limit (currently 10), it gets adjusted back down to the upper limit
- If a worker or manager puts that their preference is a non-numeric value or a negative number, it'll go down as a 0
- If a worker puts that they can't do a task (any non-numeric value or a value less than 1), but the management preferences spreadsheet says that they have been trained to do the task, you'll get a little warning when you're running the program, and their preference value for that job at that date will be adjusted upward to a 3
### Miscellaneous
- This is a repo on GitHub under the user `willnearn` and the repo name `job_scheduling`. This file is online at https://github.com/willnearn/job_scheduling/blob/main/README.md
