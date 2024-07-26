from flask import Flask, request, redirect, session, render_template, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from datetime import datetime, timedelta
from google.ads.googleads.v16.services.types import google_ads_service
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY")  # Set this in Replit Secrets

# Set up OAuth 2.0 flow
flow = Flow.from_client_config(
    {
        "web": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=["https://www.googleapis.com/auth/adwords"])
flow.redirect_uri = "https://updatemate-ppc.nicklafferty1.repl.co/oauth2callback"


@app.route('/')
def index():
    if 'credentials' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', clients=get_client_list())


@app.route('/login')
def login():
    authorization_url, _ = flow.authorization_url(prompt='consent')
    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect(url_for('index'))


def get_google_ads_client():
    credentials = Credentials(**session['credentials'])
    return GoogleAdsClient(credentials=credentials)


def get_client_list():
    client = get_google_ads_client()
    customer_service = client.get_service("CustomerService")
    accessible_customers = customer_service.list_accessible_customers()

    client_list = []
    for resource_name in accessible_customers.resource_names:
        customer_id = resource_name.split('/')[-1]
        client_list.append({
            "id": customer_id,
            "name": f"Client {customer_id}"
        })

    return client_list


@app.route('/fetch_changes', methods=['POST'])
def fetch_change_history(client, client_id, days):
    ga_service = client.get_service("GoogleAdsService")

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    query = f"""
    SELECT
      change_event.resource_name,
      change_event.change_date_time,
      change_event.change_resource_name,
      change_event.user_email,
      change_event.client_type,
      change_event.change_resource_type
    FROM change_event
    WHERE change_event.change_date_time >= '{start_date}'
      AND change_event.change_date_time <= '{end_date}'
    ORDER BY change_event.change_date_time DESC
    """

    stream = ga_service.search_stream(customer_id=client_id, query=query)

    changes = []
    for batch in stream:
        for row in batch.results:
            change = {
                'date_time': row.change_event.change_date_time,
                'user_email': row.change_event.user_email,
                'client_type': row.change_event.client_type.name,
                'resource_type': row.change_event.change_resource_type.name,
                'resource_name': row.change_event.change_resource_name
            }
            changes.append(change)

    return changes


@app.route('/fetch_changes', methods=['POST'])
def fetch_changes():
    client_id = request.form['client_id']
    start_date = datetime.strptime(request.form['start_date'],
                                   '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
    days = (end_date - start_date).days

    try:
        client = get_google_ads_client()
        changes = fetch_change_history(client, client_id, days)
        summary = summarize_changes(changes)
        return render_template('summary.html',
                               summary=summary,
                               client_id=client_id,
                               days=days)
    except GoogleAdsException as ex:
        return f"An error occurred: {ex}"


def summarize_changes(changes):
    summary = ""
    for change in changes:
        summary += f"Date: {change['date_time']}\n"
        summary += f"User: {change['user_email']}\n"
        summary += f"Client Type: {change['client_type']}\n"
        summary += f"Resource Type: {change['resource_type']}\n"
        summary += f"Resource Name: {change['resource_name']}\n"
        summary += "-" * 50 + "\n"
    return summary


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
    app = Flask(__name__)
    app.secret_key = os.environ.get(
        "FLASK_SECRET_KEY")  # Set this in Replit Secrets

    # Set up OAuth 2.0 flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=["https://www.googleapis.com/auth/adwords"])
    flow.redirect_uri = "https://your-repl-name.your-username.repl.co/oauth2callback"

    @app.route('/')
    def index():
        if 'credentials' not in session:
            return redirect(url_for('login'))
        return render_template('index.html', clients=get_client_list())

    @app.route('/login')
    def login():
        authorization_url, _ = flow.authorization_url(prompt='consent')
        return redirect(authorization_url)

    @app.route('/oauth2callback')
    def oauth2callback():
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        return redirect(url_for('index'))

    def get_google_ads_client():
        credentials = Credentials(**session['credentials'])
        return GoogleAdsClient(credentials=credentials)

    def get_client_list():
        client = get_google_ads_client()
        customer_service = client.get_service("CustomerService")
        accessible_customers = customer_service.list_accessible_customers()

        client_list = []
        for resource_name in accessible_customers.resource_names:
            customer_id = resource_name.split('/')[-1]
            client_list.append({
                "id": customer_id,
                "name": f"Client {customer_id}"
            })

        return client_list


@app.route('/fetch_changes', methods=['POST'])
def fetch_change_history(client, client_id, days):
    ga_service = client.get_service("GoogleAdsService")

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    query = f"""
    SELECT
      change_event.resource_name,
      change_event.change_date_time,
      change_event.change_resource_name,
      change_event.user_email,
      change_event.client_type,
      change_event.change_resource_type
    FROM change_event
    WHERE change_event.change_date_time >= '{start_date}' 
      AND change_event.change_date_time <= '{end_date}'
    ORDER BY change_event.change_date_time DESC
    """

    stream = ga_service.search_stream(customer_id=client_id, query=query)

    changes = []
    for batch in stream:
        for row in batch.results:
            change = {
                'date_time': row.change_event.change_date_time,
                'user_email': row.change_event.user_email,
                'client_type': row.change_event.client_type.name,
                'resource_type': row.change_event.change_resource_type.name,
                'resource_name': row.change_event.change_resource_name
            }
            changes.append(change)

    return changes


@app.route('/fetch_changes', methods=['POST'])
def fetch_changes():
    client_id = request.form['client_id']
    days = int(request.form['date_range'])

    try:
        client = get_google_ads_client()
        changes = fetch_change_history(client, client_id, days)
        summary = summarize_changes(changes)
        return render_template('summary.html',
                               summary=summary,
                               client_id=client_id,
                               days=days)
    except GoogleAdsException as ex:
        return f"An error occurred: {ex}"


def summarize_changes(changes):
    summary = ""
    for change in changes:
        summary += f"Date: {change['date_time']}\n"
        summary += f"User: {change['user_email']}\n"
        summary += f"Client Type: {change['client_type']}\n"
        summary += f"Resource Type: {change['resource_type']}\n"
        summary += f"Resource Name: {change['resource_name']}\n"
        summary += "-" * 50 + "\n"
    return summary


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
