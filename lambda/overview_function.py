"""Handles the event that a `GET: /overview` request is received.

This gets and returns information for an overview of the user's budget.
"""

import os

from configparser import ConfigParser
from utils import datatier, auth, api_utils


def lambda_handler(event, context):
    """Gets an overview of the user's budget.

    Args:
        event (dict): A JSON representation of the HTTP request.
        context (lambda context object): Provides information about the invocation,
            function, and runtime environment.

    Returns:
        dict: The success response containing `sum`, `top_3`, `begin_range`, and
            `end_range` or an error response.
    """
    try:
        print("**STARTING**")
        print("**Lambda: Overview**")

        #
        # Setup AWS based on config file.
        #
        config_file = "lambda-config.ini"
        os.environ["AWS_SHARED_CREDENTIALS_FILE"] = config_file

        configur = ConfigParser()
        configur.read(config_file)

        #
        # Configure for RDS access
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
        # Read month and year from the event body.
        #
        if "queryStringParameters" not in event:
            return api_utils.error(400, "no query parameters in request")

        month = int(event["queryStringParameters"]["month"])
        year = str(event["queryStringParameters"]["year"])
        end_date = ""

        match month:
            case 1 | 3 | 5 | 7 | 8 | 10 | 12:
                end_date = "31"
            case 4 | 6 | 9 | 11:
                end_date = "30"
            case 2:
                if int(year) % 4 == 0:
                    end_date = "29"
                else:
                    end_date = "28"

        month = "{0:0=2d}".format(month)
        begin_range = year + "-" + month + "-01"
        end_range = year + "-" + month + "-" + end_date

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

        #
        # 1st Query: Sum of transactions for that month
        # 2nd Query: 3 most expensive transactions
        #
        query_1 = """
        SELECT SUM(cost)
        FROM transactions
        WHERE userid = %s
        AND date(transactiondate) >= %s
        AND date(transactiondate) <= %s;
        """

        query_2 = """
        SELECT name, cost, transactiondate
        FROM transactions
        WHERE userid = %s
        AND date(transactiondate) >= %s
        AND date(transactiondate) <= %s
        ORDER BY cost DESC
        LIMIT 3;
        """

        res_1 = datatier.retrieve_one_row(
            db_conn, query_1, [userid, begin_range, end_range]
        )
        res_2 = datatier.retrieve_all_rows(
            db_conn, query_2, [userid, begin_range, end_range]
        )
        top_3 = []

        if res_1 == ():
            res_1 = [0]
        if res_2 == []:
            res_2 = "No transactions found!"
        else:
            for row in res_2:
                transaction = (row[0], row[1], str(row[2]))
                top_3.append(transaction)
        #
        # Respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format.
        #
        print("**DONE, returning sum and top three transactions**")
        return api_utils.success(
            200,
            {
                "sum": res_1[0],
                "top_3": top_3,
                "begin_range": begin_range,
                "end_range": end_range,
            },
        )

    except Exception as err:
        print("**ERROR**")
        print(str(err))

        return api_utils.error(500, str(err))
