# Hotel Ganaraj

A Django-based web application for managing hotel and restaurant operations.

## Features
- **User Module**: Online food ordering, room booking, user authentication (Login/Register/Profile), and cart management.
- **Admin Module**: Dashboard analytics, menu management, and order processing.
- **Payment**: Integration with Razorpay (as seen in models).

## Tech Stack
- **Backend**: Python, Django
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Database**: SQLite3

## Quick Start
1. Clone the repository.
2. Apply migrations:
   ```bash
   python manage.py migrate
   ```
3. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
4. Run the server:
   ```bash
   python manage.py runserver
   ```
