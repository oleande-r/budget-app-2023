"""Handles the event that a `POST: /delete/.` request is received.

This deletes a category, transaction, or recurring payment.
"""

import json
import os

from configparser import ConfigParser
from utils import datatier, auth, api_utils


def lambda_handler(event, context):
    """Deletes a specified category, transaction, or recurring payment.

    Args:
        event (dict): A JSON representation of the HTTP request.
        context (lambda context object): Provides information about the invocation,
            function, and runtime environment.

    Returns:
        dict: The success response containing an `id` or an error response.
    """
    try:
        print("**STARTING**")
        print("**Lambda: Delete**")

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
        # Find out what's being deleted.
        #
        if "body" not in event:
            return api_utils.error(400, "no body in request")

        body = json.loads(event["body"])
        table = event["pathParameters"]["args"]
        column = ""
        delete = ""
        update = ""
        trans_cost = 0

        if "category" in body:
            delete = body["category"]
            column = "category"
        elif "new-category" in body:
            delete = body["old-category"]
            update = body["new-category"]
            column = "category"
        elif "cost-category" in body:
            update = body["cost-category"]
            delete = body["id"]

            if "trans-cost" in body:
                column = "transactionid"
                trans_cost = body["trans-cost"]
            else:
                column = "paymentid"
        else:
            return api_utils.error(400, "unspecified delete request")

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

        if "new-category" in body:
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
            row = datatier.retrieve_one_row(db_conn, sql1, [userid, delete])
            row2 = datatier.retrieve_one_row(db_conn, sql2, [userid, update])
        elif "trans-cost" in body:
            sql = """
            SELECT spent
            FROM categories
            WHERE userid = %s
            AND category = %s
            """
            row = datatier.retrieve_one_row(db_conn, sql, [userid, update])
        else:
            sql = """
            SELECT spent
            FROM categories
            WHERE userid = %s
            """
            row = datatier.retrieve_one_row(db_conn, sql, [userid])

        if row == ():  # no such user
            print("**No such user, returning...**")
            return api_utils.error(404, "no such user")

        #
        # Delete
        #
        query_1 = """
        DELETE FROM """ + table + """
        WHERE """ + column + """ = %s;
        """

        datatier.perform_action(db_conn, query_1, [delete])

        if "new-category" in body:
            new_cat_spent = row2[0] + row[0]

            query_2 = """
            UPDATE categories
            SET spent = %s
            WHERE category = %s;
            """
            query_3 = """
            UPDATE transactions
            SET category = %s
            WHERE category = %s
            AND userid = %s;
            """
            datatier.perform_action(db_conn, query_2, [new_cat_spent, update])
            datatier.perform_action(db_conn, query_3, [update, delete, userid])
        if "trans-cost" in body:
            updated_spent = row[0] - trans_cost

            query_4 = """
            UPDATE categories
            SET spent = %s
            WHERE category = %s;
            """
            datatier.perform_action(db_conn, query_4, [updated_spent, update])

        #
        # Respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format.
        #
        print("**DONE**")
        return api_utils.success(200, {"id": userid})

    except Exception as err:
        print("**ERROR**")
        print(str(err))

        return api_utils.error(500, str(err))
