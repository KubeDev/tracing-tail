
# Tracing-Tail

O **Tracing-Tail** é um projeto que demonstra a instrumentação de tracing distribuído utilizando **FastAPI** e **OpenTelemetry**. Ele implementa **propagação de contexto**, **eventos de tracing**, **links entre spans**, **registro de exceções**, além de permitir a **simulação de latência e falhas** para testes de resiliência.


## Tecnologias Utilizadas

- **FastAPI** – Framework web assíncrono para Python
- **OpenTelemetry** – Para instrumentação e rastreamento de requisições
- **OTLP Exporter** – Para exportação de traces para um coletor OpenTelemetry
- **Jaeger / Grafana Tempo** – Para visualização dos traces (opcional)
- **Docker** – Para execução local do OpenTelemetry Collector (opcional)

## Funcionalidades

- **Tracing distribuído** para monitorar requisições entre serviços
- **Propagação de contexto** via headers HTTP
- **Registro de eventos** para marcação de momentos-chave na requisição
- **Simulação de falhas** para testes de resiliência
- **Simulação de latência variável** para avaliar desempenho da aplicação
- **Links entre spans** para rastreamento de chamadas distribuídas
- **Registro de exceções** para depuração de erros

## Configuração

O **Tracing-Tail** utiliza variáveis de ambiente para configurar as simulações de latência e falhas.

| Variável          | Descrição |
|------------------|------------|
| `APP_NAME`       | Nome do serviço (padrão: `tracing-tail`) |
| `APP_URL_DESTINO` | Lista de URLs de serviços downstream (separados por vírgula) |
| `OTLP_ENDPOINT`  | Endpoint do OpenTelemetry Collector (padrão: `http://collector:4318/v1/traces`) |
| `APP_ERRORS`     | Porcentagem de erro simulado (0 a 100) |
| `APP_LATENCY`    | Tempo máximo de atraso simulado em milissegundos |

## Instalação

### 1. Clonar o Repositório
```sh
git clone https://github.com/KubeDev/tracing-tail.git
cd tracing-tail
```

### 2. Criar um Ambiente Virtual e Instalar Dependências
```sh
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Execução

### 1. Definir Variáveis de Ambiente
```sh
export APP_ERRORS=20
export APP_LATENCY=1000
export OTLP_ENDPOINT=http://localhost:4318/v1/traces
```

### 2. Iniciar a Aplicação
```sh
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 3. Testar a API
```sh
curl -X POST http://localhost:8000/process -H "Content-Type: application/json" -d '["item1", "item2"]'
```

## Observação dos Traces

Caso utilize Jaeger ou Grafana Tempo para visualizar os traces:

### 1. Executar um Coletor OpenTelemetry com Jaeger
```sh
docker run --rm -p 4317:4317 -p 4318:4318 -p 16686:16686 \
      --name otel-collector jaegertracing/all-in-one:latest
```

### 2. Acessar os Traces
- **Jaeger**: [http://localhost:16686](http://localhost:16686)
- **Grafana Tempo**: Configuração necessária via Prometheus/Grafana

## Estrutura do Código

```
📂 tracing-tail
 ┣ 📜 app.py             # Código principal com FastAPI e OpenTelemetry
 ┣ 📜 requirements.txt   # Dependências do projeto
 ┣ 📜 README.md          # Documentação do projeto
```
