# Requisitos de Migração e Melhoria do Gamma Engine

Baseado na análise da arquitetura legada (Hydra) e na arquitetura atual do Gamma Engine, foram identificados os seguintes requisitos de migração e melhoria para restaurar funcionalidades chave e aumentar a robustez do sistema.

## 1. Implementação de RAG Local (Alta Prioridade)
**Origem:** O Hydra utilizava `Weaviate` e `Faiss` para RAG local. O Gamma depende exclusivamente do `Vertex AI`.
**Justificativa:** Redução de custos, maior privacidade de dados e funcionamento offline/local.
**Requisito:** Implementar um provedor de RAG alternativo no `gamma_engine` que utilize `Chromadb` ou `Faiss` localmente.
**Detalhes Técnicos:**
- Criar interface `RAGProvider` abstrata.
- Implementar `LocalRAGProvider` usando `sentence-transformers` (presente no `setup.py` do Hydra) e um banco vetorial leve (`Chromadb` ou `Faiss`).
- Permitir configuração via variável de ambiente `RAG_PROVIDER=local` ou `RAG_PROVIDER=vertex`.

## 2. Sistema de Observabilidade (Média Prioridade)
**Origem:** O Hydra possuía integração com `Loki` (Logs) e `Prometheus` (Métricas). O Gamma possui apenas logs de aplicação.
**Justificativa:** Monitoramento de saúde, performance e erros em produção é crítico para sistemas autônomos.
**Requisito:** Adicionar middleware de métricas e exportação de logs estruturados.
**Detalhes Técnicos:**
- Integrar `prometheus-fastapi-instrumentator` no `gamma_server.py`.
- Configurar logger para formatar logs em JSON (compatível com Loki/ELK).
- (Opcional) Criar container `prometheus` e `grafana` no `docker-compose.yml`.

## 3. Modularização de Ingestão de Dados (Baixa Prioridade)
**Origem:** O Hydra tinha um "Serviço de Ingestão" separado. No Gamma, a ingestão é feita via upload direto na API ou ferramenta.
**Justificativa:** Para grandes volumes de dados, o upload síncrono trava a API ou o Agente.
**Requisito:** Criar um worker assíncrono (ex: via Celery ou BackgroundTasks do FastAPI) para processamento e ingestão de documentos.
**Detalhes Técnicos:**
- Mover lógica de `upload_file` para uma `BackgroundTask`.
- Implementar fila de processamento de documentos.

## 4. Pipeline de Treino e Avaliação (Baixa Prioridade - Futuro)
**Origem:** O Hydra possuía "Orquestrador de Treino".
**Justificativa:** Customização do modelo para domínios específicos.
**Requisito:** Se houver necessidade de fine-tuning, reintroduzir o pipeline. Por enquanto, focar em In-Context Learning (RAG).

## 5. Testes de Integração Automatizados (Alta Prioridade)
**Origem:** O script `validate_project.py` do Hydra verificava a estrutura. O Gamma precisa de testes mais robustos.
**Requisito:** Expandir a suíte de testes (`tests/`) para cobrir cenários de RAG e fluxo completo de Agente.
**Detalhes Técnicos:**
- Criar testes de integração que simulam uma conversa completa com mocks de LLM.
- Verificar se a recuperação de contexto (RAG) está funcionando corretamente.
