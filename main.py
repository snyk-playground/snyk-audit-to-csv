import typer
import json

import pandas as pd

from snyk import SnykClient

from typing import List, Optional

from pathlib import Path

# internal libraries
from util import get_snyk_pages, get_eight_days_ago, get_yesterday
from events import org_events, group_events



def org_callback(events):
    invalid_events = [x for x in events if x not in org_events]

    if len(invalid_events) > 0:
        raise typer.BadParameter(f"Following event types are not supported for Org: {invalid_events}")
    
    return events

def group_callback(events):
    invalid_events = [x for x in events if x not in group_events]

    if len(invalid_events) > 0:
        raise typer.BadParameter(f"Following event types are not supported for Org: {invalid_events}")
    
    return events

app = typer.Typer(add_completion=False)

def token_callback(snyk_token: str):
    client = SnykClient(snyk_token,tries=3, delay=1, backoff=1,user_agent=f"pysnyk/snyk_services/audit-to-csv")

    try:
        client.get('/user/me').json()
    except Exception as e:
        raise typer.BadParameter("Unable to connect to Snyk API with provided Snyk Token")
    
    return snyk_token


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    snyk_token: str = typer.Option(
        ...,
        prompt="Snyk Token",
        help="Snyk Token required to authenticate to Snyk Endpoint",
        envvar="SNYK_TOKEN",
        callback=token_callback
    )
):
    ctx.obj = vars()

@app.command()
def org(
    ctx: typer.Context,
    snyk_org: str = typer.Argument("", help="The Snyk Org Slug retrieve audit events from"),
    start_date: str = typer.Option(get_eight_days_ago(), help="Starting date range to search for events"),
    end_date: str = typer.Option(get_yesterday(), help="End date range to search for events"),
    user_id: str = typer.Option("", help="Only show events including this userId"),
    project_id: str = typer.Option("", help="The show events from this Project"),
    save_csv: bool = typer.Option(False,'--csv', help="Save a CSV to local directory"),
    save_json: bool = typer.Option(False,'--json', help="Save a JSON file to local directory"),
    output_dir: Path = typer.Option(Path.cwd(), dir_okay=True,writable=True, help="Local directory save files"),
    excludeevent: str = typer.Option("", help="Exclude an event of this specific type (e.g. api.access) NOTE: This cannot be used in conjunction with --event"),
    events: Optional[List[str]] = typer.Option(
        [],
        '--event',
        help="Pass multiple events to filter by with --event one --event two",
        callback=org_callback
    )
):
    """
    Retrieve the audit issues for a specific Org, with optional filters
    """
    snyk_token = ctx.obj['snyk_token']

    client = SnykClient(snyk_token,tries=3, delay=1, backoff=1,user_agent=f"pysnyk/snyk_services/audit-to-csv")

    orgs = client.organizations.all()

    the_org = [o for o in orgs if o.slug == snyk_org]

    if len(the_org) > 1:
        print(f"error: Found more than 1 org that matches: {snyk_org}")
        print(the_org)
        typer.Abort()

    org_id = the_org[0].id

    group_id = the_org[0].group.id

    client = SnykClient(snyk_token,tries=3, delay=1, backoff=1,user_agent=f"pysnyk/snyk_services/audit-to-csv")

    body = {
        "filters": {
        "userId": user_id,
        "projectId": project_id,
        "excludeEvent": excludeevent
        }
    }
    
    if len(events) > 0:
        body['filters']['event'] = events

    path = f'org/{org_id}/audit?&sortOrder=ASC&from={start_date}&to={end_date}'

    print(f"Processing page 1")
    results = get_snyk_pages(client,path,body)

    print(f"Total events found: {len(results)}")

    for r in results:
        r['groupId'] = group_id

    if save_csv:
        csv_file = output_dir / f'{snyk_org}_{start_date}_to_{end_date}.csv'
        csv_path = str(csv_file.resolve())
        df = pd.DataFrame.from_dict(results)
        df.to_csv(csv_path)
        print(f'CSV saved to {csv_path}')

    if save_json:
        json_file = output_dir / f'{snyk_org}_{start_date}_to_{end_date}.json'
        with json_file.open("w", encoding ="utf-8") as f:
            f.write(json.dumps(results, indent=4))
        print(f'JSON saved to {json_file}')


@app.command()
def group(
    ctx: typer.Context,
    snyk_group: str = typer.Argument("", help="The Snyk Group Name retrieve audit events from"),
    start_date: str = typer.Option(get_eight_days_ago(), help="Starting date range to search for events"),
    end_date: str = typer.Option(get_yesterday(), help="End date range to search for events"),
    user_id: str = typer.Option("", help="Only show events including this userId"),
    project_id: str = typer.Option("", help="The show events from this Project"),
    save_csv: bool = typer.Option(False,'--csv', help="Save a CSV to local directory"),
    save_json: bool = typer.Option(False,'--json', help="Save a JSON file to local directory"),
    output_dir: Path = typer.Option(Path.cwd(), dir_okay=True,writable=True, help="Local directory save files"),
    excludeevent: str = typer.Option("", help="Exclude an event of this specific type (e.g. api.access) NOTE: This cannot be used in conjunction with --event"),
    events: Optional[List[str]] = typer.Option(
        [],
        '--event',
        help="Pass multiple events to filter by with --event one --event two",
        callback=group_callback
    )
):
    """
    Retrieve the audit issues for a specific Group, with optional filters
    """
    snyk_token = ctx.obj['snyk_token']

    client = SnykClient(snyk_token,tries=3, delay=1, backoff=1,user_agent=f"pysnyk/snyk_services/audit-to-csv")

    orgs = client.organizations.all()

    groups = [g.group for g in orgs if g.group is not None]

    groups = list(set([g.id for g in groups if g.name == snyk_group]))

    if len(groups) > 1:
        print(f"error: Found more than 1 org that matches: {snyk_group}")
        print(groups)
        typer.Abort()

    group_id = groups[0]

    group_down_case = snyk_group.lower()
    group_down_case = group_down_case.replace(' ','_')

    client = SnykClient(snyk_token,tries=3, delay=1, backoff=1,user_agent=f"pysnyk/snyk_services/audit-to-csv")

    body = {
        "filters": {
        "userId": user_id,
        "projectId": project_id,
        "excludeEvent": excludeevent
        }
    }

    if len(events) > 0:
        body['filters']['event'] = events

    path = f'group/{group_id}/audit?&sortOrder=ASC&from={start_date}&to={end_date}'

    print(f"Processing page 1")
    results = get_snyk_pages(client,path,body)

    print(f"Total events found: {len(results)}")

    for r in results:
        r['groupId'] = group_id

    if save_csv:
        csv_file = output_dir / f'{group_down_case}_{start_date}_to_{end_date}.csv'
        csv_path = str(csv_file.resolve())
        df = pd.DataFrame.from_dict(results)
        df.to_csv(csv_path)
        print(f'CSV saved to {csv_path}')

    if save_json:
        json_file = output_dir / f'{group_down_case}_{start_date}_to_{end_date}.json'
        with json_file.open("w", encoding ="utf-8") as f:
            f.write(json.dumps(results, indent=4))
        print(f'JSON saved to {json_file}')




if __name__ == "__main__":
    app()