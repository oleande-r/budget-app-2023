"""The functions for creating new users, categories, transactions, and payments.

Functions:

    * add_user - creates a new user for the service app
    * create_new_budget_category - creates a new budget category
    * add_new_transaction - creates a new transaction
    * add_new_recurring_payment - creates a new recurring payment
"""

import requests

from client_utils import calculate_remainder, handle_error, valid_date
from query import query
from main import get_active_session, login


def add_user(baseurl: str):
    """Adds a new user to the database and creates a default budget category for them.

    Args:
        baseurl (str): The base url for the web service.

    Returns:
        None
    """
    print("Enter username>")
    username = input()

    print("Enter password>")
    password = input()

    data = {"username": username, "password": password}

    #
    # Call the web service:
    #
    api = "/users"
    url = baseurl + api
    res = requests.post(url, json=data)

    if not res.ok:
        handle_error(url, res)
        return

    #
    # Success, extract userid:
    #
    body = res.json()
    userid = body["userid"]
    print("User added, id =", userid)
    login(baseurl, username, password)

    _, token = get_active_session()
    data = {"name": "Uncategorized", "budget": None}

    api = "/create/budget-category"
    url = baseurl + api
    res = requests.post(url, json=data, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    print("The default budget category 'Uncategorized' has been created for you.")
    return


def create_new_budget_category(baseurl):
    """Creates a new budget category for the given user.

    Args:
        baseurl (str): The base url for the web service.
    """
    print("Enter category name>")
    name = input()

    print(f"Enter {name} budget>")
    try:
        budget = float(input())
    except Exception as _:
        print("The value you entered is not a number.")
        return

    _, token = get_active_session()

    data = {"name": name, "budget": budget}

    api = "/create/budget-category"
    url = baseurl + api
    res = requests.post(url, json=data, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    right_of_decimal = str(budget).split(".")[1]
    trailing_zero = "0" * (2 - len(right_of_decimal))

    print(f"Added category `{name}` with budget of ${budget}{trailing_zero}")
    return


def add_new_transaction(baseurl):
    """Adds a new transaction for the given user.

    Args:
        baseurl (str): The base url for the web service.
    """
    date = ""
    existing_categories = [None]

    print("Enter transaction name>")
    name = input()

    print("Enter transaction cost>")
    try:
        cost = float(input())
    except Exception as _:
        print("The cost you entered is not a number.")
        return

    rows = query(baseurl, "categories")

    print("To which category does this transaction belong?>")
    for i, row in enumerate(rows):  # type: ignore
        category_name = row[1]
        print(f"   {i + 1} => {category_name}")
        existing_categories.append(category_name)

    category_index = int(input())
    while category_index not in range(1, len(existing_categories)):
        print(
            f"Invalid category number, please enter a number between 1 and {len(existing_categories) - 1}"
        )

        for i, _ in enumerate(existing_categories):
            if i == 0:
                continue
            print(f"   {i} => {existing_categories[i]}")
        category_index = int(input())

    category = existing_categories[category_index]

    print("Enter transaction year (YYYY)>")
    yr = input()
    while len(yr) != 4:
        print("Please enter a four-digit number.")
        yr = input()
    date += yr

    print("Enter transaction month (MM)")
    mo = input()
    while len(mo) != 2:
        print("Please enter a two-digit number.")
        mo = input()
    date += mo

    print("Enter transaction day (DD)")
    day = input()
    while len(day) != 2:
        print("Please enter a two-digit number.")
        day = input()
    date += day

    if valid_date(yr, mo, day):
        pass
    else:
        print("Invalid date entered!")
        return

    _, token = get_active_session()

    data = {"name": name, "cost": cost, "category": category, "date": date}

    api = "/create/transaction"
    url = baseurl + api
    res = requests.post(url, json=data, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    body = res.json()
    right_of_decimal = str(cost).split(".")[1]
    trailing_zero = "0" * (2 - len(right_of_decimal))

    print("")
    print(
        f"Added transaction of ${cost}{trailing_zero} on {yr}-{mo}-{day} in category `{category}`"
    )
    print(f"   Total Spent for {category}: ${body['spent']}")

    if category != "Uncategorized":
        calculate_remainder(body["totalbudget"], body["spent"])
    return


def add_new_recurring_payment(baseurl):
    """Adds a new recurring payment for the current user.

    Args:
        baseurl (str): The base url for the web service.

    Returns:
        None
    """
    date = ""
    existing_categories = [None]

    print("Enter payment name>")
    name = input()

    print("Enter payment cost>")
    try:
        cost = float(input())
    except Exception as _:
        print("The cost you entered is not a number.")
        return

    date = ""
    print("Enter transaction year (YYYY)>")
    yr = input()
    while len(yr) != 4:
        print("Please enter a four-digit number.")
        yr = input()
    date += yr

    print("Enter transaction month (MM)")
    mo = input()
    while len(mo) != 2:
        print("Please enter a two-digit number.")
        mo = input()
    date += mo

    print("Enter transaction day (DD)")
    day = input()
    while len(day) != 2:
        print("Please enter a two-digit number.")
        day = input()
    date += day

    if valid_date(yr, mo, day):
        pass
    else:
        print("Invalid date entered!")
        return

    print("To which category does this transaction belong?>")
    rows = query(baseurl, "categories")

    for i, row in enumerate(rows):  # type: ignore
        category_name = row[1]
        print(f"   {i + 1} => {category_name}")
        existing_categories.append(category_name)
    category_index = int(input())

    while category_index not in range(1, len(existing_categories)):
        print(
            f"Invalid category number, please enter a number between 1 and {len(existing_categories) - 1}"
        )
        for i, x in enumerate(existing_categories):
            if i == 0:
                continue
            print(f"   {i} => {existing_categories[i]}")
        category_index = int(input())
    category = existing_categories[category_index]

    _, token = get_active_session()

    data = {"name": name, "cost": cost, "date": date, "category": category}

    api = "/create/recurring-payment"
    url = baseurl + api
    res = requests.post(url, json=data, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    right_of_decimal = str(cost).split(".")[1]
    trailing_zero = "0" * (2 - len(right_of_decimal))
    print(
        f"Added recurring payment {name} on {yr}-{mo}-{day} for ${cost}{trailing_zero} in category {category}"
    )
    return
