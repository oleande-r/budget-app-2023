"""Contains functions for querying the server.

Functions:

    * query - queries for a specified database table
    * get_users - prints all users in the database
    * find_transaction - allows the user to find a specific transaction
    * find_recurring_payment - allows the user to find a specific payment
    * overview - prints out an overview of the user's budget
    * print_transactions - prints out all transactions for the given user
    * print_recurring_payments - prints out all payments for the given user
    * print_categories - prints out all budget categories for the given user
"""

import requests

from datetime import datetime

from client_utils import calculate_remainder, handle_error, Transaction, User
from main import get_active_session


def query(baseurl, type):
    """Queries the server for a specified database table.

    Args:
        baseurl (str): The base url for web service.
        type (str): The type being queried. Can be 'categories', 'transactions', or
            'recurringpayments'.

    Returns:
        list: The queried rows.
    """
    api = f"/query/{type}"
    url = baseurl + api
    _, token = get_active_session()
    res = requests.get(url, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return []

    body = res.json()
    return body["rows"]


def get_users(baseurl: str):
    """Prints out all the users in the database.

    Args:
        baseurl (str): The base url for web service.

    Returns:
        None
    """
    #
    # Call the web service:
    #
    api = "/users"
    url = baseurl + api
    res = requests.get(url)

    if not res.ok:
        handle_error(url, res)
        return

    #
    # Deserialize and extract users:
    #
    body = res.json()

    #
    # Map each row into a User object:
    #
    users = []
    for row in body:
        user = User(row)
        users.append(user)

    if len(users) == 0:
        print("no users...")
        return

    for user in users:
        print(user.userid)
        print(" ", user.username)
        print(" ", user.pwdhash)

    return


def find_transaction(baseurl):
    """Queries the server to allow the user to select a specific transaction.

    Args:
        baseurl (str): The base url for the web service.

    Returns:
        None
    """
    rows = query(baseurl, "transactions")

    if len(rows) == 0:
        print("You haven't created any transactions yet.")
        return []

    transaction_name = ""
    transaction_cost = 0
    transaction_category = ""
    transaction_date = ""

    print("")
    existing_transaction = []
    count = 0

    for i, row in enumerate(rows):
        if count == 6:
            print("")
            print("Continue seeing transactions? -> y/n")
            answer = input()
            if answer == "y":
                print("")
                count = 0
            else:
                break

        transaction_id = row[0]
        transaction_name = row[2]
        transaction_cost = row[3]
        transaction_category = row[4]
        transaction_date = row[5]

        print(f"   {i + 1} => {transaction_name}")
        print(f"        Cost: {transaction_cost}")
        print(f"        Category: {transaction_category}")
        print(f"        Date: {transaction_date}")

        existing_transaction.append(
            [
                transaction_id,
                transaction_name,
                transaction_cost,
                transaction_category,
                transaction_date,
            ]
        )
        count += 1

    print("")
    print("Select a transaction>")
    transaction_index = int(input())

    while transaction_index not in range(1, len(existing_transaction)):
        print(
            f"Invalid transaction number, please enter a number between 1 and {len(existing_transaction) - 1}"
        )

        for i, x in enumerate(existing_transaction):
            if i == 0:
                continue

            print("")
            print(f"   {i} => {existing_transaction[i][1]}")
            print(f"        Cost: {existing_transaction[i][2]}")
            print(f"        Category: {existing_transaction[i][3]}")
            print(f"        Date: {existing_transaction[i][4]}")
        transaction_index = int(input())

    transaction = existing_transaction[transaction_index]
    return transaction


def find_recurring_payment(baseurl):
    """Queries the server to allow the user to select a specific recurring payment.

    Args:
        baseurl (str): The base url for web service.

    Returns:
        None
    """
    rows = query(baseurl, "recurringpayments")

    if len(rows) == 0:
        print("You haven't created any recurring payments yet.")
        return []

    payment_name = ""
    payment_cost = 0
    payment_category = ""
    payment_date = ""

    print("")
    existing_payment = []
    count = 0

    for i, row in enumerate(rows):
        if count == 6:
            print("")
            print("Continue seeing payments? -> y/n")
            answer = input()
            if answer == "y":
                print("")
                count = 0
            else:
                break

        payment_id = row[0]
        payment_name = row[1]
        payment_cost = row[4]
        payment_category = row[3]
        payment_date = row[5]

        print(f"   {i + 1} => {payment_name}")
        print(f"        Cost: {payment_cost}")
        print(f"        Category: {payment_category}")
        print(f"        Date: {payment_date}")

        existing_payment.append(
            [payment_id, payment_name, payment_cost, payment_category, payment_date]
        )
        count += 1

    print("")
    print("Select a recurring payment>")
    payment_index = int(input())

    while payment_index not in range(1, len(existing_payment)):
        print(
            f"Invalid payment number, please enter a number between 1 and {len(existing_payment) - 1}"
        )

        for i, x in enumerate(existing_payment):
            if i == 0:
                continue

            print("")
            print(f"   {i} => {existing_payment[i][1]}")
            print(f"        Cost: {existing_payment[i][2]}")
            print(f"        Category: {existing_payment[i][3]}")
            print(f"        Date: {existing_payment[i][4]}")

        payment_index = int(input())

    payment = existing_payment[payment_index]
    return payment


def overview(baseurl):
    """Prints a summary of all financial information for the month.

    Args:
        baseurl (str): The base url for web service.

    Returns:
        None
    """
    api = "/overview"
    url = baseurl + api
    _, token = get_active_session()

    print("Enter year you'd like an overview for (YYYY)>")
    year = int(input())

    if year > datetime.now().year:
        print("Invalid year")
        return

    print("Enter month you'd like an overview for (DD)>")
    month = int(input())

    if month < 0 or month > 12:
        print("Invalid month")
        return

    query = "?year=" + str(year) + "&month=" + str(month)
    url = url + query
    res = requests.get(url, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    body = res.json()
    sum = body["sum"]
    top_3 = body["top_3"]
    begin_range = body["begin_range"]
    end_range = body["end_range"]
    count = 0

    if sum is None:
        print("")
        print("No transactions found for given year and month.")
        return

    transactions = []
    for row in top_3:
        transaction = Transaction(row)
        transactions.append(transaction)

    print("")
    print(
        "Here is an overview of your purchases for "
        + begin_range
        + " -> "
        + end_range
        + ":"
    )
    print("")
    print("Total Expenditures:")
    print("   $" + str(sum))
    print(
        "Most Expensive Transactions:",
    )
    for transaction in transactions:
        count += 1

        print("   Name:", transaction.name)
        print("   Cost: $", transaction.cost)
        print("   Date:", transaction.date)

        if count < len(transactions):
            print("")
    return


def print_transactions(baseurl):
    """Prints out all transactions for the current user.

    Args:
        baseurl (str): The base url for web service.
    """
    rows = query(baseurl, "transactions")
    transactions = []
    count = 0

    if len(rows) == 0:
        print("You have no recorded transactions.")
        return

    for row in rows:
        transaction = [row[2], row[3], row[4], row[5]]
        transactions.append(transaction)

    print("")
    print("Here are all of your recorded transactions:")
    for transaction in transactions:
        if count == 6:
            print("")
            print("Continue seeing transactions? -> y/n")
            answer = input()

            if answer == "y":
                print("")
                count = 0
            else:
                break

        print("")
        print("Name:", transaction[0])
        print("   Cost: $" + str(transaction[1]))
        print("   Category:", transaction[2])
        print("   Date:", transaction[3])
        count += 1

    return


def print_recurring_payments(baseurl):
    """Prints out all recurring payments for the current user.

    Args:
        baseurl (str): The base url for web service.
    """
    rows = query(baseurl, "recurringpayments")
    payments = []
    count = 0

    if len(rows) == 0:
        print("You have no recorded recurring payments.")
        return

    for row in rows:
        payment = [row[1], row[4], row[3], row[5]]
        payments.append(payment)

    print("")
    print("Here are all of your recorded recurring payments:")
    for payment in payments:
        if count == 6:
            print("")
            print("Continue seeing payments? -> y/n")
            answer = input()
            if answer == "y":
                print("")
                count = 0
            else:
                break

        print("")
        print("Name:", payment[0])
        print("   Cost: $" + str(payment[1]))
        print("   Category:", payment[2])
        print("   Date:", payment[3])

        count += 1

    return


def print_categories(baseurl):
    """Prints out all categories for the current user.

    Args:
        baseurl (str): The base url for web service.
    """
    rows = query(baseurl, "categories")
    categories = []
    count = 0

    for row in rows:
        category = [row[1], row[3], row[4]]
        categories.append(category)

    print("")
    print("Here are all of your budget categories:")
    for category in categories:
        if count == 6:
            print("")
            print("Continue seeing categories? -> y/n")
            answer = input()
            if answer == "y":
                print("")
                count = 0
            else:
                break

        print("")
        print("Name:", category[0])

        if category[0] == "Uncategorized":
            print("   Total Spent: $" + str(category[2]))
        else:
            print("   Total Budget: $" + str(category[1]))
            print("   Total Spent: $" + str(category[2]))
            calculate_remainder(category[1], category[2])

        count += 1

    return
