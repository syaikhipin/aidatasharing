# Quick Testing Reference Card

## 🔑 Test Credentials (Copy & Paste Ready)

### TechCorp Industries
```
alice.smith@techcorp.com
tech2024
```
```
bob.johnson@techcorp.com
tech2024
```
```
carol.williams@techcorp.com
tech2024
```

### DataScience Hub
```
david.brown@datasci.org
data2024
```
```
eva.davis@datasci.org
data2024
```
```
frank.miller@datasci.org
data2024
```

### StartupLab
```
grace.wilson@startuplab.io
startup2024
```
```
henry.moore@startuplab.io
startup2024
```

### Academic Research Institute
```
iris.taylor@research.edu
research2024
```
```
jack.anderson@research.edu
research2024
```

## 📊 Test Datasets Quick Reference

| Dataset Name | ID | Owner | Sharing | Type | Rows |
|--------------|----|---------|---------|----|------|
| Financial Market Data | 4 | carol.williams@techcorp.com | **PUBLIC** | CSV | 10,000 |
| Sales Performance Q1 2024 | 2 | alice.smith@techcorp.com | **ORG** | CSV | 5,000 |
| Research Publications | 5 | david.brown@datasci.org | **ORG** | JSON | 1,500 |
| E-commerce Transaction Log | 7 | frank.miller@datasci.org | **ORG** | JSON | 8,000 |
| Customer Feedback Analysis | 3 | bob.johnson@techcorp.com | **PRIVATE** | JSON | 2,500 |
| IoT Sensor Network Data | 6 | eva.davis@datasci.org | **PRIVATE** | CSV | 50,000 |

## 🧪 Quick Test Scenarios

### Test 1: Public Access
1. Login: `grace.wilson@startuplab.io` / `startup2024`
2. Should see: **Financial Market Data** (ID: 4)
3. Should NOT see: Any private or other org datasets

### Test 2: Organization Access
1. Login: `alice.smith@techcorp.com` / `tech2024`
2. Should see: **Sales Performance Q1 2024** (same org)
3. Should NOT see: DataScience Hub org datasets

### Test 3: Private Access
1. Login: `bob.johnson@techcorp.com` / `tech2024`
2. Should see: **Customer Feedback Analysis** (own private)
3. Login: `alice.smith@techcorp.com` / `tech2024` (same org, admin)
4. Should NOT see: Bob's private dataset

### Test 4: AI Chat
1. Login: Any user
2. Access any visible dataset
3. Ask: "What insights can you provide about this data?"
4. Verify: Context-appropriate response

## 🔧 Proxy Ports
- MySQL: `10101`
- PostgreSQL: `10102`
- API: `10103`
- ClickHouse: `10104`
- MongoDB: `10105`
- S3: `10106`
- Shared Links: `10107`

## ✅ Quick Validation Checklist
- [ ] Login works for all users
- [ ] Public dataset visible to all
- [ ] Organization datasets restricted properly
- [ ] Private datasets only visible to owners
- [ ] AI chat responds with context
- [ ] Fallback system works if MindsDB fails

## 🚨 Expected Behaviors
- **PUBLIC**: Visible to everyone
- **ORGANIZATION**: Only visible within same organization
- **PRIVATE**: Only visible to dataset owner
- **AI Chat**: Should work with graceful fallback
- **Cross-Org**: Users cannot see other organization's data