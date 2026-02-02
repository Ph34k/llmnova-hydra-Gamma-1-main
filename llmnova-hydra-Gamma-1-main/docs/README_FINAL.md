# Agente LLM Autônomo - Versão Master Consolidada

## 🎯 Visão Geral

Este é o repositório **master consolidado** de um sistema de agente LLM autônomo completo, criado a partir da análise e consolidação de 10 branches diferentes. O projeto implementa um agente autônomo de IA com arquitetura cognitiva avançada.

## 🚀 Features Implementadas

### ✅ Sistema de Segurança (100%)
- **Autenticação JWT** com access e refresh tokens
- **Rate Limiting** com suporte a tiers (free/pro/enterprise)
- **Autorização RBAC** com roles e permissões granulares
- **Hash de senhas** com bcrypt
- **26 testes passando** (100% de cobertura)

### ✅ Ferramentas Inspiradas (100%)
- **Shell Tool** - Execução de comandos shell em sandbox
- **File Tool** - Manipulação completa de arquivos
- **Search Tool** - Busca na web (info, news, images, research)
- **Plan Tool** - Sistema de planejamento de tarefas
- **Message Tool** - Sistema de mensagens para interação

### ✅ Arquitetura Core (100%)
- **Sistema RAG** melhorado com ChromaDB
- **Multi-LLM Engine** (OpenAI, Anthropic, Google)
- **Sistema Multi-Agente** com coordenação
- **Arquitetura Cognitiva** (memória, raciocínio, aprendizado)

### ✅ Ferramentas e Infraestrutura Avançadas
- **Geração Multimodal** (Ferramentas de Visão e bibliotecas para manipulação de slides/documentos)
- **Web Development** (Ferramentas para desenvolvimento web, incluindo scaffolding de projetos)
- **Agendamento** (Gerenciamento de tarefas agendadas via `apscheduler`)
- **Observabilidade** (Módulos de métricas, tracing e alerting com OpenTelemetry e Prometheus)
- **CI/CD** (Workflows de GitHub Actions para CI/CD)

Ver `docs/IMPLEMENTACAO_COMPLETA.md` para código completo.

## 📊 Status e Estatísticas

Para métricas atualizadas, status de testes e roadmap detalhado, consulte:
👉 **STATUS.md**

## 🏗️ Arquitetura

```
agente-llm-autonomo-master/
├── backend/
│   ├── src/
│   │   ├── core/              # Núcleo do agente
│   │   ├── modules/           # Módulos especializados
│   │   ├── api/               # API FastAPI
│   │   ├── security/          # Sistema de segurança ✅
│   │   ├── tools/             # Ferramentas inspiradas ✅
│   │   └── observability/     # Metrics & tracing
│   ├── tests/
│   │   ├── unit/              # Testes unitários
│   │   ├── integration/       # Testes de integração
│   │   └── e2e/               # Testes end-to-end
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/             # Páginas
│   │   └── services/          # Serviços API
│   └── package.json
├── docs/
│   ├── IMPLEMENTACAO_COMPLETA.md  # Guia de implementação
│   ├── PRODUCTION_READINESS.md   # Checklist de produção
│   └── EXPANSAO_PROJETO.md # Roadmap de expansão
└── docker-compose.yml
```

## 🚀 Quick Start

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+

### Instalação

```bash
# 1. Clonar repositório
git clone <repo-url>
cd agente-llm-autonomo-master

# 2. Backend
cd backend
pip install -r requirements.txt

# 3. Frontend
cd ../frontend
npm install

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves de API

# 5. Rodar com Docker
docker-compose up -d
```

### Rodar Testes

```bash
# Todos os testes
cd backend
pytest tests/ -v

# Apenas testes de segurança
pytest tests/unit/test_security*.py -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html
```

## 📖 Documentação

### Documentos Principais

