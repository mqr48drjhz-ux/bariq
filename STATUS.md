# Bariq Web App - Project Status (December 26, 2025)

## Current State: MVP Ready for Testing with Full Role Hierarchy

The application is now functional with complete customer and merchant portals, including a full hierarchical staff management system.

---

## What's Working

### Backend (Flask API)
- JWT Authentication (Customer, Merchant, Admin)
- Customer CRUD + Credit Management
- Merchant CRUD + Branch/Staff Management
- **NEW: Full Staff Role Hierarchy** (Owner, Executive Manager, Region Manager, Branch Manager, Cashier)
- Transaction Creation & Confirmation Flow
- Payment Processing
- Settlement Tracking
- All API endpoints tested and functional

### Frontend (Jinja2 Templates)

#### Public Pages
| Page | URL | Status |
|------|-----|--------|
| Landing Page | `/` | Complete |
| Login Page | `/login` | Complete |

#### Customer Portal
| Page | URL | Status |
|------|-----|--------|
| Dashboard | `/customer` | Complete |
| Transactions | `/customer/transactions` | Complete |
| Profile | `/customer/profile` | Complete |
| Credit Details | `/customer/credit` | Complete |
| Payments | `/customer/payments` | Complete |
| Make Payment | `/customer/pay` | Complete |

#### Merchant Portal
| Page | URL | Status |
|------|-----|--------|
| Dashboard | `/merchant` | Complete (Role-Based) |
| Reports | `/merchant/reports` | **NEW** - Complete |
| Team/Staff Hierarchy | `/merchant/team` | **NEW** - Complete |
| Regions | `/merchant/regions` | **NEW** - Complete |
| New Transaction | `/merchant/new-transaction` | Complete |
| Transactions | `/merchant/transactions` | Complete |
| Settlements | `/merchant/settlements` | Complete |
| Branches | `/merchant/branches` | Complete |

---

## Staff Role Hierarchy

The merchant portal now supports a complete organizational hierarchy:

```
Owner (المالك)
├── Executive Manager (المدير التنفيذي) - Same permissions as Owner
│   ├── Can see ALL regions and branches
│   ├── Can manage ALL staff
│   └── Full reports access
│
├── Region Manager (مدير المنطقة)
│   ├── Can see branches in their region only
│   ├── Can manage staff in their region
│   └── Reports for their region only
│
├── Branch Manager (مدير الفرع)
│   ├── Can see their branch only
│   ├── Can manage cashiers in their branch
│   └── Reports for their branch only
│
└── Cashier (كاشير)
    ├── Can create transactions
    └── Can view their own transactions
```

### Role-Based Features
- **Dynamic Navigation**: Each role sees only relevant menu items
- **Role-Based Dashboard**: Custom welcome messages and quick actions per role
- **Staff Hierarchy View**: Tree visualization + list view with filters
- **Reports Page**: Daily/weekly/monthly reports with transactions, staff performance, settlements, and customer analytics

---

## Test Credentials

### Admin
| Role | Email | Password |
|------|-------|----------|
| Super Admin | `admin@bariq.sa` | `Admin@123` |

### Customer
| Username | Password | Bariq ID |
|----------|----------|----------|
| `ahmed_ali` | `Customer@123` | `123456` |

### Merchant Staff
| Role | Email | Password |
|------|-------|----------|
| Owner | `owner@albaraka.sa` | `Owner@123` |
| Executive Manager | `exec@albaraka.sa` | `Exec@123` |
| Region Manager (Riyadh) | `region.riyadh@albaraka.sa` | `Region@123` |
| Region Manager (Jeddah) | `region.jeddah@albaraka.sa` | `Region@123` |
| Branch Manager (Olaya) | `branch.olaya@albaraka.sa` | `Branch@123` |
| Branch Manager (Malaz) | `branch.malaz@albaraka.sa` | `Branch@123` |
| Branch Manager (Tahlia) | `branch.tahlia@albaraka.sa` | `Branch@123` |
| Cashier | `cashier@albaraka.sa` | `Cashier@123` |

---

## Latest Session Updates (December 26, 2025)

### Full Staff Hierarchy Implementation
- Added `executive_manager` role with same permissions as owner
- Created role hierarchy constants in MerchantUser model
- Helper methods for role-based access control

