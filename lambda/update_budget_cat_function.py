"""Handles the event that a `POST: /update/budget-category` request is received.

This updates the total budget of a given category.
"""

import json
import os

from configparser import ConfigParser
from utils import datatier, auth, api_utils


def lambda_handler(event, context):
    """Updates the total budget of a given category.

    Args:
        event (dict): A JSON representation of the HTTP request.
        context (lambda context object): Provides information about the invocation,
            function, and runtime environment.

    Returns:
        dict: The success response containing `spent` or an error response.
    """
    try:
        print("**STARTING**")
        print("**Lambda: Update Budget Category**")

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
        # Read the token from the event body.
        #
        print("**Accessing request headers**")
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

        #
        # Read budget from the event body.
        #
        if "body" not in event:
            return api_utils.error(400, "no body in request")

        body = json.loads(event["body"])

        if "budget" not in body or "category" not in body:
            return api_utils.error(400, "missing category or new budget")

        budget = body["budget"]
        category = body["category"]

        #
        # Open connection to the database.
        #
        print("**Opening connection**")
        db_conn = datatier.get_db_conn(
            rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname
        )

        print("**Checking if userid is valid and getting current spent**")
        sql = """
        SELECT spent
        FROM categories
        WHERE userid = %s
        AND category = %s
        """
        row = datatier.retrieve_one_row(db_conn, sql, [userid, category])

        if row == ():  # no such user
            print("**No such user, returning...**")
            return api_utils.error(404, "no such user")

        spent = row[0]

        #
        # Update category's totalbudget column.
        #
        query_1 = """
        UPDATE categories
        SET totalbudget = %s
        WHERE userid = %s
        AND category = %s;
        """

        datatier.perform_action(db_conn, query_1, [budget, userid, category])

        #
        # Respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format.
        #
        print("**DONE, returning sum and top three transactions**")
        return api_utils.success(200, {"spent": spent})

    except Exception as err:
        print("**ERROR**")
        print(str(err))

        return api_utils.error(500, str(err))
