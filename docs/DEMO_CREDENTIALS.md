# Demo Credentials - Clean Minimal Setup

This document contains the login credentials for the clean minimal demo setup.

## Overview
The system has been cleaned and contains only essential demo data:
- **2 Organizations** with 1 user each
- **1 Admin user** (not tied to any organization)
- **1 API Connector** (JSONPlaceholder demo API)
- **1 Sample Dataset** (Sales CSV file)

## Login Credentials

### Admin Account
- **Email:** `admin@example.com`
- **Password:** `SuperAdmin123!`
- **Role:** System Administrator
- **Organization:** None (cross-organization access)
- **Permissions:** Full admin access to all features

### Organization Users

#### TechCorp Solutions
- **Email:** `alice@techcorp.com`
- **Password:** `Password123!`
- **Full Name:** Alice Johnson
- **Role:** Data Analyst
- **Organization:** TechCorp Solutions (Enterprise)

#### Data Analytics Inc
- **Email:** `bob@dataanalytics.com`
- **Password:** `Password123!`
- **Full Name:** Bob Wilson
- **Role:** Data Scientist
- **Organization:** Data Analytics Inc (Small Business)

## Available Data

### API Connector
- **Name:** Sample REST API
- **Type:** API
- **URL:** https://jsonplaceholder.typicode.com
- **Organization:** TechCorp Solutions
- **Status:** Active and tested

### Sample Dataset
- **Name:** Sample Sales Data
- **Type:** CSV File
- **Owner:** Bob Wilson (Data Analytics Inc)
- **Sharing Level:** Organization
- **File:** Contains 5 sample sales records

## URLs

### Frontend
- **Main App:** http://localhost:3000
- **Admin Panel:** http://localhost:3000/admin
- **Organizations:** http://localhost:3000/admin/organizations

### Backend API
- **API Base:** http://localhost:8000
- **Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Testing Scenarios

### Admin Testing
1. Login as admin
2. Access admin panel
3. Manage organizations
4. View all users and datasets across organizations

### User Testing
1. Login as Alice or Bob
2. View organization datasets
3. Test data sharing features
4. Access API connectors (Alice only)

### Data Management
1. Upload new datasets
2. Test AI chat features
3. Create new connectors
4. Generate shared links

## Resetting Data

To reset to clean state, run:
```bash
cd backend
python seed_clean_minimal_data.py
```

This will recreate the minimal clean dataset with the credentials listed above.