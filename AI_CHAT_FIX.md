# AI Chat Fix: Google API Key Configuration

## Problem
The AI chat functionality is not working because the Google API key is missing:
```
2025-07-27 16:41:30,220 - app.services.mindsdb - WARNING - ⚠️ No Google API key found in settings
2025-07-27 16:41:30,220 - app.services.mindsdb - ERROR - ❌ No Google API key found in environment either
```

## Solution: Multiple Ways to Configure Google API Key

### Method 1: Using the Setup Script (Recommended)
```bash
# Run the interactive setup script
./setup-google-api-key.sh
```

### Method 2: Manual Environment Setup
```bash
# Create .env file
echo "GOOGLE_API_KEY=your_actual_api_key_here" > .env

# Or export for current session
export GOOGLE_API_KEY="your_actual_api_key_here"

# Add to shell profile for permanent setup
echo 'export GOOGLE_API_KEY="your_actual_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### Method 3: Through Admin Interface
1. Go to the admin panel in your browser: `http://localhost:3000/admin`
2. Look for "Google API Key" section
3. Click "Set Key" or "Update" button
4. Enter your Google API key when prompted

## How to Get a Google API Key

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create/Select Project**: Create a new project or select existing one
3. **Enable API**: Enable the "Generative Language API" (for Gemini)
4. **Create Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the generated API key
5. **Secure the Key**: Restrict the API key to your specific APIs and IPs if needed

## After Setting the API Key

1. **Restart Backend Server**:
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```

2. **Verify Setup**:
   ```bash
   # Check if key is set
   echo $GOOGLE_API_KEY
   
   # Check backend logs - should show:
   # ✅ Google API key loaded: AIza...xyz
   ```

3. **Test AI Chat**:
   - Go to any dataset in the frontend
   - Try using the AI chat functionality
   - It should now work without errors

## Security Notes

- ⚠️ **Never commit your API key to version control**
- 🔒 **Keep your API key secure and private**
- 🛡️ **Consider restricting the API key to specific IPs/domains**
- 💰 **Monitor your Google Cloud billing for API usage**

## Troubleshooting

If AI chat still doesn't work after setting the key:

1. **Check Environment**:
   ```bash
   echo $GOOGLE_API_KEY  # Should show your key
   ```

2. **Check Backend Logs**:
   - Look for "✅ Google API key loaded" message
   - If still showing warnings, restart backend

3. **Check API Key Validity**:
   - Test the key with a simple API call
   - Ensure the Generative Language API is enabled

4. **Check Database Configuration**:
   - The key might be stored in database configuration table
   - Check admin interface for current status

## Files Created/Modified

- `.env.template` - Template for environment variables
- `setup-google-api-key.sh` - Interactive setup script
- This documentation file

The AI chat should work perfectly once the Google API key is properly configured!