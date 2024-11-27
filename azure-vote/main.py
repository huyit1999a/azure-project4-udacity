from flask import Flask, request, render_template
import os
import random
import redis
import socket
import sys
import logging
from datetime import datetime

# App Insights
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.log_exporter import AzureEventHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.azure.metrics_exporter import MetricsExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.ext.flask.flask_middleware import FlaskMiddleware

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(AzureLogHandler(connection_string="InstrumentationKey=d7782c03-95ee-493b-a269-e3cec97701ed;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=e0dc0e7f-ed9e-48cf-83df-6a4193a2e7e3"))
logger.addHandler(AzureEventHandler(connection_string="InstrumentationKey=d7782c03-95ee-493b-a269-e3cec97701ed;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=e0dc0e7f-ed9e-48cf-83df-6a4193a2e7e3"))
# Metrics
exporter = MetricsExporter(connection_string="InstrumentationKey=d7782c03-95ee-493b-a269-e3cec97701ed;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=e0dc0e7f-ed9e-48cf-83df-6a4193a2e7e3")

# Tracing
tracer = Tracer(exporter=AzureExporter(connection_string="InstrumentationKey=d7782c03-95ee-493b-a269-e3cec97701ed;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=e0dc0e7f-ed9e-48cf-83df-6a4193a2e7e3"),
                sampler=ProbabilitySampler(1.0))

app = Flask(__name__)

# Requests
middleware = FlaskMiddleware(app, 
                              exporter=AzureExporter(connection_string="InstrumentationKey=d7782c03-95ee-493b-a269-e3cec97701ed;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=e0dc0e7f-ed9e-48cf-83df-6a4193a2e7e3"),
                              sampler=ProbabilitySampler(1.0))

# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if ("VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']):
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if ("VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']):
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if ("TITLE" in os.environ and os.environ['TITLE']):
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Redis Connection
r = redis.StrictRedis(host='redis', port=6379, db=0)

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1): r.set(button1, 0)
if not r.get(button2): r.set(button2, 0)

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':
        # Get current values
        vote1 = r.get(button1).decode('utf-8')
        tracer.span(name="CatVote").add_attribute("vote.count", vote1)  # Use tracer object to trace cat vote
        vote2 = r.get(button2).decode('utf-8')
        tracer.span(name="DogVote").add_attribute("vote.count", vote2)  # Use tracer object to trace dog vote

        # Return index with values
        return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

    elif request.method == 'POST':

        if request.form['vote'] == 'reset':
            # Empty table and return results
            r.set(button1, 0)
            r.set(button2, 0)
            vote1 = r.get(button1).decode('utf-8')
            properties = {'custom_dimensions': {'Cats Vote': vote1}}
            logger.info("Votes reset - Cats", extra=properties)  # Use logger object to log cat vote

            vote2 = r.get(button2).decode('utf-8')
            properties = {'custom_dimensions': {'Dogs Vote': vote2}}
            logger.info("Votes reset - Dogs", extra=properties)  # Use logger object to log dog vote

            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

        else:
            # Insert vote result into DB
            vote = request.form['vote']
            r.incr(vote, 1)

            # Get current values
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')

            # Add custom telemetry for Cats and Dogs button clicks
            if vote == button1:
                logger.info("Cats Vote", extra={'custom_dimensions': {'vote.count': vote1}})
                tracer.span(name="CatVote").add_attribute("vote.count", vote1)
            elif vote == button2:
                logger.info("Dogs Vote", extra={'custom_dimensions': {'vote.count': vote2}})
                tracer.span(name="DogVote").add_attribute("vote.count", vote2)

            # Return results
            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

if __name__ == "__main__":
    # For local development (run locally)
    # app.run(debug=True)  

    # For production (e.g., running in Docker or VM)
    app.run(host='0.0.0.0', port=5000, debug=False)  # Ensure it's accessible externally

