"""Handles common authentication tasks.

Original Author:
    Dilan Nair
    Northwestern University

Edited By:
    Lior Thornton

This file contains the following functions:

    * hash_password - creates a password hash using bcrypt
    * check_password - compares password str against a hash
    * generate_token - creates an access token for a given user
    * get_token_from_header - returns token from authorization header
    * get_user_from_token - returns the user of a given token
"""

import datetime

import bcrypt
import jwt


def hash_password(password: str, salt_rounds: int=12):
    """Hashes a password.

    Args:
        password (str): The password to hash.
        salt_rounds (int): The number of rounds of hashing to apply. Defaults to 12.

    Returns:
        str: The hashed password.

    Raises:
        ValueError: Password is too long.
    """
    if len(password) > 72:
        raise ValueError("Password must be less than 72 characters.")

    salt = bcrypt.gensalt(salt_rounds)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    return hashed.decode("utf-8")


def check_password(password: str, hashed: str):
    """Checks a password against a hash.

    Args:
        password (str): The password to check.
        hashed (str): The hash to check against.

    Returns:
        bool: True if the password is correct, False otherwise.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def generate_token(user_id: str, secret: str, exp_minutes: int=60):
    """Generates an access token for a user.

    Args:
        user_id (str): The user's unique ID.
        secret (str): The secret key to encrypt the token with.
        exp_minutes (int): The number of minutes until the token expires. Defaults to 60.

    Returns:
        str: The access token.
    """
    return jwt.encode(
        {
            "user_id": user_id,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=exp_minutes),
        },
        secret,
        algorithm="HS256",
    )


def get_token_from_header(headers: dict):
    """Gets an access token from the Authorization header.

    Args:
        headers (dict): The headers from the request.

    Returns:
        str: The access token.
    """
    if "Authorization" not in headers:
        return None

    auth_header = headers["Authorization"]

    if not auth_header.startswith("Bearer "):
        return None

    return auth_header[7:]


def get_user_from_token(token: str, secret: str):
    """Verifies an access token and gets a user's ID from it.

    An [exception](https://pyjwt.readthedocs.io/en/stable/api.html#exceptions)
    will be raised if the token is invalid.

    Args:
        token (str): The access token.
        secret (str): The secret key to decrypt the token with.

    Returns:
        str: The user's unique ID.
    """
    return jwt.decode(token, secret, algorithms=["HS256"])["user_id"]
