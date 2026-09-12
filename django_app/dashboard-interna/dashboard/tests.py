import shutil
import tempfile
from django.test import TestCase, override_settings
from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
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


class WorkshopViewTests(TestCase):
    """
    Automated integration and UI tests for Milestone 2: Talleres Telemáticos.
    Validates full page view, HTMX partial rendering, year filtering, media URLs,
    written guide links, empty states, responsive grid classes, and query counts.
    """

    def setUp(self):
        # 1. Create temporary directory for media files to avoid host permission errors
        self.temp_dir = tempfile.mkdtemp()

        # 2. Setup temporary media files and fixtures
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            # Workshop 1: Year 2024, type taller, has guide URL and primary image
            self.w2024_1 = Workshop.objects.create(
                title="Taller de Antenas y Propagación",
                description="Diseño práctico de monopolos y dipolos en laboratorio.",
                year=2024,
                event_type="taller",
                guia_url="https://wiki-diftel.josnic.cl/p/guia-antenas-2024"
            )
            self.img2024_1 = WorkshopImage.objects.create(
                workshop=self.w2024_1,
                image=self._create_dummy_image("antenas.png"),
                order=0,
                caption="Medición de ROE en analizador de espectro"
            )
            # Add a second image to test multi-image carousel
            self.img2024_1_b = WorkshopImage.objects.create(
                workshop=self.w2024_1,
                image=self._create_dummy_image("antenas_patron.png"),
                order=1,
                caption="Patrón de radiación en cámara anecoica"
            )

            # Workshop 2: Year 2024, type charla, empty guide URL, NO images attached
            self.w2024_2 = Workshop.objects.create(
                title="Charla de Ciberseguridad Ofensiva",
                description="Análisis de vulnerabilidades en protocolos IoT.",
                year=2024,
                event_type="charla",
                guia_url=""  # Blank URL
            )

            # Workshop 3: Year 2023, type conferencia, None guide URL
            self.w2023 = Workshop.objects.create(
                title="Conferencia de Redes Ópticas DWDM",
                description="Topologías metropolitanas y amplificación óptica EDFA.",
                year=2023,
                event_type="conferencia",
                guia_url=None  # Null URL
            )

            # Workshop 4: Year 2025, type hackathon, has guide URL and image
            self.w2025 = Workshop.objects.create(
                title="Hackathon Telemática UTFSM 2025",
                description="Desarrollo de aplicaciones telemáticas distribuidas.",
                year=2025,
                event_type="hackathon",
                guia_url="https://wiki-diftel.josnic.cl/p/guia-hackathon-2025"
            )
            self.img2025 = WorkshopImage.objects.create(
                workshop=self.w2025,
                image=self._create_dummy_image("hackathon.png"),
                order=0,
                caption="Equipos trabajando en el laboratorio"
            )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_dummy_image(self, filename="dummy.png"):
        """Creates a valid 1x1 in-memory PNG file."""
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00'
            b'\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf'
            b'\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return SimpleUploadedFile(filename, png_data, content_type="image/png")

    # --------------------------------------------------------------------------
    # 1. Full Page View Tests
    # --------------------------------------------------------------------------
    def test_workshops_full_page_view_status_and_templates(self):
        """GET /talleres/ returns 200, uses workshops.html, extends base.html, and renders shell."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('workshops'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'dashboard/workshops.html')
            self.assertTemplateUsed(response, 'base.html')
            self.assertTemplateUsed(response, 'dashboard/partials/workshops_list.html')

            # Verify full page shell elements are present
            self.assertContains(response, '<!DOCTYPE html>')
            self.assertContains(response, 'Biblioteca Diftel Admin')
            self.assertContains(response, 'Talleres Telemáticos')

    def test_workshops_full_page_view_context_keys(self):
        """GET /talleres/ provides expected context keys: workshops, years, selected_year, etc."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('workshops'))
            self.assertEqual(response.status_code, 200)

            # Context keys
            self.assertIn('workshops', response.context)
            self.assertIn('years', response.context)
            self.assertIn('selected_year', response.context)
            self.assertIn('active_year', response.context)
            self.assertIn('event_types', response.context)
            self.assertIn('selected_type', response.context)

            # All 4 workshops returned by default
            workshops_in_context = list(response.context['workshops'])
            self.assertEqual(len(workshops_in_context), 4)

            # Years ordered newest first: [2025, 2024, 2023]
            years_list = list(response.context['years'])
            self.assertEqual(years_list, [2025, 2024, 2023])

            # Default selected_year is None (showing all years)
            self.assertIsNone(response.context['selected_year'])

    # --------------------------------------------------------------------------
    # 2. HTMX Partial Request Tests
    # --------------------------------------------------------------------------
    def test_workshops_htmx_partial_request(self):
        """HTMX request returns 200, uses workshops_list.html partial, and omits base shell."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('workshops'), HTTP_HX_REQUEST='true')
            self.assertEqual(response.status_code, 200)

            # Partial template used
            self.assertTemplateUsed(response, 'dashboard/partials/workshops_list.html')

            # Full layout shell MUST NOT be used
            self.assertTemplateNotUsed(response, 'base.html')
            self.assertTemplateNotUsed(response, 'dashboard/workshops.html')

            # Assert absence of outer HTML document structures
            self.assertNotContains(response, '<!DOCTYPE html>')
            self.assertNotContains(response, '<html')
            self.assertNotContains(response, '<head>')
            self.assertNotContains(response, '<nav class="navbar')
            self.assertNotContains(response, '<footer')

            # Assert partial content is rendered
            self.assertContains(response, 'Taller de Antenas y Propagación')
            self.assertContains(response, 'grid-cols-1')

    # --------------------------------------------------------------------------
    # 3. Year Filtering Tests
    # --------------------------------------------------------------------------
    def test_workshops_year_filter_via_query_param(self):
        """GET /talleres/?year=2024 filters workshops to only those from 2024."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(f"{reverse('workshops')}?year=2024")
            self.assertEqual(response.status_code, 200)

            workshops = list(response.context['workshops'])
            self.assertEqual(len(workshops), 2)
            self.assertEqual({w.year for w in workshops}, {2024})

            # Check rendered content contains 2024 items and excludes 2023 / 2025
            self.assertContains(response, self.w2024_1.title)
            self.assertContains(response, self.w2024_2.title)
            self.assertNotContains(response, self.w2023.title)
            self.assertNotContains(response, self.w2025.title)

    def test_workshops_year_filter_htmx_partial(self):
        """HTMX GET /talleres/?year=2024 returns filtered partial without base shell."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(f"{reverse('workshops')}?year=2024", HTTP_HX_REQUEST='true')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'dashboard/partials/workshops_list.html')
            self.assertTemplateNotUsed(response, 'base.html')

            self.assertContains(response, self.w2024_1.title)
            self.assertContains(response, self.w2024_2.title)
            self.assertNotContains(response, self.w2023.title)
            self.assertNotContains(response, self.w2025.title)

    def test_workshops_year_filter_via_path_param(self):
        """GET /talleres/year/2024/ returns 200 and filters workshops to 2024."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('workshops_by_year', kwargs={'year': 2024}))
            self.assertEqual(response.status_code, 200)
            workshops = list(response.context['workshops'])
            self.assertEqual(len(workshops), 2)
            self.assertEqual(response.context['selected_year'], 2024)

    def test_workshops_list_view_explicit_endpoint(self):
        """GET /talleres/partial/ and /talleres/partial/year/<year>/ return partial directly."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            # Base partial endpoint
            res_all = self.client.get(reverse('workshops_list'))
            self.assertEqual(res_all.status_code, 200)
            self.assertTemplateUsed(res_all, 'dashboard/partials/workshops_list.html')
            self.assertTemplateNotUsed(res_all, 'base.html')
            self.assertEqual(len(list(res_all.context['workshops'])), 4)

            # Year-filtered partial endpoint
            res_year = self.client.get(reverse('workshops_list_by_year', kwargs={'year': 2024}))
            self.assertEqual(res_year.status_code, 200)
            self.assertTemplateUsed(res_year, 'dashboard/partials/workshops_list.html')
            self.assertTemplateNotUsed(res_year, 'base.html')
            self.assertEqual(len(list(res_year.context['workshops'])), 2)

    # --------------------------------------------------------------------------
    # 4. Media Serving / Image URLs in Rendered HTML
    # --------------------------------------------------------------------------
    def test_workshop_media_image_urls_rendered(self):
        """Rendered HTML contains workshop.primary_image.image.url pointing to /media/workshops/."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('workshops'))
            self.assertEqual(response.status_code, 200)

            # Workshop 1 has an image
            self.assertIsNotNone(self.w2024_1.primary_image)
            image_url = self.w2024_1.primary_image.image.url
            self.assertTrue(image_url.startswith('/media/workshops/'))

            # Verify image tag in rendered HTML
            self.assertContains(response, image_url)
            self.assertContains(response, f'src="{image_url}"')

            # Verify multi-image carousel components rendered for w2024_1
            self.assertContains(response, 'carousel')
            self.assertContains(response, 'carousel-item')

    def test_workshop_without_images_renders_fallback_placeholder(self):
        """Workshops without images render graceful placeholder and do not throw errors."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            # Filter specifically for 2024 where w2024_2 has no image
            response = self.client.get(f"{reverse('workshops')}?year=2024")
            self.assertEqual(response.status_code, 200)

            # Verify placeholder label is present in HTML
            self.assertContains(response, 'Sin fotografías adjuntas')

    # --------------------------------------------------------------------------
    # 5. Written Guide URL Tests
    # --------------------------------------------------------------------------
    def test_workshop_guia_url_rendering_and_omission(self):
        """Rendered HTML contains guia_url link when present, and omits it when null or blank."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('workshops'))
            self.assertEqual(response.status_code, 200)

            # Workshop 1 has valid guide URL
            self.assertContains(response, 'href="https://wiki-diftel.josnic.cl/p/guia-antenas-2024"')
            self.assertContains(response, 'target="_blank"')
            self.assertContains(response, 'rel="noopener noreferrer"')
            self.assertContains(response, 'Ver Guía Escrita')

            # Verify no broken or empty hrefs are rendered for guide buttons
            self.assertNotContains(response, 'href=""')
            self.assertNotContains(response, 'href="None"')

    # --------------------------------------------------------------------------
    # 6. Empty State Tests
    # --------------------------------------------------------------------------
    def test_workshops_empty_state_for_unregistered_year(self):
        """Filtering by a year with zero workshops displays user-friendly empty message."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(f"{reverse('workshops')}?year=2010", HTTP_HX_REQUEST='true')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['workshops']), 0)

            # Empty state feedback
            self.assertContains(response, 'No se encontraron talleres')
            self.assertContains(response, 'No hay actividades o talleres registrados para el año 2010')

    def test_workshops_empty_state_when_no_records_in_database(self):
        """When database is completely empty of workshops, friendly global message is shown."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            Workshop.objects.all().delete()
            response = self.client.get(reverse('workshops'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['workshops']), 0)

            self.assertContains(response, 'No se encontraron talleres')
            self.assertContains(response, 'Aún no hay talleres registrados en la base de datos')

    # --------------------------------------------------------------------------
    # 7. Responsive Classes & Visual Badges
    # --------------------------------------------------------------------------
    def test_responsive_grid_and_daisyui_classes(self):
        """Rendered HTML contains required mobile-first grid and DaisyUI card classes."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('workshops'), HTTP_HX_REQUEST='true')
            self.assertEqual(response.status_code, 200)

            # Responsive layout requirement
            self.assertContains(response, 'grid-cols-1')
            self.assertContains(response, 'md:grid-cols-2')
            self.assertContains(response, 'lg:grid-cols-3')
            self.assertContains(response, 'gap-6')

            # DaisyUI card components
            self.assertContains(response, 'card')
            self.assertContains(response, 'card-body')
            self.assertContains(response, 'badge')

    def test_event_type_badges_rendered(self):
        """Event types render their corresponding badges (Taller, Charla, Conferencia, Hackathon)."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('workshops'))
            self.assertEqual(response.status_code, 200)

            self.assertContains(response, 'badge-primary')    # Taller
            self.assertContains(response, 'badge-secondary')  # Charla
            self.assertContains(response, 'badge-accent')     # Conferencia
            self.assertContains(response, 'badge-warning')    # Hackathon

    def test_event_type_filtering(self):
        """Filtering by event_type returns only matching events."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(f"{reverse('workshops')}?type=charla")
            self.assertEqual(response.status_code, 200)
            workshops = list(response.context['workshops'])
            self.assertEqual(len(workshops), 1)
            self.assertEqual(workshops[0].title, self.w2024_2.title)

    # --------------------------------------------------------------------------
    # 8. Query Optimization (N+1 Prevention) & Resilience Tests
    # --------------------------------------------------------------------------
    def test_workshops_query_efficiency_and_prefetch(self):
        """Full page executes at most 3 queries and HTMX partial executes at most 2 queries."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            # Full page view: 1 for distinct years, 1 for workshops, 1 for prefetched images
            with self.assertNumQueries(3):
                res_full = self.client.get(reverse('workshops'))
                _ = res_full.content

            # HTMX partial view: 1 for workshops, 1 for prefetched images (lazy years not evaluated)
            with self.assertNumQueries(2):
                res_htmx = self.client.get(reverse('workshops'), HTTP_HX_REQUEST='true')
                _ = res_htmx.content

    def test_invalid_year_parameter_resilience(self):
        """Malformed or non-numeric year query parameters are handled gracefully without 500."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            for malformed_val in ['invalid_text', '-2024', '1e5', 'null', '%20', 'all', 'todos']:
                response = self.client.get(f"{reverse('workshops')}?year={malformed_val}")
                # Must return 200 (falling back to all workshops) rather than uncaught 500
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'dashboard/workshops.html')


class InitialProjectViewTests(TestCase):
    """Verifies that initial_projects view renders cleanly with base.html."""
    def test_initial_projects_view_renders_successfully(self):
        response = self.client.get(reverse('initial_projects'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/initial_projects.html')
        self.assertTemplateUsed(response, 'base.html')



