# Project Structure - Hexagonal Architecture

This project follows the **Hexagonal Architecture** (also known as Ports and Adapters) pattern, which promotes separation of concerns and makes the application independent of external frameworks, databases, and UI.

## 📁 Project Structure

```
hexa/
├── 📂 data/
├── 📂 dockerfile/
├── 📂 logs/
├── 📂 notebooks/
├── 📂 src/
│   ├── 📂 application/
│   │   ├── 📂 agents/
│   │   ├── 📂 dto/
│   │   ├── 📂 prompts/
│   │   ├── 📂 services/
│   │   ├── 📂 usecases/
│   │   └── 📄 __init__.py
│   ├── 📂 domain/
│   │   ├── 📂 repositories/
│   │   └── 📄 __init__.py
│   ├── 📂 infrastructure/
│   │   ├── 📂 AI/
│   │   ├── 📂 connections/
│   │   ├── 📂 database/
│   │   ├── 📂 external/
│   │   ├── 📄 __init__.py
│   │   └── 📄 logging_config.py
│   └── 📂 interface/
│       ├── 📂 cli/
│       ├── 📂 http/
│       └── 📄 __init__.py
├── 📂 test/
└── 📄 README.md
```

## 🏗️ Architecture Layers

### `src/` - Source Code Directory

#### 🎯 `domain/`
**The Core - Business Logic Layer**

This is the heart of your hexagonal architecture and contains:
- **Entities**: Core business objects and models (e.g., User, Order, Product)
- **Value Objects**: Immutable objects representing domain concepts
- **Business Rules**: Pure business logic without any external dependencies
- **Domain Services**: Complex business operations that don't naturally fit in entities
- **Domain Events**: Important occurrences in the business process

**Current Structure:**
- `repositories/` - **Port interfaces** (abstract base classes/protocols) that define how to persist domain entities

**⚠️ Note**: Repository interfaces belong here, but implementations go in `infrastructure/database/`

**Key Principle**: This layer has NO dependencies on any other layer and knows nothing about databases, APIs, or frameworks.

---

#### 🔌 `application/`
**Use Cases & Application Services Layer**

Contains the application-specific business rules and orchestrates the flow of data.

**Current Structure:**

- **`agents/`** - AI agent orchestration and workflow logic
  - Agent definitions and behaviors
  - Multi-agent coordination
  - Agent decision-making logic

- **`dto/`** - Data Transfer Objects
  - Request/Response models
  - Data structures for inter-layer communication
  - Validation schemas

- **`prompts/`** - AI prompt templates and management
  - Prompt templates for LLM interactions
  - Prompt versioning and configuration
  - Prompt engineering logic

- **`services/`** - Application services
  - Coordinate domain objects to fulfill use cases
  - Orchestrate multiple domain operations
  - Handle cross-cutting application concerns

- **`usecases/`** - Specific business use cases
  - Single-purpose operations (e.g., CreateUser, ProcessOrder)
  - Input/Output port definitions
  - Use case interactors

**Key Principle**: Depends only on the domain layer. Defines what the application does, not how it does it.

---

#### 🔧 `infrastructure/`
**External Adapters & Implementation Layer**

Contains implementations of the ports defined in the application and domain layers.

**Current Structure:**

- **`AI/`** - AI/ML service implementations
  - LLM integrations (OpenAI, Anthropic, etc.)
  - Model wrappers and adapters
  - AI service configurations
  - Vector database connections

- **`connections/`** - External connection management
  - Connection pools
  - Client configurations
  - Authentication handlers
  - Retry and circuit breaker logic

- **`database/`** - Database implementations
  - Repository implementations (concrete classes)
  - ORM models and mappings
  - Database migrations
  - Query builders

- **`external/`** - Third-party service integrations
  - Payment gateways
  - Email services
  - SMS providers
  - External APIs

- **`logging_config.py`** - Centralized logging configuration
  - Log formatters
  - Log handlers
  - Logging levels
  - Structured logging setup

**Key Principle**: Implements the output ports. Can be replaced without affecting the domain or application layers.

---

#### 🌐 `interface/`
**Entry Points & Delivery Mechanisms Layer**

Contains all the ways external actors interact with your application.

**Current Structure:**

- **`cli/`** - Command-line interface
  - CLI commands and arguments
  - Terminal user interactions
  - Script runners

- **`http/`** - HTTP/REST API interface
  - API endpoints and routes
  - Request/Response handlers
  - HTTP middleware
  - API documentation

**Potential additions:**
- `graphql/` - GraphQL resolvers
- `grpc/` - gRPC services
- `websocket/` - WebSocket handlers
- `events/` - Message queue consumers

**Key Principle**: Implements the input ports. Translates external requests into application use cases.

---

## 📦 Supporting Directories

### `data/`
Contains application data files:
- Sample datasets
- Seed data
- Static files
- Test fixtures

### `dockerfile/`
Docker configuration files:
- Dockerfiles for different environments
- Docker Compose configurations
- Container orchestration files

