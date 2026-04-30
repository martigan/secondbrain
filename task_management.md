# Exercise: Building a Simple Task Management API

## Objective:
Design and implement a RESTful API for managing tasks. The API should allow users to create, retrieve, update, and delete tasks. Additionally, implement user authentication to secure the API.

## Requirements:

### User Model:

ID (auto-generated)
email: string with verification
password
created_at

### Task Model:

Define a Task model with the following attributes:
* id (auto-generated): uuid v6 +
* title: textfield
* description: textfield
* due_date: date field in the future 
* status : enum [new, running, complete, error, pause]
* created_by: User
* created_at : Date auto now at creation
* updated_at: Date auto now at update

### API Endpoints:

Implement the following RESTful endpoints using a framework of your choice (e.g., Flask, Express, Django):
* POST /tasks: Create a new task.
* GET /tasks: Retrieve a list of all tasks.
* GET /tasks/{id}: Retrieve details of a specific task by ID.
* PUT /tasks/{id}: Update the details of a specific task.
* DELETE /tasks/{id}: Delete a specific task.

### User Authentication:

* Implement a simple user authentication system using JWT.
* Create endpoints for user registration and login.
* Ensure that task-related endpoints are protected and can only be accessed by authenticated users.

### Validation and Error Handling:

* Implement proper input validation for task creation and update.
* Handle errors gracefully and return meaningful error messages with appropriate HTTP status codes.

### Testing:

* Write unit tests for at least one endpoint.
* Include tests for both successful and unsuccessful scenarios.

## Additional Considerations (Optional):

* Implement pagination for the list of tasks to manage large datasets.
* Add filtering options to retrieve tasks based on status, due date, etc.
* Include sorting options for the list of tasks.
* Use a database of your choice (e.g., SQLite, PostgreSQL) to persist task and user data.

## Submission:
Share the codebase along with a README file explaining how to set up and run the application. Include details on API usage, authentication, and any additional features implemented.

Note:
Feel free to use any programming language, framework, or additional libraries that you are comfortable with. The exercise is designed to assess your skills in API design, database interaction, user authentication, and testing.
