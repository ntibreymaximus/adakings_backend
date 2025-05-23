# Restaurant Front Desk System

A full-stack restaurant management system built with Django, focusing on streamlining front desk operations for restaurants including reservations, order management, menu handling, and customer service.

## Project Overview

This system aims to provide restaurants with an all-in-one solution to manage:
- Customer reservations and seating
- Menu management and real-time updates
- Order processing and tracking
- Payment handling (Cash and Mobile Money via Paystack)
- Staff scheduling and management
- Customer data and preferences

## Setup & Installation

### Prerequisites
- Python 3.8 or higher
- Git
- Windows, macOS, or Linux operating system

### Installation Steps

1. **Clone the repository**
   ```
   git clone <repository-url>
   cd RestaurantApp
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
   
   The application will be available at `http://127.0.0.1:8000/`

7. **Configure Environment Variables**
   
   Create a `.env` file in the project root with the following variables:
   ```
   PAYSTACK_PUBLIC_KEY=your_paystack_public_key
   PAYSTACK_SECRET_KEY=your_paystack_secret_key
   ```
   
   You can obtain Paystack API keys from your [Paystack Dashboard](https://dashboard.paystack.com/#/settings/developer)
   
   For development, you can use test keys to simulate payments without actual charges.

## Project Structure

```
RestaurantApp/
│
├── restaurant_frontdesk/      # Main project directory
│   ├── settings.py            # Project settings
│   ├── urls.py                # Main URL routing
│   ├── wsgi.py                # WSGI configuration
│   └── asgi.py                # ASGI configuration
│
├── apps/                      # Applications directory
│   ├── users/                 # User management
│   ├── menu/                  # Menu management
│   ├── orders/                # Order processing
│   ├── payments/              # Payment handling
│   ├── delivery/              # Delivery management
│   └── desk/                  # Front desk operations
│
├── templates/                 # HTML templates
│   ├── base.html             # Base template
│   └── ...
│
├── static/                    # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                     # User-uploaded files
│
├── manage.py                  # Django management script
├── requirements.txt           # Project dependencies
├── .gitignore                 # Git ignore file
└── README.md                  # This file
```

## Development State

- **Current Version**: v0.4.0
- **Current Branch**: feature/v0.4.0-payments-implementation
- **Development Stage**: Payment system implementation and orders restructuring

### Version History

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

### Running the Application

1. Ensure your virtual environment is activated:
   ```
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

2. Start the development server:
   ```
   python manage.py runserver
   ```

3. Access the application at `http://127.0.0.1:8000/`

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

## License

[Specify your license here]

## Contact

[Your contact information]

 
## Branch: feature/v0.4.0-payments-implementation
## Version: v0.4.0
### Changes in this update: 
- Implemented payment system with Paystack integration
- Restructured order management system
- Fixed email generation for mobile payments
Timestamp: Fri 05/23/2025 14:14:33.85
 
