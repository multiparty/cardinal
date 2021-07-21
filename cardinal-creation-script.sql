CREATE TABLE dataset (
    id int,
    dataset_id varchar(150),
    source_bucket varchar(150),
    source_key varchar(150),
    pid int,
    PRIMARY KEY (id)
);
CREATE TABLE workflow (
    source_key varchar(150),
    source_bucket varchar(150),
    operation varchar(150),
    dataset_id varchar(150),
    big_number bit,
    fixed_point bit,
    decimal_digits int,
    integer_digits int,
    negative_number bit,
    zp int
    PRIMARY KEY (source_key)
);
CREATE TABLE pod (
    id int,
    workflow_name varchar(150),
    ip_addr varchar(150),
    pid int,
    PRIMARY KEY (id)
);
CREATE TABLE jiff_server (
    workflow_name varchar(150),
    ip_addr varchar(150),
    PRIMARY KEY (workflow_name)
);