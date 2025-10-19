#!/bin/bash

# ============================================================
# Vercel Frontend Deployment Script
# Deploys the Next.js app to: https://freefaceswap.vercel.app/
# ============================================================

set -e  # Exit on error

echo "🚀 Starting Vercel Frontend Deployment..."
echo "============================================================"

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found!"
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Navigate to frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../frontend/faceswap"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"
echo "📂 Working directory: $FRONTEND_DIR"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

# Build the project (optional, Vercel will build automatically)
echo ""
echo "🔨 Building project..."
npm run build

# Deploy to Vercel
echo ""
echo "🚀 Deploying to Vercel..."
echo "============================================================"

# Production deployment
vercel --prod \
    --name freefaceswap \
    --yes

echo ""
echo "============================================================"
echo "✅ Deployment complete!"
echo "🌐 Your app is live at: https://freefaceswap.vercel.app/"
echo "============================================================"
