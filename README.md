# Adakings Backend API

A RESTful API backend for the Adakings restaurant management system, built with Django and Django REST Framework.
This backend serves a separate React frontend.

## Project Overview

This system aims to provide restaurants with an all-in-one solution to manage:
The backend provides API endpoints for:
- User authentication and management (registration, login, profile, password reset)
- Menu management
- Order processing and tracking
- Payment handling (Cash and Mobile Money via Paystack integration)
- Staff management and role-based access control

## Setup & Installation

### Prerequisites
- Python 3.8 or higher
- Git
- Windows, macOS, or Linux operating system

### Installation Steps

1. **Clone the repository**
   ```
   git clone <repository-url>
   cd adakings_backend
   ```

2. **Create and activate a virtual environment**
   
   For Windows:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
   
   For macOS/Linux:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

4. **Apply migrations**
   ```
   python manage.py migrate
   ```

5. **Create a superuser (admin)**
   ```
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```
   python manage.py runserver
   ```
   The API will be available at `http://127.0.0.1:8000/api/`

7. **Configure Environment Variables**
   
   Create a `.env` file in the project root with the following variables:
   ```
   PAYSTACK_PUBLIC_KEY=your_paystack_public_key
   PAYSTACK_SECRET_KEY=your_paystack_secret_key
   ```
   
   You can obtain Paystack API keys from your [Paystack Dashboard](https://dashboard.paystack.com/#/settings/developer)
   
   For development, you can use test keys to simulate payments without actual charges.

## API Documentation

The API documentation is automatically generated using `drf-spectacular` and can be accessed at the following endpoints:

- **OpenAPI Schema**: `/api/schema/`
- **Swagger UI**: `/api/docs/swagger/`
- **ReDoc**: `/api/docs/`

## Authentication Flow

The API uses session-based authentication by default for web browsers and basic authentication for other clients. 
Future enhancements may include token-based authentication (e.g., JWT).

- **Registration**: `POST /api/users/register/`
- **Login**: `POST /api/users/login/` (establishes a session)
- **Logout**: `POST /api/users/logout/` (invalidates the session)
- **Profile**: `GET /api/users/me/` (requires authentication)
- **Profile Update**: `PUT/PATCH /api/users/profile/` (requires authentication)

Permissions are handled using Django REST Framework's permission classes, including `IsAuthenticated` and `IsAdminUser` for protected endpoints.

## Project Structure

```
adakings_backend/
│
├── adakings_backend/         # Main Django project directory
│   ├── settings.py            # Project settings
│   ├── urls.py                # Main URL routing
│   ├── wsgi.py                # WSGI configuration
│   ├── asgi.py                # ASGI configuration
│   └── __init__.py            # Python package marker
│
├── apps/                      # Applications directory
│   ├── __init__.py            # Python package marker
│   ├── menu/                  # Menu management
│   │   ├── migrations/        # Database migrations
│   │   ├── admin.py           # Admin interface configuration
│   │   ├── apps.py            # App configuration
│   │   ├── forms.py           # Forms for data input
│   │   ├── models.py          # Database models
│   │   ├── tests.py           # Unit tests
│   │   ├── urls.py            # URL routing
│   │   ├── views.py           # View functions/classes
│   │   └── __init__.py        # Python package marker
│   ├── orders/                # Order processing
│   │   ├── management/        # Custom management commands
│   │   │   └── commands/      # Management command files
│   │   ├── migrations/        # Database migrations
│   │   ├── templatetags/      # Custom template tags
│   │   ├── admin.py           # Admin interface configuration
│   │   ├── apps.py            # App configuration
│   │   ├── forms.py           # Forms for data input
│   │   ├── models.py          # Database models
│   │   ├── signals.py         # Django signals
│   │   ├── tests.py           # Unit tests
│   │   ├── urls.py            # URL routing
│   │   ├── views.py           # View functions/classes
│   │   └── __init__.py        # Python package marker
│   ├── payments/              # Payment handling
│   │   ├── migrations/        # Database migrations
│   │   ├── admin.py           # Admin interface configuration
│   │   ├── apps.py            # App configuration
│   │   ├── models.py          # Database models
│   │   ├── tests.py           # Unit tests
│   │   ├── urls.py            # URL routing
│   │   ├── views.py           # View functions/classes
│   │   └── __init__.py        # Python package marker
│   └── users/                 # User management
│       ├── migrations/        # Database migrations
│       ├── admin.py           # Admin interface configuration
│       ├── apps.py            # App configuration
│       ├── models.py          # Database models
│       ├── tests.py           # Unit tests
│       ├── urls.py            # URL routing
│       ├── views_api.py       # API view functions/classes for users
│       └── __init__.py        # Python package marker
│
├── static/                    # Static files (CSS, JS, images)
│   └── css/                   # Stylesheets
│
├── venv/                      # Virtual environment (excluded from git)
│
├── .env                       # Environment variables (excluded from git)
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
├── CHANGELOG.md               # Project changelog
├── db.sqlite3                 # SQLite database (development)
├── manage.py                  # Django management script
└── README.md                  # This file
```

## Development State

- **Current Version**: v0.6.0
- **Current Branch**: feature/v0.6.0-codebase-restructuring
- **Development Stage**: **MAJOR RESTRUCTURING COMPLETE** - Converted from full-stack Django application to pure REST API backend. Removed all Django templates, forms, and web interface components. Now serves exclusively as an API backend for separate frontend applications.

### Version History

- **v0.6.0**: **MAJOR RESTRUCTURING** - Pure API Backend Conversion
  - **BREAKING CHANGE**: Removed all Django templates, forms, and web interface components
  - Converted all views to API-only using Django REST Framework
  - Added comprehensive serializers for all models (menu, orders, payments, users)
  - Implemented proper API permissions and authentication
  - Removed static CSS files and template directories
  - Updated URL routing to serve API endpoints exclusively
  - Added API documentation with Swagger/OpenAPI schema
  - Streamlined models for API consumption
  - Added new database migrations for model optimizations
  - **Result**: Now serves as a pure REST API backend ready for separate frontend applications

- **v0.5.0**: Comprehensive application updates and refactoring
  - Refactored Admin Dashboard UI to align with the new unified theme (using `theme.css` and Bootstrap).
  - Updated models, forms, views, and admin configurations across `menu`, `orders`, `payments`, and `users` applications.
  - Managed and updated database migrations to reflect schema changes.
  - Introduced new application features/modules including Django signals and custom template tags.
  - Enhanced static file management and overall theme consistency.
  - General improvements to application templates, settings, and overall code structure.
- **v0.4.0**: Payment system implementation and order management updates
  - Implemented Paystack payment integration for mobile money transactions
  - Restructured Order model to incorporate customer information directly
  - Added payment processing, verification, and webhook support
  - Created order management interface with status tracking
  - Implemented comprehensive order creation and update workflow
  - Added support for environment variables configuration
- **v0.1.2**: Project restructuring and template fixes
  - Reorganized project structure with dedicated apps/ and templates/ directories
  - Implemented template inheritance system with base.html
  - Fixed template syntax errors in profile and staff management pages
  - Improved code organization and maintainability
- **v0.1.1**: Initial Django project setup and basic configuration
- **v0.1.0**: Project initialization

## Usage Instructions

1. Ensure your virtual environment is activated.

2. Start the development server:
   ```
   python manage.py runserver
   ```

3. Access the API at `http://127.0.0.1:8000/api/` and the documentation as listed above.

### Admin Interface

Access the Django admin interface at `http://127.0.0.1:8000/admin/` using the superuser credentials created during setup.

### Payment Processing

The system supports two payment methods:

1. **Cash Payments**: For in-person transactions
2. **Mobile Money**: Integrated with Paystack for secure mobile payments

To process mobile payments:
1. Select "Mobile Money" as the payment method when finalizing an order
2. Enter the customer's phone number in the specified format
3. The system will redirect to Paystack's payment interface
4. Payment status will be automatically updated upon completion

For testing, use Paystack's test cards and credentials from their [documentation](https://paystack.com/docs/payments/test-payments/).

### Development Workflow

1. Create a feature branch for new development:
   ```
   git checkout -b feature/v[version]-[feature-name]
   ```

2. Make changes and commit with descriptive messages:
   ```
   git add .
   git commit -m "Descriptive message about the changes"
   ```

3. Push changes to the feature branch:
   ```
   git push origin feature/v[version]-[feature-name]
   ```

4. When ready, merge to the dev branch:
   ```
   git checkout dev
   git merge feature/v[version]-[feature-name]
   git push origin dev
   ```

## Management Commands

### Update Order Numbers (`update_order_numbers`)

- **Purpose**: This command is used to populate or correct the `order_number` field for any existing orders. It targets orders where this field is currently blank/empty OR orders where the `order_number` exists but is not in the standard `DDMMYY-XXX` format (e.g., `300525-001`). It ensures all targeted orders receive a unique, correctly formatted order number, where `XXX` is a sequential counter that resets daily.
- **Usage**: To run the command, execute the following from the project root directory (where `manage.py` is located):
  ```bash
  python manage.py update_order_numbers
  ```
- **Details**: The command iterates through all orders in the database. It identifies orders that either have a blank/null `order_number` or have an `order_number` that does not conform to the `DDMMYY-XXX` regex pattern. For each such identified order, it first sets its `order_number` to null (to ensure regeneration) and then calls the order's `save()` method. The `Order` model's `save()` method contains logic to automatically generate and assign a correctly formatted `order_number` if it's missing or has been cleared. The command will output the total number of orders that were successfully updated, or a message if no orders required an update. It also includes error handling for individual order updates and overall execution.

## License

[Specify your license here]

## Contact

[Your contact information]

