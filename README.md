# Budget Application 2023

> Developed by Lior Thornton and Sean Carlson

This was a simple, manual budgeting application built utilizing Amazon AWS API Gateway, Lambda, and RDS. Both the client-side application and the lambda functions hosted on AWS were built using Python.

Using the client, a user is able to issue requests to the server via the AWS Web Server and manage their finances through the creation, altering, and deletion of multiple budget categories and financial transactions.

Originally created in 2023, this project is now deprecated and its functioning cannot be guaranteed. Since then, the code has been edited for clarity (better code legibility, inclusion of docstrings, etc.) and this is what has been documented in this repo.

This refactored code has been provided, plus the MySQL script and config files that would allow you to recreate the application in its entirety.

## Architecture

The project was built using a serviceless architecture that was managed by Amazon AWS. A schema of the full service architecture, including the MySQL RDS databases, is depicted below.

![A schema of the project's archietecture](/assets/schema.png "Schema")

## Web Server API Method Requests

The method requests are shown in the schema above. Provided here are more in-depth examples of some of them.

### /create

> Create has sub methods that specify what exactly is being created. One of these is `/create/transaction`, which specifies that a new transaction is being created for the user.

**HTTP Method**: PUT
**Example Response**:

```python
    "statusCode": 200,
    "body": {
        "totalbudget": 250,
        "spent": 0,
        }
```

### /overview

> Overview provides a summary of the user's transactions. This includes the sum of all transaction costs, the top three most expensive transactions, and the specified range from which these transactions were pulled.

**HTTP Method**: GET
**Example Response**:

```python
{
    "statusCode": 200,
    "body": {
        "sum": 120.05,
        "top_3": [
            ('Game', 62.00, 2023-12-12),
            ('Popeyes', 15.05, 2023-12-01),
            ('Movies', 12.00, 2023-12-05)
        ]
        "begin_range": 2023-12-01,
        "end_range": 2023-12-31
        }
}
```

## Improvements

This section is a post-mortem of the project. There were issues I discovered as I was refactoring the code, and this a documentation of some of those issues to consider in future projects.

- Separate the Lambda handler from core logic:
  - Amazon recommends this as best practices when using AWS Lambda. The handler should be pulling relevant information from the event object, and then passing that to another function that handles the rest of the logic.
- Consolidate repeated code
  - There are a lot of places in the lambda functions— like making sure that the body, headers, etc. exist and throwing a bad request error if they do not— that could've been made into separate utility files to import for use. This would've made for cleaner and more legible code.
- The `Users` lambda function should be split into two separate functions that handles `GET` and `POST` separately.
  - Doing this would not only make the code more legible, but it also would've made this particular lambda function more RESTful. As it currently exists, this function handles two different HTTP Methods; that is confusing, especially when no other function does.
