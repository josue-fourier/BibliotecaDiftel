import os
import shutil
import tempfile
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse, resolve
from django.core.files.uploadedfile import SimpleUploadedFile
from dashboard.models import CommunityMember
from dashboard import views


class BaseCommunityTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.rf = RequestFactory()
        # Create standard test members
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            self.member_with_pic = CommunityMember.objects.create(
                name="Valentina Concha",
                generation=2019,
                bio="Arquitecta de Redes y Cloud Computing.",
                current_role="Cloud Engineer en GlobalTech",
                linkedin_url="https://linkedin.com/in/valentinaconcha",
                github_url="https://github.com/vconcha",
                email="valentina.concha@alumnos.usm.cl",
                profile_picture=self._create_dummy_image("valentina.png")
            )
            self.member_no_pic = CommunityMember.objects.create(
                name="Sebastián González",
                generation=2021,
                bio="Especialista en sistemas distribuidos y seguridad.",
                current_role="DevOps Engineer",
                linkedin_url="",
                github_url="https://github.com/sgonzalez",
                email="sebastian.gonzalez@usm.cl",
                profile_picture=None
            )
            self.member_minimal = CommunityMember.objects.create(
                name="Camila Tapia",
                generation=2023,
                bio="Investigadora en IoT y redes 5G.",
                current_role="",
                linkedin_url="",
                github_url="",
                email="",
                profile_picture=None
            )

    def _create_dummy_image(self, filename="dummy.png"):
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00'
            b'\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf'
            b'\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return SimpleUploadedFile(filename, png_data, content_type="image/png")


