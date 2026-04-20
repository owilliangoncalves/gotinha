# Gotinha

Backend inicial de um buscador inteligente de informacoes em saude para a atencao primaria, com foco em rastreabilidade documental.

## O que ja esta implementado

- API em `FastAPI`.
- Upload de PDF em `/api/v1/documents/upload`.
- Sincronizacao de PDFs locais em `/api/v1/documents/sync`.
- Extracao real de texto via `PyMuPDF`.
- Segmentacao em chunks com pagina, secao e hash do documento.
- Consulta em linguagem natural em `/api/v1/consultas`.
- Respostas geradas a partir dos trechos recuperados, com suporte opcional a Groq.
- Historico simples de consultas em memoria.

## O que esta preparado para evoluir

- OCR para PDFs escaneados com `OCRmyPDF` e `Tesseract`.
- Persistencia em `PostgreSQL` com `pgvector`.
- Fila assincrona com `Celery` e `Redis`.
- Integracao com `Ollama` para sintese mais robusta, sempre restrita ao contexto recuperado.
- Busca hibrida real, combinando full-text search e embeddings.

## Estrutura

```text
app/
  api/                Endpoints HTTP
  core/               Configuracoes
  models/             Modelos de dominio
  schemas/            Contratos de entrada e saida
  services/
    pdf_processing/   Extracao e chunking
    retrieval/        Recuperacao inicial dos trechos
    llm/              Sintese baseada em evidencia
```

## Endpoints principais

- `GET /`
- `GET /api/v1/health`
- `POST /api/v1/documents/upload`
- `POST /api/v1/documents/sync`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `POST /api/v1/consultas`
- `GET /api/v1/consultas`

## Configuracao local

- `PRECISION_MODE`: perfil de operacao do pipeline. Use `max_precision` para favorecer respostas mais fieis ao documento e reduzir inferencias; `balanced` deixa o filtro menos estrito.
- `DOCUMENTS_DIR`: pasta monitorada para sincronizacao de PDFs. Padrao `pdf/atencao_basica`.
- `AUTO_INGEST_ON_STARTUP`: quando `true`, os PDFs da pasta sao carregados ao iniciar a API.
- `CHUNK_SIZE` e `CHUNK_OVERLAP`: ajustam a granularidade da indexacao. No perfil `max_precision`, o projeto usa chunks menores com mais sobreposicao para preservar contexto.
- `DEFAULT_TOP_K`: quantidade padrao de trechos considerados na sintese.
- `MIN_RELEVANCE_SCORE`: score minimo para um trecho entrar na resposta. No perfil `max_precision`, o padrao e `0.70`.
- `MIN_OVERLAP_TERMS`: quantidade minima de termos relevantes em comum para consultas maiores. No perfil `max_precision`, o padrao e `3`.
- `GROQ_API_KEY`: habilita a sintese com o modelo configurado na Groq.
- `GROQ_MODEL`: modelo utilizado na chamada da Groq.
- `GROQ_TEMPERATURE`: controle de variacao do modelo. Para maxima precisao, mantenha `0.0`.

## Configuracao recomendada para maxima precisao

Use estas variaveis no seu `.env`:

```dotenv
PRECISION_MODE=max_precision
AUTO_INGEST_ON_STARTUP=true
CHUNK_SIZE=800
CHUNK_OVERLAP=200
DEFAULT_TOP_K=8
MIN_RELEVANCE_SCORE=0.70
MIN_OVERLAP_TERMS=3
GROQ_TEMPERATURE=0.0
```

Essa combinacao deixa o sistema mais conservador: ele privilegia trechos com maior cobertura da pergunta, reduz respostas baseadas em evidencia fraca e, quando necessario, prefere dizer que nao ha suporte documental suficiente.

## Executando localmente

1. Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instale as dependencias:

```bash
pip install -e ".[dev]"
```

3. Suba a API:

```bash
python main.py
```

4. Acesse a documentacao interativa:

```text
http://localhost:8000/docs
```

5. Acesse a interface web basica:

```text
http://localhost:8000/
```

## Exemplo de resposta

```json
{
  "resposta": "Pacientes com risco cardiovascular elevado devem receber acompanhamento continuo.",
  "suficiente": true,
  "fontes": [
    {
      "chunk_id": "a1b2c3",
      "documento": "protocolo_hipertensao.pdf",
      "pagina": 17,
      "secao": "Tratamento Medicamentoso",
      "trecho": "Pacientes com risco cardiovascular elevado devem receber acompanhamento continuo...",
      "score_relevancia": 0.92
    }
  ]
}
```

## Observacao importante

Esta primeira entrega e uma espinha dorsal executavel. Ela prioriza o principio central do projeto:

- o documento e a fonte da verdade;
- a resposta precisa carregar sua origem;
- quando nao houver evidencia suficiente, o sistema deve sinalizar isso.
