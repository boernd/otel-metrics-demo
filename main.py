import random
import time
from flask import Flask, jsonify

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_NAMESPACE, SERVICE_VERSION, Resource

# Service name is required for most backends
resource = Resource(attributes={
    SERVICE_NAME: "otel",
    SERVICE_NAMESPACE: "demo",
    SERVICE_VERSION: "1.0.0"
})

COLLECTOR_ENDPOINT = "http://xyz:4317"
INTERVAL_SEC = 10

# Boiler plate initialization
metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=COLLECTOR_ENDPOINT), INTERVAL_SEC)
provider = MeterProvider(metric_readers=[metric_reader], resource=resource)

# Sets the global default meter provider
metrics.set_meter_provider(provider)

# Creates a meter from the global meter provider
meter = metrics.get_meter("demo", "1.0.0")

# Add instruments
calls = meter.create_counter(name='otel_metrics_demo_api_calls')
errors = meter.create_counter(name='otel_metrics_demo_api_errors')

app = Flask(__name__)

def do_roll():
    time.sleep(random.randint(1, 3))
    return random.randint(1, 8)


@app.route('/demo')
def roll():
    roll = do_roll()
    if roll > 6:
        errors.add(1, {'path': '/demo'})
    calls.add(1, {'path': '/demo'})
    return jsonify({'message': 'Welcome to Demo!'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15000, debug=True)
