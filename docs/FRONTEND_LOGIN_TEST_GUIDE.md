# Simple Frontend Login Test Guide

## 🧪 Manual Testing Instructions

The frontend login page has been updated with comprehensive simulation users. Since there's a mismatch between the demo users API and actual passwords, here's how to test manually:

### 1. Access the Login Page
Open your browser and go to: **http://localhost:3000/login**

### 2. Test User Credentials (Copy & Paste)

#### TechCorp Industries Users
```
Email: alice.smith@techcorp.com
Password: tech2024
```

```
Email: bob.johnson@techcorp.com
Password: tech2024
```

```
Email: carol.williams@techcorp.com
Password: tech2024
```

#### DataScience Hub Users
```
Email: david.brown@datasci.org
Password: data2024
```

```
Email: eva.davis@datasci.org
Password: data2024
```

```
Email: frank.miller@datasci.org
Password: data2024
```

#### StartupLab Users
```
Email: grace.wilson@startuplab.io
Password: startup2024
```

```
Email: henry.moore@startuplab.io
Password: startup2024
```

#### Academic Research Institute Users
```
Email: iris.taylor@research.edu
Password: research2024
```

```
Email: jack.anderson@research.edu
Password: research2024
```

#### Demo Organization Users (Original)
```
Email: demo1@demo.com
Password: demo123
```

```
Email: demo2@demo.com
Password: demo123
```

### 3. Testing Steps

1. **Copy any email/password combination** from above
2. **Paste into the login form** on the frontend
3. **Click "Sign In"**
4. **Verify successful login** and redirect to dashboard
5. **Test different users** to verify cross-organization access controls

### 4. Expected Behavior

- ✅ **Login Success**: Should redirect to dashboard after successful authentication
- ✅ **User Profile**: Should display correct user information and organization
- ✅ **Dataset Access**: Should show datasets based on sharing levels:
  - **PUBLIC**: Visible to all users
  - **ORGANIZATION**: Only visible within same organization  
  - **PRIVATE**: Only visible to dataset owner

### 5. Demo User Buttons

The login page includes demo user buttons that auto-fill credentials. These may show the old demo users from the API, but you can:

1. **Click any demo button** to auto-fill the form
2. **Manually replace** with the correct credentials from above
3. **Submit the form** with the updated credentials

### 6. Quick Test Scenarios

#### Test Cross-Organization Access
1. Login as `alice.smith@techcorp.com` / `tech2024`
2. Navigate to datasets page
3. Should see TechCorp datasets + public datasets
4. Should NOT see DataScience Hub private/org datasets

#### Test Dataset Sharing Levels
1. Login as any user
2. Look for these test datasets:
   - **Financial Market Data** (PUBLIC - visible to all)
   - **Sales Performance Q1 2024** (ORGANIZATION - TechCorp only)
   - **Customer Feedback Analysis** (PRIVATE - Bob Johnson only)

### 7. Troubleshooting

If login fails:
- ✅ **Check credentials** are copied exactly (case-sensitive)
- ✅ **Verify backend is running** on port 8000
- ✅ **Check browser console** for any JavaScript errors
- ✅ **Try different user** to isolate the issue

### 8. Success Criteria

- [ ] Can login with TechCorp users (tech2024 password)
- [ ] Can login with DataScience users (data2024 password)  
- [ ] Can login with StartupLab users (startup2024 password)
- [ ] Can login with Academic users (research2024 password)
- [ ] Can login with Demo users (demo123 password)
- [ ] Dashboard loads correctly after login
- [ ] User profile shows correct organization
- [ ] Dataset visibility follows sharing rules

## 🎯 Ready for Manual Testing!

The frontend login interface is now ready with all comprehensive simulation users. The UI is kept simple and clean as requested, with easy-to-use credential buttons and clear testing instructions.