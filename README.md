# OneRagTimeBills
This program calculates the cash call for the bills generated for each investor.
## Running the program
To run the program. Run ./run.sh
```bash
./run.sh
```
It automatically starts the scripts after installing the necessary libraries
## Cli Usage
```bash
    # press y or n to start the process
    Ready to Create a new bill?

    #Advanced process for chnaging the date of change of membership fess calculation.
    # Usually the answer is n
    Do you want to change settings for membership fees calculation ? [y/n]

    # Groups by investors
    Do you want to group by investor ?

    #Only for dropping data which are implied non vlaidated
    # press n to proceed to next stage without dropping rows
    Ready to drop data which are not validate? [y/n]

    #Next stage generates cash call and random email status list
    # All the results are stored in /db/ as csv and json
```

## Notes
Few things could be improved:
* Better code refactoring
* Calculation of overdue payment left instead of showing the full amount
* All the results are stored in /db/ as csv and json
## Important
If you have installed python and would like to run directly please go to:
```
cd src/
```
And, then
```
python cashcCalls.py
```