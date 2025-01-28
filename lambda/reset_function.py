"""Handles the event that a `DELETE: /reset` request is received.

Resets the budget app to its default state by deleting all users and all information.
"""

import os

from configparser import ConfigParser
from utils import datatier, api_utils


def lambda_handler(event, context):
    """Clears all tables and resets them to their empty state.

    Args:
        event (dict): A JSON representation of the HTTP request.
        context (lambda context object): Provides information about the invocation,
            function, and runtime environment.

    Returns:
        dict: The success response containing success or an error response.
    """
    try:
        print("**STARTING**")
        print("**Lambda: Reset**")

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

        #
        # Open connection to the database.
        #
        print("**Opening connection**")

        db_conn = datatier.get_db_conn(
            rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname
        )

        #
        # Delete all rows from tables.
        #
        print("**Deleting budget categories**")
        sql = "SET FOREIGN_KEY_CHECKS = 0;"
        datatier.perform_action(db_conn, sql)

        sql = "TRUNCATE TABLE categories;"
        datatier.perform_action(db_conn, sql)

        print("**Deleting users**")
        sql = "TRUNCATE TABLE users;"
        datatier.perform_action(db_conn, sql)

        print("**Deleting transactions**")
        sql = "TRUNCATE TABLE transactions"
        datatier.perform_action(db_conn, sql)

        print("**Deleting recurring payments**")
        sql = "TRUNCATE TABLE recurringpayments;"
        datatier.perform_action(db_conn, sql)

        sql = "SET FOREIGN_KEY_CHECKS = 1;"
        datatier.perform_action(db_conn, sql)

        sql = "ALTER TABLE users AUTO_INCREMENT = 80001;"
        datatier.perform_action(db_conn, sql)

        sql = "ALTER TABLE categories AUTO_INCREMENT = 1;"
        datatier.perform_action(db_conn, sql)

        sql = "ALTER TABLE transactions AUTO_INCREMENT = 1;"
        datatier.perform_action(db_conn, sql)

        sql = "ALTER TABLE recurringpayments AUTO_INCREMENT = 1;"
        datatier.perform_action(db_conn, sql)

        #
        # Respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format.
        #
        print("**DONE, returning success**")
        return api_utils.success(200, {"success": 0})

    except Exception as err:
        print("**ERROR**")
        print(str(err))

        return api_utils.error(500, str(err))
