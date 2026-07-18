# Free Cloud Deployment Guide

Deploy X-DMRA Rescue to free cloud services (Neon PostgreSQL, Render, Vercel).

## Prerequisites

- GitHub account
- Node.js 18+
- Python 3.10+

---

## Step 1: Create Neon PostgreSQL Project

1. Go to [Neon Console](https://neon.tech)
2. Sign up / Log in (free tier available)
3. Click **New Project**
4. Configure:
   - Project name: `xdmra-rescue`
   - Region: Choose nearest to your users
   - PostgreSQL version: 15 (default)
5. Click **Create Project**

## Step 2: Copy the Pooled Connection String

1. In the Neon dashboard, go to **Connection Details**
2. Select **Pooled connection string** (recommended for serverless/ Render)
3. Copy the connection string - it looks like:

```
postgresql://username:password@ep-xxxxxxxx-xxxxxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

4. **Keep this string private** - it contains database credentials

## Step 3: Keep the Connection String Private

Never commit or share the connection string. In Step 7 you will add it to Render as a secret environment variable.

---

## Step 4: Run Database Initialization

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/x-dmra-rescue.git
cd x-dmra-rescue/backend
```

2. Create a `.env` file:

```bash
cp .env.example .env
```

3. Set your database URL:

```bash
# Windows
set DATABASE_URL=postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# macOS/Linux
export DATABASE_URL="postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"
```

4. Initialize tables (creates all tables without demo data):

```bash
python -m scripts.init_db
```

Expected output:
```
Initializing database tables...
Database tables initialized successfully.
```

---

## Step 5: Create the Production Administrator

1. In the `backend` directory, run:

```bash
python -m scripts.create_admin --name "Admin Name" --email admin@example.com --password "YourSecurePassword123"
```

2. Expected output:

```
Administrator account created successfully:
  Name:  Admin Name
  Email: admin@example.com
  Role:  admin
  ID:    1
```

3. Save the credentials securely - you will need them to log in after deployment.

**Security notes:**
- The password is hashed before storage
- The password is never printed or logged
- The database connection string is never printed

---

## Step 6: Create Render Backend Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** and select **Blueprint**
3. Connect your GitHub repository
4. Select the `render.yaml` file from the repository root
5. Click **Apply**

---

## Step 7: Add Render Environment Variables

In the Render dashboard, go to your service's **Environment** tab and add:

### Secrets (set values manually - do not commit real values)

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Your Neon pooled connection string (from Step 2) |
| `JWT_SECRET` | Generate a strong random string (e.g., 64+ characters) |
| `FRONTEND_ORIGIN` | Your Vercel frontend URL (set after Step 12) |
| `ALLOWED_ORIGINS` | Same as FRONTEND_ORIGIN for now |

### Committed values (already set in render.yaml)

| Key | Value |
|-----|-------|
| `ENVIRONMENT` | `production` |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `MIN_PASSWORD_LENGTH` | `8` |

---

## Step 8: Deploy and Verify /api/health

1. Render will automatically deploy from the `master` branch
2. Wait for the deployment to complete
3. Visit your backend health endpoint:

```
https://your-backend.onrender.com/api/health
```

4. Expected response:

```json
{"status":"ok"}
```

---

## Step 9: Create Vercel Frontend Project

1. Go to [Vercel Dashboard](https://vercel.com)
2. Click **Add New...** → **Project**
3. Import your GitHub repository
4. For **Root Directory**, select `frontend`
5. Click **Deploy**

---

## Step 10: Set VITE_API_URL

1. In Vercel project settings, go to **Environment Variables**
2. Add:

| Name | Value |
|------|-------|
| `VITE_API_URL` | `https://your-backend.onrender.com/api` |

3. Redeploy the frontend for the change to take effect

---

## Step 11: Deploy Frontend

1. Vercel auto-deploys on every push to `master`
2. Wait for deployment to complete
3. Note your frontend URL (e.g., `https://x-dmra-rescue.vercel.app`)

---

## Step 12: Copy the Vercel URL

Your deployed frontend URL is shown on the Vercel project dashboard. Copy it for the next step.

Example: `https://x-dmra-rescue.vercel.app`

---

## Step 13: Update Render FRONTEND_ORIGIN and ALLOWED_ORIGINS

1. Go back to Render dashboard
2. Go to your backend service's **Environment** tab
3. Update:

| Key | New Value |
|-----|-----------|
| `FRONTEND_ORIGIN` | `https://x-dmra-rescue.vercel.app` |
| `ALLOWED_ORIGINS` | `https://x-dmra-rescue.vercel.app` |

4. Redeploy the backend

---

## Step 14: Redeploy Backend

1. In Render, go to your backend service
2. Click **Manual Deploy** → **Deploy latest commit**
3. Wait for deployment to complete

---

## Step 15: Test Login and Complete Workflow

1. Open your Vercel frontend URL
2. Navigate to `/login`
3. Log in with the administrator credentials you created in Step 5
4. Verify:
   - Dashboard loads correctly
   - Incidents, Teams, and other features work
   - API calls go to your Render backend (check browser DevTools Network tab)

---

## Step 16: Rotate Compromised Secrets

If a secret is ever exposed:

### Neon Database Password
1. In Neon console, go to **Settings** → **Connection Details**
2. Click **Reset password**
3. Update `DATABASE_URL` in Render with the new password

### JWT Secret
1. Generate a new strong random string
2. Update `JWT_SECRET` in Render
3. All existing tokens become invalid - users must log in again

### FRONTEND_ORIGIN / ALLOWED_ORIGINS
1. Update the values in Render
2. Redeploy the backend

---

## Step 17: Neon Backup and Export

### Manual Backup
1. In Neon console, go to your project
2. Click **Backups**
3. Click **Create Backup** for manual snapshots

### Export Data
Use `pg_dump` with your Neon connection string:

```bash
pg_dump "postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" > backup.sql
```

### Branching for Development
Neon allows branching - create a development branch from the dashboard to test without affecting production.

---

## Step 18: Free-Tier Cold Start Limitation

### What Happens
Free-tier services on Render and Vercel spin down after inactivity. The first request after dormancy may take **30-60 seconds** to respond as the service wakes up.

### Expected Behavior
1. First request after idle → long response time or timeout
2. Subsequent requests → normal response times
3. Periodic pings → can keep services awake (some automation services offer this)

### Mitigation Options
- Upgrade to paid plans for always-on instances
- Use a free uptime monitoring service (e.g., UptimeRobot) to ping your backend every 25 minutes
- Accept cold starts as a limitation of free deployment

---

## Architecture Summary

```
Browser
   |
   v
Vercel Frontend (React)
   |
   | VITE_API_URL
   v
Render Backend (FastAPI)
   |
   | DATABASE_URL
   v
Neon PostgreSQL (Pooled)
```

---

## Environment Variables Reference

### Backend (Render)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection | `postgresql://user:pass@ep-xxx...` |
| `JWT_SECRET` | Token signing secret | `your-64-char-random-string` |
| `ENVIRONMENT` | Runtime environment | `production` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `MIN_PASSWORD_LENGTH` | Minimum password length | `8` |
| `FRONTEND_ORIGIN` | Vercel frontend URL | `https://x-dmra.vercel.app` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `https://x-dmra.vercel.app` |

### Frontend (Vercel)

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `https://x-dmra-api.onrender.com/api` |

---

## Troubleshooting

### Health check fails
- Verify `DATABASE_URL` is correct and set in Render
- Check Render logs for startup errors

### CORS errors
- Verify `FRONTEND_ORIGIN` and `ALLOWED_ORIGINS` match exactly (including https://)
- Ensure no trailing slashes

### 401 Unauthorized on API calls
- JWT_SECRET may not match between Render and frontend expectations
- Clear browser session storage and log in again

### Frontend shows "Health check failed"
- Verify `VITE_API_URL` ends with `/api`
- Check browser console for specific error messages