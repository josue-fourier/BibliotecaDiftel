from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MaxLengthValidator


class USMUser(models.Model):
    pin = models.IntegerField(null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    checked = models.BooleanField(default=False) # If the user's pin was looked upon

class InitialProject(models.Model):
    title = models.CharField(max_length=100, verbose_name="Título del Proyecto")
    description = models.TextField(verbose_name="Descripción", validators=[MaxLengthValidator(500)])
    generation = models.IntegerField(verbose_name="Generación (Año)", validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    members = models.TextField(verbose_name="Integrantes", help_text="Nombres separados por comas o saltos de línea", validators=[MaxLengthValidator(150)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proyecto Inicial"
        verbose_name_plural = "Proyectos Iniciales"
        ordering = ['-generation', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.generation})"

class ProjectImage(models.Model):
    project = models.ForeignKey(InitialProject, on_delete=models.CASCADE, related_name='images', verbose_name="Proyecto")
    image = models.ImageField(upload_to='initial_projects/', verbose_name="Imagen")
    order = models.IntegerField(default=0, verbose_name="Orden de aparición")

    class Meta:
        verbose_name = "Imagen de Proyecto"
        verbose_name_plural = "Imágenes de Proyecto"
        ordering = ['order']

    def __str__(self):
        return f"Imagen {self.order} para {self.project.title}"


EVENT_TYPE_CHOICES = [
    ('taller', 'Taller'),
    ('charla', 'Charla'),
    ('conferencia', 'Conferencia'),
    ('hackathon', 'Hackathon'),
    ('otro', 'Otro'),
]


class Workshop(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título del Taller")
    description = models.TextField(verbose_name="Descripción")
    year = models.IntegerField(verbose_name="Año de Realización", db_index=True)
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        default='taller',
        verbose_name="Tipo de Evento"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Taller Telemático"
        verbose_name_plural = "Talleres Telemáticos"
        ordering = ['-year', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.year})"

    @property
    def primary_image(self):
        return self.images.first()


class WorkshopImage(models.Model):
    workshop = models.ForeignKey(
        Workshop,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Taller"
    )
    image = models.ImageField(upload_to='workshops/', verbose_name="Fotografía")
    order = models.IntegerField(default=0, verbose_name="Orden de aparición")
    caption = models.CharField(max_length=200, blank=True, verbose_name="Leyenda")

    class Meta:
        verbose_name = "Fotografía de Taller"
        verbose_name_plural = "Fotografías de Taller"
        ordering = ['order', 'id']

    def __str__(self):
        return f"Fotografía {self.order} para {self.workshop.title}"


class CommunityMember(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre Completo")
    generation = models.IntegerField(verbose_name="Generación (Año de Egreso)", db_index=True)
    bio = models.TextField(verbose_name="Biografía")
    current_role = models.CharField(max_length=200, blank=True, verbose_name="Rol o Cargo Actual")
    linkedin_url = models.URLField(max_length=255, blank=True, verbose_name="LinkedIn")
    github_url = models.URLField(max_length=255, blank=True, verbose_name="GitHub")
    email = models.EmailField(blank=True, verbose_name="Correo de Contacto")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Miembro de la Comunidad"
        verbose_name_plural = "Comunidad y Exalumnos"
        ordering = ['-generation', 'name']

    def __str__(self):
        return f"{self.name} ({self.generation})"

