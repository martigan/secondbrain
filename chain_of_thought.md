# Chain of thoughts


## Basic implementation

### Modelisation

I added the creator in the Task model and created_at/updated_at to have more info and to apply filter on tasks queries based on user. In a multi tenant environment, one should not access data from others.
I plan on to add an organization system if I have time.
created_at might be redundant with uuid (datetime of creation is stored in it) but I find it more readable and easier for filtering which I plan to do later, having a computated field might lead to performance issue on very large dataset without pagination

The user model is strictly minimal for this exercice, in a production environment, some fields may be useful to add (last_login for example) and some more endpoint to handle password reset and more.