class TestHTMXPartialAndHeaderContracts(BaseCommunityTestCase):
    """
    Stress-tests HTMX partial requests with diverse header combinations,
    query parameters, and verifies strict shell vs partial invariants.
    """

    def test_standard_get_renders_full_shell(self):
        """Standard GET without HTMX headers must render full document shell."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('community'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'dashboard/community.html')
            self.assertTemplateUsed(response, 'base.html')
            self.assertTemplateUsed(response, 'dashboard/partials/community_list.html')

            # Verify DOCTYPE, navbar, and footer are present
            self.assertContains(response, '<!DOCTYPE html>')
            self.assertContains(response, '<html lang="es"')
            self.assertContains(response, '<nav class="navbar')
            self.assertContains(response, 'Biblioteca Diftel Admin')
            self.assertContains(response, '<footer class="footer')
            self.assertContains(response, 'id="community-search-input"')
            self.assertContains(response, 'id="community-container"')

    def test_htmx_header_renders_only_partial_without_shell(self):
        """GET with HX-Request: true must render ONLY the partial without DOCTYPE/navbar/footer."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(reverse('community'), HTTP_HX_REQUEST='true')
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'dashboard/partials/community_list.html')
            self.assertTemplateNotUsed(response, 'base.html')
            self.assertTemplateNotUsed(response, 'dashboard/community.html')

            # Negative assertions: verify complete omission of shell
            self.assertNotContains(response, '<!DOCTYPE')
            self.assertNotContains(response, '<html')
            self.assertNotContains(response, '<head>')
            self.assertNotContains(response, '<nav')
            self.assertNotContains(response, 'navbar')
            self.assertNotContains(response, '<footer')
            self.assertNotContains(response, 'footer-center')
            self.assertNotContains(response, 'id="community-search-input"')
            self.assertNotContains(response, 'id="community-container"')
            self.assertNotContains(response, 'Biblioteca Diftel Admin')
            self.assertNotContains(response, 'htmx:configRequest')

            # Positive assertion: partial content is rendered
            self.assertContains(response, 'Valentina Concha')
            self.assertContains(response, 'Sebastián González')

    def test_htmx_header_false_or_malformed_renders_full_shell(self):
        """When HX-Request is false, 0, or malformed, view falls back to full shell."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            for bad_header in ['false', 'False', '0', 'null', 'no', '']:
                response = self.client.get(reverse('community'), HTTP_HX_REQUEST=bad_header)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'base.html')
                self.assertTemplateUsed(response, 'dashboard/community.html')
                self.assertContains(response, '<!DOCTYPE html>')
                self.assertContains(response, '<nav class="navbar')
                self.assertContains(response, '<footer class="footer')

    def test_query_param_partial_variations(self):
        """?partial=1, ?partial=true, ?partial=True render partial without shell; ?partial=0 renders shell."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            # True variations
            for p_val in ['1', 'true', 'True']:
                response = self.client.get(f"{reverse('community')}?partial={p_val}")
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'dashboard/partials/community_list.html')
                self.assertTemplateNotUsed(response, 'base.html')
                self.assertNotContains(response, '<!DOCTYPE')
                self.assertNotContains(response, '<nav')
                self.assertNotContains(response, '<footer')

            # False variations
            for p_val in ['0', 'false', 'False', 'no', 'random']:
                response = self.client.get(f"{reverse('community')}?partial={p_val}")
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'base.html')
                self.assertContains(response, '<!DOCTYPE html>')
                self.assertContains(response, '<nav class="navbar')

    def test_direct_partial_endpoints_never_leak_shell(self):
        """
        Direct partial endpoints (/comunidad/partial/, /comunidad/search/,
        /comunidad/partial/generacion/<gen>/) must never leak base shell under any client condition.
        """
        endpoints = [
            reverse('community_list'),
            reverse('community_search'),
            reverse('community_list_by_generation', kwargs={'generation': 2021}),
        ]
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            for ep in endpoints:
                # 1. Standard browser request (no HX header)
                res1 = self.client.get(ep)
                self.assertEqual(res1.status_code, 200)
                self.assertTemplateUsed(res1, 'dashboard/partials/community_list.html')
                self.assertTemplateNotUsed(res1, 'base.html')
                self.assertNotContains(res1, '<!DOCTYPE')
                self.assertNotContains(res1, '<nav')
                self.assertNotContains(res1, '<footer')

                # 2. Explicit non-HTMX header (HX-Request: false)
                res2 = self.client.get(ep, HTTP_HX_REQUEST='false')
                self.assertEqual(res2.status_code, 200)
                self.assertTemplateNotUsed(res2, 'base.html')
                self.assertNotContains(res2, '<!DOCTYPE')

    def test_request_htmx_middleware_attribute_handling(self):
        """View accurately honors request.htmx boolean when set by django-htmx middleware."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            # Simulated middleware setting request.htmx = True
            req_htmx = self.rf.get('/comunidad/')
            req_htmx.htmx = True
            resp_htmx = views.community_view(req_htmx)
            content_htmx = resp_htmx.content.decode('utf-8')
            self.assertNotIn('<!DOCTYPE', content_htmx)
            self.assertNotIn('<nav class="navbar', content_htmx)
            self.assertIn('Valentina Concha', content_htmx)

            # Simulated middleware setting request.htmx = False
            req_full = self.rf.get('/comunidad/')
            req_full.htmx = False
            resp_full = views.community_view(req_full)
            content_full = resp_full.content.decode('utf-8')
            self.assertIn('<!DOCTYPE html>', content_full)
            self.assertIn('<nav class="navbar', content_full)


class TestProfilePictureResolutionAndFallbacks(BaseCommunityTestCase):
    """
    Stress-tests profile picture resolution, file missing from storage,
    ORM image deletion, DaisyUI avatar placeholders, and unicode/accents.
    """

    def test_valid_profile_picture_rendering(self):
        """Member with valid profile_picture renders <img> tag with proper media path and alt text."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(f"{reverse('community')}?q=Valentina")
            self.assertEqual(response.status_code, 200)
            url = self.member_with_pic.profile_picture.url
            self.assertTrue(url.startswith('/media/community/profile_pics/'))
            self.assertContains(response, f'src="{url}"')
            self.assertContains(response, f'alt="Fotografía de {self.member_with_pic.name}"')
            self.assertNotContains(response, 'avatar placeholder')

    def test_no_profile_picture_renders_placeholder_with_initial(self):
        """Member without profile_picture renders DaisyUI placeholder with capitalized initial."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            response = self.client.get(f"{reverse('community')}?q=Sebasti%C3%A1n")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'avatar placeholder')
            self.assertContains(response, '<span>S</span>')
            self.assertNotContains(response, f'alt="Fotografía de {self.member_no_pic.name}"')

    def test_profile_picture_file_deleted_from_disk_no_server_crash(self):
        """If image file is deleted from disk, server still renders 200 without throwing 500 error."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            file_path = self.member_with_pic.profile_picture.path
            self.assertTrue(os.path.exists(file_path))
            os.remove(file_path)
            self.assertFalse(os.path.exists(file_path))

            # View should still render gracefully without FileNotFoundError
            response = self.client.get(f"{reverse('community')}?q=Valentina")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Valentina Concha')
            self.assertContains(response, 'src="/media/community/profile_pics/')

    def test_profile_picture_cleared_via_orm_delete_immediately_falls_back(self):
        """When member.profile_picture is deleted via ORM, template immediately falls back to placeholder."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            # Create a dedicated member with picture
            m = CommunityMember.objects.create(
                name="Diego Riquelme",
                generation=2022,
                bio="Ingeniero en Telecomunicaciones.",
                profile_picture=self._create_dummy_image("diego.png")
            )
            res_before = self.client.get(f"{reverse('community')}?q=Diego")
            self.assertContains(res_before, 'src="/media/community/profile_pics/')
            self.assertNotContains(res_before, '<span>D</span>')

            # Delete the picture via ORM
            m.profile_picture.delete(save=True)
            m.refresh_from_db()
            self.assertFalse(bool(m.profile_picture))

            # Request again
            res_after = self.client.get(f"{reverse('community')}?q=Diego")
            self.assertEqual(res_after.status_code, 200)
            self.assertNotContains(res_after, 'src="/media/community/profile_pics/')
            self.assertContains(res_after, 'avatar placeholder')
            self.assertContains(res_after, '<span>D</span>')

    def test_placeholder_initial_with_various_names(self):
        """Avatar placeholder initial handles accented chars, lowercase, emojis, and single chars."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            # 1. Lowercase name
            CommunityMember.objects.create(name="ignacio rojas", generation=2020, bio="Bio")
            res_lower = self.client.get(f"{reverse('community')}?q=ignacio")
            self.assertContains(res_lower, '<span>I</span>')

            # 2. Accented initial
            CommunityMember.objects.create(name="Álvaro Morales", generation=2020, bio="Bio")
            res_accent = self.client.get(f"{reverse('community')}?q=%C3%81lvaro")
            self.assertContains(res_accent, '<span>Á</span>')

            # 3. Umlaut initial
            CommunityMember.objects.create(name="Ömer Yilmaz", generation=2020, bio="Bio")
            res_umlaut = self.client.get(f"{reverse('community')}?q=%C3%96mer")
            self.assertContains(res_umlaut, '<span>Ö</span>')

            # 4. Single character name
            CommunityMember.objects.create(name="Z", generation=2020, bio="Bio")
            res_single = self.client.get(f"{reverse('community')}?q=Z")
            self.assertContains(res_single, '<span>Z</span>')


