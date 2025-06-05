# E-Commerce API

SMS-based authentication va JWT token bilan ishlaydigan to'liq e-commerce API.

## Xususiyatlar

- SMS orqali ro'yxatdan o'tish va login
- JWT authentication
- Mahsulotlar katalogi
- Savatcha boshqaruvi
- Buyurtmalar tizimi
- Mahsulotlarga baho berish
- Celery va Redis bilan asinxron SMS yuborish

## O'rnatish

1. Repository'ni clone qiling
2. Virtual environment yarating
3. Dependencylarni o'rnating: `pip install -r requirements.txt`
4. Environment variablelarni sozlang
5. Migratsiyalarni bajaring: `python manage.py migrate`
6. Serverni ishga tushiring: `python manage.py runserver`

## API Dokumentatsiyasi

Swagger UI: [your-domain.com/api/docs/](https://your-domain.com/api/docs/)

## Deployment

Loyiha Vercel platformasida deploy qilingan: [your-domain.com](https://your-domain.com)

## Texnologiyalar

- Django 4.2
- Django REST Framework
- Celery
- Redis
- PostgreSQL
- Vercel