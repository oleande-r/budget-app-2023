"""The client-side python app for the budget application.

Authors:
    Sean Carlson
    Northwestern University

    Lior Thornton
    Northwestern University
"""

import requests
import json
import pathlib
import logging
import sys
import os

import alter
import create
import query
import remove

from client_utils import handle_error
from configparser import ConfigParser

SESSIONS = {}
STATE = "logged out"


def log_out():
    """Updates the state to `logged out`."""
    global STATE
    STATE = "logged out"


def add_new():
    """Updates the state to `add new`."""
    global STATE
    STATE = "add new"


def update():
    """Updates the state to `update`."""
    global STATE
    STATE = "update"


def delete():
    """Updates the state to `delete`."""
    global STATE
    STATE = "delete"


def back():
    """Updates the state to the previous state."""
    global STATE
    match STATE:
        case "add new":
            STATE = "logged in"
        case "update":
            STATE = "logged in"
        case "delete":
            STATE = "logged in"
        case _:
            print("TODO")


def load_sessions():
    """Loads the previous sessions from the sessions.json file.

    Args:
        None

    Returns:
        None
    """
    global SESSIONS
    if os.path.exists("sessions.json"):
        with open("sessions.json", "r") as f:
            SESSIONS = json.load(f)


def get_active_session():
    """Returns the active session.

    Args:
        None

    Returns:
        None
    """
    global SESSIONS
    for username in SESSIONS:
        if SESSIONS[username]["active"]:
            return username, SESSIONS[username]["token"]
    return None, None


def use_session(username: str):
    """Sets the session with the given username to active.

    Args:
        username (str): The user's username.

    Returns:
        None
    """
    global SESSIONS
    for session in SESSIONS:
        SESSIONS[session]["active"] = False
    SESSIONS[username]["active"] = True
    with open("sessions.json", "w") as f:
        json.dump(SESSIONS, f, indent=2)


def update_session(username: str, token: str):
    """Updates the session with the given username and token.

    Args:
        username (str): The user's username.
        token (str): The user's access_token.

    Returns:
        None
    """
    global SESSIONS
    SESSIONS[username] = {"token": token, "active": False}

    use_session(username)


def clear_sessions():
    """Clears all sessions.

    Args:
        None

    Returns:
        None
    """
    global SESSIONS
    SESSIONS = {}
    with open("sessions.json", "w") as f:
        json.dump(SESSIONS, f, indent=2)


def reset_everything(baseurl: str):
    """Resets the database back to initial state and clears all sessions.

    Args:
        baseurl (str): The base url for the web service.

    Returns:
        None
    """
    clear_sessions()

    api = "/reset"
    url = baseurl + api
    res = requests.delete(url)

    if not res.ok:
        handle_error(url, res)
        return

    body = res.json()
    msg = body

    print(msg)
    return


def login(baseurl: str, username: str | None = None, password: str | None = None):
    """Log in as a user.

    Args:
        baseurl (str): The base url for the web service.
        username (str | None): The given username.
        password (str | None): The given password.

    Returns:
        None
    """
    if username is None:
        print("Enter username>")
        username = input()

        print("Enter password>")
        password = input()

    data = {"username": username, "password": password}

    api = "/auth"
    url = baseurl + api
    res = requests.post(url, json=data)

    if not res.ok:
        handle_error(url, res)
        return

    body = res.json()
    token = body["access_token"]

    print("")
    print("User logged in, username =", username)

    #
    # Update sessions:
    #
    update_session(username, token)
    global STATE
    STATE = "logged in"
    return