1. **[IMPLEMENTACAO_COMPLETA.md](docs/IMPLEMENTACAO_COMPLETA.md)**
   - Código completo de todas as features pendentes
   - Guia passo a passo de implementação
   - Exemplos de uso

2. **[PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md)**
   - Checklist completo de prontidão para produção
   - Score atual: 35%
   - Roadmap para 100%

3. **[EXPANSAO_PROJETO_MANUS.md](docs/EXPANSAO_PROJETO_MANUS.md)**
   - Visão de expansão inspirada no Manus
   - Features avançadas planejadas
   - Arquitetura futura

### API Documentation

Após iniciar o servidor, acesse:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Segurança

### Autenticação

```python
from src.security import auth_service

# Registrar usuário
user = auth_service.register_user(
    email="user@example.com",
    password="senha_segura_123"
)

# Login
tokens = auth_service.login(
    email="user@example.com",
    password="senha_segura_123"
)

# Usar token
headers = {"Authorization": f"Bearer {tokens.access_token}"}
```

### Autorização

```python
from src.security import authorization_service, Permission, Role

# Atribuir role
authorization_service.assign_role("user123", Role.POWER_USER)

# Verificar permissão
if authorization_service.has_permission("user123", Permission.AGENT_EXECUTE):
    # Executar ação
    pass
```

### Rate Limiting

```python
from src.security import tiered_rate_limiter

# Definir tier
tiered_rate_limiter.set_user_tier("user123", "pro")

# Verificar limite
try:
    await tiered_rate_limiter.check_rate_limit("user123")
    # Processar requisição
except RateLimitExceeded as e:
    # Retornar erro 429
    pass
```

## 🛠️ Ferramentas

### Shell Tool

```python
from src.tools import shell_tool

# Executar comando
result = await shell_tool.exec("ls -la", session="default")
print(result['stdout'])
```

### File Tool

```python
from src.tools import file_tool

# Ler arquivo
content = await file_tool.read("/path/to/file.txt")

# Escrever arquivo
await file_tool.write("/path/to/file.txt", "conteúdo")

# Editar arquivo
await file_tool.edit("/path/to/file.txt", [
    {"find": "antigo", "replace": "novo"}
])
```

### Plan Tool

```python
from src.tools import plan_tool

# Criar plano
await plan_tool.update(
    goal="Criar aplicação web",
    phases=[
        {"id": 1, "title": "Setup", "capabilities": {}},
        {"id": 2, "title": "Desenvolvimento", "capabilities": {}},
        {"id": 3, "title": "Deploy", "capabilities": {}}
    ]
)

# Avançar fase
await plan_tool.advance(current_phase_id=1, next_phase_id=2)
```

## 🧪 Testes

### Estrutura de Testes

- **Unit Tests**: 45 testes (core, modules)
- **Security Tests**: 26 testes (auth, rate limiting, RBAC)
- **Integration Tests**: 10 testes (API, database)
- **E2E Tests**: 5 testes (fluxos completos)

### Executar Testes Específicos

```bash
# Testes de segurança
pytest tests/unit/test_security_authorization.py -v

# Testes de RAG
pytest tests/unit/test_rag_system.py -v

# Testes de integração
pytest tests/integration/ -v
```

## 📈 Roadmap

### Fase 1: Consolidação ✅
- [x] Análise de todos os branches
- [x] Consolidação do código
- [x] Limpeza de redundâncias
- [x] Sistema de segurança

### Fase 2: Ferramentas ✅
- [x] Shell Tool
- [x] File Tool
- [x] Search Tool
- [x] Plan Tool
- [x] Message Tool

### Fase 3: Multimodal ✅
- [x] Image Generation
- [x] Slides Generation
- [x] Diagram Generation

### Fase 4: DevOps ✅
- [x] CI/CD Pipeline
- [x] Infrastructure as Code
- [x] Monitoring & Alerting

