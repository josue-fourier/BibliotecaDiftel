import os
import shutil
import tempfile
from datetime import datetime, timezone
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from dashboard.models import Workshop, WorkshopImage, CommunityMember, InitialProject


class TestNullBlankHandling(TestCase):
    """Stress test null and blank constraints across new models."""

    def test_workshop_guia_url_null_and_blank(self):
        # 1. Null is permitted
        w1 = Workshop.objects.create(
            title="Taller Null Guia",
            description="Desc",
            year=2024,
            guia_url=None
        )
        self.assertIsNone(w1.guia_url)
        w1.full_clean()  # Must not raise

        # 2. Blank string is permitted
        w2 = Workshop.objects.create(
            title="Taller Blank Guia",
            description="Desc",
            year=2024,
            guia_url=""
        )
        self.assertEqual(w2.guia_url, "")
        w2.full_clean()  # Must not raise

        # 3. Invalid URL format rejected on full_clean
        w3 = Workshop(
            title="Taller Invalid URL",
            description="Desc",
            year=2024,
            guia_url="not-a-valid-url"
        )
        with self.assertRaises(ValidationError) as ctx:
            w3.full_clean()
        self.assertIn('guia_url', ctx.exception.message_dict)

        # 4. Exceeding max_length=255 rejected on full_clean
        long_url = "https://example.org/" + ("a" * 250)
        w4 = Workshop(
            title="Taller Long URL",
            description="Desc",
            year=2024,
            guia_url=long_url
        )
        with self.assertRaises(ValidationError) as ctx:
            w4.full_clean()
        self.assertIn('guia_url', ctx.exception.message_dict)

    def test_community_member_blank_fields_permissiveness(self):
        # All optional fields set to empty strings or None (for profile_picture)
        member = CommunityMember.objects.create(
            name="Estudiante Mínimo",
            generation=2022,
            bio="Biografía mínima.",
            current_role="",
            linkedin_url="",
            github_url="",
            email="",
            profile_picture=None
        )
        member.full_clean()
        self.assertEqual(member.current_role, "")
        self.assertEqual(member.linkedin_url, "")
        self.assertEqual(member.github_url, "")
        self.assertEqual(member.email, "")
        self.assertFalse(bool(member.profile_picture))

    def test_community_member_null_handling_on_string_fields(self):
        # In Django CharFields/URLFields/EmailFields with blank=True and null=False (default),
        # None is in EMPTY_VALUES, so full_clean() treats None as empty and does NOT raise a ValidationError.
        # However, saving None directly into the DB violates the NOT NULL column constraint!
        from django.db import IntegrityError, transaction
        fields_to_test = ['current_role', 'linkedin_url', 'github_url', 'email']
        for field_name in fields_to_test:
            kwargs = {
                'name': 'Test Member',
                'generation': 2023,
                'bio': 'Bio',
                field_name: None
            }
            member = CommunityMember(**kwargs)
            # full_clean() passes because None in EMPTY_VALUES and blank=True
            member.full_clean()

            # But saving None violates database NOT NULL constraint!
            with transaction.atomic():
                with self.assertRaises(IntegrityError, msg=f"Field {field_name}=None must violate DB NOT NULL constraint"):
                    member.save()

    def test_community_member_invalid_format_rejection(self):
        # Invalid email
        m1 = CommunityMember(name="A", generation=2020, bio="B", email="notanemail")
        with self.assertRaises(ValidationError) as ctx:
            m1.full_clean()
        self.assertIn('email', ctx.exception.message_dict)

        # Invalid linkedin url
        m2 = CommunityMember(name="A", generation=2020, bio="B", linkedin_url="ht!tp://broken")
        with self.assertRaises(ValidationError) as ctx:
            m2.full_clean()
        self.assertIn('linkedin_url', ctx.exception.message_dict)

        # Invalid github url
        m3 = CommunityMember(name="A", generation=2020, bio="B", github_url="git@@github.com")
        with self.assertRaises(ValidationError) as ctx:
            m3.full_clean()
        self.assertIn('github_url', ctx.exception.message_dict)

    def test_community_member_profile_picture_empty_access(self):
        member = CommunityMember.objects.create(
            name="Sin Foto",
            generation=2021,
            bio="Bio sin imagen"
        )
        self.assertFalse(bool(member.profile_picture))
        self.assertFalse(member.profile_picture.name)
        with self.assertRaises(ValueError):
            # Accessing .url on empty ImageField raises ValueError
            _ = member.profile_picture.url


