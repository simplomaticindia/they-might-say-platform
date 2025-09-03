# They Might Say - Deployment Guide

## 🚀 Quick Start (Recommended)

### Option 1: One-Command Start
```bash
./start.sh
```

### Option 2: Manual Docker Compose
```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

## 🔧 System Requirements

- **Docker**: 20.10+ with Docker Compose
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space
- **Network**: Ports 3000, 8000, 5432, 6379, 9000, 9001

## 🌐 Access Points

Once started, access these URLs:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main application |
| **Admin Dashboard** | http://localhost:3000/dashboard | Admin interface |
| **Backend API** | http://localhost:8000 | REST API |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs |
| **MinIO Console** | http://localhost:9001 | Object storage admin |

## 🔑 Demo Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Administrator (full access)

### MinIO Storage
- **Username**: `minioadmin`
- **Password**: `minioadmin123`

## 📊 Service Health Checks

### Check All Services
```bash
docker-compose ps
```

### Individual Service Logs
```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# Database logs
docker-compose logs -f postgres
```

### Health Endpoints
- **Backend**: `curl http://localhost:8000/health`
- **Database**: Check with `docker-compose ps postgres`
- **Redis**: Check with `docker-compose ps redis`

## 🔧 Common Operations

### Start/Stop System
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend
```

### Database Operations
```bash
# Access PostgreSQL
docker exec -it tms-postgres psql -U tms_user -d tms

# View database tables
docker exec -it tms-postgres psql -U tms_user -d tms -c "\dt"

# Reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d postgres
```

### View System Status
```bash
# All services status
docker-compose ps

# Resource usage
docker stats

# Service logs
docker-compose logs -f
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### 3. Frontend Build Errors
```bash
# Rebuild frontend
docker-compose build frontend

# Clear cache and rebuild
docker-compose build --no-cache frontend
```

#### 4. Backend API Errors
```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Check environment variables
docker-compose exec backend env | grep -E "(DATABASE|JWT|REDIS)"
```

### Service Dependencies

Services start in this order:
1. **PostgreSQL** (database)
2. **Redis** (caching)
3. **MinIO** (storage)
4. **Backend** (API server)
5. **Frontend** (web application)

If a service fails, dependent services may not work properly.

## 🔒 Security Considerations

### Development vs Production

This configuration is for **development/demo** use. For production:

1. **Change Default Passwords**
   ```bash
   # Edit .env file
   JWT_SECRET_KEY=your-production-secret-key
   # Change database passwords
   # Change MinIO credentials
   ```

2. **Enable HTTPS**
   - Add SSL certificates
   - Configure nginx reverse proxy
   - Update CORS settings

3. **Secure Database**
   - Use strong passwords
   - Enable SSL connections
   - Restrict network access

4. **Environment Variables**
   - Never commit .env files
   - Use secrets management
   - Rotate keys regularly

## 📈 Performance Tuning

### Database Optimization
```sql
-- Connect to PostgreSQL
docker exec -it tms-postgres psql -U tms_user -d tms

-- Check database size
SELECT pg_size_pretty(pg_database_size('tms'));

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM users;
```

### Resource Limits
Edit `docker-compose.yml` to add resource limits:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

## 🔄 Updates and Maintenance

### Update System
```bash
# Pull latest changes
git pull

# Rebuild services
docker-compose build

# Restart with new images
docker-compose up -d
```

### Backup Data
```bash
# Backup database
docker exec tms-postgres pg_dump -U tms_user tms > backup.sql

# Backup MinIO data
docker cp tms-minio:/data ./minio-backup
```

### Clean Up
```bash
# Remove unused Docker resources
docker system prune

# Remove all project containers and volumes
docker-compose down -v --remove-orphans
```

## 📞 Support

### Getting Help
1. Check this deployment guide
2. Review service logs: `docker-compose logs -f`
3. Check the main [README.md](README.md)
4. Review API documentation at http://localhost:8000/docs

### Reporting Issues
When reporting issues, include:
- Operating system and Docker version
- Output of `docker-compose ps`
- Relevant logs from `docker-compose logs`
- Steps to reproduce the issue

---

**They Might Say** - Your AI-powered historical conversation system is ready! 🎉