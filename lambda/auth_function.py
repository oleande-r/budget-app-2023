"""A lambda function that handles the event that a `POST: /auth` request is received.

This authenticates a user attempting to login.
"""
import json
import os

from configparser import ConfigParser
from utils import datatier, auth, api_utils

SECRET = "hidden"


def lambda_handler(event, context):
    """Processes the event that a `POST: /auth` request is received.

    Args:
        event (object): A JSON-formatted document to process.
        context (object): Provides information about the invocation, function, and
            runtime environment.

    Returns:
        dict: The success response containing an `access_token` or an error response
            containing an error.
    """
    try:
        print("**STARTING**")
        print("**Lambda: Authentication**")

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
        # Read the username and password from the event body.
        #
        print("**Accessing request body**")

        if "body" not in event:
            return api_utils.error(400, "no body in request")

        body = json.loads(event["body"])

        if "username" not in body or "password" not in body:
            return api_utils.error(400, "missing credentials in body")

        username = body["username"]
        password = body["password"]

        #
        # open connection to the database
        #
        print("**Opening connection**")

        db_conn = datatier.get_db_conn(
            rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname
        )

        sql = """
        SELECT *
        FROM users
        WHERE username = %s;
        """
        row = datatier.retrieve_one_row(db_conn, sql, [username])
        if row == ():
            return api_utils.error(404, "no such user")

        sql = """
        SELECT pwdhash
        FROM users
        WHERE username = %s;
        """
        pwdhash = datatier.retrieve_one_row(db_conn, sql, [username])[0]
        if not auth.check_password(password, pwdhash):
            return api_utils.error(401, "password incorrect")

        sql = """
        SELECT userid
        FROM users
        WHERE username = %s;
        """
        row = datatier.retrieve_one_row(db_conn, sql, [username])
        userid = row[0]
        token = auth.generate_token(userid, SECRET)

        #
        # respond in an HTTP-like way, i.e. with a status
        # code and body in JSON format:
        #
        print("**DONE, returning token**")

        return api_utils.success(200, {"access_token": token})

    except Exception as err:
        print("**ERROR**")
        print(str(err))

        return api_utils.error(500, str(err))