class TestLongStringsAndUnicode(TestCase):
    """Stress test boundary string lengths, emojis, accents, and massive text payloads."""

    def test_unicode_and_emojis_in_all_fields(self):
        title = "📡 Taller 5G & Óptica: USM Valparaíso 🚀 (Ñandú & Pingüino) 智利"
        desc = (
            "Laboratorio con tildes (á, é, í, ó, ú), diéresis (ü), símbolos matemáticos "
            "(λ=1550nm, Δf=50GHz, ∑, ∫, ≤, ≥), emojis (🤖💡💻), y kanji (光通信研究所)."
        )
        workshop = Workshop.objects.create(
            title=title,
            description=desc,
            year=2024,
            guia_url="https://wiki-diftel.josnic.cl/p/guía-óptica-2024"
        )
        self.assertEqual(workshop.title, title)
        self.assertEqual(str(workshop), f"{title} (2024)")

        # Unicode in CommunityMember
        name = "María-José Ñandú González-Müller 👩‍💻"
        role = "Líder de I+D en Telecomunicaciones Ópticas 🌐"
        member = CommunityMember.objects.create(
            name=name,
            generation=2020,
            bio=desc,
            current_role=role,
            email="maría.ñandú@alumnos.usm.cl"
        )
        self.assertEqual(member.name, name)
        self.assertEqual(str(member), f"{name} (2020)")

    def test_workshop_title_length_boundaries(self):
        # 200 chars: exact limit -> valid
        valid_title = "T" * 200
        w_valid = Workshop(title=valid_title, description="Desc", year=2024)
        w_valid.full_clean()

        # 201 chars: exceeds limit -> invalid on full_clean
        invalid_title = "T" * 201
        w_invalid = Workshop(title=invalid_title, description="Desc", year=2024)
        with self.assertRaises(ValidationError) as ctx:
            w_invalid.full_clean()
        self.assertIn('title', ctx.exception.message_dict)

    def test_community_member_name_and_role_length_boundaries(self):
        # Name: 200 valid, 201 invalid
        m_valid = CommunityMember(name="N" * 200, generation=2022, bio="Bio", current_role="R" * 200)
        m_valid.full_clean()

        m_invalid_name = CommunityMember(name="N" * 201, generation=2022, bio="Bio")
        with self.assertRaises(ValidationError) as ctx:
            m_invalid_name.full_clean()
        self.assertIn('name', ctx.exception.message_dict)

        m_invalid_role = CommunityMember(name="Valid Name", generation=2022, bio="Bio", current_role="R" * 201)
        with self.assertRaises(ValidationError) as ctx:
            m_invalid_role.full_clean()
        self.assertIn('current_role', ctx.exception.message_dict)

    def test_huge_payload_in_text_fields(self):
        # TextField should support arbitrary large strings (e.g. 50,000 characters)
        huge_text = "Diftel Telematics " * 3000  # ~54,000 characters
        workshop = Workshop.objects.create(
            title="Taller Big Payload",
            description=huge_text,
            year=2024
        )
        fetched_w = Workshop.objects.get(id=workshop.id)
        self.assertEqual(len(fetched_w.description), len(huge_text))

        member = CommunityMember.objects.create(
            name="Member Big Bio",
            generation=2021,
            bio=huge_text
        )
        fetched_m = CommunityMember.objects.get(id=member.id)
        self.assertEqual(len(fetched_m.bio), len(huge_text))

    def test_workshop_image_caption_length_boundary(self):
        workshop = Workshop.objects.create(title="W", description="D", year=2024)
        img_valid = WorkshopImage(workshop=workshop, order=1, caption="C" * 200)
        img_valid.full_clean(exclude=['image'])

        img_invalid = WorkshopImage(workshop=workshop, order=1, caption="C" * 201)
        with self.assertRaises(ValidationError) as ctx:
            img_invalid.full_clean(exclude=['image'])
        self.assertIn('caption', ctx.exception.message_dict)


