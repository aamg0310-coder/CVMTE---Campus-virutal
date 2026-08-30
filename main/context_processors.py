from .models import Categoria

def categorias(request):
    return {
        'categorias': Categoria.objects.filter(activa=True).order_by('orden', 'nombre')
    }
