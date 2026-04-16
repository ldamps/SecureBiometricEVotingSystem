"""Load test for the Secure Biometric E-Voting System API.

Simulates realistic traffic patterns during a polling window:
- Voters browse elections, verify identity, and cast votes
- Officials log in, view audit logs, and manage elections

The backend runs inside Docker and is only reachable through the
Nginx gateway at https://localhost (port 8000 is not published to
the host). TLS certificate verification is disabled because the
deployment uses a self-signed cert in dev.

429 (Too Many Requests) responses from the gateway rate limiter are
counted as successes, not failures — they prove the rate limiting
works. Only 5xx errors and connection failures count as real failures.

Run with web UI (dashboard at http://localhost:8089):
    locust -f tests/load/locustfile.py --host https://localhost

Headless (no browser needed, exports CSV results):
    locust -f tests/load/locustfile.py --host https://localhost \
           --headless -u 50 -r 5 -t 60s --csv tests/load/results/load_test

    -u 50    = 50 concurrent users
    -r 5     = spawn 5 users/second
    -t 60s   = run for 60 seconds
    --csv    = export results to CSV files
"""

import uuid

from locust import HttpUser, between, events, tag, task


# ---------------------------------------------------------------------------
# Track rate-limited requests separately so they don't pollute failure stats.
# ---------------------------------------------------------------------------

