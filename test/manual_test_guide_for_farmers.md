# Manual Testing Guide for Farmers
*AI Share Platform - Simple Testing Instructions*

## Getting Started

### 1. Access the Platform
- Open your web browser
- Go to: `http://localhost:3000`
- You should see the AI Share Platform login page

### 2. Login
**Admin Account (for testing everything):**
- Email: `admin@example.com`
- Password: `admin123`

**Regular User Account (if needed):**
- Create a new account by clicking "Sign Up"
- Use your farm email and create a password

---

## What to Test

### 📂 File Upload & Management
**What farmers would use this for:** Upload farm data like crop yields, livestock records, financial reports

**Test Steps:**
1. Click "Upload Dataset" or "Add New Dataset"
2. Try uploading these file types:
   - Excel files (.xlsx) - like your farm spreadsheets
   - CSV files (.csv) - data exports
   - PDF files (.pdf) - reports and documents
   - Word documents (.docx) - farm plans
3. **Check:** File uploads successfully
4. **Check:** You can see a preview of your data
5. **Check:** File appears in your dataset list

**What to look for:**
- ✅ File uploads without errors
- ✅ Data shows up correctly
- ✅ You can view/preview the content
- ❌ Error messages during upload
- ❌ Missing or corrupted data

### 🤖 AI Chat & Questions
**What farmers would use this for:** Ask questions about your farm data, get insights

**Test Steps:**
1. Upload a farm data file (Excel with crop data works best)
2. Click "Chat with Data" or AI chat icon
3. Ask simple questions like:
   - "What's my total corn yield this year?"
   - "Show me my best performing crops"
   - "What month had the highest expenses?"
4. **Check:** AI responds with helpful answers
5. **Check:** Answers make sense based on your data

**What to look for:**
- ✅ AI understands your questions
- ✅ Answers are relevant to your data
- ✅ Chat loads quickly
- ❌ AI gives wrong information
- ❌ Chat doesn't respond or is very slow

### 🔗 Data Sharing
**What farmers would use this for:** Share harvest reports with buyers, financial data with accountants

**Test Steps:**
1. Select a dataset you uploaded
2. Click "Share" or sharing icon
3. Set sharing options:
   - Password protection: ON
   - Expiry date: Set to 1 week
4. Copy the share link
5. **Test in new browser window:** Open the link
6. Enter the password
7. **Check:** Others can view your shared data

**What to look for:**
- ✅ Share link works
- ✅ Password protection works
- ✅ Data displays correctly for viewer
- ✅ Share expires when set
- ❌ Link doesn't work
- ❌ Wrong data shows up

### 📊 Database Connections (Advanced)
**What farmers would use this for:** Connect to farm management software databases

**Test Steps:**
1. Go to "Data Connectors" or "Database"
2. Try connecting to:
   - A CSV file on your computer
   - Excel file with multiple sheets
3. **Check:** Connection works
4. **Check:** Data imports correctly

**What to look for:**
- ✅ Connection successful
- ✅ All data imports properly
- ✅ No missing records
- ❌ Connection fails
- ❌ Some data missing

### 👤 User Management (Admin Only)
**What farm managers would use this for:** Add farm workers, set permissions

**Test Steps:**
1. Go to "Admin Panel" (only visible for admin)
2. Click "Users" or "User Management"
3. Add a new user:
   - Email: test-farmer@farm.com
   - Role: Regular user
4. **Check:** New user can login
5. **Check:** User has appropriate access

**What to look for:**
- ✅ New users can be created
- ✅ Users can login successfully
- ✅ Permissions work correctly
- ❌ Users can't login
- ❌ Users see data they shouldn't

---

## Common Farm Use Cases to Test

### 🌾 Crop Yield Analysis
1. Upload Excel file with columns: Crop, Field, Date, Yield, Cost
2. Ask AI: "Which field gave the best corn yield?"
3. Share results with your agricultural advisor

### 🐄 Livestock Tracking
1. Upload CSV with: Animal_ID, Breed, Weight, Date, Health_Status
2. Ask AI: "How many animals need health checkups?"
3. Generate sharing link for veterinarian

### 💰 Financial Records
1. Upload farm expense spreadsheet
2. Ask AI: "What were my biggest expenses last quarter?"
3. Share summary with accountant (password protected)

### 📈 Seasonal Planning
1. Upload historical yield data
2. Ask AI: "What crops performed best in wet seasons?"
3. Use insights for next season planning

---

## Quick Checklist

**Before Each Test Session:**
- [ ] Platform is running (http://localhost:3000 works)
- [ ] You have test farm data files ready
- [ ] Admin login works

**Test Results:**
- [ ] File uploads work for common farm file types
- [ ] AI chat gives helpful answers about farm data
- [ ] Data sharing links work properly
- [ ] User management functions work
- [ ] No major errors or crashes

**Report Issues:**
- Note which browser you're using
- Write down exact error messages
- Describe what you were trying to do
- Include screenshots if helpful

---

## Tips for Farmers

1. **Start Simple:** Begin with one Excel file of crop data
2. **Use Real Data:** Test with actual farm files (remove sensitive info first)
3. **Ask Natural Questions:** Chat with AI like you're talking to a farm advisor
4. **Test Sharing:** Make sure your data can be safely shared with partners
5. **Check Mobile:** Try accessing on your phone/tablet

**Remember:** This platform is designed to help farmers make better decisions with their data. If something doesn't work as expected, it's important feedback for improving the system!

---

*This guide is for testing the AI Share Platform at Airfield Estate. Report any issues or suggestions to the development team.*