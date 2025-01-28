"""Handles the event that a `POST: /create/transaction` request is received.

This creates a transaction for the specified user.
"""

import json
import os

from configparser import ConfigParser
from utils import datatier, auth, api_utils


def lambda_handler(event, context):
    """Creates a new transaction for the current user.

    Args:
        event (dict): A JSON representation of the HTTP request.
        context (lambda context object): Provides information about the invocation,
            function, and runtime environment.

    Returns:
        dict: The success response containing `total_budget` and `spent` or an error
            response.
    """
    try:
        print("**STARTING**")
        print("**Lambda: Create Transaction**")

        #
        # Setup AWS based on config file.
        #
        config_file = "lambda-config.ini"
        os.environ["AWS_SHARED_CREDENTIALS_FILE"] = config_file

        configur = ConfigParser()
        configur.read(config_file)

        #
        # Configure for RDS access.
        #
        rds_endpoint = configur.get("rds", "endpoint")
        rds_portnum = int(configur.get("rds", "port_number"))
        rds_username = configur.get("rds", "user_name")
        rds_pwd = configur.get("rds", "user_pwd")
        rds_dbname = configur.get("rds", "db_name")
        secret = configur.get("secret", "key")

        #
        # Read the transaction information from the event body.
        #
        print("**Accessing request body**")

        if "body" not in event:
            return api_utils.error(400, "no body in request")

        body = json.loads(event["body"])

        if "cost" not in body or "category" not in body or "date" not in body:
            return api_utils.error(400, "missing cost, category, or date")

        if "headers" not in event:
            return api_utils.error(400, "no headers in request")

        headers = event["headers"]
        token: str = auth.get_token_from_header(headers)  # type: ignore

        if token is None:
            api_utils.error(401, "no bearer token in headers")

        try:
            userid = auth.get_user_from_token(token, secret)
        except Exception as _:
            return api_utils.error(401, "invalid access token: " + token)

        name = body["name"]
        cost = body["cost"]
        category = body["category"]
        date = body["date"]

        #
        # Open connection to the database.
        #
        print("**Opening connection**")
        db_conn = datatier.get_db_conn(
            rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname
        )

        print("**Checking if userid is valid**")
        sql = """
        SELECT totalbudget, spent
        FROM categories
        WHERE userid = %s
        AND category = %s;
        """
        row = datatier.retrieve_one_row(db_conn, sql, [userid, category])

        if row == ():  # no such user
            print("**No such user, returning...**")
            return api_utils.error(404, "no such user")

        totalbudget = row[0]
        spent = row[1] + cost

        sql1 = """
        INSERT INTO transactions (userid, name, cost, category, transactiondate)
        VALUES (%s,%s, %s, %s, %s)
        """

        sql2 = """
        UPDATE categories
        SET spent = %s
        WHERE userid = %s
        AND category = %s
        """

        datatier.perform_action(db_conn, sql1, [userid, name, cost, category, date])
        datatier.perform_action(db_conn, sql2, [spent, userid, category])

        #
        # Respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format.
        #
        print("**DONE, returning token**")
        return api_utils.success(200, {"totalbudget": totalbudget, "spent": spent})

    except Exception as err:
        print("**ERROR**")
        print(str(err))

        return api_utils.error(500, str(err))