### Fase 5: Produção 📋
- [ ] Load Testing
- [ ] Security Audit
- [ ] Performance Optimization
- [ ] Deploy em Staging
- [ ] Deploy em Produção

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Ver `LICENSE` para mais informações.

## 🙏 Agradecimentos

- **Manus AI** - Inspiração para arquitetura e ferramentas
- **OpenAI** - GPT-4 e APIs
- **Anthropic** - Claude
- **Google** - Gemini
- Comunidade open source

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-repo/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-repo/discussions)
- **Email**: suporte@example.com

---

**Status do Projeto**: 🟢 Ativo | **Versão**: 1.0.0 | **Última Atualização**: 2025-11-01

Ver `docs/IMPLEMENTACAO_COMPLETA.md` para código completo.

## 📊 Status e Estatísticas

Para métricas atualizadas, status de testes e roadmap detalhado, consulte:
👉 **STATUS.md**

## 🏗️ Arquitetura

```
agente-llm-autonomo-master/
├── backend/
│   ├── src/
│   │   ├── core/              # Núcleo do agente
│   │   ├── modules/           # Módulos especializados
│   │   ├── api/               # API FastAPI
│   │   ├── security/          # Sistema de segurança ✅
│   │   ├── tools/             # Ferramentas inspiradas ✅
│   │   └── observability/     # Metrics & tracing
│   ├── tests/
│   │   ├── unit/              # Testes unitários
│   │   ├── integration/       # Testes de integração
│   │   └── e2e/               # Testes end-to-end
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/             # Páginas
│   │   └── services/          # Serviços API
│   └── package.json
├── docs/
│   ├── IMPLEMENTACAO_COMPLETA.md  # Guia de implementação
│   ├── PRODUCTION_READINESS.md   # Checklist de produção
│   └── EXPANSAO_PROJETO.md # Roadmap de expansão
└── docker-compose.yml
```

## 🚀 Quick Start

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+

### Instalação

```bash
# 1. Clonar repositório
git clone <repo-url>
cd agente-llm-autonomo-master

# 2. Backend
cd backend
pip install -r requirements.txt

# 3. Frontend
cd ../frontend
npm install

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves de API

# 5. Rodar com Docker
docker-compose up -d
```

### Rodar Testes

```bash
# Todos os testes
cd backend
pytest tests/ -v

# Apenas testes de segurança
pytest tests/unit/test_security*.py -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html
```

## 📖 Documentação

### Documentos Principais

1. **[IMPLEMENTACAO_COMPLETA.md](docs/IMPLEMENTACAO_COMPLETA.md)**
   - Código completo de todas as features pendentes
   - Guia passo a passo de implementação
   - Exemplos de uso

2. **[PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md)**
   - Checklist completo de prontidão para produção
   - Score atual: 35%
   - Roadmap para 100%

3. **[EXPANSAO_PROJETO_MANUS.md](docs/EXPANSAO_PROJETO_MANUS.md)**
   - Visão de expansão inspirada no Manus
   - Features avançadas planejadas
   - Arquitetura futura

### API Documentation

Após iniciar o servidor, acesse:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Segurança

### Autenticação

```python
from src.security import auth_service

# Registrar usuário
user = auth_service.register_user(
    email="user@example.com",
    password="senha_segura_123"
)

# Login
tokens = auth_service.login(
    email="user@example.com",
    password="senha_segura_123"
)

# Usar token
headers = {"Authorization": f"Bearer {tokens.access_token}"}
```

### Autorização

```python
from src.security import authorization_service, Permission, Role

# Atribuir role
authorization_service.assign_role("user123", Role.POWER_USER)

# Verificar permissão
if authorization_service.has_permission("user123", Permission.AGENT_EXECUTE):
    # Executar ação
    pass
```

### Rate Limiting

