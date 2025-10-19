# Free Face Swap

## 🚀 Quick Deployment

### Frontend (Vercel)

1. **Install Vercel CLI:**

   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**

   ```bash
   vercel login
   ```

3. **Deploy:**

   ```bash
   cd deployment
   chmod +x deploy_frontend.sh
   ./deploy_frontend.sh
   ```

4. **Or deploy manually:**
   ```bash
   cd frontend/faceswap
   vercel --prod
   ```

### Set Environment Variables in Vercel Dashboard:

1. Go to: https://vercel.com/your-username/freefaceswap
2. Settings → Environment Variables
3. Add:
   - `BACKEND_API_URL` = `https://your-backend-url.com`

---

## 📦 Project Structure
