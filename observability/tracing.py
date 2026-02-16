# tracing.py
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.anthropic import AnthropicInstrumentor

def setup_phoenix_tracing():
    """
    Configures the application to send traces to Phoenix (local or cloud).

    For Phoenix Cloud:
    - Set PHOENIX_SPACE_ID environment variable (from Phoenix Cloud Settings)
    - Set PHOENIX_API_KEY environment variable (System Key from Phoenix Cloud)
    - Optionally set PHOENIX_PROJECT_NAME (defaults to 'enterprise-cx-agent')

    For local Phoenix:
    - Leave environment variables unset, will default to localhost
    """
    # Check for Phoenix Cloud configuration
    space_id = os.getenv("PHOENIX_SPACE_ID")
    api_key = os.getenv("PHOENIX_API_KEY")
    project_name = os.getenv("PHOENIX_PROJECT_NAME", "enterprise-cx-agent")

    if space_id and api_key:
        # Phoenix Cloud configuration using arize-otel
        from arize.otel import register

        tracer_provider = register(
            space_id=space_id,
            api_key=api_key,
            project_name=project_name,
        )
        print(f"🔭 Observability: Tracing enabled. Sending to Phoenix Cloud (project: {project_name})")
    else:
        # Local Phoenix configuration (HTTP)
        # 1. Initialize the Tracer Provider
        tracer_provider = TracerProvider()
        trace.set_tracer_provider(tracer_provider)

        # 2. Configure the Exporter for local Phoenix
        # Phoenix local HTTP endpoint is localhost:6006/v1/traces
        phoenix_exporter = OTLPSpanExporter(
            endpoint="http://localhost:6006/v1/traces"
        )

        # 3. Add the processor
        span_processor = BatchSpanProcessor(phoenix_exporter)
        tracer_provider.add_span_processor(span_processor)

        print("🔭 Observability: Tracing enabled. Sending to Phoenix (localhost:6006)")

    # 4. Auto-Instrument Anthropic (works for both cloud and local)
    # This magically wraps every client.messages.create() call
    AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)