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
│   ├── 📂 domain/
│   ├── 📂 infrastructure/
│   ├── 📂 interface/
│   └── 📂 utils/
├── 📂 test/
└── 📄 README.md
```

## 🏗️ Architecture Layers

### `src/` - Source Code Directory

#### 🎯 `domain/`
**The Core - Business Logic Layer**

This is the heart of your hexagonal architecture and contains:
- **Entities**: Core business objects and models
- **Value Objects**: Immutable objects representing domain concepts
- **Business Rules**: Pure business logic without any external dependencies
- **Domain Services**: Complex business operations that don't naturally fit in entities
- **Domain Events**: Important occurrences in the business process

**Key Principle**: This layer has NO dependencies on any other layer and knows nothing about databases, APIs, or frameworks.

#### 🔌 `application/`
**Use Cases & Application Services Layer**

Contains the application-specific business rules and orchestrates the flow of data:
- **Use Cases**: Specific application operations (e.g., CreateUser, ProcessOrder)
- **Application Services**: Coordinate domain objects to fulfill use cases
- **Port Interfaces**: Define contracts (interfaces) for external dependencies
  - **Input Ports**: Interfaces for driving the application (e.g., use case interfaces)
  - **Output Ports**: Interfaces for driven adapters (e.g., repository interfaces, external service interfaces)
- **DTOs**: Data Transfer Objects for communication between layers
- **Mappers**: Convert between domain models and DTOs

**Key Principle**: Depends only on the domain layer. Defines what the application does, not how it does it.

#### 🔧 `infrastructure/`
**External Adapters & Implementation Layer**

Contains implementations of the ports defined in the application layer:
- **Database Adapters**: Concrete implementations of repository interfaces (PostgreSQL, MongoDB, etc.)
- **External Services**: Third-party API integrations (payment gateways, email services)
- **Persistence**: ORM configurations, database migrations, queries
- **Message Brokers**: Kafka, RabbitMQ implementations
- **File Storage**: S3, local file system implementations
- **Configuration**: Application settings, environment variables

**Key Principle**: Implements the output ports. Can be replaced without affecting the domain or application layers.

#### 🌐 `interface/`
**Entry Points & Delivery Mechanisms Layer**

Contains all the ways external actors interact with your application:
- **REST API Controllers**: HTTP endpoints and request handlers
- **GraphQL Resolvers**: GraphQL schema and resolvers
- **CLI Commands**: Command-line interface implementations
- **Message Consumers**: Event/message queue consumers
- **gRPC Services**: gRPC server implementations
- **WebSocket Handlers**: Real-time communication handlers
- **Request/Response Models**: API-specific data structures
- **Middleware**: Authentication, logging, error handling

**Key Principle**: Implements the input ports. Translates external requests into application use cases.

#### 🛠️ `utils/`
**Shared Utilities & Helpers**

Common utilities used across layers:
- **Helpers**: Generic helper functions
- **Constants**: Application-wide constants
- **Validators**: Reusable validation logic
- **Formatters**: Data formatting utilities
- **Decorators**: Common decorators/annotations
- **Exceptions**: Custom exception classes

**Key Principle**: Should contain only pure functions with no business logic.

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
All test files:
- Unit tests
- Integration tests
- E2E tests
- Test utilities
- Mock implementations

---

## 🔄 Dependency Flow

```
interface → application → domain
              ↓
         infrastructure
```

**Key Rules:**
1. **Domain** has no dependencies on other layers
2. **Application** depends only on domain
3. **Infrastructure** depends on application (implements output ports)
4. **Interface** depends on application (implements input ports)
5. Dependencies always point inward toward the domain

---

## 🎯 Benefits of This Architecture

- **Independence**: Core business logic is isolated from external concerns
- **Testability**: Easy to test each layer independently
- **Flexibility**: Easy to swap databases, frameworks, or delivery mechanisms
- **Maintainability**: Clear separation of concerns
- **Business-Focused**: Domain logic is the center, not technical details
- **Scalability**: Different parts can evolve independently

---

## 🚀 Getting Started

[Add your specific setup instructions here]

## 📝 License

[Add your license information here]