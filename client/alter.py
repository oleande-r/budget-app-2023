"""Contains functions for altering categories, transactions, and payments.

Functions:

    * update_budget_category - updates a given budget category
    * update_transaction - updates a given transaction
    * update_recurring_payment - updates a given recurring payment
"""

import requests

from client_utils import calculate_remainder, handle_error, valid_date
from query import find_recurring_payment, find_transaction, query
from main import get_active_session


def update_budget_category(baseurl: str):
    """Changes the total budget for a given category.

    Args:
        baseurl (str): The base url for web service.

    Returns:
        None
    """
    existing_categories = [None]
    rows = query(baseurl, "categories")

    print("")
    print("Which budget do you want to change?>")
    for i, row in enumerate(rows):
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

    if category == "Uncategorized":
        print("You cannot change this category's budget.")
        return

    print("")
    print("What is the new budget?")
    try:
        budget = float(input())
    except Exception as _:
        print("The budget you entered is not a number.")
        return

    _, token = get_active_session()
    data = {"budget": budget, "category": category}
    api = "/update/budget-category"
    url = baseurl + api
    res = requests.post(url, json=data, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    body = res.json()
    spent = body["spent"]

    print("")
    print(f"Total budget for `{category}` has been updated to ${budget}")
    calculate_remainder(budget, spent)
    return


def update_transaction(baseurl):
    """Updates the specified transaction.

    Args:
        baseurl (str): The base url for web service.

    Returns:
        None
    """
    transaction = find_transaction(baseurl)
    helper(baseurl, "/update/transaction", transaction)
    return


def update_recurring_payment(baseurl):
    """Updates the specified payment.

    Args:
        baseurl (str): The base url for web service.

    Returns:
        None
    """
    payment = find_recurring_payment(baseurl)
    helper(baseurl, "/update/recurring-payment", payment)
    return


def helper(baseurl, api, entry):
    """A helper function that handles the updating of transactions and payments.

    Args:
        baseurl (str): The base url for web service.
        api (str): The corresponding api string for whats being updated.
        entry (array): The payment or transaction that is being updated.

    Returns:
        None
    """
    new_name = ""
    new_cost = 0
    new_category = ""
    new_date = ""
    data = {}
    table = ""

    if "transaction" in api:
        table = "transactions"
    else:
        table = "recurringpayments"

    print("")
    print("What do you want to update?>")
    print("   0 => transaction name")
    print("   1 => transaction cost")
    print("   2 => transaction category")
    print("   3 => transaction date")
    index = int(input())

    match index:
        case 0:
            print("")
            print("What is the new name?>")
            new_name = input()
            if table == "transactions":
                updating = "name"
            else:
                updating = "paymentname"
            data = {
                "updating": updating,
                "new-name": new_name,
                "id": entry[0],
                "table": table,
            }

        case 1:
            print("")
            print("What is the new cost?>")

            try:
                new_cost = float(input())
            except Exception as _:
                print("The cost you entered is not a number.")
                return

            data = {
                "updating": "cost",
                "old-cost": entry[2],
                "new-cost": new_cost,
                "category": entry[3],
                "id": entry[0],
                "table": table,
            }

        case 2:
            print("")
            print("What is the new category?>")
            rows = query(baseurl, "categories")
            existing_categories = [None]

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

            new_category = existing_categories[category_index]
            data = {
                "updating": "category",
                "cost": entry[2],
                "old-category": entry[3],
                "new-category": new_category,
                "id": entry[0],
                "table": table,
            }

        case 3:
            print("")
            date = ""

            print("Enter new year (YYYY)>")
            yr = input()
            while len(yr) != 4:
                print("Please enter a four-digit number.")
                yr = input()
            date += yr + "-"

            print("Enter new month (MM)")
            mo = input()
            while len(mo) != 2:
                print("Please enter a two-digit number.")
                mo = input()
            date += mo + "-"

            print("Enter new day (DD)")
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

            if "transaction" in api:
                updating = "transactiondate"
            else:
                updating = "duedate"

            new_date = date
            data = {
                "updating": updating,
                "new-date": new_date,
                "id": entry[0],
                "table": table,
            }

    _, token = get_active_session()
    url = baseurl + "/update/transaction"
    res = requests.post(url, json=data, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    match index:
        case 0:
            print("")
            print(f"Name successfully changed from `{entry[1]}` to `{new_name}`")
        case 1:
            print("")
            print(f"Cost successfully changed from ${entry[2]} to ${new_cost}")
        case 2:
            print("")
            print(
                f"Category successfully changed from `{entry[3]}` to `{new_category}`"
            )
        case 3:
            print("")
            print(f"Date successfully changed from `{entry[4]}` to `{new_date}`")

    return
