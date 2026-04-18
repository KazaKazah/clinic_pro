# Первый модуль клиники

Этот комплект файлов добавляет первый рабочий маршрут:

```text
регистратор -> пациент -> обращение -> услуга -> оплата -> прием -> врач
```

## Что добавить в репозиторий

Скопируйте содержимое папки `clinic_pro_ready` в корень проекта `clinic_pro`.

Файлы из `clinic_pro_ready/config` заменяют существующие:

- `config/settings.py`
- `config/urls.py`
- `config/views.py`

Новые приложения:

- `users`
- `patients`
- `outpatient`
- `billing`

Новые шаблоны:

- `templates/base.html`
- `templates/login.html`
- `templates/dashboard.html`
- `templates/patients/*`
- `templates/outpatient/*`

## Команды на Ubuntu

```bash
source venv/bin/activate
pip install -r requirment.txt
python manage.py makemigrations users patients outpatient billing
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Первое заполнение

В админке создайте:

1. специальность;
2. пользователя врача;
3. врача с привязкой к пользователю;
4. медицинскую услугу с ценой.

После этого регистратор может открыть `Новое обращение`, найти или создать пациента, выбрать услугу, врача, оплату и создать прием.
