"""Handles the event that a `GET: /query` request is received.

This gets and returns the queried information.
"""

import os

from configparser import ConfigParser
from utils import datatier, auth, api_utils


def lambda_handler(event, context):
    """Queries information from the database.

    Query uses a path parameter {args} to specify a table to query from. Supported args
    are 'categories', 'transactions', or 'recurringpayments', for which query returns
    all rows in the specified table whose userid matches the id of the user who called
    query.

    Args:
        event (dict): A JSON representation of the HTTP request.
        context (lambda context object): Provides information about the invocation,
            function, and runtime environment.

    Returns:
        dict: The success response containing `rows` or an error response.
    """
    try:
        print("**STARTING**")
        print("**Lambda: Query**")

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
        # Read the arguments from the event body.
        #
        if "args" in event:
            args = event["args"]
        elif "pathParameters" in event:
            if "args" in event["pathParameters"]:
                args = event["pathParameters"]["args"]
            else:
                return api_utils.error(400, "no args in pathParameters")
        else:
            return api_utils.error(400, "no args in event")

        split_args = args.split(",")

        if len(split_args) > 1:
            return api_utils.error(
                400, "Implement functionality for query with more than one argument"
            )

        type = args

        #
        # Open connection to the database.
        #
        print("**Opening connection**")
        db_conn = datatier.get_db_conn(
            rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname
        )

        print("**Checking if userid is valid**")
        sql = "SELECT * FROM users WHERE userid = %s;"
        row = datatier.retrieve_one_row(db_conn, sql, [userid])

        if row == ():  # no such user
            print("**No such user, returning...**")
            return api_utils.error(404, "no such user")

        if type not in ["categories", "transactions", "recurringpayments"]:
            return api_utils.error(500, "Invalid query type")

        sql = """
        SELECT *
        FROM """ + type + """
        WHERE userid = %s
        """

        rows = datatier.retrieve_all_rows(db_conn, sql, [userid])

        #
        # Respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format.
        #
        print("**DONE**")
        return api_utils.success(200, {"rows": rows})

    except Exception as err:
        print("**ERROR**")
        print(str(err))

        return api_utils.error(500, str(err))
