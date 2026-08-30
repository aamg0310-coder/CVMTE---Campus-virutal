from django.db import models

class Nivel(models.TextChoices):
    MODULO_BASE = 'Modulo Base', 'Módulo Base'
    NIVEL_III = 'Nivel III', 'Nivel III'
    NIVEL_II = 'Nivel II', 'Nivel II'
    NIVEL_I = 'Nivel I', 'Nivel I'
