# Comprehensive Manual Testing Guide

## Overview
This guide provides detailed instructions for manually testing the AI Share Platform with the comprehensive simulation data that has been created. The simulation includes multiple organizations, users, datasets, and sharing scenarios.

## Test Environment Setup

### Organizations Created
- **TechCorp Industries** (3 users, 3 datasets)
- **DataScience Hub** (3 users, 3 datasets)  
- **StartupLab** (2 users, 0 datasets)
- **Academic Research Institute** (2 users, 0 datasets)
- **Demo Organization** (2 users, 1 dataset)
- **Open Source Community** (2 users, 0 datasets)

### Test User Credentials

#### TechCorp Industries
- `alice.smith@techcorp.com` / `tech2024` (Admin)
- `bob.johnson@techcorp.com` / `tech2024` (Analyst)
- `carol.williams@techcorp.com` / `tech2024` (Member)

#### DataScience Hub
- `david.brown@datasci.org` / `data2024` (Admin)
- `eva.davis@datasci.org` / `data2024` (Researcher)
- `frank.miller@datasci.org` / `data2024` (Member)

#### StartupLab
- `grace.wilson@startuplab.io` / `startup2024` (Founder)
- `henry.moore@startuplab.io` / `startup2024` (Developer)

#### Academic Research Institute
- `iris.taylor@research.edu` / `research2024` (Professor)
- `jack.anderson@research.edu` / `research2024` (Student)

#### Demo Organization
- `demo1@demo.com` / `demo123` (Member)
- `demo2@demo.com` / `demo123` (Member)

#### Open Source Community
- `opensource1@opensource.org` / `open123` (Member)
- `opensource2@opensource.org` / `open123` (Member)

## Dataset Test Scenarios

### Datasets by Sharing Level

#### PUBLIC (Visible to All Users)
- **Financial Market Data** (ID: 4)
  - Owner: `carol.williams@techcorp.com`
  - Type: CSV, 10,000 rows
  - Test: Login with any user and verify visibility

#### ORGANIZATION (Visible Within Same Organization)
- **Sales Performance Q1 2024** (ID: 2)
  - Owner: `alice.smith@techcorp.com` (TechCorp Industries)
  - Type: CSV, 5,000 rows
  
- **Research Publications Database** (ID: 5)
  - Owner: `david.brown@datasci.org` (DataScience Hub)
  - Type: JSON, 1,500 rows
  
- **E-commerce Transaction Log** (ID: 7)
  - Owner: `frank.miller@datasci.org` (DataScience Hub)
  - Type: JSON, 8,000 rows

#### PRIVATE (Visible Only to Owner)
- **Customer Feedback Analysis** (ID: 3)
  - Owner: `bob.johnson@techcorp.com`
  - Type: JSON, 2,500 rows
  
- **IoT Sensor Network Data** (ID: 6)
  - Owner: `eva.davis@datasci.org`
  - Type: CSV, 50,000 rows

## Manual Testing Procedures

### 1. Authentication Testing

#### Test 1.1: Basic Login
1. Navigate to the platform login page
2. Test each user credential set
3. Verify successful authentication
4. Check user profile information displays correctly

#### Test 1.2: Cross-Organization Access
1. Login as `alice.smith@techcorp.com`
2. Navigate to datasets page
3. Verify you can see:
   - ✅ Financial Market Data (PUBLIC)
   - ✅ Sales Performance Q1 2024 (ORGANIZATION - same org)
   - ❌ Should NOT see private datasets from other users
   - ❌ Should NOT see organization datasets from other orgs

### 2. Dataset Visibility Testing

#### Test 2.1: Public Dataset Access
1. Login with different users from different organizations
2. Navigate to datasets page
3. Verify **Financial Market Data** is visible to all users
4. Test dataset details page access
5. Verify download and API access permissions

#### Test 2.2: Organization-Level Sharing
1. Login as `alice.smith@techcorp.com` (TechCorp Industries)
2. Verify you can see **Sales Performance Q1 2024**
3. Login as `david.brown@datasci.org` (DataScience Hub)
4. Verify you can see **Research Publications Database** and **E-commerce Transaction Log**
5. Verify you CANNOT see TechCorp's organization datasets

#### Test 2.3: Private Dataset Access
1. Login as `bob.johnson@techcorp.com`
2. Verify you can see **Customer Feedback Analysis** (your private dataset)
3. Login as `alice.smith@techcorp.com` (same organization, admin role)
4. Verify you CANNOT see Bob's private dataset
5. Login as `eva.davis@datasci.org`
6. Verify you can see **IoT Sensor Network Data** (your private dataset)

### 3. AI Chat Testing

#### Test 3.1: Dataset-Specific Chat Context
1. Login as `carol.williams@techcorp.com`
2. Navigate to **Financial Market Data** dataset
3. Start AI chat session
4. Ask: "What insights can you provide about this financial data?"
5. Verify response includes:
   - Dataset-specific context
   - Appropriate analysis for financial data
   - Reference to stock prices, trading volumes, etc.

