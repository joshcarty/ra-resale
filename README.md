# RA Resale Ticket Alerts
Get alerts when Resident Advisor tickets become available on resale.

https://ra-resale.appspot.com/

## Preview
![Screenshot](screenshot.png)

## Quickstart
### Installation
```bash
$ git clone https://github.com/joshcarty/ra-resale
$ cd ra-resale
$ pip install -r requirements.txt
```

### Configure
```bash
export EMAIL_HOST=''
export EMAIL_HOST_PASSWORD=''
export EMAIL_HOST_USER=''
export DATABASE_NAME=''
export DATABASE_USER=''
export DATABASE_PASSWORD=''
export DATABASE_HOST=''
export PROJECT_SECRET=''
```

### Running
```bash
$ python manage.py makemigrations
$ python manage.py migrate
$ python manage.py runserver
```

## Project
```
LICENSE
├── README.md
├── alerts
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── migrations
│   ├── models.py
│   ├── static
│   ├── templates
│   ├── tests.py
│   └── views.py
├── app.yaml
├── cron.yaml
├── manage.py
├── requirements.txt
├── resale
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── screenshot.png
├── setup.sh
└── static
    ├── admin
    └── alerts
```