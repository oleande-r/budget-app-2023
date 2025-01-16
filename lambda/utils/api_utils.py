"""Supplies utility functions for API Gateway Lambda functions.

Original author:
    Dilan Nair
    Northwestern University

Edited by:
    Lior Thornton

Functions:

    * success - creates a RESTful success response
    * error - creates an RESTful error response
"""

import json


def success(status_code: int, body: dict):
    """Creates a success response.

    Args:
        status_code (int): The response status code to return.
        body(dict): The response body to return.

    Returns:
        dict: The success response:

    Raises:
        ValueError: An invalid status_code value was given.

    """
    if status_code < 200 or status_code >= 300:
        raise ValueError("Only success status codes should be used (2XX).")

    return {
        "statusCode": status_code,
        "body": json.dumps(body),
    }


def error(status_code: int, message: str):
    """Creates an error response.

    Args:
        status_code (int): The response status code to return.
        message (str): The response message to return.

    Returns:
        dict: The error response.

    Raises:
        ValueError: An invalid status_code value was given.

    """
    if status_code < 400 or status_code >= 600:
        raise ValueError("Only error status codes should be used (4XX or 5XX).")

    print("**ERROR**")
    print(message)

    return {
        "statusCode": status_code,
        "body": json.dumps(
            {
                "message": message,
            }
        ),
    }
