import shutil
import tempfile
from django.test import TestCase, override_settings
from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from dashboard.models import Workshop, WorkshopImage, CommunityMember, EVENT_TYPE_CHOICES
from dashboard.admin import WorkshopAdmin, CommunityMemberAdmin, WorkshopImageInline


class WorkshopModelTests(TestCase):
    def test_workshop_creation_defaults(self):
        workshop = Workshop.objects.create(
            title="Taller de Redes Ópticas",
            description="Introducción a la tecnología DWDM y fibra monomodo.",
            year=2024,
        )
        self.assertEqual(workshop.title, "Taller de Redes Ópticas")
        self.assertEqual(workshop.year, 2024)
        self.assertEqual(workshop.event_type, "taller")
        self.assertEqual(str(workshop), "Taller de Redes Ópticas (2024)")
        self.assertIsNotNone(workshop.created_at)

    def test_workshop_custom_event_type(self):
        workshop = Workshop.objects.create(
            title="Conferencia de Ciberseguridad",
            description="Seguridad en redes IoT y protocolos industriales.",
            year=2025,
            event_type="conferencia",
        )
        self.assertEqual(workshop.event_type, "conferencia")
        self.assertEqual(str(workshop), "Conferencia de Ciberseguridad (2025)")

    def test_workshop_ordering(self):
        w1 = Workshop.objects.create(title="W 2023", description="Desc", year=2023)
        w2 = Workshop.objects.create(title="W 2025", description="Desc", year=2025)
        w3 = Workshop.objects.create(title="W 2024", description="Desc", year=2024)
        workshops = list(Workshop.objects.all())
        self.assertEqual(workshops, [w2, w3, w1])

    def test_workshop_guia_url(self):
        workshop = Workshop.objects.create(
            title="Taller con Guía",
            description="Taller práctico",
            year=2024,
            guia_url="https://wiki-diftel.josnic.cl/p/guia-taller-1",
        )
        self.assertEqual(workshop.guia_url, "https://wiki-diftel.josnic.cl/p/guia-taller-1")


class WorkshopImageModelTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.workshop = Workshop.objects.create(
            title="Taller de Antenas",
            description="Diseño y simulación de arreglos de antenas en HFSS.",
            year=2024,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_dummy_image(self, filename="test_img.png"):
        # 1x1 transparent PNG payload
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00'
            b'\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf'
            b'\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return SimpleUploadedFile(filename, png_data, content_type="image/png")

    def test_workshop_image_creation_and_reverse_relation(self):
        with override_settings(MEDIA_ROOT=self.temp_dir):
            img = WorkshopImage.objects.create(
                workshop=self.workshop,
                image=self._create_dummy_image("foto1.png"),
                order=1,
                caption="Laboratorio de microondas",
            )
            self.assertEqual(img.workshop, self.workshop)
            self.assertEqual(img.order, 1)
            self.assertEqual(img.caption, "Laboratorio de microondas")
            self.assertIn("workshops/", img.image.name)
            self.assertEqual(str(img), f"Fotografía 1 para {self.workshop.title}")

            # Test reverse relation
            self.assertEqual(self.workshop.images.count(), 1)
            self.assertEqual(list(self.workshop.images.all()), [img])
            self.assertEqual(self.workshop.primary_image, img)

    def test_workshop_image_ordering(self):
        with override_settings(MEDIA_ROOT=self.temp_dir):
            img2 = WorkshopImage.objects.create(
                workshop=self.workshop,
                image=self._create_dummy_image("foto2.png"),
                order=2,
            )
            img1 = WorkshopImage.objects.create(
                workshop=self.workshop,
                image=self._create_dummy_image("foto1.png"),
                order=0,
            )
            images = list(self.workshop.images.all())
            self.assertEqual(images, [img1, img2])
            self.assertEqual(self.workshop.primary_image, img1)

    def test_workshop_cascade_deletion(self):
        with override_settings(MEDIA_ROOT=self.temp_dir):
            WorkshopImage.objects.create(
                workshop=self.workshop,
                image=self._create_dummy_image("foto1.png"),
                order=0,
            )
            self.assertEqual(WorkshopImage.objects.count(), 1)
            self.workshop.delete()
            self.assertEqual(WorkshopImage.objects.count(), 0)


class CommunityMemberModelTests(TestCase):
    def test_community_member_creation(self):
        member = CommunityMember.objects.create(
            name="Valeria Carrasco",
            generation=2018,
            bio="Ingeniera Civil Telemática especializada en redes 5G y cloud computing.",
            current_role="Senior Network Architect en Telco Corp",
            linkedin_url="https://linkedin.com/in/valeriacarrasco",
            github_url="https://github.com/valeriacarrasco",
            email="valeria.carrasco@alumnos.usm.cl",
        )
        self.assertEqual(member.name, "Valeria Carrasco")
        self.assertEqual(member.generation, 2018)
        self.assertEqual(str(member), "Valeria Carrasco (2018)")
        self.assertEqual(member.current_role, "Senior Network Architect en Telco Corp")
        self.assertEqual(member.linkedin_url, "https://linkedin.com/in/valeriacarrasco")
        self.assertEqual(member.github_url, "https://github.com/valeriacarrasco")
        self.assertEqual(member.email, "valeria.carrasco@alumnos.usm.cl")
        self.assertIsNone(member.profile_picture.name)
        self.assertIsNotNone(member.created_at)

    def test_community_member_profile_picture(self):
        temp_dir = tempfile.mkdtemp()
        try:
            with override_settings(MEDIA_ROOT=temp_dir):
                png_data = (
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                    b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00'
                    b'\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf'
                    b'\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
                )
                photo = SimpleUploadedFile("avatar.png", png_data, content_type="image/png")
                member = CommunityMember.objects.create(
                    name="Carolina Mendoza",
                    generation=2019,
                    bio="Especialista en Telecomunicaciones",
                    profile_picture=photo,
                )
                self.assertIn("community/profile_pics/", member.profile_picture.name)
                import os
                self.assertTrue(os.path.exists(member.profile_picture.path))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_community_member_optional_fields(self):
        member = CommunityMember.objects.create(
            name="Ignacio Silva",
            generation=2021,
            bio="Interesado en investigación de SDN.",
        )
        self.assertEqual(member.current_role, "")
        self.assertEqual(member.linkedin_url, "")
        self.assertEqual(member.github_url, "")
        self.assertEqual(member.email, "")
        self.assertFalse(bool(member.profile_picture))
        self.assertEqual(str(member), "Ignacio Silva (2021)")

    def test_community_member_ordering(self):
        m1 = CommunityMember.objects.create(name="Beatriz", generation=2015, bio="Bio")
        m2 = CommunityMember.objects.create(name="Andrés", generation=2020, bio="Bio")
        m3 = CommunityMember.objects.create(name="Carlos", generation=2020, bio="Bio")
        members = list(CommunityMember.objects.all())
        # Ordered by -generation, then name
        self.assertEqual(members, [m2, m3, m1])


class AdminRegistrationTests(TestCase):
    def test_workshop_admin_registered(self):
        self.assertIn(Workshop, admin.site._registry)
        model_admin = admin.site._registry[Workshop]
        self.assertIsInstance(model_admin, WorkshopAdmin)
        self.assertEqual(
            model_admin.list_display,
            ('title', 'year', 'event_type', 'guia_url', 'created_at')
        )
        self.assertEqual(model_admin.list_filter, ('year', 'event_type'))
        self.assertEqual(model_admin.search_fields, ('title', 'description', 'guia_url'))
        self.assertEqual(len(model_admin.inlines), 1)
        self.assertEqual(model_admin.inlines[0], WorkshopImageInline)

    def test_workshop_image_inline_configuration(self):
        inline = WorkshopImageInline(Workshop, admin.site)
        self.assertEqual(inline.model, WorkshopImage)
        self.assertEqual(inline.extra, 1)
        self.assertEqual(inline.fields, ('image', 'order', 'caption'))
        self.assertEqual(inline.ordering, ('order',))

    def test_community_member_admin_registered(self):
        self.assertIn(CommunityMember, admin.site._registry)
        model_admin = admin.site._registry[CommunityMember]
        self.assertIsInstance(model_admin, CommunityMemberAdmin)
        self.assertEqual(
            model_admin.list_display,
            ('name', 'generation', 'current_role', 'email')
        )
        self.assertEqual(model_admin.list_filter, ('generation',))
        self.assertEqual(
            model_admin.search_fields,
            ('name', 'bio', 'current_role', 'email')
        )


class MediaConfigurationTests(TestCase):
    def test_media_settings_and_storage(self):
        temp_dir = tempfile.mkdtemp()
        try:
            with override_settings(MEDIA_ROOT=temp_dir, MEDIA_URL='/media/'):
                workshop = Workshop.objects.create(
                    title="Taller de Python",
                    description="Intro",
                    year=2024,
                )
                png_data = (
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                    b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00'
                    b'\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf'
                    b'\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
                )
                upload = SimpleUploadedFile("python_logo.png", png_data, content_type="image/png")
                w_img = WorkshopImage.objects.create(
                    workshop=workshop,
                    image=upload,
                    order=1,
                )
                import os
                self.assertTrue(os.path.exists(w_img.image.path))
                self.assertTrue(w_img.image.path.startswith(temp_dir))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @override_settings(DEBUG=True)
    def test_media_urls_configured_when_debug(self):
        from django.conf.urls.static import static
        from django.conf import settings
        media_patterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        self.assertTrue(len(media_patterns) > 0)
        self.assertIsNotNone(media_patterns[0].pattern.regex.search('media/workshops/test.png'))

