# Fleet Optimization - 128 Business Council Transit Network 🚌🛣️

Optimizing fleet size and routes for efficient transit operations.

## Overview
This project aims to optimize the fleet size and routes for the 128 Business Council Transit Network using integer programming techniques. The optimization models were formulated and solved to minimize the number of buses required (86) and reduce deadheading distance (5704.65m).

## Tools and Technologies
- Python
- CPLEX
- Pandas
- NetworkX
- OSMnx
## Project Structure
```plaintext
.
├── notebooks
│   ├── minbuses.ipynb          # Jupyter notebook with the main project code
├── data
│   ├── 128_Business_Council_GTFS     # Folder containing GTFS dataset
├── output
│   ├── example1.sol           # Solution file for minimizing buses
│   ├── example2.sol           # Solution file for minimizing deadheading distance
├── README.md                  # Project documentation