class TestYearGenerationBoundaries(TestCase):
    """Stress test negative, zero, and extreme integer values in year and generation."""

    def test_initial_project_generation_has_validators(self):
        # InitialProject explicitly defines MinValueValidator(2000), MaxValueValidator(2100)
        p_invalid_neg = InitialProject(title="P", description="D", generation=1999, members="M")
        with self.assertRaises(ValidationError) as ctx:
            p_invalid_neg.full_clean()
        self.assertIn('generation', ctx.exception.message_dict)

    def test_workshop_year_boundary_empirical_behavior(self):
        # Workshop.year defines MinValueValidator(1990) and MaxValueValidator(2100).
        # It rejects negative years (-500), zero (0), and future years (99999) during full_clean().
        w_neg = Workshop(title="Taller BC", description="Desc", year=-500)
        with self.assertRaises(ValidationError) as ctx:
            w_neg.full_clean()
        self.assertIn('year', ctx.exception.message_dict)

        w_zero = Workshop(title="Taller Año Cero", description="Desc", year=0)
        with self.assertRaises(ValidationError) as ctx:
            w_zero.full_clean()
        self.assertIn('year', ctx.exception.message_dict)

        w_future = Workshop(title="Taller Año 99999", description="Desc", year=99999)
        with self.assertRaises(ValidationError) as ctx:
            w_future.full_clean()
        self.assertIn('year', ctx.exception.message_dict)

        # Valid boundaries (1990 and 2100) pass full_clean
        w_min = Workshop(title="Taller Min", description="Desc", year=1990)
        w_min.full_clean()
        w_min.save()
        self.assertEqual(w_min.year, 1990)

        w_max = Workshop(title="Taller Max", description="Desc", year=2100)
        w_max.full_clean()
        w_max.save()
        self.assertEqual(w_max.year, 2100)

    def test_community_member_generation_boundary_empirical_behavior(self):
        # CommunityMember.generation defines MinValueValidator(1990) and MaxValueValidator(2100).
        # It rejects negative generation (-1) and zero (0) during full_clean().
        m_neg = CommunityMember(name="Viajero del Tiempo", generation=-1, bio="Bio")
        with self.assertRaises(ValidationError) as ctx:
            m_neg.full_clean()
        self.assertIn('generation', ctx.exception.message_dict)

        m_zero = CommunityMember(name="Generación Cero", generation=0, bio="Bio")
        with self.assertRaises(ValidationError) as ctx:
            m_zero.full_clean()
        self.assertIn('generation', ctx.exception.message_dict)

        # Valid boundaries (1990 and 2100) pass full_clean
        m_min = CommunityMember(name="Primer Egreso", generation=1990, bio="Bio")
        m_min.full_clean()
        m_min.save()
        self.assertEqual(m_min.generation, 1990)

        m_max = CommunityMember(name="Futuro Egreso", generation=2100, bio="Bio")
        m_max.full_clean()
        m_max.save()
        self.assertEqual(m_max.generation, 2100)


