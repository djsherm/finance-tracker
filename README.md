# Personal Finance Tracker
This is a tool built to help track, categorize, and visualize your income/expenses to help you gain a better understanding of your spending habits and help with budgeting.

**Main Features**
- Import transactions from your bank to view and edit in an Excel-like table
- Uses ML to autocategorize transactions
- Automatically creates a Sankey chart to visualize the flow of money from any time period

## Prerequisites
1. Requires Python and pip to be installed. Install requirements with `pip install -r requirements.txt`
2. Requires a MongoDB instance to be running locally on your machine. You can install the community edition [here](https://www.mongodb.com/try/download/community).
3. Banks currently supported:
    - RBC

### How Auto-Categorization Works
The ML algorithm works by learning from your previous transactions. Since it is learning solely from your own spending, you will need to start by categorizing your transactions manually, and it will start auto-categorizing new imports once at least 10 transactions have been categorized. With only 10 transactions, new predictions are unlikely to be very accurate, but it will learn and improve over time as you correct the mistakes and build up a large collection of transactions.

You can choose your own categories as you see fit and add new categories at any time. It is suggested to have between 5-12 categories but this is not a requirement. Here's a list of suggested categories:
- Income
- Mortgage/Rent
- Bills
- Car Payment
- Investments
- Food/Drink
- Travel
- Shopping
- Subscriptions
- Misc Spending

## How to Get Transactions from Your Bank
### RBC
1. On the main page of RBC online banking, open your main banking account and click on the *Download* button above the transactions.
2. Check the box beside *Comma Delimited (.csv for Excel, Quattro Pro, Lotus, etc.)*, choose *All Chequing, Savings & Credit Card Accounts* from the dropdown and choose:
    - *All Transactions on File* if you are importing data for the first time. Note that RBC only lets you export the last 3 months of transactions because technology has not yet advanced to the point where it is possible to export more than 3 months of data.
    - *Only New Transactions Since Last Download* if you've already exported data previously.
3. Click *Continue* to get your csv file.

## How to Use App
1. Once all the prereqs are met, clone the repository to a local directory and run `streamlit run Data.py` to start the webapp.
2. Upload the csv you downloaded from you bank using the file uploader.
3. Edit any transactions and add categories, then click the *Update* button.
4. Click on the *Visualize* tab to view your transactions in a Sankey chart. Use the slider to select a date range.