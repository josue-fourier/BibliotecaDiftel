from django.db import models
from django.db.models import CheckConstraint, Q


class ValoresFinancieros(models.Model):
    fecha = models.DateField(unique=True, null=False)

    valor_uf = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Valor UF")
    valor_utm = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Valor UTM")
    dolar_observado = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Valor Dólar Observado")

    def __str__ (self):
        return f"UF {self.valor_uf} - UTM {self.valor_utm} - Dólar {self.dolar_observado}"


class ValoresCalculadora(models.Model):
    fecha = models.DateField(unique=True)

    valor_retencion = models.DecimalField(max_digits=2, decimal_places=2, verbose_name="Valor Retención")
    valor_iva = models.DecimalField(max_digits=2, decimal_places=2, verbose_name="Valor IVA")
    valor_ppm = models.DecimalField(max_digits=2, decimal_places=2, verbose_name="Valor PPM")

    def __str__ (self):
        return f"Retención {self.valor_retencion} - IVA {self.valor_iva}"


class ServiciosBase(models.Model):
    id_servicio = models.CharField(max_length=20, unique=True, blank=False, null=False, verbose_name="ID del servicio")
    nombre = models.CharField(max_length=40, unique=True, blank=False, verbose_name="Nombre del servicio")
    semanas_base = models.IntegerField(blank=False, null=False, verbose_name="Semanas base del servicio")

    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(semanas_base__gte=1),
                name='check_minimo_semanas_base'
            ),
            CheckConstraint(
                condition=Q(semanas_base__lte=60),
                name='check_maximo_semanas_base'
            )
        ]

    def __str__(self) -> str:
        return f"Servicio '{self.id_servicio}'. Nombre '{self.nombre}'. Semanas Base '{self.semanas_base}'"

class ServiciosExtra(models.Model):
    id_servicio = models.CharField(max_length=20, unique=True, blank=False, null=False, verbose_name="ID del servicio extra")
    nombre = models.CharField(max_length=40, unique=True, blank=False, verbose_name="Nombre del servicio extra")
    semanas_penalizacion = models.IntegerField(blank=False, null=False, verbose_name="Semanas de Penalización")

    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(semanas_penalizacion__gte=1),
                name='check_minimo_semanas_penalizacion'
            ),
            CheckConstraint(
                condition=Q(semanas_penalizacion__lte=60),
                name='check_maximo_semanas_penalizacion'
            )
        ]
    
    def __str__(self) -> str:
        return f"Servicio '{self.id_servicio}'. Nombre '{self.nombre}'. Semanas Penalización '{self.semanas_penalizacion}'"
