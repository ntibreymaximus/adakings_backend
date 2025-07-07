# Quick Railway Deployment Checklist

## Files Created for Railway Deployment:
✅ `Procfile` - Process file for Railway
✅ `railway.toml` - Railway configuration  
✅ `requirements-prod.txt` - Production dependencies
✅ `Dockerfile` - Container configuration
✅ `.env.production` - Environment variables template
✅ `nixpacks.toml` - Build configuration
✅ `RAILWAY_DEPLOYMENT.md` - Detailed deployment guide

## Quick Deploy Steps:

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 2. Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add PostgreSQL database: "New Service" → "Database" → "PostgreSQL"

### 3. Set Environment Variables
In Railway dashboard → Variables tab, add:
```
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DATABASE_ENGINE=postgresql
SECURE_SSL_REDIRECT=True
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### 4. Deploy!
Railway will automatically:
- Install dependencies
- Run migrations
- Start your Django app
- Provide a public URL

## After Deployment:
1. Visit `/health/` to verify deployment
2. Create a superuser via Railway console
3. Test your API endpoints
4. Update frontend to use new backend URL

## Need Help?
See `RAILWAY_DEPLOYMENT.md` for detailed instructions.