class TestCascadeDeletionAndFileRetention(TestCase):
    """Stress test cascade deletion and verify file retention on disk."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_dummy_image(self, filename="img.png"):
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00'
            b'\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf'
            b'\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return SimpleUploadedFile(filename, png_data, content_type="image/png")

    def test_cascade_deletion_removes_all_images(self):
        with override_settings(MEDIA_ROOT=self.temp_dir):
            workshop = Workshop.objects.create(title="Workshop Cascade", description="Desc", year=2024)
            images = [
                WorkshopImage.objects.create(
                    workshop=workshop,
                    image=self._create_dummy_image(f"foto_{i}.png"),
                    order=i,
                    caption=f"Foto {i}"
                )
                for i in range(5)
            ]
            self.assertEqual(WorkshopImage.objects.filter(workshop=workshop).count(), 5)
            w_id = workshop.id
            workshop.delete()

            # Verify all related images removed from DB
            self.assertEqual(WorkshopImage.objects.filter(workshop_id=w_id).count(), 0)
            self.assertEqual(Workshop.objects.filter(id=w_id).count(), 0)

    def test_file_retention_on_cascade_deletion(self):
        # EMPIRICAL PROBE: Standard Django CASCADE deletion removes DB rows but does NOT
        # delete physical image files from disk unless a post_delete signal or django-cleanup is used.
        with override_settings(MEDIA_ROOT=self.temp_dir):
            workshop = Workshop.objects.create(title="Workshop Orphan Test", description="Desc", year=2024)
            img = WorkshopImage.objects.create(
                workshop=workshop,
                image=self._create_dummy_image("orphan_test.png"),
                order=0
            )
            file_path = img.image.path
            self.assertTrue(os.path.exists(file_path))

            workshop.delete()
            self.assertEqual(WorkshopImage.objects.count(), 0)

            # Check whether file remains on disk
            file_still_exists = os.path.exists(file_path)
            # Standard Django leaves files on disk
            self.assertTrue(file_still_exists, "Django default on_delete=CASCADE does not delete filesystem files.")


class TestOrderingDeterminism(TestCase):
    """Stress test ordering determinism and tiebreaker behavior."""

    def test_workshop_ordering_multi_year_and_timestamp(self):
        w2022 = Workshop.objects.create(title="W 2022", description="D", year=2022)
        w2024_a = Workshop.objects.create(title="W 2024 Early", description="D", year=2024)
        w2024_b = Workshop.objects.create(title="W 2024 Late", description="D", year=2024)
        w2025 = Workshop.objects.create(title="W 2025", description="D", year=2025)

        results = list(Workshop.objects.all())
        # Ordering is ['-year', '-created_at']
        # w2025 first, then w2024_b (created later), w2024_a (created earlier), w2022 last
        self.assertEqual(results[0], w2025)
        self.assertEqual(results[1], w2024_b)
        self.assertEqual(results[2], w2024_a)
        self.assertEqual(results[3], w2022)

    def test_community_member_ordering_generation_and_name(self):
        m2020_c = CommunityMember.objects.create(name="Carlos", generation=2020, bio="B")
        m2020_a = CommunityMember.objects.create(name="Andrés", generation=2020, bio="B")
        m2020_b = CommunityMember.objects.create(name="Beatriz", generation=2020, bio="B")
        m2024 = CommunityMember.objects.create(name="Zoe", generation=2024, bio="B")
        m2019 = CommunityMember.objects.create(name="Ana", generation=2019, bio="B")

        results = list(CommunityMember.objects.all())
        # Ordering is ['-generation', 'name']
        # 2024 first, then 2020 (Andrés, Beatriz, Carlos), then 2019 (Ana)
        expected = [m2024, m2020_a, m2020_b, m2020_c, m2019]
        self.assertEqual(results, expected)

    def test_workshop_image_ordering_order_and_id(self):
        workshop = Workshop.objects.create(title="W Images", description="D", year=2024)
        # Images with order=1, 0, 1, 2
        img_order1_first = WorkshopImage.objects.create(workshop=workshop, order=1, caption="1st")
        img_order0 = WorkshopImage.objects.create(workshop=workshop, order=0, caption="0th")
        img_order1_second = WorkshopImage.objects.create(workshop=workshop, order=1, caption="2nd")
        img_order2 = WorkshopImage.objects.create(workshop=workshop, order=2, caption="3rd")

        results = list(workshop.images.all())
        # Ordering is ['order', 'id']
        expected = [img_order0, img_order1_first, img_order1_second, img_order2]
        self.assertEqual(results, expected)
        self.assertEqual(workshop.primary_image, img_order0)


class TestEventTypeChoicesValidation(TestCase):
    """Stress test Workshop event_type choices constraint."""

    def test_valid_event_type_choices(self):
        for choice in ['taller', 'charla', 'conferencia', 'hackathon', 'otro']:
            w = Workshop(title=f"Event {choice}", description="D", year=2024, event_type=choice)
            w.full_clean()

    def test_invalid_event_type_choice_raises_validation_error(self):
        w = Workshop(title="Event Invalid", description="D", year=2024, event_type="hackfest")
        with self.assertRaises(ValidationError) as ctx:
            w.full_clean()
        self.assertIn('event_type', ctx.exception.message_dict)

    def test_orm_create_bypasses_model_clean(self):
        # EMPIRICAL PROBE: Calling .create() directly does NOT call full_clean(),
        # so invalid event_type is stored in DB unless checked at form/admin level.
        w = Workshop.objects.create(title="Bypassed Clean", description="D", year=2024, event_type="invalid_type")
        self.assertEqual(w.event_type, "invalid_type")
        # However, calling full_clean afterwards identifies the violation
        with self.assertRaises(ValidationError):
            w.full_clean()


class TestSecurityAndQueryTraps(TestCase):
    """Stress test security boundaries, URL schemes, query traps, and prefetch efficiency."""

    def test_url_schemes_and_relative_paths(self):
        # 1. Relative paths are rejected by URLField
        w_relative = Workshop(title="W", description="D", year=2024, guia_url="/p/guia-1")
        with self.assertRaises(ValidationError) as ctx:
            w_relative.full_clean()
        self.assertIn('guia_url', ctx.exception.message_dict)

        # 2. Dangerous URI schemes like javascript: are rejected
        w_js = Workshop(title="W", description="D", year=2024, guia_url="javascript:alert(1)")
        with self.assertRaises(ValidationError) as ctx:
            w_js.full_clean()
        self.assertIn('guia_url', ctx.exception.message_dict)

        # 3. Data URIs rejected
        w_data = Workshop(title="W", description="D", year=2024, guia_url="data:text/html,<script>alert(1)</script>")
        with self.assertRaises(ValidationError) as ctx:
            w_data.full_clean()
        self.assertIn('guia_url', ctx.exception.message_dict)

    def test_integer_overflow_empirical_behavior(self):
        # Workshop.year defines MaxValueValidator(2100).
        # Full_clean() prevents integer overflow (such as 2147483648) by raising ValidationError.
        w_overflow = Workshop(title="Overflow Int", description="D", year=2147483648)
        with self.assertRaises(ValidationError) as ctx:
            w_overflow.full_clean()
        self.assertIn('year', ctx.exception.message_dict)

    def test_guia_url_dual_representation_query_trap(self):
        # Null vs blank creates two distinct states in database:
        w_null = Workshop.objects.create(title="Null Guia", description="D", year=2024, guia_url=None)
        w_blank = Workshop.objects.create(title="Blank Guia", description="D", year=2024, guia_url="")
        w_has_url = Workshop.objects.create(
            title="Has Guia", description="D", year=2024, guia_url="https://wiki-diftel.josnic.cl/p/guia"
        )

        # Trap 1: filter(guia_url__isnull=False) returns BOTH w_blank and w_has_url!
        not_null_count = Workshop.objects.filter(guia_url__isnull=False).count()
        self.assertEqual(not_null_count, 2)  # Matches w_blank and w_has_url!

        # Trap 2: exclude(guia_url="") returns BOTH w_null and w_has_url!
        not_blank_count = Workshop.objects.exclude(guia_url="").count()
        self.assertEqual(not_blank_count, 2)  # Matches w_null and w_has_url!

        # Trap 3: exclude(guia_url__in=[None, ""]) fails in SQL due to NULL IN (...) evaluating to UNKNOWN!
        # Thus w_null is NOT excluded!
        trap_query = list(Workshop.objects.exclude(guia_url__in=[None, ""]))
        self.assertIn(w_null, trap_query, "SQL NULL three-valued logic causes w_null to survive exclude(guia_url__in=[None, ''])!")

        # Correct query to find items with an actual guide requires chaining or Q objects:
        correct_query = list(Workshop.objects.exclude(guia_url__isnull=True).exclude(guia_url=""))
        self.assertEqual(correct_query, [w_has_url])

    def test_primary_image_prefetch_behavior(self):
        # Setup temporary media
        temp_dir = tempfile.mkdtemp()
        try:
            with override_settings(MEDIA_ROOT=temp_dir):
                workshop = Workshop.objects.create(title="W Prefetch", description="D", year=2024)
                png_data = (
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                    b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00'
                    b'\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf'
                    b'\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
                )
                img = SimpleUploadedFile("dummy.png", png_data, content_type="image/png")
                WorkshopImage.objects.create(workshop=workshop, image=img, order=0)

                # 1. Non-prefetched: accessing primary_image executes 1 SQL query
                w_non_prefetched = Workshop.objects.get(id=workshop.id)
                with self.assertNumQueries(1):
                    self.assertIsNotNone(w_non_prefetched.primary_image)

                # 2. Prefetched: accessing primary_image uses result_cache, executing 0 SQL queries
                w_prefetched = Workshop.objects.prefetch_related('images').get(id=workshop.id)
                with self.assertNumQueries(0):
                    self.assertIsNotNone(w_prefetched.primary_image)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

