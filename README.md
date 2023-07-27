## Snyk audit to csv

This is a simple CLI app that uses the [pysnyk](https://github.com/snyk-labs/pysnyk) module to load issues from Snyk's audit API, it supports pulling issues down for group and org, along with adding selective filters. By default it looks for all events for the last week (from 8 days ago until yesterday), but that can be changed via flags.

### Building

For easier runtime, you can build this entire project into a docker container:
```
docker build --force-rm -f Dockerfile -t snyk-audit-to-csv:latest .
```

This step is not required if you have `python`, `typer`, `pandas`, and `pysnyk` installed locally.


### Running

To run this script, you need to have a SNYK_TOKEN set if your environment, if you have jq and the snyk cli already installed on your workstation, that can be done quickly with:

```shell
# first authenticate and make sure you have a .config directory
snyk auth

# export your api token from the .config/configstore/snyk.json file
export SNYK_TOKEN=$(jq -r '.api' ~/.config/configstore/snyk.json)
```

With the token set, ensure it is passed to the local container. If you are running from inside this directory, use the file_output directory as a place to deposit the json or csv data. For Snyk Group's we need the full, quoted name of the group, such as `"Customer Success Engineer"`. To get events from a Snyk Organization, we need the shortname, which is found in the URL of the organization's settings page, such as `"cse-ownership"` derived from `https://app.snyk.io/org/cse-ownership/manage/settings`.

```shell
# Group Example
docker run --rm -it -e SNYK_TOKEN -v "${PWD}"/file_output:/runtime snyk-audit-to-csv:latest group "Customer Success Engineering" --json
Total events found: 3214
JSON saved to /runtime/customer_success_engineering_2021-10-11_to_2021-10-18.json

# Org Example
❯ docker run --rm -it -e SNYK_TOKEN -v "${PWD}"/file_output:/runtime snyk-audit-to-csv:latest org cse-ownership --json
Total events found: 1188
JSON saved to /runtime/cse-ownership_2021-10-11_to_2021-10-18.json
```

If running locally rather than through the docker container you can launch the script directly through python:

```shell
# Group example
python main.py group "GroupName Ltd"

# Org Example
python main.py org team-unicorn-org
```

### CSV output

```shell
❯ docker run --rm -it -e SNYK_TOKEN -v "${PWD}"/file_output:/runtime snyk-audit-to-csv:latest org cse-ownership --csv
Total events found: 1188
CSV saved to /runtime/cse-ownership_2021-10-11_to_2021-10-18.csv
```

```shell
❯ python main.py org team-unicorn-org --csv
```

|FIELD1                                                          |groupId|orgId                               |userId                              |event     |content                                                                                                             |created                 |
|----------------------------------------------------------------|-------|------------------------------------|------------------------------------|----------|--------------------------------------------------------------------------------------------------------------------|------------------------|
|0                                                               |36863d40-ba29-491f-af63-7a1a7d79e411|da450e98-1581-4cd1-a4fc-06a3b76f5004|b7f4b234-e888-4054-8532-0d7e3a2ec690|api.access|{'url': '/api/v1/org/da450e98-1581-4cd1-a4fc-06a3b76f5004/audit?from=2021-10-03&to=2021-10-10&sortOrder=ASC&page=1'}|2021-10-11T08:50:14.558Z|
|1                                                               |36863d40-ba29-491f-af63-7a1a7d79e411|da450e98-1581-4cd1-a4fc-06a3b76f5004|b7f4b234-e888-4054-8532-0d7e3a2ec690|api.access|{'url': '/api/v1/org/da450e98-1581-4cd1-a4fc-06a3b76f5004/audit?from=2021-10-03&to=2021-10-10&sortOrder=ASC&page=2'}|2021-10-11T08:50:16.280Z|
|2                                                               |36863d40-ba29-491f-af63-7a1a7d79e411|da450e98-1581-4cd1-a4fc-06a3b76f5004|b7f4b234-e888-4054-8532-0d7e3a2ec690|api.access|{'url': '/api/v1/org/da450e98-1581-4cd1-a4fc-06a3b76f5004/audit?from=2021-10-03&to=2021-10-10&sortOrder=ASC&page=3'}|2021-10-11T08:50:16.542Z|




### Help Output

```
# Getting Org information
Either of the following commands, depending on whether you are using the docker container or running directly:
❯ docker run --rm -it -e SNYK_TOKEN -v "${PWD}"/file_output:/runtime snyk-audit-to-csv:latest org --help
❯ python main.py org --help

Usage: main.py org [OPTIONS] [SNYK_ORG]

  Retrieve the audit issues for a specific Org, with optional filters

Arguments:
  [SNYK_ORG]  The Snyk Org Slug retrieve audit events from  [default: ]

Options:
  --start-date TEXT     Starting date range to search for events  [default: {7 days before today}]
  --end-date TEXT       End date range to search for events  [default: {today}]
  --user-id TEXT        Only show events including this userId
  --project-id TEXT     The show events from this Project
  --csv                 Save a CSV to local directory
  --json                Save a JSON file to local directory
  --output-dir PATH     Local directory save files  [default: /runtime]
  --event TEXT          Pass multiple events to filter by with --event one --event two
  --excludeevent TEXT   Exclude an event of this specific type (e.g. api.access) NOTE: This cannot be used in conjunction with --event
  --help                Show this message and exit.

# Getting Group information
Either of the following commands, depending on whether you are using the docker container or running directly:
❯ docker run --rm -it -e SNYK_TOKEN -v "${PWD}"/file_output:/runtime snyk-audit-to-csv:latest group --help
❯ python main.py group --help

Usage: main.py group [OPTIONS] [SNYK_GROUP]

  Retrieve the audit issues for a specific Group, with optional filters

Arguments:
  [SNYK_GROUP]  The Snyk Group Name retrieve audit events from  [default: ]

Options:
  --start-date TEXT     Starting date range to search for events  [default: {7 days before today}]
  --end-date TEXT       End date range to search for events  [default: {today}]
  --user-id TEXT        Only show events including this userId
  --project-id TEXT     The show events from this Project
  --csv                 Save a CSV to local directory
  --json                Save a JSON file to local directory
  --output-dir PATH     Local directory save files  [default: /runtime]
  --event TEXT          Pass multiple events to filter by with --event one --event two
  --excludeevent TEXT   Exclude an event of this specific type (e.g. api.access) NOTE: This cannot be used in conjunction with --event
  --help                Show this message and exit.

```
