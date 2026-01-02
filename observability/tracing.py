# tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.anthropic import AnthropicInstrumentor

def setup_phoenix_tracing():
    """
    Configures the application to send traces to a local Arize Phoenix server.
    """
    # 1. Initialize the Tracer Provider (The core OTEL engine)
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)

    # 2. Configure the Exporter (Where to send data)
    # Phoenix listens on localhost:4317 (gRPC) by default for OTEL data
    phoenix_exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:4317")

    # 3. Add the processor (Batches logs for performance)
    span_processor = BatchSpanProcessor(phoenix_exporter)
    tracer_provider.add_span_processor(span_processor)

    # 4. Auto-Instrument Anthropic
    # This magically wraps every client.messages.create() call
    AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
    
    print("🔭 Observability: Tracing enabled. Sending to Phoenix (localhost:6006)")