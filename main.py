import os
import random
import logging
import time
from flask import Flask, jsonify

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
# from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_NAMESPACE, SERVICE_VERSION, Resource

# Service name is required for most backends
resource = Resource(attributes={
    SERVICE_NAME: 'otel',
    SERVICE_NAMESPACE: 'demo',
    SERVICE_VERSION: '1.0.0'
})

#################
# METRICS SETUP #
#################
METRICS_COLLECTOR_ENDPOINT =  os.environ.get('METRICS_COLLECTOR_ENDPOINT', 'http://localhost:4318/v1/metrics')
INTERVAL_SEC = 10

# Boiler plate initialization
metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=METRICS_COLLECTOR_ENDPOINT), INTERVAL_SEC)
metrics_provider = MeterProvider(metric_readers=[metric_reader], resource=resource)

# Sets the global default meter provider
metrics.set_meter_provider(metrics_provider)

# Creates a meter from the global meter provider
meter = metrics.get_meter("demo", "1.0.0")

# Add instruments
calls = meter.create_counter(name='otel_metrics_demo_api_calls')
errors = meter.create_counter(name='otel_metrics_demo_api_errors')


#################
# LOGS SETUP #
#################
LOGS_COLLECTOR_ENDPOINT =  os.environ.get('LOGS_COLLECTOR_ENDPOINT', 'localhost:4319')
# Create a logger provider with service information
logger_provider = LoggerProvider(
    resource=resource,
)
set_logger_provider(logger_provider)

# Configure OTLP exporter to send logs to the collector
logs_exporter = OTLPLogExporter(
    endpoint=LOGS_COLLECTOR_ENDPOINT,
    insecure=True,
)

# Add batch processor for efficient log handling
logger_provider.add_log_record_processor(BatchLogRecordProcessor(logs_exporter))

# Create and attach an OpenTelemetry handler to the Python root logger
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)

logger = logging.getLogger(__name__)

app = Flask(__name__)

def do_roll():
    time.sleep(random.randint(1, 3))
    logger.info("Rolling the dice")
    return random.randint(1, 8)


@app.route('/demo')
def roll():
    roll = do_roll()
    if roll > 6:
        logger.error("Roll failed", extra={'roll': roll})
        errors.add(1, {'path': '/demo'})
    calls.add(1, {'path': '/demo'})
    return jsonify({'message': 'Welcome to Demo!'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15000, debug=True)