### `logs/`
Application log files:
- Runtime logs
- Error logs
- Audit logs
- Debug traces

### `notebooks/`
Jupyter notebooks for:
- Data analysis
- Experimentation
- Documentation
- Prototyping

### `test/`
All test files mirroring the src structure:
- `test/unit/` - Unit tests
- `test/integration/` - Integration tests
- `test/e2e/` - End-to-end tests
- Test utilities and fixtures
- Mock implementations

---

## 🔄 Dependency Flow

```
interface (cli, http) 
    ↓
application (usecases, services, agents, prompts, dto)
    ↓
domain (entities, repositories interfaces)
    ↑
infrastructure (AI, database, connections, external)
```

**Dependency Rules:**
1. ✅ **Domain** has no dependencies on other layers
2. ✅ **Application** depends only on domain
3. ✅ **Infrastructure** implements domain ports (repositories) and application ports
4. ✅ **Interface** depends on application (calls use cases)
5. ✅ Dependencies always point inward toward the domain

---

## 🎯 Your Implementation Strengths

✅ **Clean Layer Separation** - Clear distinction between all four layers
✅ **Agent-Based Architecture** - Well-organized AI agent structure
✅ **Prompt Management** - Separated prompt engineering concerns
✅ **Multiple Interfaces** - Support for both CLI and HTTP
✅ **Repository Pattern** - Proper use of repository interfaces in domain

---

## ⚠️ Architectural Observations & Recommendations

### 1. **Domain Layer Needs More Content**
**Current Issue**: Your domain layer only has `repositories/` folder

**Recommendations**:
```
domain/
├── entities/           # Add your core business entities
│   ├── user.py
│   ├── agent.py
│   └── conversation.py
├── value_objects/      # Add immutable domain concepts
│   ├── email.py
│   └── agent_role.py
├── services/          # Add domain services (pure business logic)
│   └── agent_validator.py
├── repositories/      # ✅ Already have this (port interfaces)
│   └── agent_repository.py
└── events/           # Optional: domain events
    └── agent_created.py
```

**Why**: The domain should contain your core business models and rules, not just repository interfaces.

---

### 2. **`prompts/` Location Question**
**Current**: `prompts/` is in the application layer

**Consider**: Prompts might belong in different places depending on their nature:
- **Application Layer** ✅ - If prompts are templates used by use cases
- **Infrastructure Layer** - If prompts are external configurations
- **Domain Layer** - If prompts define core business behavior

**Your current placement is fine** if prompts are use-case specific templates.

---

### 3. **`agents/` Clarity**
**Question**: Are agents:
- Application services that orchestrate use cases? → Keep in `application/`
- Domain entities representing agent concepts? → Move to `domain/entities/`

**Recommendation**: 
```
domain/
├── entities/
│   └── agent.py          # Agent as a domain concept

application/
├── agents/
│   └── agent_executor.py  # Agent execution logic
```

---

### 4. **Missing Utils**
You don't have a `utils/` folder. Consider adding:
```
src/
├── utils/
│   ├── validators.py
│   ├── formatters.py
│   ├── constants.py
│   └── exceptions.py
```

---

### 5. **DTOs Consideration**
**Current**: `dto/` is in application layer ✅

**Best Practice**: Consider organizing by layer:
```
application/
├── dto/
│   ├── requests/      # Input DTOs from interface layer
│   ├── responses/     # Output DTOs to interface layer
│   └── internal/      # DTOs between application components
```

---

## 🚀 Recommended Next Steps

1. **Populate Domain Layer**
   - Add your core entities
   - Define value objects
   - Create domain services with business logic

2. **Add Missing Entity Classes**
   - What are your core business objects?
   - User? Agent? Conversation? Task?

3. **Create Repository Implementations**
   - Implement repository interfaces in `infrastructure/database/`

4. **Add Utils Folder**
   - Common validators, exceptions, constants

5. **Document Your Agents**
   - What type of agents are you building?
   - What's their purpose and workflow?

6. **Add Integration Tests**
   - Test the flow from interface → application → infrastructure

---

## 💡 Example Flow

Here's how a request should flow through your architecture:

```
1. HTTP Request arrives at interface/http/
2. Controller calls a use case in application/usecases/
3. Use case uses application/agents/ to orchestrate
4. Agent uses application/prompts/ for LLM interaction
5. Use case interacts with domain/entities/
6. Use case calls domain/repositories/ interface
7. Infrastructure/database/ implements the repository
8. Infrastructure/AI/ handles LLM calls
9. Response flows back through the layers
```

---

## 📚 Benefits of This Architecture

- **Independence**: Core business logic is isolated from external concerns
- **Testability**: Easy to test each layer independently
- **Flexibility**: Easy to swap LLM providers, databases, or interfaces
- **Maintainability**: Clear separation of concerns
- **Business-Focused**: Domain logic is the center, not technical details
- **AI-Ready**: Clean separation between AI infrastructure and business logic

---

## 🚀 Getting Started

[Add your specific setup instructions here]

## 📝 License

[Add your license information here]