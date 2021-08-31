# cardinal

Please check the wiki of this repo for detailed instructions for setting up the cardinal-chamberlain system. Below is a a quick description of the main components of the repo.

## wsgi.py

At a high level, `wsgi.py` is the web server whose responsibilities include:
- Waiting for POST requests from chamberlain to start computations
- Interacting with a database storing dataset locations (along with other internally used tables)
- Waiting for POST requests from computation pods to terminate workflows (this should clean up all resources - pods, services, configmaps, etc. - that were used for a particular workflow)


## cardinal/orchestrator

The `Orchestrator` class is just initialized with a workflow request, resolves which cloud environment handler to use, and launches a `Party` object.


## cardinal/party

The `Party` class is responsible for generating and launching all configuration files and kubernetes objects. The main entrypoints for the class are the `prepare_all()` and `launch_all()` methods, which build objects and launch objects, respectively. 

## cardinal/handlers

The `Handlers` class is responsible for interacting with the different cloud providers. The subclasses can be modified to include whatever API calls to the different cloud providers that are needed.

## cardinal/database

This set of classes represents the tables in the cardinal database and contains all the queries that are available to perform on the database.

The remaining scripts and files are addressed in the wiki.