rate_limited_count = 0


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, exception, **kwargs):
    """Count 429 responses globally for reporting."""
    global rate_limited_count
    if response is not None and response.status_code == 429:
        rate_limited_count += 1


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Print rate-limit summary at the end of the run."""
    if rate_limited_count > 0:
        print(f"\n--- Rate Limiting Summary ---")
        print(f"Requests throttled by gateway (429): {rate_limited_count}")
        print(f"This confirms the Nginx rate limiter is active.\n")


# ---------------------------------------------------------------------------
# Helper: treat 429 as expected behaviour, not a failure
# ---------------------------------------------------------------------------

def _is_ok(status_code: int, *extra_ok_codes: int) -> bool:
    """True for 2xx, 429 (rate limited), and any extra codes passed."""
    return (200 <= status_code < 300) or status_code == 429 or status_code in extra_ok_codes


class VoterUser(HttpUser):
    """Simulates a voter browsing elections, viewing results, and checking health.

    Voter-facing endpoints that don't require a live database or real voter
    registration are tested here. The cast-vote endpoint is excluded because
    it requires a fully registered voter with biometric credentials, a valid
    ballot token, and an open election — conditions that only exist in the
    real database.
    """

    weight = 7  # 70% of simulated users are voters
    wait_time = between(1, 3)

    @tag("health")
    @task(3)
    def health_check(self):
        """GET /health — lightweight probe, high frequency."""
        with self.client.get("/health", name="/health", verify=False, catch_response=True) as resp:
            if _is_ok(resp.status_code):
                resp.success()

    @tag("elections")
    @task(5)
    def browse_elections(self):
        """GET /api/v1/election/ — voters check what elections are available."""
        with self.client.get("/api/v1/election/", name="/api/v1/election/", verify=False, catch_response=True) as resp:
            if _is_ok(resp.status_code):
                resp.success()

    @tag("elections")
    @task(2)
    def get_single_election(self):
        """GET /api/v1/election/{id} — voter views election details.

        Uses a random UUID which will likely 404, but the goal is to
        measure response time and throughput under load, not functional
        correctness.
        """
        fake_id = str(uuid.uuid4())
        with self.client.get(
            f"/api/v1/election/{fake_id}",
            name="/api/v1/election/{election_id}",
            catch_response=True,
            verify=False,
        ) as resp:
            if _is_ok(resp.status_code, 404):
                resp.success()

    @tag("referendums")
    @task(3)
    def browse_referendums(self):
        """GET /api/v1/referendum/ — voters check active referendums."""
        with self.client.get("/api/v1/referendum/", name="/api/v1/referendum/", verify=False, catch_response=True) as resp:
            if _is_ok(resp.status_code):
                resp.success()

    @tag("referendums")
    @task(1)
    def get_single_referendum(self):
        """GET /api/v1/referendum/{id} — voter views referendum details."""
        fake_id = str(uuid.uuid4())
        with self.client.get(
            f"/api/v1/referendum/{fake_id}",
            name="/api/v1/referendum/{referendum_id}",
            catch_response=True,
            verify=False,
        ) as resp:
            if _is_ok(resp.status_code, 404):
                resp.success()

    @tag("parties")
    @task(2)
    def browse_parties(self):
        """GET /api/v1/party/ — voters browse political parties."""
        with self.client.get("/api/v1/party/", name="/api/v1/party/", verify=False, catch_response=True) as resp:
            if _is_ok(resp.status_code):
                resp.success()

    @tag("constituencies")
    @task(1)
    def browse_constituencies(self):
        """GET /api/v1/constituency/ — voters look up their constituency."""
        with self.client.get("/api/v1/constituency/", name="/api/v1/constituency/", verify=False, catch_response=True) as resp:
            if _is_ok(resp.status_code):
                resp.success()


class OfficialUser(HttpUser):
    """Simulates an election official logging in and performing admin tasks.

    Tests the authentication flow and protected endpoints. Failed logins
    are included to verify rate limiting and lockout behaviour under load.
    """

    weight = 3  # 30% of simulated users are officials
    wait_time = between(2, 5)

    def on_start(self):
        """Attempt login at the start of each user session."""
        self.token = None
        self._login()

    def _login(self):
        """POST /api/v1/auth/login — authenticate and store JWT."""
        with self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin1", "password": "Password1"},
            name="/api/v1/auth/login",
            verify=False,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                resp.success()
            elif resp.status_code == 429:
                resp.success()

    def _auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @tag("auth")
    @task(2)
    def login_attempt(self):
        """POST /api/v1/auth/login — repeated login attempts."""
        with self.client.post(
            "/api/v1/auth/login",
            json={"username": "admin1", "password": "Password1"},
            name="/api/v1/auth/login",
            verify=False,
            catch_response=True,
        ) as resp:
            if _is_ok(resp.status_code):
                resp.success()

    @tag("auth")
    @task(1)
    def failed_login_attempt(self):
        """POST /api/v1/auth/login — deliberate wrong password.

        Tests that the server handles bad credentials efficiently under load.
        Uses a non-existent username so the real admin1 account is not locked.
        """
        with self.client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent_user", "password": "WrongPassword!"},
            name="/api/v1/auth/login [bad_creds]",
            catch_response=True,
            verify=False,
        ) as resp:
            if _is_ok(resp.status_code, 401):
                resp.success()

    @tag("auth")
    @task(2)
    def get_current_user(self):
        """GET /api/v1/auth/me — verify token and fetch profile."""
        with self.client.get(
            "/api/v1/auth/me",
            headers=self._auth_headers(),
            name="/api/v1/auth/me",
            catch_response=True,
            verify=False,
        ) as resp:
            if _is_ok(resp.status_code, 401):
                resp.success()

    @tag("elections")
    @task(3)
    def browse_elections(self):
        """GET /api/v1/election/ — official views all elections."""
        with self.client.get(
            "/api/v1/election/",
            headers=self._auth_headers(),
            name="/api/v1/election/",
            verify=False,
            catch_response=True,
        ) as resp:
            if _is_ok(resp.status_code):
                resp.success()

    @tag("audit")
    @task(2)
    def view_audit_logs(self):
        """GET /api/v1/audit/ — official reviews recent audit trail."""
        with self.client.get(
            "/api/v1/audit/",
            headers=self._auth_headers(),
            name="/api/v1/audit/",
            catch_response=True,
            verify=False,
        ) as resp:
            if _is_ok(resp.status_code, 401, 403):
                resp.success()

    @tag("health")
    @task(1)
    def health_check(self):
        """GET /health — basic availability check."""
        with self.client.get("/health", name="/health", verify=False, catch_response=True) as resp:
            if _is_ok(resp.status_code):
                resp.success()