### New Merchant Pages
1. **Reports Page** (`/merchant/reports`)
   - Period selector (daily/weekly/monthly)
   - Date range filters
   - Region/branch filters for managers
   - Four report types: Transactions, Staff Performance, Settlements, Customer Analytics
   - Summary cards with key metrics

2. **Team Page** (`/merchant/team`)
   - Tree view: Visual organizational hierarchy
   - List view: Filterable table with search
   - Add/Edit staff modals
   - Role-based staff visibility

3. **Regions Page** (`/merchant/regions`)
   - Region cards with branch counts
   - Region manager assignment display
   - Branch listing per region
   - Add/Edit region modals

### Enhanced Dashboard
- Role-based welcome messages
- Custom quick actions per role
- Team summary cards for managers
- Scope badges for region/branch managers

### API Updates
- `GET /merchants/me/staff/<id>` - Get staff member details
- Updated valid roles to include `executive_manager`
- Role-based data filtering in staff queries

---

## Files Structure

```
bariq/
├── wsgi.py                 # Entry point - run this
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── extensions.py       # Flask extensions
│   ├── api/v1/             # REST API endpoints
│   │   ├── auth/           # Authentication
│   │   ├── customers/      # Customer endpoints
│   │   ├── merchants/      # Merchant endpoints (updated)
│   │   └── admin/          # Admin endpoints
│   ├── models/
│   │   └── merchant_user.py # Updated with role hierarchy
│   ├── services/           # Business logic
│   ├── static/
│   │   ├── css/main.css    # Global styles
│   │   └── js/api.js       # API helper (updated)
│   ├── templates/
│   │   ├── base.html       # Base layout
│   │   ├── customer/       # Customer portal
│   │   └── merchant/       # Merchant portal
│   │       ├── layout.html     # Updated with dynamic nav
│   │       ├── dashboard.html  # Role-based dashboard
│   │       ├── reports.html    # NEW
│   │       ├── team.html       # NEW
│   │       └── regions.html    # NEW
│   └── frontend/
│       └── __init__.py     # Frontend routes (updated)
├── scripts/
│   └── seed_data.py        # Updated with full hierarchy
└── migrations/             # Database migrations
```

---

## How to Run

```bash
cd /Users/ibrahimfakhry/Desktop/bariq
source venv/bin/activate
python wsgi.py
```

Server runs at: **http://localhost:5001**

### To Reseed Database (for new staff hierarchy):
```bash
# Delete existing database
rm -f app.db

# Recreate and seed
flask db upgrade
python scripts/seed_data.py
```

---

## Next Steps (Priority Order)

### 1. Admin Dashboard (High Priority)
Create admin portal at `/admin` with:
- Dashboard with system-wide statistics
- Customer management (view, activate, suspend, adjust credit)
- Merchant management (approve, suspend merchants)
- Transaction monitoring
- Settlement approval workflow

### 2. Customer Registration (High Priority)
- Registration page with form
- Nafath authentication mock/integration
- OTP verification flow
- Credit limit assignment

### 3. Role-Based Data Filtering (Medium Priority)
- Update transaction queries to filter by user's accessible branches
- Update settlement queries for role-based access
- API-level enforcement of role permissions

### 4. Enhanced Features (Medium Priority)
- Notifications system (in-app + email)
- Transaction history export (PDF/Excel)
- Real-time transaction confirmation

### 5. Security & Production (Before Launch)
- Input validation enhancement
- Rate limiting
- HTTPS setup
- Environment variables for secrets

---

## Known Limitations

1. **No Admin UI** - Admin endpoints exist but no frontend
2. **No Registration** - Users must be seeded manually
3. **No Email/SMS** - Notifications are in-app only
4. **Mock Nafath** - No real Nafath integration yet
5. **No Payment Gateway** - Payments are recorded but not processed
6. **Role Filtering Partial** - Some queries don't fully filter by role at API level yet

---

## Tech Stack

- **Backend:** Flask 3.x, SQLAlchemy, Flask-JWT-Extended
- **Database:** PostgreSQL (configured) / SQLite (dev fallback)
- **Frontend:** Jinja2, Vanilla JS, Custom CSS
- **Auth:** JWT tokens with refresh
- **Design:** RTL Arabic, Teal & White theme, Mobile responsive
