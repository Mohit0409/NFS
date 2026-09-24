from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import sqlite3
from contextlib import closing

from gateway import member_gateway


class MemberGatewayEligibilityTests(TestCase):
    NOW = 2_000_000_000

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.database = Path(self.temp.name) / "gravity.sqlite3"
        with closing(sqlite3.connect(self.database)) as connection:
            connection.executescript("""
            CREATE TABLE customers (
                id TEXT PRIMARY KEY, phone_e164 TEXT, status TEXT,
                person_type TEXT, created_by_admin_user_id TEXT
            );
            CREATE TABLE memberships (
                id TEXT PRIMARY KEY, customer_id TEXT, status TEXT,
                starts_at INTEGER, ends_at INTEGER
            );
            """)
        self.database_patch = patch.object(member_gateway, "MEMBER_DATABASE", self.database)
        self.time_patch = patch.object(member_gateway.time, "time", return_value=self.NOW)
        self.database_patch.start()
        self.time_patch.start()
    def tearDown(self):
        self.time_patch.stop()
        self.database_patch.stop()
        self.temp.cleanup()

    def add_person(self, person_id, phone, *, status="active", person_type="member", owner="admin-1"):
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "INSERT INTO customers VALUES (?,?,?,?,?)",
                    (person_id, phone, status, person_type, owner),
                )

    def add_membership(self, membership_id, person_id, *, status="active", start=None, end=None):
        start = self.NOW - 100 if start is None else start
        end = self.NOW + 100 if end is None else end
        with closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "INSERT INTO memberships VALUES (?,?,?,?,?)",
                    (membership_id, person_id, status, start, end),
                )

    def test_active_owner_managed_member_with_current_membership_is_eligible(self):
        self.add_person("p1", "+919999999901")
        self.add_membership("m1", "p1")
        self.assertTrue(member_gateway._member_is_eligible("+919999999901"))
        self.assertTrue(member_gateway._customer_is_login_eligible("p1"))

    def test_expired_membership_is_not_eligible(self):
        self.add_person("p2", "+919999999902")
        self.add_membership("m2", "p2", end=self.NOW)
        self.assertFalse(member_gateway._member_is_eligible("+919999999902"))
        self.assertFalse(member_gateway._customer_is_login_eligible("p2"))
    def test_future_scheduled_membership_is_not_eligible(self):
        self.add_person("p3", "+919999999903")
        self.add_membership("m3", "p3", status="scheduled", start=self.NOW + 1, end=self.NOW + 100)
        self.assertFalse(member_gateway._member_is_eligible("+919999999903"))

    def test_due_scheduled_membership_is_eligible_before_reconciliation(self):
        self.add_person("p4", "+919999999904")
        self.add_membership("m4", "p4", status="scheduled", start=self.NOW, end=self.NOW + 100)
        self.assertTrue(member_gateway._member_is_eligible("+919999999904"))

    def test_staff_disabled_and_unmanaged_people_are_not_eligible(self):
        cases = [
            ("p5", "+919999999905", "active", "staff", "admin-1"),
            ("p6", "+919999999906", "disabled", "member", "admin-1"),
            ("p7", "+919999999907", "active", "member", None),
        ]
        for index, (person_id, phone, status, person_type, owner) in enumerate(cases, start=5):
            self.add_person(person_id, phone, status=status, person_type=person_type, owner=owner)
            self.add_membership(f"m{index}", person_id)
            self.assertFalse(member_gateway._member_is_eligible(phone))

    def test_membership_summary_requires_active_current_period(self):
        active = {"current": {"status": "active", "startsAt": self.NOW - 1, "endsAt": self.NOW + 1}}
        expired = {"current": {"status": "active", "startsAt": self.NOW - 10, "endsAt": self.NOW}}
        future = {"current": {"status": "active", "startsAt": self.NOW + 1, "endsAt": self.NOW + 10}}
        self.assertTrue(member_gateway._membership_summary_allows_access(active))
        self.assertFalse(member_gateway._membership_summary_allows_access(expired))
        self.assertFalse(member_gateway._membership_summary_allows_access(future))
        self.assertFalse(member_gateway._membership_summary_allows_access({"current": None}))

    def test_renewal_restores_login_eligibility(self):
        self.add_person("p8", "+919999999908")
        self.add_membership("m8-old", "p8", status="expired", start=self.NOW - 1000, end=self.NOW - 500)
        self.add_membership("m8-new", "p8", status="active", start=self.NOW - 10, end=self.NOW + 1000)
        self.assertTrue(member_gateway._member_is_eligible("+919999999908"))
        self.assertTrue(member_gateway._customer_is_login_eligible("p8"))
