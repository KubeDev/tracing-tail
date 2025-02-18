import os
import time
import random
import requests
from fastapi import FastAPI, Response, status, Request
from typing import List
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.trace import Link
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# ================================
#  CONFIGURAÇÃO DO OPENTELEMETRY
# ================================

APP_NAME = os.getenv("APP_NAME", "app-a")
APP_URL_DESTINO = os.getenv("APP_URL_DESTINO", "")
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://collector:4318/v1/traces")

# Simulação de problemas
APP_ERRORS = int(os.getenv("APP_ERRORS", "0"))  # Porcentagem de erro (0 a 100)
APP_LATENCY = int(os.getenv("APP_LATENCY", "0"))  # Tempo máximo de atraso (em ms)

# Configuração do OpenTelemetry
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: APP_NAME,
    ResourceAttributes.SERVICE_VERSION: "1.0.0"
})

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(APP_NAME)
propagator = TraceContextTextMapPropagator()

app = FastAPI()

@app.post("/process")
def process_request(payload: List[str], response: Response, request: Request):
    """
    Endpoint que processa um payload, simula falhas e latência variável,
    e propaga a requisição para outros serviços.
    """

    original_payload = payload.copy()
    original_payload.append(APP_NAME)

    # ================================
    #  EXTRAÇÃO DO CONTEXTO DE TRACE
    # ================================
    context = propagator.extract(request.headers)

    # ================================
    #  CRIAÇÃO DO SPAN PRINCIPAL
    # ================================
    with tracer.start_as_current_span("process-request", context=context) as span:
        span.set_attribute(SpanAttributes.HTTP_ROUTE, "/process")
        span.set_attribute(SpanAttributes.HTTP_METHOD, "POST")

        # Adicionando um evento ao span para indicar o início do processamento
        span.add_event("Início do processamento", {"payload_tamanho": len(payload)})

        # Simulação de latência variável dentro do span para ser registrada no tracing
        if APP_LATENCY > 0:
            simulated_latency = random.randint(0, APP_LATENCY)  # Define um atraso aleatório entre 0 e APP_LATENCY
            span.set_attribute("process.runtime.latency_ms", simulated_latency)  # Seguindo naming convention do OTel
            time.sleep(simulated_latency / 1000)  # Converte ms para segundos

        # Simulação de erro com base na porcentagem definida
        if random.randint(1, 100) <= APP_ERRORS:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_msg = f"Erro simulado em {APP_NAME}"
            span.record_exception(Exception(error_msg))
            span.set_status(Status(StatusCode.ERROR))
            span.add_event("Erro simulado", {"mensagem": error_msg})
            span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 500)
            return {"error": error_msg}

        # Se houver serviços de destino, propaga a requisição
        if APP_URL_DESTINO:
            urls = APP_URL_DESTINO.split(',')
            for url in urls:
                try:
                    headers = {}
                    propagator.inject(headers, context=trace.set_span_in_context(span))

                    # Criar um link com o span atual, conectando os serviços distribuídos
                    link = Link(span.get_span_context())

                    resp = requests.post(
                        f"{url}/process",
                        json=original_payload,
                        headers=headers,
                        timeout=5
                    )

                    span.set_attribute("net.peer.name", url)  # Define o serviço de destino

                    if resp.status_code == 200:
                        original_payload = resp.json()
                        span.add_event("Requisição externa bem-sucedida", {"url": url})
                    else:
                        response.status_code = status.HTTP_502_BAD_GATEWAY
                        span.record_exception(Exception(f"Erro ao enviar para {url}: {resp.status_code}"))
                        span.set_status(Status(StatusCode.ERROR))
                        span.add_event("Erro na requisição externa", {"url": url, "status_code": resp.status_code})
                        span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 502)

                except requests.RequestException as e:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR))
                    span.add_event("Falha na requisição externa", {"erro": str(e)})
                    span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 400)

        # Finalizando o span com sucesso
        span.set_status(Status(StatusCode.OK))
        span.add_event("Processamento concluído", {"payload_final_tamanho": len(original_payload)})

    return original_payload
