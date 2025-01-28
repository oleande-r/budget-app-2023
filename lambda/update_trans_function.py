"""Handles the event that a `POST: /update/.` request is received.

This updates the specified transaction or recurring payment.
"""

import json
import os

from configparser import ConfigParser
from utils import datatier, auth, api_utils


def lambda_handler(event, context):
    """Updates the specified transaction.

    Args:
        event (dict): A JSON representation of the HTTP request.
        context (lambda context object): Provides information about the invocation,
            function, and runtime environment.

    Returns:
        dict: The success response containing `id` or an error response.
    """
    try:
        print("**STARTING**")
        print("**Lambda: Update Transaction/Recurring Payment**")

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
        # Read the token from the event headers.
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
        # Find out what we're updating.
        #
        if "body" not in event:
            return api_utils.error(400, "no body in request")

        body = json.loads(event["body"])

        if "updating" not in body:
            return api_utils.error(400, "not specified what to update")

        table = body["table"]
        updating = body["updating"]
        trans_id = body["id"]
        old_info = ""
        new_info = ""
        cost_category = ""
        cost = ""
        column = ""

        if table == "transactions":
            column = "transactionid"
        else:
            column = "paymentid"

        if "new-name" in body:
            new_info = body["new-name"]
        elif "new-cost" in body:
            old_info = body["old-cost"]
            new_info = body["new-cost"]
            cost_category = body["category"]
        elif "new-category" in body:
            old_info = body["old-category"]
            new_info = body["new-category"]
            cost = body["cost"]
        elif "new-date" in body:
            new_info = body["new-date"]
        else:
            return api_utils.error(400, "no column given to update")

        #
        # Open connection to the database.
        #
        print("**Opening connection**")
        db_conn = datatier.get_db_conn(
            rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname
        )

        print("**Checking if userid is valid and getting current spent**")
        row = ""
        row2 = ""

        if updating == "category":
            sql1 = """
            SELECT spent
            FROM categories
            WHERE userid = %s
            AND category = %s
            """
            sql2 = """
            SELECT spent
            FROM categories
            WHERE userid = %s
            AND category = %s
            """
            row = datatier.retrieve_one_row(db_conn, sql1, [userid, old_info])
            row2 = datatier.retrieve_one_row(db_conn, sql2, [userid, new_info])
        elif updating == "cost":
            sql = """
            SELECT spent
            FROM categories
            WHERE userid = %s
            AND category = %s
            """
            row = datatier.retrieve_one_row(db_conn, sql, [userid, cost_category])
        else:
            sql = """
            SELECT *
            FROM categories
            WHERE userid = %s
            """
            row = datatier.retrieve_one_row(db_conn, sql, [userid])

        if row == ():  # no such user
            print("**No such user, returning...**")
            return api_utils.error(404, "no such user")

        #
        # Update table.
        #
        query_1 = """
        UPDATE """ + table + """
        SET """ + updating +""" = %s
        WHERE """ + column + """ = %s;
        """

        datatier.perform_action(db_conn, query_1, [new_info, trans_id])

        if updating == "category" and table != "recurringpayments":
            old_cat_spent = row[0]
            new_cat_spent = row2[0]

            old_cat_spent -= cost
            new_cat_spent += cost

            query_2 = """
            UPDATE categories
            SET spent = %s
            WHERE category = %s;
            """
            query_3 = """
            UPDATE categories
            SET spent = %s
            WHERE category = %s;
            """

            datatier.perform_action(db_conn, query_2, [old_cat_spent, old_info])
            datatier.perform_action(db_conn, query_3, [new_cat_spent, new_info])

        if updating == "cost" and table != "recurringpayments":
            updated_spent = float(row[0]) - float(old_info) + float(new_info)

            query_4 = """
            UPDATE categories
            SET spent = %s
            WHERE category = %s;
            """

            datatier.perform_action(db_conn, query_4, [updated_spent, cost_category])

        #
        # Respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format.
        #
        print("**DONE, returning sum and top three transactions**")
        return api_utils.success(200, {"id": trans_id})

    except Exception as err:
        print("**ERROR**")
        print(str(err))

        return api_utils.error(500, str(err))
