# cardinal

## wsgi.py

At a high level, `wsgi.py` is the web server whose responsibilities include: \
    - Wait for computation requests from chamberlain. If a computation request is received \
    via the `/submit` endpoint, cardinal does the following: \
        1. Check if a job with this name is already running (via a lookup in the `RUNNING_JOBS` table). \
        2. Construct an Orchestrator object if this job doesn't already exist, and add it to the `RUNNING_JOBS` \
        table. \
    - Handle POST requests from other cardinal servers with information about which IP address they will \
    attaching to the pod they generate. If a request is received via the `/api/submit_ip_address` endpoint, \
    cardinal does the following: \
        1. Check if a job with this name is running (via a lookup in the `RUNNING_JOBS` table). \
        2. If this job is running, it will edit the table on the orchestrator object for this entry which \
        stores the IP addresses of other pods in the computation with the data from the request. \
    - Handle POST requests from compute pods when they complete a computation. If a request is received via \
    the `/api/workflow_complete` endpoint, cardinal does the following: \
        1. Check if a job with this name is running (via a lookup in the `RUNNING_JOBS` table). \
        2. If this job is running, it will remove the job from the `RUNNING_JOBS` table. \


The contents of this API are just a rough sketch and there isn't much error handling or anything like that. \
We'll eventually want the `RUNNING_JOBS` table to be an actual DB, and for it to store some kind of state, \
so that state can be queried by chamberlain if an analyst wants to ask how a job is going.


## cardinal/orchestrator.py

The `Orchestrator` class is just initialized with a workflow request, resolves which cloud environment handler \
to use, and launches a `ComputeParty` object.


## cardinal/compute_party.py

The `ComputeParty` class is responsible for generating and launching all configuration files and kubernetes objects. \
The main entrypoints for the class are the `build_all()` and `launch_all()` methods, which build objects and launch \
objects, respectively. 


## Notes

You'll likely need to load authentication data so that you can use cloud provider APIs, so that you can pass \
them to the generated pods (since the pods themselves will need to download data from some cloud storage and \
push computation outputs back to some other cloud storage using the curia library). I think EC2 just stores \
this data in the environment when you launch an instance, I'm not sure. \

(disclaimer) I haven't tested any of this code, it's all just a sketch of cardinal's architecture. 