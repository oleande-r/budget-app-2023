"""Contains functions for deleting categories, transactions, and payments.

Functions:

    * delete_budget_category - deletes the specified budget category
    * delete_transaction - deletes the specified transaction
    * delete_recurring_payment - deletes the specified recurring payment
"""

import requests

from client_utils import handle_error
from query import query, find_transaction, find_recurring_payment
from main import get_active_session


def delete_budget_category(baseurl):
    """Deletes the specified budget category.

    Args:
        baseurl (str): The base url for web service.
    """
    new_category_index = 0
    new_category = []
    existing_categories = []
    api = "/delete/categories"
    data = {}

    rows = query(baseurl, "categories")

    print("")
    print("Which category do you want to delete?>")
    for i, row in enumerate(rows):
        category_name = row[1]
        print(f"   {i + 1} => {category_name}")
        existing_categories.append([category_name, row[4]])
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

    if category[0] == "Uncategorized":
        print("You cannot delete this category.")
        return

    if category[1] > 0:
        print("")
        print("This category has transactions associated with it.")
        print(
            "What new category should be used for those transactions after this category is deleted?"
        )

        while new_category_index not in range(1, len(existing_categories)):
            for i, x in enumerate(existing_categories):
                if i == 0 or i == category_index:
                    continue
                print(f"   {i} => {existing_categories[i][0]}")
            new_category_index = int(input())
        new_category = existing_categories[new_category_index]

        data = {"old-category": category[0], "new-category": new_category[0]}
    else:
        data = {"category": category[0]}

    _, token = get_active_session()
    url = baseurl + api
    res = requests.delete(url, json=data, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    print("")
    print(f"Category `{category[0]}` successfully deleted.")
    return


def delete_transaction(baseurl):
    """Deletes the specified transaction.

    Args:
        baseurl (str): The base url for web service.
    """
    api = "/delete/transactions"
    transaction = find_transaction(baseurl)
    data = {
        "id": transaction[0],
        "trans-cost": transaction[2],
        "cost-category": transaction[3],
    }

    _, token = get_active_session()
    url = baseurl + api
    res = requests.delete(url, json=data, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    print("")
    print(f"Transaction `{transaction[1]}` successfully deleted.")
    return


def delete_recurring_payment(baseurl):
    """Deletes the specified recurring payment.

    Args:
        baseurl (str): The base url for web service.
    """
    api = "/delete/recurringpayments"
    payment = find_recurring_payment(baseurl)
    data = {"id": payment[0], "cost-category": payment[4]}

    _, token = get_active_session()
    url = baseurl + api
    res = requests.delete(url, json=data, headers={"Authorization": "Bearer " + token})  # type: ignore

    if not res.ok:
        handle_error(url, res)
        return

    print("")
    print(f"Payment `{payment[1]}` successfully deleted.")
    return
