CREATE SCHEMA IF NOT EXISTS `cardinal` DEFAULT CHARACTER SET utf8 COLLATE utf8_bin ;
USE `cardinal` ;

CREATE TABLE dataset (
    id int(11),
    dataset_id varchar(150),
    source_bucket varchar(150),
    source_key varchar(150),
    pid int(11),
    PRIMARY KEY (id)
);

CREATE TABLE jiff_server (
    workflow_name varchar(150),
    ip_addr varchar(150),
    PRIMARY KEY (workflow_name)
);

CREATE TABLE pod (
    id int(11),
    workflow_name varchar(150),
    pid int(11),
    ip_addr varchar(150),
    PRIMARY KEY (id)
);
CREATE TABLE pod_event_timestamp (
    id int(11),
    workflow_name varchar(150),
    pid	int(11),
    jiff_server_launched time,
    service_ip_retrieved time,
    exchanged_ips time,
    built_specs_configs time,
    launched_config time,
    launched_pod time,
    pod_succeeded time,
    workflow_stopped time
);

CREATE TABLE pod_resource_consumption (
    id int(11),
    pid int(11),
    workflow_name varchar(1000),
    cpu_usage int(11),
    memory_usage int(11),
    timestamp time
);
