from django.contrib import admin
from .models import Ruta, Categoria, Seccion_petrolera, Card_petrolera, Progreso


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'orden', 'activa', 'created_at')
    list_filter = ('activa',)
    search_fields = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}
    list_editable = ('orden', 'activa')
    ordering = ('orden', 'nombre')


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'nivel', 'puntuacion', 'destacada', 'duracion_horas', 'updated_at')
    list_filter = ('categoria', 'nivel', 'destacada')
    search_fields = ('titulo', 'descripcion', 'categoria__nombre')
    prepopulated_fields = {'slug': ('titulo',)}
    list_editable = ('destacada',)
    readonly_fields = ('video_preview',)
    autocomplete_fields = ['categoria']

    def video_preview(self, obj):
        if obj.video_file:
            from django.utils.html import format_html
            return format_html('<video src="{}" controls style="max-width:320px;max-height:180px;border-radius:8px;"></video><br><small>{}</small>', obj.video_file.url, obj.video_filename)
        return "Sin video — sube un MP4/WebM"
    video_preview.short_description = "Vista previa video"

    fieldsets = (
        (None, {'fields': ('titulo', 'slug', 'descripcion', 'descripcion_corta', 'img', 'categoria', 'nivel', 'puntuacion', 'destacada')}),
        ('Curso / Video (solo archivo subido por admin)', {'fields': ('video_file', 'video_preview', 'duracion_horas', 'duracion_semanas', 'modalidad', 'instructor', 'cupos', 'incluye')}),
        ('Contenido pedagógico', {'fields': ('objetivos', 'competencias', 'requisitos')}),
    )


class CardPetroleraInline(admin.TabularInline):
    model = Card_petrolera
    extra = 1
    prepopulated_fields = {'slug': ('titulo',)}
    fields = ('titulo', 'slug', 'img', 'nivel', 'orden', 'puntuacion')


@admin.register(Seccion_petrolera)
class SeccionPetroleraAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'orden')
    inlines = [CardPetroleraInline]


@admin.register(Card_petrolera)
class CardPetroleraAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'seccion', 'nivel', 'puntuacion', 'duracion_horas', 'orden', 'img_preview', 'has_video')
    readonly_fields = ('img_preview', 'video_preview')

    def img_preview(self, obj):
        if obj.img:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="width:80px;height:50px;object-fit:cover;border-radius:8px;" />', obj.img.url)
        return "—"
    img_preview.short_description = "Imagen"

    def video_preview(self, obj):
        if obj.video_file:
            from django.utils.html import format_html
            return format_html('<video src="{}" controls style="max-width:320px;max-height:180px;border-radius:8px;"></video><br><small>{}</small>', obj.video_file.url, obj.video_filename)
        return "Sin video"
    video_preview.short_description = "Video"

    def has_video(self, obj):
        return bool(obj.video_file)
    has_video.boolean = True
    has_video.short_description = "Video"

    list_filter = ('nivel', 'seccion')
    search_fields = ('titulo', 'descripcion')
    prepopulated_fields = {'slug': ('titulo',)}
    fieldsets = (
        (None, {'fields': ('seccion', 'titulo', 'slug', 'descripcion', 'descripcion_corta', 'img', 'nivel', 'puntuacion', 'orden')}),
        ('Curso / Video (solo archivo subido por admin)', {'fields': ('video_file', 'video_preview', 'duracion_horas', 'duracion_semanas', 'modalidad', 'instructor', 'incluye')}),
        ('Contenido pedagógico', {'fields': ('objetivos', 'competencias', 'requisitos')}),
    )


@admin.register(Progreso)
class ProgresoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'curso_titulo', 'curso_tipo', 'estado', 'completado', 'actualizado_en', 'completado_en')
    list_filter = ('estado', 'completado')
    search_fields = ('usuario__username', 'ruta__titulo', 'programa__titulo')
    readonly_fields = ('iniciado_en', 'actualizado_en')