class TestReverseUrlsAndKwargs(TestCase):
    """
    Verifies all URL patterns, names, reverse resolutions, kwargs, and HTTP 404 routing.
    """

    def test_reverse_urls_match_expected_paths(self):
        """Verify URL reversal matches the exact required routes."""
        self.assertEqual(reverse('community'), '/comunidad/')
        self.assertEqual(reverse('community_by_generation', kwargs={'generation': 2024}), '/comunidad/generacion/2024/')
        self.assertEqual(reverse('community_search'), '/comunidad/search/')
        self.assertEqual(reverse('community_list'), '/comunidad/partial/')
        self.assertEqual(reverse('community_list_by_generation', kwargs={'generation': 2024}), '/comunidad/partial/generacion/2024/')

    def test_url_resolvers_point_to_correct_views(self):
        """Verify that resolved URL paths bind to the appropriate view callables."""
        self.assertEqual(resolve('/comunidad/').func, views.community_view)
        self.assertEqual(resolve('/comunidad/generacion/2024/').func, views.community_view)
        self.assertEqual(resolve('/comunidad/search/').func, views.community_list_view)
        self.assertEqual(resolve('/comunidad/partial/').func, views.community_list_view)
        self.assertEqual(resolve('/comunidad/partial/generacion/2024/').func, views.community_list_view)

    def test_non_integer_generation_routes_raise_404(self):
        """Path converter <int:generation> strictly rejects non-digits and negative numbers."""
        invalid_paths = [
            '/comunidad/generacion/abc/',
            '/comunidad/generacion/-2024/',
            '/comunidad/generacion/2024.5/',
            '/comunidad/partial/generacion/abc/',
            '/comunidad/partial/generacion/-2024/',
        ]
        for path in invalid_paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)


