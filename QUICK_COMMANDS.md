# Quick Commands Reference

## 🧪 Run Tests (Fixed Database Permission Issue)

### Windows (PowerShell)
```powershell
$env:DJANGO_SETTINGS_MODULE = "core.test_settings"
python manage.py test skills.test_quest_autofill -v 2
```

### Windows (Command Prompt)
```cmd
run_tests.bat skills.test_quest_autofill
```

### Linux/Mac
```bash
bash run_tests.sh skills.test_quest_autofill
```

### Direct Command (All Platforms)
```bash
DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test skills.test_quest_autofill -v 2
```

## 🗄️ Database Migrations

```bash
# Apply all pending migrations
python manage.py migrate

# Apply specific app migrations
python manage.py migrate users

# Check migration status
python manage.py showmigrations

# Rollback to previous migration
python manage.py migrate users 0001
```

## 🚀 Start Development Services

### Terminal 1: Django Server
```bash
python manage.py runserver
```

### Terminal 2: Celery Worker
```bash
celery -A core worker -l info
```

### Terminal 3: Redis (if not running as service)
```bash
redis-server
```

### Terminal 4: Frontend Dev Server
```bash
cd frontend
npm run dev
```

## 🔗 API Testing

### Generate Skill Tree
```bash
curl -X POST http://localhost:8000/api/skills/generate/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python Basics", "depth": 2}'
```

### Check Tree Status
```bash
curl http://localhost:8000/api/skills/generated/TREE_ID/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Start Quest Auto-Fill
```bash
curl -X POST http://localhost:8000/api/skills/generated/TREE_ID/autofill-quests/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Update Onboarding Profile
```bash
curl -X POST http://localhost:8000/api/onboarding/update-profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "generated_topic": "Python Basics",
    "generated_tree_id": "TREE_ID",
    "path_generated": true
  }'
```

### Get Onboarding Profile
```bash
curl http://localhost:8000/api/onboarding/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🐍 Django Shell Commands

```bash
# Open Django shell
python manage.py shell

# Create test user
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.create_user('testuser', 'test@example.com', 'pass123')

# Create onboarding profile
from users.onboarding_models import OnboardingProfile
profile = OnboardingProfile.objects.create(
    user=user,
    primary_goal='job_prep',
    target_role='Developer',
    experience_years=2,
    category_levels={'algorithms': 'beginner'},
    selected_interests=['python'],
    weekly_hours=10
)

# Generate tree
from skills.ai_tree_generator import SkillTreeGeneratorService
service = SkillTreeGeneratorService()
result = service.generate_tree('Python', user, depth=2)
print(result)

# Check tree status
from skills.models import GeneratedSkillTree
tree = GeneratedSkillTree.objects.get(id=result['tree_id'])
print(tree.status)

# Auto-fill quests
from skills.quest_autofill import QuestAutoFillService
autofill = QuestAutoFillService()
autofill_result = autofill.autofill_quests_for_tree(str(tree.id))
print(autofill_result)
```

## 📊 Check Service Status

### Redis
```bash
redis-cli ping
# Should return: PONG
```

### LM Studio
```bash
curl http://localhost:1234/models
# Should return list of available models
```

### Celery
```bash
# In Django shell
from celery import current_app
current_app.control.inspect().active()
```

## 🔍 View Logs

### Django Logs
```bash
tail -f django.log
```

### Celery Logs
```bash
tail -f celery.log
```

### Redis Logs
```bash
redis-cli MONITOR
```

## 🧹 Clean Up

### Delete Test Database
```bash
rm db.sqlite3
```

### Clear Redis Cache
```bash
redis-cli FLUSHALL
```

### Clear Celery Queue
```bash
celery -A core purge
```

### Remove All Migrations (Dangerous!)
```bash
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
```

## 📦 Install Dependencies

### Backend
```bash
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## 🚢 Production Deployment

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Run Migrations
```bash
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Start Gunicorn
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Start Celery Worker
```bash
celery -A core worker -l info --concurrency=4
```

## 🐛 Debugging

### Enable Debug Mode
```bash
export DEBUG=True
python manage.py runserver
```

### Run Tests with Verbose Output
```bash
DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test skills.test_quest_autofill -v 3
```

### Check Database Queries
```python
# In Django shell
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as context:
    # Your code here
    pass

print(f"Queries: {len(context)}")
for query in context:
    print(query['sql'])
```

### Profile Code Performance
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## 📚 Documentation Files

- `IMPLEMENTATION_SUMMARY.md` - Complete overview
- `QUEST_AUTOFILL_QUICK_REFERENCE.md` - Quick reference
- `backend/skills/QUEST_AUTOFILL_README.md` - Full documentation
- `QUEST_AUTOFILL_INTEGRATION.md` - Integration guide
- `TESTING_AND_INTEGRATION_GUIDE.md` - Testing guide
- `QUICK_COMMANDS.md` - This file

## ✅ Verification Checklist

- [ ] Tests pass: `DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test skills.test_quest_autofill`
- [ ] Migrations applied: `python manage.py migrate`
- [ ] Redis running: `redis-cli ping`
- [ ] LM Studio running: `curl http://localhost:1234/models`
- [ ] Celery worker running: `celery -A core worker -l info`
- [ ] Django server running: `python manage.py runserver`
- [ ] Frontend dev server running: `npm run dev`
- [ ] API endpoints accessible
- [ ] WebSocket connections working
- [ ] Database updates persisting

## 🎯 Common Issues & Solutions

### Issue: "permission denied to create database"
**Solution:** Use test settings
```bash
DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test skills.test_quest_autofill
```

### Issue: "Redis connection refused"
**Solution:** Start Redis
```bash
redis-server
```

### Issue: "LM Studio not found"
**Solution:** Start LM Studio or check URL
```bash
curl http://localhost:1234/models
```

### Issue: "Celery task not executing"
**Solution:** Start Celery worker
```bash
celery -A core worker -l info
```

### Issue: "WebSocket connection failed"
**Solution:** Check Channels configuration and Redis
```bash
redis-cli ping
```

## 🚀 Ready to Go!

All commands are ready to use. Start with:
```bash
# 1. Run tests
DJANGO_SETTINGS_MODULE=core.test_settings python manage.py test skills.test_quest_autofill

# 2. Apply migrations
python manage.py migrate

# 3. Start services
python manage.py runserver &
celery -A core worker -l info &
redis-server &

# 4. Access frontend
# http://localhost:5173
```
