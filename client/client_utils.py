"""Supplies utility classes and functions for client functions.

Classes:

    * user - represents a budget app user
    * transaction - represents a budget app transaction

Functions:

    * handle_error - handles an error from a request
    * valid_date - checks if the given date is valid
    * calculate_remainder - calculates remainding budget
"""

import requests

from datetime import datetime


class User:
    """A budget app user."""

    def __init__(self, row):
        """Creates a new user object.

        Args:
            row (tuple): Contains information about a user.
        """
        self.userid = row[0]
        self.username = row[1]
        self.pwdhash = row[2]


class Transaction:
    """A budget app transaction."""

    def __init__(self, row):
        """Creates a new transaction object.

        Args:
            row (tuple): Contains information about a transaction.
        """
        self.name = row[0]
        self.cost = row[1]
        self.date = row[2]


def handle_error(url: str, res: requests.Response):
    """Formats an error response from a request.

    Args:
        url (str): The API url related to the request.
        res (requests.Response): The response from the failed request.

    Returns:
        None
    """
    print("Failed with status code:", res.status_code)
    print("  url:", url)
    print("  message:", res.json()["message"])


def valid_date(year: str, month: str, day: str):
    """Checks if the given date is valid.

    Args:
        year (str): The year.
        month (str): The month.
        day (str): The day.

    Returns:
        bool: True if the date is valid, otherwise false.
    """
    try:
        datetime(int(year), int(month), int(day))
        return True
    except Exception as _:
        return False


def calculate_remainder(totalbudget: float, spent: float):
    """Calculates and prints the remaining budget.

    Args:
        totalbudget (int): The total budget.
        spent (int): The amount of the budget that's been spent.
    """
    remainder = totalbudget - spent
    percentage = spent / totalbudget * 100

    print(f"   Remaining Budget: ${remainder}")
    if percentage > 100:
        print("   WARNING: You've overspent on your budget!")
    elif percentage >= 75:
        print("   NOTICE: You've spent at least 75% of your budget!")
    elif percentage >= 50:
        print("   NOTICE: You've spent at least 50% of your budget!")
