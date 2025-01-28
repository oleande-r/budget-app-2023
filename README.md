# Budget App 2023

Room for Improvement
- Redo the lambda functions to separate the lambda_handler from core logic
- Consolidate repeated code: there are a lot of places in the lambda functions where the checking to make sure that the body, headers, etc. exist could've been make into separate utility files. These files could then be imported and used, making the code within the functions much cleaner.
- Users function should be split into two separate functions that handles "GET" and "POST" separately.