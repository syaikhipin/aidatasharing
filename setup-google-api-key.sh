#!/bin/bash

# Google API Key Setup Script for AI Share Platform

echo "🔑 Google API Key Setup for AI Share Platform"
echo "=============================================="
echo ""

# Check if API key is already set
if [ ! -z "$GOOGLE_API_KEY" ]; then
    echo "✅ Google API key is already set in environment"
    echo "   Masked key: ${GOOGLE_API_KEY:0:4}...${GOOGLE_API_KEY: -4}"
    echo ""
    read -p "Do you want to update it? (y/N): " update_key
    if [[ ! $update_key =~ ^[Yy]$ ]]; then
        echo "Keeping existing key."
        exit 0
    fi
fi

echo "To enable AI chat functionality, you need a Google API key."
echo ""
echo "📝 How to get a Google API key:"
echo "1. Go to: https://console.cloud.google.com/"
echo "2. Create a new project or select an existing one"
echo "3. Enable the 'Generative Language API' (Gemini)"
echo "4. Go to 'APIs & Services' > 'Credentials'"
echo "5. Click 'Create Credentials' > 'API Key'"
echo "6. Copy the generated API key"
echo ""

# Get API key from user
read -p "Enter your Google API key: " api_key

if [ -z "$api_key" ]; then
    echo "❌ No API key provided. Exiting."
    exit 1
fi

# Validate API key format (basic check)
if [[ ${#api_key} -lt 20 ]]; then
    echo "⚠️  Warning: API key seems too short. Please verify it's correct."
fi

echo ""
echo "🔧 Setting up Google API key..."

# Method 1: Create/update .env file
echo "GOOGLE_API_KEY=$api_key" > .env
echo "✅ Created .env file with Google API key"

# Method 2: Export for current session
export GOOGLE_API_KEY="$api_key"
echo "✅ Exported API key for current session"

# Method 3: Add to shell profile (optional)
echo ""
read -p "Add to your shell profile (~/.zshrc) for permanent setup? (y/N): " add_to_profile

if [[ $add_to_profile =~ ^[Yy]$ ]]; then
    # Check if already exists in profile
    if grep -q "GOOGLE_API_KEY" ~/.zshrc 2>/dev/null; then
        echo "⚠️  GOOGLE_API_KEY already exists in ~/.zshrc"
        echo "   Please update it manually if needed."
    else
        echo "" >> ~/.zshrc
        echo "# AI Share Platform - Google API Key" >> ~/.zshrc
        echo "export GOOGLE_API_KEY=\"$api_key\"" >> ~/.zshrc
        echo "✅ Added to ~/.zshrc"
        echo "   Run 'source ~/.zshrc' or restart terminal to apply"
    fi
fi

echo ""
echo "🎉 Google API key setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Restart your backend server:"
echo "   cd backend && python -m uvicorn main:app --reload --port 8000"
echo ""
echo "2. The AI chat should now work in your datasets"
echo ""
echo "🔍 To verify setup:"
echo "   echo \$GOOGLE_API_KEY"
echo ""
echo "🛡️  Security note: Keep your API key secure and never commit it to version control"