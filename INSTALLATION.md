# 🚀 Installation & Setup Guide

## 📋 **Prerequisites**

### **System Requirements**
- **Operating System**: macOS, Linux, or Windows
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for dependencies

### **Required Software**
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check pip
pip --version

# Optional: Check git
git --version
```

## 🔧 **Quick Installation**

### **1. Clone Repository**
```bash
git clone <your-repo-url>
cd CascadeProjects
```

### **2. Automated Setup**
```bash
# Make scripts executable
chmod +x start_complete_system.sh stop_complete_system.sh

# Start complete system (installs dependencies automatically)
./start_complete_system.sh
```

### **3. Access System**
- **Main Interface**: http://localhost:3000
- **Simple Test**: http://localhost:3000/static/simple.html
- **API Docs**: http://localhost:3000/docs

---

## 🔨 **Manual Installation**

### **Phase 1: Smart Triage & Scheduling**

```bash
# Navigate to Phase 1
cd phase1-scheduling-system

# Install dependencies
pip install fastapi uvicorn python-multipart pydantic python-dotenv
pip install httpx python-jose passlib bcrypt pandas numpy
pip install sentence-transformers faiss-cpu email-validator

# Create storage directories
mkdir -p storage data
touch storage/users.txt storage/doctors.txt storage/patients.txt
touch storage/appointments.txt storage/triage_assessments.txt

# Start Phase 1
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### **Phase 2: No-Show Prevention (Optional)**

```bash
# Navigate to Phase 2
cd patient-noshow-prevention

# Install dependencies
pip install -r requirements.txt

# Setup PostgreSQL (if needed)
# brew install postgresql  # macOS
# sudo apt-get install postgresql  # Ubuntu

# Start Phase 2
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🧪 **Verification & Testing**

### **1. System Health Check**
```bash
# Check Phase 1
curl http://localhost:3000/health

# Expected response:
# {"status":"healthy","timestamp":"2024-..."}
```

### **2. Run Integration Tests**
```bash
cd phase1-scheduling-system
python test_complete_system.py
```

### **3. Manual Testing**
1. Open http://localhost:3000/static/simple.html
2. Click "Check System Health" → Should show ✅
3. Register a doctor → Should return doctor ID
4. Register a patient → Should return patient ID
5. Perform triage → Should return priority assessment

---

## 🐳 **Docker Installation (Alternative)**

### **Create Dockerfile for Phase 1**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
```

### **Docker Compose**
```yaml
version: '3.8'
services:
  phase1:
    build: ./phase1-scheduling-system
    ports:
      - "3000:3000"
    volumes:
      - ./phase1-scheduling-system/storage:/app/storage
  
  phase2:
    build: ./patient-noshow-prevention
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/healthcare
  
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=healthcare
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 🔧 **Configuration**

### **Environment Variables**
Create `.env` files in each phase directory:

**Phase 1 (.env)**
```env
# Phase 1 Configuration
DATABASE_URL=file://storage/
PHASE2_API_URL=http://localhost:8000

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# AI Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
TRIAGE_PROTOCOLS_FILE=data/triage_protocols.csv

# Logging
LOG_LEVEL=INFO
```

**Phase 2 (.env)**
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/healthcare
REDIS_URL=redis://localhost:6379

# ML Model
MODEL_PATH=models/noshow_model.pkl
RETRAIN_SCHEDULE=0 2 * * *  # Daily at 2 AM

# Communication
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
SENDGRID_API_KEY=your_sendgrid_key

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Kill processes on ports
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

#### **Module Not Found**
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### **Permission Denied**
```bash
# Fix script permissions
chmod +x *.sh
```

#### **Database Connection Error**
```bash
# Check PostgreSQL status
brew services start postgresql  # macOS
sudo service postgresql start   # Linux
```

### **Debug Mode**
```bash
# Start with debug logging
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload --log-level debug
```

### **Health Checks**
```bash
# System status
curl http://localhost:3000/health
curl http://localhost:8000/health

# API documentation
open http://localhost:3000/docs
open http://localhost:8000/docs
```

---

## 🔄 **Updates & Maintenance**

### **Update Dependencies**
```bash
# Update Python packages
pip install --upgrade -r requirements.txt

# Check for security vulnerabilities
pip audit
```

### **Backup Data**
```bash
# Backup Phase 1 data
cp -r phase1-scheduling-system/storage/ backup/storage-$(date +%Y%m%d)

# Backup Phase 2 database
pg_dump healthcare > backup/healthcare-$(date +%Y%m%d).sql
```

### **Monitor Logs**
```bash
# View real-time logs
tail -f phase1.log
tail -f phase2.log

# Search logs
grep "ERROR" phase1.log
grep "WARNING" phase2.log
```

---

## 📞 **Support**

### **Getting Help**
1. Check the logs: `phase1.log`, `phase2.log`
2. Verify system health: http://localhost:3000/health
3. Test with simple interface: http://localhost:3000/static/simple.html
4. Review API documentation: http://localhost:3000/docs

### **Common Commands**
```bash
# Start system
./start_complete_system.sh

# Stop system
./stop_complete_system.sh

# Restart Phase 1 only
cd phase1-scheduling-system && ./start.sh

# View system status
ps aux | grep uvicorn
lsof -i :3000
lsof -i :8000
```

---

**🎉 You're ready to use the Complete Healthcare System!** 🏥✨
