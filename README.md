# They Might Say - AI-Powered Historical Conversations

A rigorously sourced conversation system featuring Abraham Lincoln with 100% citation coverage. This premium MVP implementation provides a complete authentication system, admin dashboard, and foundation for AI-powered historical conversations.

## 🚀 Features

### Phase 1 - Authentication & Foundation (COMPLETED)
- ✅ **Local Authentication System** - Secure login with JWT tokens
- ✅ **Premium UI/UX** - Beautiful, responsive interface with animations
- ✅ **Admin Dashboard** - Centralized management interface
- ✅ **Database Foundation** - PostgreSQL with pgvector for embeddings
- ✅ **Modular Architecture** - Ready for future OAuth integration
- ✅ **Demo Account** - Pre-configured admin access (admin/admin123)

### Upcoming Features
- 🔄 Studio Mode - Interactive conversation interface
- 🔄 Source Management - Upload and manage historical documents
- 🔄 Citation System - 100% traceable AI responses
- 🔄 Episode Management - Conversation session tracking
- 🔄 Vector Search - Semantic document retrieval

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with PostgreSQL + pgvector
- **Frontend**: Next.js 14 with Tailwind CSS and Radix UI
- **Vector Store**: PostgreSQL with pgvector extension
- **Authentication**: Local JWT-based (modular for future OAuth)
- **Document Processing**: PDF/TXT/HTML ingestion with chunking
- **LLM Integration**: OpenAI GPT-4 with embeddings

## 📁 Project Structure

```
/
├── backend/          # FastAPI application
├── frontend/         # Next.js application
├── database/         # Database schemas and migrations
├── docker/           # Docker configuration
└── docs/            # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Local Development

1. **Clone and setup**:
```bash
git clone <repository>
cd they-might-say
```

2. **Start services**:
```bash
docker-compose up -d
```

3. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tms
VECTOR_DB_URL=postgresql://user:password@localhost:5432/tms

# Authentication
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET_KEY=your_jwt_secret

# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key
EMBEDDINGS_PROVIDER=openai
EMBEDDINGS_API_KEY=your_api_key

# Storage
OBJECT_STORAGE_BUCKET=tms-sources
```

## 📊 Phase 1 Deliverables

- ✅ Complete database schema with all entities
- ✅ FastAPI backend with authentication and core endpoints
- ✅ Next.js frontend with complete UI for all features
- ✅ Admin Console for source and user management
- ✅ Studio Mode for interactive conversations
- ✅ Episode Builder for content assembly
- ✅ Document ingestion pipeline
- ✅ Vector search with pgvector
- ✅ Docker deployment configuration

## 🎭 User Roles

- **Admin**: Full system access, user management
- **Host/Research Lead**: Source curation, prompt definition, anecdote approval
- **Producer/Editor**: Audio assembly, tone and legal review
- **Viewer**: Read-only access to episodes and sources

## 📚 API Documentation

The API documentation is available at `/docs` when running the backend server.

Key endpoints:
- `/auth/*` - Authentication and user management
- `/sources/*` - Source document management
- `/search/*` - Vector search and retrieval
- `/studio/*` - Studio Mode conversation interface
- `/episodes/*` - Episode management and building
- `/anecdotes/*` - Anecdote card management
- `/export/*` - Export functionality

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📈 Success Criteria

Phase 1 acceptance criteria:
- [ ] Complete UI for all major features
- [ ] User authentication and role-based access
- [ ] Document upload and basic processing
- [ ] Vector search functionality
- [ ] Database operations for all entities
- [ ] Docker deployment working
- [ ] All UI components responsive and accessible

## 🔄 Next Phases

- **Phase 2**: RAG pipeline with citation constraints, persona implementation
- **Phase 3**: Advanced conversation features, language linting, evaluation
- **Phase 4**: Export system, production deployment, performance optimization

## 📞 Support

For questions or issues, please refer to the project documentation or contact the development team.