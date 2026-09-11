from django.db import models


class USMUser(models.Model):
    pin = models.IntegerField(null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    checked = models.BooleanField(default=False) # If the user's pin was looked upon

class InitialProject(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título del Proyecto")
    description = models.TextField(verbose_name="Descripción")
    generation = models.IntegerField(verbose_name="Generación (Año)")
    members = models.TextField(verbose_name="Integrantes", help_text="Nombres separados por comas o saltos de línea")
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
