# LLM Nova e Hydra - Master Branch

> Sistema completo de agente autônomo baseado em LLM com arquitetura cognitiva avançada, sistema RAG melhorado, multi-agente e interface moderna.

## 🚀 Características Principais

### Backend
- **Arquitetura Cognitiva Avançada**: Sistema de planejamento hierárquico e raciocínio
- **Multi-LLM Engine**: Suporte para múltiplos modelos LLM (OpenAI, Anthropic, Google, etc.)
- **Sistema RAG Melhorado**: Enhanced RAG com reranking e pipeline otimizado
- **Multi-Agent System**: Coordenação de múltiplos agentes especializados
- **Multimodal Processing**: Processamento de texto, imagem, áudio e vídeo
- **Sandbox Environment**: Ambiente isolado para execução segura
- **Security & Alignment**: Sistema de segurança e alinhamento
- **Monitoring & Observability**: Backstage panel e OpenTelemetry

### Frontend
- **Interface React Moderna**: UI responsiva e intuitiva
- **Real-time Updates**: Atualizações em tempo real via WebSocket
- **Healthcheck Dashboard**: Monitoramento visual do sistema
- **Componentes Otimizados**: Componentes React reutilizáveis

### Infraestrutura
- **Docker Completo**: Containerização com Docker Compose
- **Configurações de Produção**: Otimizações para ambiente de produção
- **Scripts de Deploy**: Automação de deploy e backup
- **Testes Abrangentes**: Suite de testes unitários e integração

## 📁 Estrutura do Projeto

```
llmnova-hydra-project/
├── backend/
│   ├── src/
│   │   ├── core/              # Motor principal do agente
│   │   ├── modules/           # Módulos especializados
│   │   ├── api/               # API FastAPI
│   │   ├── rag/               # Sistema RAG melhorado
│   │   ├── monitoring/        # Backstage panel e observability
│   │   ├── tools/             # Ferramentas do agente
│   │   └── agent/             # Implementações de agentes
│   ├── config/                # Configurações
│   ├── tests/                 # Testes
│   ├── requirements.txt
│   └── run_agent.py
├── frontend/
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/             # Páginas
│   │   └── hooks/             # React hooks
│   ├── public/
│   └── package.json
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   └── docker-compose.production.yml
├── docs/                      # Documentação completa
├── scripts/                   # Scripts de automação
└── README.md
```

## 🛠️ Instalação

### Pré-requisitos
- Docker e Docker Compose
- Node.js 18+ (para desenvolvimento frontend)
- Python 3.11+ (para desenvolvimento backend)

### Instalação Rápida com Docker

```bash
# Clonar o repositório
git clone <repository-url>
cd agente-llm-autonomo-master

# Copiar variáveis de ambiente
cp backend/.env.example backend/.env

# Configurar suas chaves de API no .env
# OPENAI_API_KEY=sua_chave_aqui

# Iniciar com Docker Compose
docker-compose up -d

# Acessar a aplicação
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Docs API: http://localhost:8000/docs
```

### Instalação para Desenvolvimento

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

pip install -r requirements.txt
python src/main.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentação

Consulte a pasta `docs/` para documentação detalhada:

- **INSTALACAO_RAPIDA.md**: Guia de instalação rápida
- **MANUAL_COMPLETO_AGENTE_LLM.md**: Manual completo do sistema
- **GUIA_COMPLETO_INSTALACAO_USO.md**: Guia completo de instalação e uso
- **MELHORIAS_IMPLEMENTADAS_V3.md**: Melhorias da versão 3
- **ARQUITETURA.md**: Arquitetura do sistema

## 🧪 Testes

```bash
# Backend
cd backend
pytest tests/

# Frontend
cd frontend
npm test
```

## 🚀 Deploy em Produção

```bash
# Usar configuração de produção
docker-compose -f docker/docker-compose.production.yml up -d

# Ou usar script de deploy
./scripts/deploy-production.sh
```

## 🔧 Configuração

### Variáveis de Ambiente

Principais variáveis no arquivo `.env`:

```env
# LLM Configuration
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379

# Application
DEBUG=False
LOG_LEVEL=INFO
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🙏 Agradecimentos

Este projeto consolidou features de múltiplos branches:
- `feature-agent-reimplementation`: Base principal
- `agente_llm_melhorado_v3_completo`: Sistema RAG melhorado e Monitoring
- `refactor-comprehensive-code-quality-improvements`: Melhorias de qualidade
- `production-ready-fixes`: Configurações de produção
- `feat-frontend-refactor`: Frontend otimizado

## 📞 Suporte

Para suporte, abra uma issue no GitHub ou entre em contato através de [seu-email@exemplo.com]

---

**Desenvolvido com ❤️ pela comunidade**
