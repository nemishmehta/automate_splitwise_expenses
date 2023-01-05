# Automate Splitwise Expenses

This project arose from a personal need to optimize the amount of time I spent on creating expenses on [Splitwise](https://secure.splitwise.com/) (a big portion of it being toggling between my bank account and Splitwise's tabs on my browser and selecting various parameters when creating an expense on Splitwise's interface). So, to reduce the amount of time I've created this tool which is meant to be used as a command line utility.

## Setup

The following pre-requisites are required before using the tool.
1. Clone this repo.
2. Install [Poetry](https://python-poetry.org/docs/#installation) on your local system.
3. Run the following commands:
    - `poetry shell`
    - `poetry install`
4. Create an account on [Splitwise](https://secure.splitwise.com/signup) if you don't have one already. 
5. [Register your application and get your consumer key, secret and API key.](https://secure.splitwise.com/oauth_clients)
6. Navigate to this repo on your local system -> Rename the `.env_template` file to `.env` and paste the `consumer key`, `consumer secret` and `API key` you recieved from Splitwise. 

## Usage

Uploading expenses on Splitwise is a two-phase process. 

### Phase 1
1. In this phase, you will need a csv of all the transactions you would like to upload on Splitwise (can be downloaded from your bank account).
2. We will first clean this csv file and make it ready for the second phase. To clean the file, run the following command on your terminal.
    - `poetry run python src/scripts/run_clean_csv.py <path to the csv file>`
3. Depending on the contents of the file, you will be asked a series of prompts that will be used to clean the csv file.
4. Once the file has been cleaned, it will be stored in the following directory `src/data/clean/` with the following name `<file name>_clean.csv`

### Phase 2
1. In phase two, we will use the cleaned csv file to upload the expenses on Splitwise. 
2. To upload the expenses, run the following command on your terminal.
    - `poetry run python src/scripts/run_upload_expenses.py src/data/clean/<file name>_clean.csv`
3. Just like in phase one, you will be asked a series of prompts that will be used to upload the expense on Splitwise.

#### Note: Currently an expense can only be split between two people.

## To-Do
1. Ability to split expense between more than two people.
2. Full test suite.

## References
1. [Splitwise API](https://dev.splitwise.com/)
2. [Splitwise Python SDK](https://github.com/namaggarwal/splitwise)
