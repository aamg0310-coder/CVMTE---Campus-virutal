from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Ruta, Categoria, Card_petrolera, Seccion_petrolera, Progreso
from .forms import RegistroForm


def Index(request):
    rutas = Ruta.objects.select_related('categoria').all()
    return render(request, 'pages/index.html', {
        'rutas': rutas,
    })


def Catalogo(request):
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    rutas_qs = Ruta.objects.select_related('categoria').all()
    if categoria and categoria.lower() != 'todas':
        # Filtrado por slug (recomendado) con fallback a nombre
        rutas_qs = rutas_qs.filter(
            Q(categoria__slug__iexact=categoria) | Q(categoria__nombre__iexact=categoria)
        )
    if q:
        rutas_qs = rutas_qs.filter(
            Q(titulo__icontains=q) | Q(descripcion__icontains=q) | Q(categoria__nombre__icontains=q)
        )

    paginator = Paginator(rutas_qs, 12)
    page = request.GET.get('page')
    rutas_page = paginator.get_page(page)

    secciones = Seccion_petrolera.objects.prefetch_related('cards').all()
    cards_petrolera = Card_petrolera.objects.select_related('seccion').all()
    return render(request, 'pages/catalogo2.html', {
        'rutas': rutas_page,
        'rutas_all': rutas_qs,
        'secciones': secciones,
        'cd': cards_petrolera,
        'q': q,
        'categoria': categoria,
    })


def api_rutas(request):
    """API JSON para búsqueda/filtrado de rutas. Usada opcionalmente por JS."""
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    rutas = Ruta.objects.select_related('categoria').all()
    if categoria and categoria.lower() != 'todas':
        rutas = rutas.filter(
            Q(categoria__slug__iexact=categoria) | Q(categoria__nombre__iexact=categoria)
        )
    if q:
        rutas = rutas.filter(
            Q(titulo__icontains=q) | Q(descripcion__icontains=q) | Q(categoria__nombre__icontains=q)
        )
    data = [
        {
            'id': r.id,
            'titulo': r.titulo,
            'descripcion': r.descripcion,
            'categoria': r.categoria.nombre if r.categoria else '',
            'categoria_slug': r.categoria.slug if r.categoria else '',
            'nivel': r.nivel,
            'puntuacion': r.puntuacion,
            'img': r.img.url if r.img else '',
            'url': f'/ruta/{r.slug or r.id}/',
            'slug': r.slug,
        }
        for r in rutas
    ]
    return JsonResponse(data, safe=False)


def detalle_ruta(request, pk=None, slug=None):
    if slug:
        ruta = get_object_or_404(Ruta.objects.select_related('categoria'), slug=slug)
    else:
        ruta = get_object_or_404(Ruta.objects.select_related('categoria'), pk=pk)
    relacionadas = Ruta.objects.filter(categoria=ruta.categoria).exclude(pk=ruta.pk)[:3] if ruta.categoria else Ruta.objects.none()
    progreso = None
    if request.user.is_authenticated:
        progreso = Progreso.objects.filter(usuario=request.user, ruta=ruta).first()
    return render(request, 'pages/detalle_ruta.html', {'ruta': ruta, 'relacionadas': relacionadas, 'progreso': progreso})


def detalle_petrolera(request, pk=None, slug=None):
    if slug:
        programa = get_object_or_404(Card_petrolera.objects.select_related('seccion'), slug=slug)
    else:
        programa = get_object_or_404(Card_petrolera.objects.select_related('seccion'), pk=pk)
    relacionadas = Card_petrolera.objects.filter(seccion=programa.seccion).exclude(pk=programa.pk)[:3]
    otras_secciones = Seccion_petrolera.objects.prefetch_related('cards').exclude(pk=programa.seccion.pk)[:2]
    progreso = None
    if request.user.is_authenticated:
        progreso = Progreso.objects.filter(usuario=request.user, programa=programa).first()
    return render(request, 'pages/detalle_petrolera.html', {
        'programa': programa,
        'relacionadas': relacionadas,
        'otras_secciones': otras_secciones,
        'progreso': progreso,
    })


# --- Auth ---

def registro_view(request):
    if request.user.is_authenticated:
        return redirect('main:perfil')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bienvenido, {user.username}!")
            return redirect('main:perfil')
    else:
        form = RegistroForm()
    return render(request, 'pages/auth.html', {'form': form, 'modo': 'registro'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('main:perfil')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or 'main:perfil'
            return redirect(next_url if next_url.startswith('/') else 'main:perfil')
    else:
        form = AuthenticationForm()
    return render(request, 'pages/auth.html', {'form': form, 'modo': 'login'})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada.")
    return redirect('main:inicio')


@login_required
def perfil_view(request):
    progresos = Progreso.objects.filter(usuario=request.user).select_related('ruta', 'programa', 'programa__seccion', 'ruta__categoria')
    en_progreso = progresos.filter(completado=False)
    completados = progresos.filter(completado=True)
    total_rutas = Ruta.objects.count()
    total_programas = Card_petrolera.objects.count()
    total_cursos = total_rutas + total_programas
    return render(request, 'pages/perfil.html', {
        'progresos': progresos,
        'en_progreso': en_progreso,
        'completados': completados,
        'total_cursos': total_cursos,
        'total_rutas': total_rutas,
        'total_programas': total_programas,
    })


@login_required
@require_POST
def toggle_progreso_ruta(request, slug):
    ruta = get_object_or_404(Ruta, slug=slug)
    progreso, created = Progreso.objects.get_or_create(usuario=request.user, ruta=ruta, defaults={'programa': None})
    # toggle completado
    progreso.completado = not progreso.completado
    progreso.estado = Progreso.Estado.COMPLETADO if progreso.completado else Progreso.Estado.EN_PROGRESO
    progreso.completado_en = timezone.now() if progreso.completado else None
    progreso.save()
    messages.success(request, f"{'Completado' if progreso.completado else 'Marcado en progreso'}: {ruta.titulo}")
    return redirect('main:detalle_ruta_slug', slug=ruta.slug)


@login_required
@require_POST
def toggle_progreso_petrolera(request, slug):
    programa = get_object_or_404(Card_petrolera, slug=slug)
    progreso, created = Progreso.objects.get_or_create(usuario=request.user, programa=programa, defaults={'ruta': None})
    progreso.completado = not progreso.completado
    progreso.estado = Progreso.Estado.COMPLETADO if progreso.completado else Progreso.Estado.EN_PROGRESO
    progreso.completado_en = timezone.now() if progreso.completado else None
    progreso.save()
    messages.success(request, f"{'Completado' if progreso.completado else 'Marcado en progreso'}: {programa.titulo}")
    return redirect('main:detalle_petrolera_slug', slug=programa.slug)