#### Test 3.2: Cross-Dataset Chat Testing
1. Login as `david.brown@datasci.org`
2. Test chat with **Research Publications Database**
3. Ask: "Analyze the research trends in this publication data"
4. Verify academic-focused response
5. Switch to **E-commerce Transaction Log**
6. Ask: "What are the key transaction patterns?"
7. Verify e-commerce focused response

#### Test 3.3: Fallback System Testing
1. Use any dataset for chat
2. Ask complex questions to trigger potential MindsDB model failures
3. Verify graceful fallback to direct Google API
4. Confirm chat continues to work even if MindsDB has issues

### 4. Role-Based Access Testing

#### Test 4.1: Admin vs Regular User Access
1. Login as `alice.smith@techcorp.com` (Admin)
2. Note available features and permissions
3. Login as `carol.williams@techcorp.com` (Member, same org)
4. Compare available features
5. Verify appropriate access restrictions

#### Test 4.2: Cross-Role Dataset Sharing
1. Login as `david.brown@datasci.org` (Admin)
2. Access **Research Publications Database**
3. Login as `frank.miller@datasci.org` (Member, same org)
4. Verify you can also access the same dataset
5. Test different permission levels if applicable

### 5. Proxy Service Testing

#### Test 5.1: Database Connectivity
1. Test connections through different proxy ports:
   - MySQL Proxy: `localhost:10101`
   - PostgreSQL Proxy: `localhost:10102`
   - API Proxy: `localhost:10103`
   - ClickHouse Proxy: `localhost:10104`
   - MongoDB Proxy: `localhost:10105`
   - S3 Proxy: `localhost:10106`
   - Shared Links Proxy: `localhost:10107`

#### Test 5.2: MindsDB Integration
1. Verify MindsDB connectivity through proxies
2. Test dataset queries through different connectors
3. Verify data retrieval and processing

### 6. Data Upload and Management Testing

#### Test 6.1: New Dataset Upload
1. Login as any user
2. Upload a new test dataset
3. Set different sharing levels
4. Verify proper categorization and metadata

#### Test 6.2: Dataset Modification
1. Access owned datasets
2. Test metadata updates
3. Verify sharing level changes
4. Test dataset deletion (if permitted)

## Expected Results Summary

### Visibility Matrix
| User | Public Datasets | Own Org Datasets | Other Org Datasets | Private Datasets |
|------|----------------|------------------|-------------------|------------------|
| alice.smith@techcorp.com | ✅ All | ✅ TechCorp only | ❌ None | ✅ Own only |
| david.brown@datasci.org | ✅ All | ✅ DataScience only | ❌ None | ✅ Own only |
| grace.wilson@startuplab.io | ✅ All | ✅ StartupLab only | ❌ None | ✅ Own only |

### AI Chat Expectations
- **Uploaded Datasets**: Standard analysis context with file-based data insights
- **Web Connector Datasets**: Enhanced real-time data context (when available)
- **Fallback Behavior**: Graceful degradation to direct Google API when MindsDB fails

### Proxy Service Expectations
- All proxy services (ports 10101-10107) should be accessible
- Database connections should route through appropriate proxies
- MindsDB integration should work through proxy layer

## Troubleshooting

### Common Issues
1. **Login Failures**: Verify credentials match exactly (case-sensitive)
2. **Dataset Not Visible**: Check sharing level and organization membership
3. **AI Chat Errors**: Verify fallback system is working
4. **Proxy Connection Issues**: Check if services are running on expected ports

### Debug Commands
```bash
# Check proxy service status
curl http://localhost:10101/health
curl http://localhost:10102/health
# ... for all proxy ports

# Verify database connectivity
python test_simulation_data.py

# Test AI chat functionality
python tests/test_enhanced_dataset_chat.py
```

## Success Criteria

### Must Pass
- [ ] All users can login with provided credentials
- [ ] Public datasets visible to all users
- [ ] Organization datasets visible only within same organization
- [ ] Private datasets visible only to owners
- [ ] AI chat works with dataset-specific context
- [ ] Fallback system activates when needed

### Should Pass
- [ ] All proxy services respond on expected ports
- [ ] MindsDB integration works through proxies
- [ ] Role-based permissions function correctly
- [ ] Dataset upload and management features work

### Nice to Have
- [ ] Web connector datasets provide real-time data
- [ ] Advanced sharing features work as expected
- [ ] Performance is acceptable under load

## Reporting Issues

When reporting issues, please include:
1. User account used for testing
2. Dataset ID and name
3. Expected vs actual behavior
4. Browser/client information
5. Any error messages or logs
6. Steps to reproduce

This comprehensive testing approach will validate all major platform features and ensure the AI chat fallback system works correctly across different user scenarios and data types.