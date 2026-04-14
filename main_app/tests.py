from datetime import date, datetime, time as time_cls, timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from rest_framework import serializers as drf_serializers
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .admin import create_workout_from_template
from .models import (
    Exercise,
    MuscleGroup,
    Profile,
    Workout,
    WorkoutItem,
    WorkoutPlan,
    WorkoutTemplate,
    WorkoutTemplateItem,
    WorkoutTemplatePlan,
)
from .serializers import WorkoutPlanSerializer
from .services.workout_scheduling import (
    build_plan_slots_for_date_range,
    parse_inclusive_end_date,
)


class BuildPlanSlotsForDateRangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("slotuser", password="testpass123")
        self.t_push = WorkoutTemplate.objects.create(
            user=self.user, title="Push", duration=60
        )
        self.t_rest = WorkoutTemplate.objects.create(
            user=self.user,
            title="Rest",
            duration=1,
            is_rest_placeholder=True,
        )
        self.plan = WorkoutPlan.objects.create(user=self.user, title="PPL")
        WorkoutTemplatePlan.objects.create(
            plan=self.plan,
            template=self.t_push,
            order=0,
            time=time_cls(10, 0),
        )
        WorkoutTemplatePlan.objects.create(
            plan=self.plan,
            template=self.t_rest,
            order=1,
            time=time_cls(12, 0),
        )
        WorkoutTemplatePlan.objects.create(
            plan=self.plan,
            template=self.t_push,
            order=2,
            time=time_cls(14, 0),
        )
        self.links = list(
            WorkoutTemplatePlan.objects.filter(plan=self.plan)
            .select_related("template")
            .order_by("order", "id")
        )

    def test_rest_consumes_day_three_days_two_workouts(self):
        start_dt = timezone.make_aware(datetime(2026, 6, 1, 8, 0, 0))
        end_date = date(2026, 6, 3)
        slots = build_plan_slots_for_date_range(
            start_dt=start_dt,
            end_date=end_date,
            ordered_links=self.links,
        )
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0][2].template_id, self.t_push.id)
        self.assertEqual(slots[1][2].template_id, self.t_push.id)
        self.assertEqual(
            timezone.localtime(slots[0][0]).date(), date(2026, 6, 1)
        )
        self.assertEqual(
            timezone.localtime(slots[1][0]).date(), date(2026, 6, 3)
        )

    def test_inclusive_end_empty_when_start_after_end(self):
        start_dt = timezone.make_aware(datetime(2026, 6, 10, 8, 0, 0))
        slots = build_plan_slots_for_date_range(
            start_dt=start_dt,
            end_date=date(2026, 6, 1),
            ordered_links=self.links,
        )
        self.assertEqual(slots, [])


class ParseInclusiveEndDateTests(TestCase):
    def test_iso_date_string(self):
        self.assertEqual(
            parse_inclusive_end_date("2026-03-22"), date(2026, 3, 22)
        )

    def test_datetime_string_uses_local_date(self):
        d = parse_inclusive_end_date("2026-03-22T15:30:00")
        self.assertEqual(d, date(2026, 3, 22))


class RestTemplateScheduleAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("scheduser", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.rest_tpl = WorkoutTemplate.objects.create(
            user=self.user,
            title="Rest block",
            duration=1,
            is_rest_placeholder=True,
        )

    def test_schedule_rejects_rest_placeholder(self):
        url = f"/api/workout-templates/{self.rest_tpl.id}/schedule/"
        start = timezone.now().replace(microsecond=0) + timedelta(days=1)
        resp = self.client.post(
            url,
            {"start_dt": start.isoformat()},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class PlanGenerateAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("genuser", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tpl = WorkoutTemplate.objects.create(
            user=self.user, title="Lift", duration=45
        )
        self.plan = WorkoutPlan.objects.create(user=self.user, title="Week")
        WorkoutTemplatePlan.objects.create(
            plan=self.plan,
            template=self.tpl,
            order=0,
            time=time_cls(9, 0),
        )

    def test_generate_does_not_delete_existing_future_plan_workouts(self):
        far = timezone.now() + timedelta(days=365)
        existing = Workout.objects.create(
            user=self.user,
            plan=self.plan,
            template=self.tpl,
            title="Existing",
            start_dt=far,
            end_dt=far + timedelta(minutes=45),
        )

        start = timezone.make_aware(datetime(2030, 1, 1, 9, 0, 0))
        end_d = date(2030, 1, 2)
        url = f"/api/workout-plans/{self.plan.id}/generate/"
        resp = self.client.post(
            url,
            {
                "start_dt": start.isoformat(),
                "end_dt": end_d.isoformat(),
                "tz": "UTC",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Workout.objects.filter(pk=existing.pk).exists(),
            "Existing future plan workout should not be deleted",
        )
        ids = resp.data.get("workout_ids") or []
        self.assertEqual(len(ids), 2)


class WorkoutPlanTemplateLinksAuthzTests(TestCase):
    """Regression: update() must enforce the same template access rules as create()."""

    def setUp(self):
        self.user_a = User.objects.create_user("alice", password="testpass123")
        self.user_b = User.objects.create_user("bob", password="testpass123")
        self.client = APIClient()
        Exercise.objects.create(name="Bench Press", exercise_type="strength")
        self.tpl_own = WorkoutTemplate.objects.create(
            user=self.user_a, title="Mine", duration=60
        )
        self.tpl_private_b = WorkoutTemplate.objects.create(
            user=self.user_b, title="Secret", duration=60, is_public=False
        )
        self.tpl_public = WorkoutTemplate.objects.create(
            user=self.user_b, title="Shared", duration=60, is_public=True
        )
        self.plan = WorkoutPlan.objects.create(user=self.user_a, title="My Plan")

    def _link_payload(self, template):
        return {
            "template_links": [
                {
                    "template": template.id,
                    "order": 0,
                    "time": "09:30:00",
                }
            ]
        }

    def test_patch_rejects_other_users_private_template(self):
        self.client.force_authenticate(user=self.user_a)
        url = f"/api/workout-plans/{self.plan.id}/"
        resp = self.client.patch(
            url, self._link_payload(self.tpl_private_b), format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_allows_own_template(self):
        self.client.force_authenticate(user=self.user_a)
        url = f"/api/workout-plans/{self.plan.id}/"
        resp = self.client.patch(
            url, self._link_payload(self.tpl_own), format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data.get("template_links", [])), 1)

    def test_patch_allows_public_template(self):
        self.client.force_authenticate(user=self.user_a)
        url = f"/api/workout-plans/{self.plan.id}/"
        resp = self.client.patch(
            url, self._link_payload(self.tpl_public), format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data.get("template_links", [])), 1)


class CreateWorkoutFromTemplateAdminActionTests(TestCase):
    """Admin action maps WorkoutTemplateItem fields to WorkoutItem with correct names."""

    def setUp(self):
        self.user = User.objects.create_user("stafftpl", password="testpass123")
        self.ex = Exercise.objects.create(name="Squat", exercise_type="strength")
        self.template = WorkoutTemplate.objects.create(
            user=self.user, title="Leg day", duration=90
        )
        WorkoutTemplateItem.objects.create(
            template=self.template,
            exercise=self.ex,
            order=2,
            sets=3,
            reps=5,
            duration=120,
            distance=400,
            distance_unit="km",
            rpe=8,
            notes="keep chest up",
        )

    def test_action_copies_prescription_fields_to_workout_items(self):
        factory = RequestFactory()
        request = factory.post("/admin/")
        request.user = self.user
        modeladmin = MagicMock()
        create_workout_from_template(
            modeladmin, request, WorkoutTemplate.objects.filter(pk=self.template.pk)
        )
        workout = Workout.objects.get(template=self.template)
        item = workout.items.get()
        self.assertEqual(item.order, 2)
        self.assertEqual(item.sets, 3)
        self.assertEqual(item.reps, 5)
        self.assertEqual(item.duration, 120)
        self.assertEqual(item.distance, 400)
        self.assertEqual(item.distance_unit, "km")
        self.assertEqual(item.rpe, 8)
        self.assertEqual(item.notes, "keep chest up")
        self.assertEqual(WorkoutItem.objects.filter(workout=workout).count(), 1)


class ExerciseVideoUrlValidationTests(TestCase):
    """SEC-004: video_url must use allowed embed hosts."""

    def test_accepts_youtube_embed_url(self):
        ex = Exercise(
            name="YouTube Move",
            exercise_type="strength",
            video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
        )
        ex.save()

    def test_rejects_non_allowed_host(self):
        ex = Exercise(
            name="Bad Embed",
            exercise_type="strength",
            video_url="https://evil.example.com/video",
        )
        with self.assertRaises(ValidationError):
            ex.save()


class WorkoutPlanSerializerErrorPropagationTests(TestCase):
    """SER-001: serialization errors must not be replaced with empty template_links."""

    def setUp(self):
        self.user = User.objects.create_user("ser001", password="testpass123")
        self.plan = WorkoutPlan.objects.create(user=self.user, title="Ser Plan")

    @patch.object(
        drf_serializers.ModelSerializer,
        "to_representation",
        side_effect=RuntimeError("simulated serialization failure"),
    )
    def test_to_representation_propagates_errors(self, _mock):
        serializer = WorkoutPlanSerializer(
            instance=self.plan, context={"request": MagicMock()}
        )
        with self.assertRaises(RuntimeError):
            serializer.to_representation(self.plan)


class ProfileViewSetPkContractTests(TestCase):
    """API-003: detail URL pk must match the authenticated user's id."""

    def setUp(self):
        self.user_a = User.objects.create_user("prof_a", password="testpass123")
        self.user_b = User.objects.create_user("prof_b", password="testpass123")
        self.client = APIClient()

    def test_detail_404_when_pk_not_current_user(self):
        self.client.force_authenticate(user=self.user_a)
        url = f"/api/profiles/{self.user_b.pk}/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_200_and_creates_profile_when_pk_matches(self):
        self.client.force_authenticate(user=self.user_a)
        url = f"/api/profiles/{self.user_a.pk}/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(Profile.objects.filter(user=self.user_a).exists())


class WorkoutListQueryCountTests(TestCase):
    """PERF-001: list endpoint prefetches items and nested exercise muscle groups."""

    def setUp(self):
        self.user = User.objects.create_user("perfuser", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        mg = MuscleGroup.objects.create(name="Quads")
        self.ex = Exercise.objects.create(name="Squat", exercise_type="strength")
        self.ex.muscle_groups.add(mg)
        base = timezone.now().replace(microsecond=0)
        for i in range(3):
            start = base + timedelta(days=i)
            w = Workout.objects.create(
                user=self.user,
                title="W",
                start_dt=start,
                end_dt=start + timedelta(minutes=45),
            )
            WorkoutItem.objects.create(
                workout=w, exercise=self.ex, order=0, sets=3, reps=5
            )

    def test_workout_list_query_count_bounded(self):
        # Without per-item prefetch this would scale with workouts × items (N+1).
        # Expected: workouts list, prefetched items+exercises, M2M muscle_groups for exercises.
        with self.assertNumQueries(3):
            resp = self.client.get("/api/workouts/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 3)


class VerifyUserViewTests(TestCase):
    """LOGIC-002: authenticated GET must return tokens and the current user without a bogus DB lookup."""

    def setUp(self):
        self.user = User.objects.create_user("verifyuser", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_returns_tokens_and_current_user(self):
        resp = self.client.get("/users/token/refresh/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertEqual(resp.data["user"]["username"], "verifyuser")
