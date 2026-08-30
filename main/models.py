import os
from django.conf import settings
from django.db.models import CASCADE, Q
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify


def validate_video_size(value):
    limit = 500 * 1024 * 1024  # 500 MB
    if value.size > limit:
        raise ValidationError(f"El video excede 500 MB ({value.size / 1024 / 1024:.1f} MB). Comprime el archivo.")

from .choices import Nivel


def _unique_slug(model, base_slug, pk=None):
    slug = base_slug
    i = 1
    while model.objects.filter(slug=slug).exclude(pk=pk).exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=90, unique=True, blank=True, verbose_name="Slug")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden")
    activa = models.BooleanField(default=True, verbose_name="Activa", help_text="Si está desactivada no aparece en filtros")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre)[:90] or 'categoria'
            self.slug = _unique_slug(Categoria, base, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Ruta(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    descripcion = models.TextField()
    descripcion_corta = models.CharField(max_length=300, blank=True, help_text="Resumen para cards")
    img = models.ImageField(upload_to='img_ruta/', blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='rutas', verbose_name="Categoría", db_index=True)
    nivel = models.CharField(max_length=50, choices=Nivel.choices, default=Nivel.MODULO_BASE, db_index=True)
    puntuacion = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="Califica del 1 al 5")
    destacada = models.BooleanField(default=False)

    # --- campos curso / detalle ---
    video_file = models.FileField(
        upload_to='videos_ruta/',
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'mov', 'mkv']), validate_video_size],
        help_text="Video del curso (MP4/WebM/MOV, máx 500 MB). Subido por administrador."
    )
    duracion_horas = models.PositiveIntegerField(default=180, help_text="Duración total en horas")
    duracion_semanas = models.PositiveIntegerField(default=6, help_text="Semanas")
    modalidad = models.CharField(max_length=100, default="Semipresencial AI-First")
    objetivos = models.TextField(blank=True, help_text="Un objetivo por línea")
    competencias = models.TextField(blank=True, help_text="Competencias, una por línea")
    requisitos = models.TextField(blank=True, help_text="Requisitos, uno por línea")
    incluye = models.TextField(blank=True, default="Open Badges 3.0 · Tutor IA · Proyecto integrador", help_text="Qué incluye, separado por · o líneas")
    instructor = models.CharField(max_length=200, blank=True, default="Equipo CVMTE")
    cupos = models.PositiveIntegerField(default=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-destacada', 'titulo']
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)[:200] or 'ruta'
            self.slug = _unique_slug(Ruta, base, self.pk)
        super().save(*args, **kwargs)

    def get_objetivos_list(self):
        return [l.strip() for l in (self.objetivos or "").splitlines() if l.strip()]

    def get_competencias_list(self):
        return [l.strip() for l in (self.competencias or "").splitlines() if l.strip()]

    @property
    def video_filename(self):
        return os.path.basename(self.video_file.name) if self.video_file else ""

    def __str__(self):
        return self.titulo


class Progreso(models.Model):
    """Un registro por usuario+curso. Curso es Ruta o Programa Petrolero (uno de los dos)."""
    class Estado(models.TextChoices):
        EN_PROGRESO = 'en_progreso', 'En progreso'
        COMPLETADO = 'completado', 'Completado'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='progresos')
    ruta = models.ForeignKey(Ruta, on_delete=CASCADE, null=True, blank=True, related_name='progresos')
    programa = models.ForeignKey('Card_petrolera', on_delete=CASCADE, null=True, blank=True, related_name='progresos')
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.EN_PROGRESO)
    completado = models.BooleanField(default=False)
    iniciado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    completado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Progreso'
        verbose_name_plural = 'Progresos'
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'ruta'], name='uniq_usuario_ruta', condition=Q(ruta__isnull=False)),
            models.UniqueConstraint(fields=['usuario', 'programa'], name='uniq_usuario_programa', condition=Q(programa__isnull=False)),
            models.CheckConstraint(condition=(Q(ruta__isnull=False, programa__isnull=True) | Q(ruta__isnull=True, programa__isnull=False)), name='progreso_un_curso'),
        ]
        ordering = ['-actualizado_en']

    def clean(self):
        if (self.ruta and self.programa) or (not self.ruta and not self.programa):
            raise ValidationError("Debe asociar exactamente un curso: Ruta o Programa Petrolero.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.completado and self.estado != self.Estado.COMPLETADO:
            self.estado = self.Estado.COMPLETADO
        if not self.completado and self.estado == self.Estado.COMPLETADO:
            self.completado = True
        super().save(*args, **kwargs)

    @property
    def curso_titulo(self):
        return self.ruta.titulo if self.ruta else self.programa.titulo

    @property
    def curso_slug(self):
        return self.ruta.slug if self.ruta else self.programa.slug

    @property
    def curso_tipo(self):
        return 'ruta' if self.ruta else 'petrolera'

    def __str__(self):
        return f"{self.usuario} - {self.curso_titulo} ({self.get_estado_display()})"


class Seccion_petrolera(models.Model):
    titulo = models.CharField(max_length=200)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'titulo']
        verbose_name = 'Sección petrolera'
        verbose_name_plural = 'Secciones petroleras'

    def __str__(self):
        return self.titulo


class Card_petrolera(models.Model):
    seccion = models.ForeignKey(Seccion_petrolera, on_delete=CASCADE, related_name='cards')
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, null=True)
    descripcion = models.TextField(blank=True, help_text="Descripción larga del programa")
    descripcion_corta = models.CharField(max_length=300, blank=True)
    img = models.ImageField(upload_to='img_petrolera/', blank=True, null=True, help_text="Imagen representativa del programa")
    nivel = models.CharField(max_length=50, choices=Nivel.choices, default=Nivel.MODULO_BASE)
    orden = models.PositiveIntegerField(default=0)

    # --- campos curso ---
    video_file = models.FileField(
        upload_to='videos_petrolera/',
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'mov', 'mkv']), validate_video_size],
        help_text="Video del programa (MP4/WebM/MOV, máx 500 MB). Subido por administrador."
    )
    duracion_horas = models.PositiveIntegerField(default=180)
    duracion_semanas = models.PositiveIntegerField(default=6)
    modalidad = models.CharField(max_length=100, default="Semipresencial AI-First")
    objetivos = models.TextField(blank=True, help_text="Un objetivo por línea")
    competencias = models.TextField(blank=True, help_text="Una por línea")
    requisitos = models.TextField(blank=True, help_text="Uno por línea")
    incluye = models.TextField(blank=True, default="Open Badges 3.0 · Práctica en campo · Analítica con IA")
    instructor = models.CharField(max_length=200, blank=True, default="Equipo Formación Petrolera")
    puntuacion = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)

    class Meta:
        ordering = ['orden', 'titulo']
        verbose_name = 'Programa petrolero'
        verbose_name_plural = 'Programas petroleros'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.titulo)[:200] or 'programa'
            self.slug = _unique_slug(Card_petrolera, base, self.pk)
        super().save(*args, **kwargs)

    def get_objetivos_list(self):
        return [l.strip() for l in (self.objetivos or "").splitlines() if l.strip()]

    def get_competencias_list(self):
        return [l.strip() for l in (self.competencias or "").splitlines() if l.strip()]

    @property
    def video_filename(self):
        return os.path.basename(self.video_file.name) if self.video_file else ""

    def __str__(self):
        return self.titulo
