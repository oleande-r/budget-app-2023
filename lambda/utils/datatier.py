"""Executes SQL queries against a MySQL database.

Original Author:
    Joe Hummel
    Northwestern University

Edited By:
    Lior Thornton

This file contains the following functions:
    * get_dbConn: returns a connection object for MySQL database
    * retrieve_one_row: returns first row retrieved by a given query
    * retrieve_all_rows: returns all rows retrieved by a given query
    * perform_action: executes an SQL action query
"""

import pymysql


def get_db_conn(endpoint: str, portnum: int, username: str, pwd: str, dbname: str):
    """Opens and returns a connection object for interacting with a MySQL database.

    Args:
        endpoint (str): The machine name or IP address of server.
        portnum (int): The server port number.
        username (str): The user name for login.
        pwd (str): The user password for login.
        dbname (str): The database name.

    Returns:
        Connection[Cursor]: A database connection object.

    Raises:
        Exception: Attempt to connect to database failed.
    """
    try:
        db_conn = pymysql.connect(
            host=endpoint, port=portnum, user=username, passwd=pwd, database=dbname
        )

        return db_conn
    except Exception as err:
        print("datatier.get_dbConn() failed:")
        print(str(err))
        raise


def retrieve_one_row(db_conn, sql, parameters: list[object] = []):
    """Executes a SQL SELECT query against the database connection.

    Args:
        db_conn (Connection[Cursor]): The database connection object.
        sql (str): The SQL SELECT query, which can be parameterized with %s.
        parameters (list[object], optional): List of values if the query was
            paramterized. Defaults to [].

    Returns:
        tuple | (): First row as a tuple, or an empty tuple if SELECT retrieves no data.

    Raises:
        Exception: Attempt to retrieve data failed.
    """
    db_cursor = db_conn.cursor()

    try:
        db_cursor.execute(sql, parameters)
        row = db_cursor.fetchone()
        # If row is none, the query was successfully executed but no data was retrieved.
        if row is None:
            return ()
        else:
            return row
    except Exception as err:
        print("datatier.retrieve_one_row() failed:")
        print(str(err))
        raise
    finally:
        db_cursor.close()


def retrieve_all_rows(db_conn, sql, parameters: list[object] = []):
    """Executres a SQL SELECT query against the database connection.

    Args:
        db_conn (Connection[Cursor]): The database connection object.
        sql (str): The SQL select query, which can be parameterized with %s.
        parameters (list[object], optional): List of values if the query was
            paramaterized. Defaults to [].

    Returns:
        tuple | []: All rows as a list of tuples, or an empty list if SELECT
            retrieves no data.

    Raises:
        Exception: Attempt to retrieve data failed.
    """
    db_cursor = db_conn.cursor()

    try:
        db_cursor.execute(sql, parameters)
        rows = db_cursor.fetchall()
        # If row is none, the query was successfully executed but no data was retrieved.
        if rows is None:
            return ()
        else:
            return rows
    except Exception as err:
        print("datatier.retrieve_all_rows() failed:")
        print(str(err))
        raise
    finally:
        db_cursor.close()


def perform_action(db_conn, sql, parameters: list[object] = []):
    """Executes a SQL ACTION query against the database connection.

    Args:
        db_conn (Connection[Cursor]): The database connection object.
        sql (str): The SQL SELECT query, which can be parameterized with %s.
        parameters (list[object], optional): List of values if the query was
            paramaterized. Defaults to [].

    Returns:
        int: The number of rows modified.

    Raises:
        Exception: Attempt to perform action failed.
    """
    db_cursor = db_conn.cursor()

    try:
        db_cursor.execute(sql, parameters)
        db_conn.commit()
        return db_cursor.rowcount
    except Exception as err:
        db_conn.rollback()
        print("datatier.perform_action() failed:")
        print(str(err))
        raise
    finally:
        db_cursor.close()
