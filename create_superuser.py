import os
import django

# Recuerda cambiar 'tu_proyecto.settings' por el nombre real del directorio donde está tu settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CVMTE.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Valores solicitados con fallback automático
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'angel')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'angel@gmail.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '123')

if not User.objects.filter(username=username).exists():
    print(f"Creando superusuario '{username}'...")
    User.objects.create_superuser(username=username, email=email, password=password)
    print("Superusuario creado exitosamente.")
else:
    print(f"El superusuario '{username}' ya existe. Se omite la creación.")
