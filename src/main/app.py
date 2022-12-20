from dotenv import dotenv_values
from splitwise import Splitwise
from splitwise.expense import Expense, ExpenseUser

config = dotenv_values(".env")
consumer_key = config["CONSUMER_KEY"]
consumer_secret = config["CONSUMER_SECRET"]
api_key = config["API_KEY"]
test_obj = Splitwise(
    consumer_key,
    consumer_secret,
    api_key=api_key,
)

# current_user = test_obj.getFriends()
# for friend in current_user:
#     print(f"{friend.getFirstName()}: {friend.getId()}")

expense = Expense()
expense.setCost("10.0")
expense.setDescription("Testing")
user1 = ExpenseUser()
user1.setId(11796737)
user1.setPaidShare("10.0")
user1.setOwedShare("2.0")
user2 = ExpenseUser()
user2.setId(14976236)
user2.setPaidShare("0.0")
user2.setOwedShare("8.0")
expense.addUser(user1)
expense.addUser(user2)
nExpense, errors = test_obj.createExpense(expense)
print(nExpense.getId())


def placeholder():
    return "Hello"


# script for cleaning & transforming csv

# script for using transformed csv

# clean and transform csv

# Return list of friends

# Return group

# Choose a friend to share expenses with

# Choose a group under which it comes --> optional

# Iterate through a csv --> Date, Amount, Description, Group

# Create expenses --> Bulk upload (group (optional), share ratio) or refer each
# expense
