from contextlib import nullcontext


def configure_tracing(service_name: str, endpoint: str, enabled: bool):
    if not enabled:
        return None
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")))
        trace.set_tracer_provider(provider)
        return trace.get_tracer(service_name)
    except (ImportError, RuntimeError, ValueError, OSError):
        return None


def span(tracer, name: str, attributes: dict | None = None):
    if tracer is None:
        return nullcontext()
    return tracer.start_as_current_span(name, attributes=attributes or {})