class TestAdversarialInputsAndPerformance(BaseCommunityTestCase):
    """
    Stress-tests search queries, XSS autoescaping, SQL injection attempts,
    generation fuzzer, and database query performance (N+1 avoidance).
    """

    def test_xss_autoescaping_in_rendered_templates(self):
        """XSS payloads in model fields and search parameters must be strictly HTML-escaped."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            xss_payload_name = "<script>alert('xss-name')</script>"
            xss_payload_role = "<svg onload=alert('xss-role')>"
            xss_payload_bio = "<img src=x onerror=alert('xss-bio')>"

            CommunityMember.objects.create(
                name=xss_payload_name,
                generation=2024,
                bio=xss_payload_bio,
                current_role=xss_payload_role
            )

            # Request full page
            res = self.client.get(f"{reverse('community')}?q=<script>")
            self.assertEqual(res.status_code, 200)

            # Script tags must be escaped
            self.assertNotContains(res, "<script>alert('xss-name')</script>")
            self.assertNotContains(res, "<svg onload=alert('xss-role')>")
            self.assertNotContains(res, "<img src=x onerror=alert('xss-bio')>")
            self.assertContains(res, "&lt;script&gt;alert(&#x27;xss-name&#x27;)&lt;/script&gt;")

    def test_sql_injection_probes_in_search_and_generation(self):
        """Common SQL injection probes must execute without syntax errors or unintended data leaks."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            sqli_probes = [
                "' OR '1'='1' --",
                '" OR ""="',
                "'; DROP TABLE dashboard_communitymember; --",
                "1' UNION SELECT 1,2,3,4,5,6,7,8,9,10 --",
                "\\x00' OR 1=1",
            ]
            for probe in sqli_probes:
                res_search = self.client.get(f"{reverse('community')}?q={probe}")
                self.assertEqual(res_search.status_code, 200)
                # Ensure no members returned unless probe literally matches
                self.assertEqual(len(list(res_search.context['members'])), 0)

                res_gen = self.client.get(f"{reverse('community')}?generation={probe}")
                self.assertEqual(res_gen.status_code, 200)

    def test_generation_fuzzer_robustness(self):
        """Wild values for ?generation= parameter fall back safely without 500 errors."""
        # Non-numeric, negative, and zero values fall back to None
        fallback_values = [
            "-1",
            "0",
            "null",
            "None",
            "NaN",
            "undefined",
            "all",
            "todos",
            "todas",
            "   ",
            "%00",
            "true",
            "false",
        ]
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            for val in fallback_values:
                res = self.client.get(f"{reverse('community')}?generation={val}")
                self.assertEqual(res.status_code, 200)
                self.assertIsNone(res.context['selected_generation'])

            # Large positive numbers are parsed safely as int, returning empty results without crash
            large_int = "9999999999999999999999999999999999999999999999999999999999999"
            res_large = self.client.get(f"{reverse('community')}?generation={large_int}")
            self.assertEqual(res_large.status_code, 200)
            self.assertEqual(len(list(res_large.context['members'])), 0)

    def test_query_count_performance_no_n_plus_one(self):
        """
        Rendering many members must execute a bounded, constant number of queries O(1),
        preventing N+1 query regression.
        """
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            # Create 30 members
            new_members = [
                CommunityMember(
                    name=f"Member {i}",
                    generation=2015 + (i % 10),
                    bio=f"Bio for member {i}",
                    current_role=f"Role {i}" if i % 2 == 0 else ""
                )
                for i in range(30)
            ]
            CommunityMember.objects.bulk_create(new_members)

            # Full page view executes exactly 3 queries:
            # 1. CommunityMember.objects.count()
            # 2. CommunityMember.objects.all() (evaluated by member loop)
            # 3. CommunityMember.objects.values_list('generation', flat=True)... (evaluated by generation loop)
            with self.assertNumQueries(3):
                res_full = self.client.get(reverse('community'))
                self.assertEqual(res_full.status_code, 200)

            # Partial view executes exactly 2 queries:
            # 1. CommunityMember.objects.count()
            # 2. CommunityMember.objects.all() (evaluated by member loop)
            # ('generations' is lazy and not evaluated in partial template)
            with self.assertNumQueries(2):
                res_partial = self.client.get(reverse('community_list'))
                self.assertEqual(res_partial.status_code, 200)


