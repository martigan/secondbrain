# Chain of thoughts


## Basic implementation

### Modelisation

I added the creator in the Task model and created_at/updated_at to have more info and to apply filter on tasks queries based on user. In a multi tenant environment, one should not access data from others.
I plan on to add an organization system if I have time.
created_at might be redundant with uuid (datetime of creation is stored in it) but I find it more readable and easier for filtering which I plan to do later, having a computated field might lead to performance issue on very large dataset without pagination

The user model is strictly minimal for this exercice, in a production environment, some fields may be useful to add (last_login for example) and some more endpoint to handle password reset and more.


## Pagination

Given the context, I implemented a cursor based pagination over a limit+offset one
- large dataset
- very changing dataset


## Filtering

I chose to have advanced operators to be able to filter with multiple status which may be practical if we want to filter the to be done tasks (new, running and paused) for example

I chose a flat suffix params syntax which I find readable.

Indexes may not be the best, depending on volume, we might need to work on this (trigram on lower(title) for example insensitive case search is very expensive)