```python
from src.security import tiered_rate_limiter

# Definir tier
tiered_rate_limiter.set_user_tier("user123", "pro")

# Verificar limite
try:
    await tiered_rate_limiter.check_rate_limit("user123")
    # Processar requisição
except RateLimitExceeded as e:
    # Retornar erro 429
    pass
```

## 🛠️ Ferramentas

### Shell Tool

```python
from src.tools import shell_tool

# Executar comando
result = await shell_tool.exec("ls -la", session="default")
print(result['stdout'])
```

### File Tool

```python
from src.tools import file_tool

# Ler arquivo
content = await file_tool.read("/path/to/file.txt")

# Escrever arquivo
await file_tool.write("/path/to/file.txt", "conteúdo")

# Editar arquivo
await file_tool.edit("/path/to/file.txt", [
    {"find": "antigo", "replace": "novo"}
])
```

### Plan Tool

```python
from src.tools import plan_tool

# Criar plano
await plan_tool.update(
    goal="Criar aplicação web",
    phases=[
        {"id": 1, "title": "Setup", "capabilities": {}},
        {"id": 2, "title": "Desenvolvimento", "capabilities": {}},
        {"id": 3, "title": "Deploy", "capabilities": {}}
    ]
)

# Avançar fase
await plan_tool.advance(current_phase_id=1, next_phase_id=2)
```

## 🧪 Testes

### Estrutura de Testes

- **Unit Tests**: 45 testes (core, modules)
- **Security Tests**: 26 testes (auth, rate limiting, RBAC)
- **Integration Tests**: 10 testes (API, database)
- **E2E Tests**: 5 testes (fluxos completos)

### Executar Testes Específicos

```bash
# Testes de segurança
pytest tests/unit/test_security_authorization.py -v

# Testes de RAG
pytest tests/unit/test_rag_system.py -v

# Testes de integração
pytest tests/integration/ -v
```

## 📈 Roadmap

### Fase 1: Consolidação ✅
- [x] Análise de todos os branches
- [x] Consolidação do código
- [x] Limpeza de redundâncias
- [x] Sistema de segurança

### Fase 2: Ferramentas ✅
- [x] Shell Tool
- [x] File Tool
- [x] Search Tool
- [x] Plan Tool
- [x] Message Tool

### Fase 3: Multimodal 📋
- [ ] Image Generation
- [ ] Slides Generation
- [ ] Diagram Generation

### Fase 4: DevOps 📋
- [ ] CI/CD Pipeline
- [ ] Infrastructure as Code
- [ ] Monitoring & Alerting

### Fase 5: Produção 📋
- [ ] Load Testing
- [ ] Security Audit
- [ ] Performance Optimization
- [ ] Deploy em Staging
- [ ] Deploy em Produção

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Ver `LICENSE` para mais informações.

## 🙏 Agradecimentos

- **Manus AI** - Inspiração para arquitetura e ferramentas
- **OpenAI** - GPT-4 e APIs
- **Anthropic** - Claude
- **Google** - Gemini
- Comunidade open source

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-repo/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-repo/discussions)
- **Email**: suporte@example.com

---

**Status do Projeto**: 🟢 Ativo | **Versão**: 1.0.0 | **Última Atualização**: 2025-11-01

## 🧰 Ferramentas do Desenvolvedor

Adicionamos um script auxiliar para desenvolvedores que aplica formatação, checa tipos e executa testes locais usando a invocação do módulo Python (evita problemas com executáveis da plataforma):

PowerShell (na raiz do projeto):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ci_fix.ps1
```

O script tenta instalar (se necessário) e executar: ruff, isort, mypy e pytest usando `python -m ...`. Se não quiser executar o script, rode os comandos manualmente com `python -m ruff`, `python -m isort`, `python -m mypy` e `python -m pytest`.

Também há uma nova ferramenta implementada no código: `PlanTool` disponível em `gamma_engine.tools.plan_tool`. Ela foi adicionada ao registro de tools e pode ser usada pelo agente para gerenciar planos multi-fase.