class TestTemplateRenderingDetailsAndSecurity(BaseCommunityTestCase):
    """
    Detailed stress-tests on template escaping, social link security attributes (tabnabbing),
    whitespace preservation in bio, and empty-state partial shell omissions.
    """

    def test_social_links_security_attributes(self):
        """External links (LinkedIn, GitHub) must have rel='noopener noreferrer' and target='_blank'."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            res = self.client.get(f"{reverse('community')}?q=Valentina", HTTP_HX_REQUEST='true')
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, 'target="_blank"')
            self.assertContains(res, 'rel="noopener noreferrer"')
            self.assertContains(res, 'href="mailto:valentina.concha@alumnos.usm.cl"')

    def test_member_with_no_social_links_omits_actions_bar(self):
        """When member has no linkedin, github, or email, the card-actions bar is completely omitted."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            res = self.client.get(f"{reverse('community')}?q=Camila", HTTP_HX_REQUEST='true')
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, 'Camila Tapia')
            # The member card must not render the contact actions footer
            self.assertNotContains(res, 'card-actions justify-end')
            self.assertNotContains(res, 'Contacto</span>')

    def test_empty_state_htmx_partial_never_leaks_shell(self):
        """Empty state partial triggered by unmatched search must not include base document shell."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            res = self.client.get(f"{reverse('community')}?q=GhostNonExistent", HTTP_HX_REQUEST='true')
            self.assertEqual(res.status_code, 200)
            self.assertTemplateUsed(res, 'dashboard/partials/community_list.html')
            self.assertTemplateNotUsed(res, 'base.html')
            self.assertNotContains(res, '<!DOCTYPE')
            self.assertNotContains(res, '<nav')
            self.assertNotContains(res, '<footer')
            self.assertContains(res, 'No se encontraron miembros que coincidan con')
            self.assertContains(res, 'GhostNonExistent')
            self.assertContains(res, 'Restablecer filtros y ver todos')

    def test_multiline_bio_rendered_with_pre_line(self):
        """Multiline bio preserves line breaks in whitespace-pre-line paragraph."""
        with override_settings(MEDIA_ROOT=self.temp_dir, MEDIA_URL='/media/'):
            multiline_bio = "Línea 1: Especialista.\nLínea 2: Investigador.\nLínea 3: Docente."
            CommunityMember.objects.create(
                name="Profesor Diftel",
                generation=2015,
                bio=multiline_bio
            )
            res = self.client.get(f"{reverse('community')}?q=Profesor", HTTP_HX_REQUEST='true')
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, "Línea 1: Especialista.")
            self.assertContains(res, "Línea 2: Investigador.")
            self.assertContains(res, "Línea 3: Docente.")