def prompt() -> int:
    """Prompts the user and returns the command number.

    Args:
        None

    Returns:
        int: Command number entered by user (0, 1, 2, ...)
    """
    print()
    print(">> Enter a command:")
    print("")
    global STATE
    match STATE:
        case "logged out":
            print("You are logged out")
            print("   1 => add user")
            print("   2 => log in")
            print("   3 => get all users")
            print("   4 => reset all users and budgets")
        case "logged in":
            print("You are logged in")
            print("   1 => add new budget category, transaction, or recurring payment")
            print("   2 => update budget category, transaction, or recurring payment")
            print("   3 => delete budget category, transaction, or recurring payment")
            print("   4 => overview of monthly spending")
            print("   5 => view transactions")
            print("   6 => view recurring payments")
            print("   7 => view categories")
            print("   8 => get all users")
            print("   9 => log out")
        case "add new":
            print("Add something to your budget")
            print("   1 => create new budget category")
            print("   2 => add new transaction")
            print("   3 => add new recurring payment")
            print("   4 => go back")
        case "update":
            print("Update your budget")
            print("   1 => update a budget category")
            print("   2 => update a transaction")
            print("   3 => update a recurring payment")
            print("   4 => go back")
        case "delete":
            print("Delete something from your budget")
            print("   1 => delete a budget category")
            print("   2 => delete a transaction")
            print("   3 => delete a recurring payment")
            print("   4 => go back")
        case _:
            print("\n\nTODO\n\n")

    print("   0 => quit")
    cmd = input()

    if cmd == "" or not cmd.isnumeric():
        cmd = -1
    else:
        cmd = int(cmd)

    return cmd


def main():
    """The main function of the budget application."""
    try:
        print("** Welcome to BudgetApp **")
        print()

        # Eliminate traceback so we just get error message:
        sys.tracebacklimit = 0

        config_file = "budgetapp-client-config.ini"

        print("Config file to use for this session?")
        print("Press ENTER to use default, or")
        print("enter config file name>")
        s = input()

        if s == "":  # Use default
            pass
        else:
            config_file = s

        if not pathlib.Path(config_file).is_file():
            print("**ERROR: config file '", config_file, "' does not exist, exiting")
            sys.exit(0)

        #
        # Setup base URL to web service:
        #
        configur = ConfigParser()
        configur.read(config_file)
        baseurl = configur.get("client", "webservice")

        if len(baseurl) < 16:
            print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
            sys.exit(0)

        if baseurl == "https://api-id.execute-api.region.amazonaws.com/stage":
            print(
                "**ERROR: update budgetapp-client-config.ini file with your gateway endpoint"
            )
            sys.exit(0)

        lastchar = baseurl[len(baseurl) - 1]
        if lastchar == "/":
            baseurl = baseurl[:-1]

        #
        # Load previous sessions:
        #
        load_sessions()

        #
        # Main processing loop:
        #
        cmd: int = prompt()

        logged_out_fns = [
            None,
            create.add_user,
            login,
            query.get_users,
            reset_everything,
        ]
        logged_in_fns = [
            None,
            add_new,
            update,
            delete,
            query.overview,
            query.print_transactions,
            query.print_recurring_payments,
            query.print_categories,
            query.get_users,
            log_out,
        ]
        add_new_fns = [
            None,
            create.create_new_budget_category,
            create.add_new_transaction,
            create.add_new_recurring_payment,
            back,
        ]
        update_fns = [
            None,
            alter.update_budget_category,
            alter.update_transaction,
            alter.update_recurring_payment,
            back,
        ]
        delete_fns = [
            None,
            remove.delete_budget_category,
            remove.delete_transaction,
            remove.delete_recurring_payment,
            back,
        ]

        fn = ""
        try:
            while cmd != 0:
                match STATE:
                    case "logged out":
                        fns = logged_out_fns
                    case "logged in":
                        fns = logged_in_fns
                    case "add new":
                        fns = add_new_fns
                    case "update":
                        fns = update_fns
                    case "delete":
                        fns = delete_fns
                    case _:
                        print("TODO")
                        break

                if cmd < 0 or cmd >= len(fns):
                    print("** Unknown command, try again...")
                    cmd = prompt()
                    continue
                fn = fns[cmd]
                if fn is None:
                    break
                fn(baseurl)
                cmd = prompt()
        except Exception as e:
            logging.error(fn.__name__ + "() failed:")  # type: ignore
            logging.error(e)

        print()
        print("** done **")
        sys.exit(0)

    except Exception as e:
        logging.error("**ERROR: main() failed:")
        logging.error(e)
        sys.exit(0)


main()
