from django.test import TestCase, Client
from django.urls import reverse
from .models import Ruta, Categoria


class RutaModelTest(TestCase):
    def test_create_and_slug(self):
        cat, _ = Categoria.objects.get_or_create(nombre="Agroproductivo", defaults={"slug": "agroproductivo-test"})
        r = Ruta.objects.create(titulo="Ruta Test Petrolera", descripcion="desc", puntuacion=4, categoria=cat, nivel="Nivel I")
        self.assertTrue(r.slug)
        self.assertIn("ruta-test", r.slug)

    def test_puntuacion_validator(self):
        from django.core.exceptions import ValidationError
        r = Ruta(titulo="X", descripcion="d", puntuacion=10)
        with self.assertRaises(ValidationError):
            r.full_clean()


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat, _ = Categoria.objects.get_or_create(nombre="Eje transversal", defaults={"slug": "eje-transversal-test"})
        Ruta.objects.create(titulo="Ruta IA", descripcion="IA aplicada", puntuacion=5, categoria=self.cat, nivel="Modulo Base")

    def test_index(self):
        self.assertEqual(self.client.get(reverse('main:inicio')).status_code, 200)

    def test_catalogo(self):
        self.assertEqual(self.client.get(reverse('main:catalogo')).status_code, 200)

    def test_api_filter(self):
        resp = self.client.get(reverse('main:api_rutas') + '?q=IA')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()) >= 1)

    def test_api_filter_categoria_slug(self):
        resp = self.client.get(reverse('main:api_rutas') + f'?categoria={self.cat.slug}')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()) >= 1)

    def test_detalle_slug(self):
        r = Ruta.objects.first()
        self.assertEqual(self.client.get(f'/ruta/{r.slug}/').status_code, 200)

    def test_filter_html_categorias(self):
        # Verifica que filter.html renderiza categorias dinámicas
        resp = self.client.get(reverse('main:catalogo'))
        self.assertContains(resp, 'Todas')
        self.assertContains(resp, self.cat.nombre)
        self.assertContains(resp, self.cat.slug)
