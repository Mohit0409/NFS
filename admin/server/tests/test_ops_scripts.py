from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import subprocess
import sys
import unittest

from server.gravity.database import Database


ROOT = Path(__file__).resolve().parents[2]
ENV_RUNNER = ROOT / "scripts" / "gravity-env.py"
NEW_GYM_PREFLIGHT = ROOT / "deploy" / "new-gym-termux" / "preflight-new-gym.py"
NEW_GYM_ACCEPTANCE = ROOT / "deploy" / "new-gym-termux" / "acceptance-new-gym.py"
NEW_GYM_CUSTOMER_RENDERER = ROOT / "deploy" / "new-gym-termux" / "render-customer-config.py"
NEW_GYM_PUBLIC_RELEASE_VERIFIER = ROOT / "deploy" / "new-gym-termux" / "verify-public-release.py"
OWNER_DEMO_ROOT = ROOT / "deploy" / "owner-demo"
OWNER_DEMO_SEED = OWNER_DEMO_ROOT / "seed-owner-demo.py"
OWNER_DEMO_EDGE = OWNER_DEMO_ROOT / "demo-edge.py"
OWNER_DEMO_SYNC = OWNER_DEMO_ROOT / "sync-ngrok-url.py"
OWNER_DEMO_PC_DEPLOYER = OWNER_DEMO_ROOT / "deploy-from-pc.ps1"
OWNER_DEMO_RUNTIME = OWNER_DEMO_ROOT / "prepare-owner-demo-runtime.sh"
OWNER_DEMO_STANDALONE = OWNER_DEMO_ROOT / "install-owner-demo-standalone.sh"
OWNER_DEMO_USB_PREFLIGHT = OWNER_DEMO_ROOT / "usb-termux-preflight.sh"
OWNER_DEMO_USB_BOOTSTRAP = OWNER_DEMO_ROOT / "usb-bootstrap-owner-demo.sh"
OWNER_DEMO_STOP_STANDALONE = OWNER_DEMO_ROOT / "stop-owner-demo-standalone.sh"


class OperationsScriptTests(unittest.TestCase):
    def test_dotenv_runner_preserves_spaces_without_shell_evaluation(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "must-not-exist"
            config = root / "gravity.env"
            config.write_text(
                "GRAVITY_PORT=9099\n"
                "BUSINESS_NAME=Gravity Fitness\n"
                f"UNTRUSTED=$(touch {marker})\n",
                encoding="utf-8",
            )
            spec = importlib.util.spec_from_file_location("gravity_env", ENV_RUNNER)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            values = module.load_file(config)
            self.assertEqual(
                [values["BUSINESS_NAME"], values["UNTRUSTED"]],
                ["Gravity Fitness", f"$(touch {marker})"],
            )
            self.assertFalse(marker.exists())

    def test_dotenv_print_is_restricted_to_non_secret_operations_keys(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ENV_RUNNER), "--print", "SECRET_KEY"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_managed_launchers_pin_the_backend_to_loopback(self) -> None:
        files = [
            ROOT / "scripts" / "start-gravity.ps1",
            ROOT / "scripts" / "start-gravity.sh",
            ROOT / "deploy" / "termux" / "services" / "gravity" / "run",
        ]
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertIn("127.0.0.1", text, path)
            self.assertIn("server.gravity", text, path)

    def test_f09_onsite_script_has_secret_safe_preflight_and_direct_tcp_guards(self) -> None:
        script = (ROOT / "scripts" / "configure-zkteco-f09.ps1").read_text(encoding="utf-8")
        requirements = (ROOT / "scripts" / "requirements-biometric-driver.txt").read_text(encoding="utf-8")
        guide = (ROOT / "docs" / "ON_SITE_F09_AUTOMATION_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("PreflightOnly", script)
        self.assertIn("Read-Host 'F09 numeric Comm Key", script)
        self.assertIn("-AsSecureString", script)
        self.assertIn("Test-NetConnection -ComputerName $DeviceIp -Port $DevicePort", script)
        self.assertIn("/api/admin/biometric/devices", script)
        self.assertIn("/sync", script)
        self.assertIn("-StartNgrok", guide)
        self.assertIn("gravity_fitness_website", guide)
        self.assertIn("pyzk==0.9", requirements)
        self.assertIn("--hash=sha256:9dcf0d40e0473c752d04d0af389fdd71ce85a0a9609bb8aca562be9171248170", requirements)
        for marker in ("SECRET_KEY=", "authtoken=", "Comm Key="):
            self.assertNotIn(marker, script)

    @unittest.skipUnless(sys.platform == "win32", "Windows PowerShell preflight")
    def test_f09_onsite_preflight_is_non_mutating(self) -> None:
        script = ROOT / "scripts" / "configure-zkteco-f09.ps1"
        with TemporaryDirectory() as temporary:
            config = Path(temporary) / "gravity.env"
            config.write_text(
                f"GRAVITY_HOST=127.0.0.1\nGRAVITY_PORT=8799\nGRAVITY_PYTHON={sys.executable}\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                 "-ConfigPath", str(config), "-PreflightOnly"],
                cwd=ROOT, capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        plan = __import__("json").loads(result.stdout.strip())
        self.assertEqual(plan["mode"], "preflight")
        self.assertEqual(plan["device"]["host"], "192.168.1.201")
        self.assertNotIn("commKey", result.stdout.casefold())

    @unittest.skipUnless(sys.platform == "win32", "Windows file-lock behavior")
    def test_operations_log_lock_falls_back_without_failing_lifecycle(self) -> None:
        common = ROOT / "scripts" / "gravity-common.ps1"
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            (runtime / "operations.log").write_text("seed\n", encoding="utf-8")
            probe = runtime / "probe.ps1"
            common_ps = str(common).replace("'", "''")
            runtime_ps = str(runtime).replace("'", "''")
            probe.write_text(
                "$ErrorActionPreference = 'Stop'\n"
                f". '{common_ps}'\n"
                f"$runtime = '{runtime_ps}'\n"
                "$path = Join-Path $runtime 'operations.log'\n"
                "$lock = [IO.File]::Open($path,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)\n"
                "try { Write-GravityOpsLog -Context ([pscustomobject]@{RuntimeDir=$runtime}) -Message 'lock-test' } finally { $lock.Dispose() }\n"
                "$fallback = Get-ChildItem $runtime -Filter 'operations.fallback.*.log' | Select-Object -First 1\n"
                "if (-not $fallback) { exit 3 }\n"
                "if ((Get-Content $fallback.FullName -Raw) -notmatch 'lock-test') { exit 4 }\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(probe)],
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_tunnel_targets_loopback_and_token_is_not_in_git(self) -> None:
        tunnel = (
            ROOT / "deploy" / "termux" / "services" / "gravity-tunnel" / "run"
        ).read_text(encoding="utf-8")
        example = (ROOT / "deploy" / "termux" / "gravity.env.example").read_text(
            encoding="utf-8"
        )
        self.assertIn("--token-file", tunnel)
        self.assertNotRegex(example, r"(?m)^SECRET_KEY=.+$")
        self.assertNotRegex(example, r"(?m)^CLOUDFLARED_TOKEN=.+$")

    def test_termux_installer_has_network_audit_dependency_and_safe_boot_install(self) -> None:
        installer = (ROOT / "deploy" / "termux" / "install-termux.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("iproute2", installer)
        self.assertRegex(installer, r"for command in python3 git curl ss sv svlogd")
        self.assertNotIn("ln -sfn", installer)
        self.assertIn("Refusing to replace existing boot script", installer)

    def test_termux_network_audit_has_android_runtime_state_fallback(self) -> None:
        audit = (ROOT / "deploy" / "termux" / "network-audit.sh").read_text(encoding="utf-8")
        self.assertIn("gravity.state.json", audit)
        self.assertIn("GRAVITY_RUNTIME_DIR", audit)
        self.assertIn('state.get("host") != "127.0.0.1"', audit)
        self.assertIn('inspection="runtime-state"', audit)
        self.assertIn('curl -fsS --max-time 5 "http://127.0.0.1:$PORT/api/health"', audit)

    def test_migration_runbook_uses_valid_windows_script_paths(self) -> None:
        runbook = (ROOT / "docs" / "TERMUX_MIGRATION_RUNBOOK.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(".\\scripts\\status-gravity.ps1", runbook)
        self.assertIn(".\\scripts\\export-gravity-migration.ps1", runbook)
        self.assertNotIn(".scriptsstatus-gravity.ps1", runbook)
        self.assertNotIn(".scriptsexport-gravity-migration.ps1", runbook)

    def test_system_watchdog_requires_explicit_ngrok_paths(self) -> None:
        installer = (ROOT / "scripts" / "install-gravity-tasks.ps1").read_text(
            encoding="utf-8"
        )
        watchdog = (ROOT / "scripts" / "watch-gravity.ps1").read_text(
            encoding="utf-8"
        )
        tunnel = (ROOT / "scripts" / "start-ngrok.ps1").read_text(
            encoding="utf-8"
        )
        runbook = (ROOT / "docs" / "OPERATIONS_RUNBOOK.md").read_text(
            encoding="utf-8"
        )
        for text in (installer, watchdog, tunnel):
            self.assertIn("NgrokConfigPath", text)
            self.assertIn("NgrokExecutablePath", text)
        self.assertIn("task runs as SYSTEM", installer)
        self.assertIn("ngrok configuration was not found", installer)
        self.assertIn("ngrok executable was not found", installer)
        self.assertIn("SYSTEM task recovery", watchdog)
        self.assertIn("-ExplicitPath $NgrokExecutablePath", tunnel)
        self.assertIn("-NgrokConfigPath C:\\ProgramData\\GravityFitness\\ngrok.yml", runbook)
        self.assertIn("-NgrokExecutablePath 'C:\\Program Files\\ngrok\\ngrok.exe'", runbook)
        self.assertIn("Controlled Windows lifecycle cutover", runbook)
        self.assertIn("-ExpectedReleaseSha $releaseSha -RequireDetachedHead -PreflightOnly", runbook)
        self.assertIn(".\\scripts\\adopt-ngrok.ps1", runbook)
        self.assertIn("-ConfirmAdopt", runbook)
        self.assertIn(".\\scripts\\verify-gravity-tasks.ps1", runbook)

    def test_windows_ngrok_refuses_duplicate_unmanaged_loopback_tunnel(self) -> None:
        tunnel = (ROOT / "scripts" / "start-ngrok.ps1").read_text(encoding="utf-8")
        selector = '[string]$_.config.addr -eq "http://127.0.0.1:$($context.Port)"'
        refusal = "Refusing to start a second ngrok process"
        launcher = "Start-Process -FilePath $ngrokExe"
        self.assertIn(selector, tunnel)
        self.assertIn(refusal, tunnel)
        self.assertLess(tunnel.index(refusal), tunnel.index(launcher))

    def test_notification_scheduler_is_isolated_from_lifecycle_tasks(self) -> None:
        installer = (ROOT / "scripts" / "install-gravity-tasks.ps1").read_text(
            encoding="utf-8"
        )
        termux_installer = (ROOT / "deploy" / "termux" / "install-termux.sh").read_text(
            encoding="utf-8"
        )
        boot = (ROOT / "deploy" / "termux" / "termux-boot-gravity.sh").read_text(
            encoding="utf-8"
        )
        service = (
            ROOT / "deploy" / "termux" / "services" / "gravity-notifications" / "run"
        ).read_text(encoding="utf-8")
        self.assertIn("GravityFitness-Notifications", installer)
        self.assertIn("GravityFitness-Watchdog", installer)
        self.assertIn("GravityFitness-DailyBackup", installer)
        self.assertIn("New-ScheduledTaskTrigger -AtStartup", installer)
        self.assertIn("-MultipleInstances IgnoreNew", installer)
        self.assertIn("run-notifications.ps1", installer)
        self.assertNotIn("SMTP_PASSWORD", installer)
        self.assertNotIn("SMS_API_KEY", installer)
        self.assertNotIn("WHATSAPP_ACCESS_TOKEN", installer)
        self.assertIn("gravity-notifications", termux_installer)
        self.assertIn("gravity-notifications", boot)
        self.assertIn("INTERVAL_SECONDS=3600", service)
        self.assertIn("run-notifications.sh", service)

    def test_admin_health_wrappers_are_read_only_and_task_commands_are_secret_free(self) -> None:
        powershell = (ROOT / "scripts" / "admin-health-check.ps1").read_text(encoding="utf-8")
        shell = (ROOT / "scripts" / "admin-health-check.sh").read_text(encoding="utf-8")
        installer = (ROOT / "scripts" / "install-gravity-tasks.ps1").read_text(encoding="utf-8")
        self.assertIn("admin-health-check.py", powershell)
        self.assertIn("admin-health-check.py", shell)
        self.assertIn("--runtime-dir", powershell)
        self.assertIn("--runtime-dir", shell)
        forbidden = (
            "SECRET_KEY=", "SMTP_PASSWORD=", "SMS_API_KEY=", "WHATSAPP_ACCESS_TOKEN=",
            "RAZORPAY_KEY_SECRET=", "RAZORPAY_WEBHOOK_SECRET=", "FIREBASE_SERVICE_ACCOUNT=",
        )
        for text in (powershell, shell, installer):
            for marker in forbidden:
                self.assertNotIn(marker, text)

    @unittest.skipUnless(sys.platform == "win32", "Windows Task Scheduler preflight")
    def test_task_installer_preflight_is_non_mutating_and_secret_free(self) -> None:
        installer = ROOT / "scripts" / "install-gravity-tasks.ps1"
        with TemporaryDirectory() as temporary:
            config = Path(temporary) / "gravity.env"
            config.write_text("GRAVITY_HOST=127.0.0.1\nGRAVITY_PORT=8799\n", encoding="utf-8")
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(installer),
                 "-ConfigPath", str(config), "-PreflightOnly"],
                cwd=ROOT, capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = __import__("json").loads(result.stdout.strip())
        self.assertEqual([item["name"] for item in plan["tasks"]], [
            "GravityFitness-Watchdog", "GravityFitness-DailyBackup", "GravityFitness-Notifications"
        ])
        self.assertTrue(all(item["principal"] == "SYSTEM" for item in plan["tasks"]))
        self.assertTrue(all(item["runLevel"] == "Highest" for item in plan["tasks"]))
        for marker in ("SECRET_KEY=", "SMTP_PASSWORD=", "SMS_API_KEY=", "authtoken="):
            self.assertNotIn(marker, result.stdout)

    def test_task_verifier_is_read_only_and_checks_release_identity(self) -> None:
        verifier = (ROOT / "scripts" / "verify-gravity-tasks.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-ScheduledTask", verifier)
        self.assertNotIn("Register-ScheduledTask", verifier)
        self.assertIn("ExpectedReleaseSha", verifier)
        self.assertIn("RequireDetachedHead", verifier)
        self.assertIn("MSFT_TaskBootTrigger", verifier)
        self.assertIn("MultipleInstances", verifier)
        self.assertIn("working_directory_mismatch", verifier)
        self.assertIn("secret_marker", verifier)
        self.assertRegex(verifier, r"if \(\$blockers\.Count -ne 0\) \{ exit 2 \}\s+exit 0")

    def test_ngrok_adoption_defaults_to_probe_only_and_requires_explicit_commit(self) -> None:
        adoption = (ROOT / "scripts" / "adopt-ngrok.ps1").read_text(encoding="utf-8")
        self.assertIn("ConfirmAdopt", adoption)
        self.assertIn("--probe-only", adoption)
        self.assertIn("Gravity loopback health must be green", adoption)
        self.assertIn("ngrok-skip-browser-warning", adoption)
        self.assertIn("Remove-Item -LiteralPath $temporaryEvidence", adoption)
        self.assertNotIn("authtoken", adoption.casefold())

    def test_release_lifecycle_check_is_read_only_and_secret_safe(self) -> None:
        script = (ROOT / "scripts" / "release-lifecycle-check.ps1").read_text(encoding="utf-8")
        self.assertIn("Get-ScheduledTaskInfo", script)
        self.assertIn("Get-NetTCPConnection", script)
        self.assertIn("verify-gravity-tasks.ps1", script)
        self.assertIn("ngrok-skip-browser-warning", script)
        self.assertNotIn("Register-ScheduledTask", script)
        self.assertNotIn("Stop-Process", script)
        self.assertNotIn("Set-Content", script)
        self.assertNotIn("Remove-Item", script)
        for marker in ("SECRET_KEY=", "SMTP_PASSWORD=", "SMS_API_KEY=", "WHATSAPP_ACCESS_TOKEN="):
            self.assertNotIn(marker, script)
        self.assertIn("--authtoken|authtoken=", script)

    def test_operations_runbook_has_single_post_reboot_acceptance_command(self) -> None:
        runbook = (ROOT / "docs" / "OPERATIONS_RUNBOOK.md").read_text(encoding="utf-8")
        self.assertIn("release-lifecycle-check.ps1", runbook)
        self.assertIn("Exit `0` with `\"ready\":true`", runbook)
        self.assertIn("does not start/stop processes", runbook)
        self.assertIn("Do not proceed to the fresh `pre-admin-v1` backup", runbook)

    def test_managed_ngrok_state_pins_config_path_for_reboot_verification(self) -> None:
        script = (ROOT / "scripts" / "start-ngrok.ps1").read_text(encoding="utf-8")
        self.assertIn("configPath = $ngrokConfig", script)
        self.assertIn("$state.configPath", script)
        self.assertIn("$ngrokConfig", script)

    def test_browser_assets_contain_no_server_secret_configuration_names(self) -> None:
        forbidden = (
            "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET", "SMTP_PASSWORD",
            "WHATSAPP_ACCESS_TOKEN", "SMS_API_KEY", "SECRET_KEY", "session_token",
        )
        for path in (ROOT / "web").rglob("*"):
            if path.suffix not in {".js", ".html"}:
                continue
            text = path.read_text(encoding="utf-8")
            for marker in forbidden:
                self.assertNotIn(marker, text, path)

    def test_termux_f09_is_explicitly_approval_gated(self) -> None:
        wrapper = (ROOT / "deploy" / "termux" / "f09-onsite.sh").read_text(encoding="utf-8")
        runner = (ROOT / "deploy" / "termux" / "f09-onsite.py").read_text(encoding="utf-8")
        approval = (ROOT / "deploy" / "termux" / "approve-f09-once.py").read_text(encoding="utf-8")
        boot = (ROOT / "deploy" / "termux" / "termux-boot-gravity.sh").read_text(encoding="utf-8")
        installer = (ROOT / "deploy" / "termux" / "install-termux.sh").read_text(encoding="utf-8")
        self.assertIn("Explicit owner approval is required", wrapper)
        self.assertIn("path.unlink()", runner)
        self.assertIn('"automaticWifiTrigger": False', runner)
        self.assertIn('"backgroundPollingEnabled": False', runner)
        self.assertIn("APPROVE F09 READ-ONLY INTEGRATION", approval)
        self.assertNotIn("f09-onsite", boot)
        self.assertNotIn("f09-onsite", installer)

    def test_zkteco_f09_adapter_has_no_device_mutation_calls(self) -> None:
        source = (ROOT / "server" / "gravity" / "biometric.py").read_text(encoding="utf-8")
        adapter = source.split("class ZKTecoF09Adapter:", 1)[1].split("def _verification_label", 1)[0]
        for allowed in (".get_serialnumber()", ".get_platform()", ".get_users()", ".get_attendance()"):
            self.assertIn(allowed, adapter)
        forbidden = (
            ".clear_attendance(", ".clear_data(", ".set_time(", ".set_user(", ".delete_user(",
            ".delete_user_template(", ".disable_device(", ".enable_device(", ".restart(",
            ".poweroff(", ".unlock(", ".test_voice(",
        )
        for marker in forbidden:
            self.assertNotIn(marker, adapter)

    def test_new_gym_termux_profile_is_isolated_and_loopback_only(self) -> None:
        profile = ROOT / "deploy" / "new-gym-termux"
        example = (profile / "new-gym.env.example").read_text(encoding="utf-8")
        installer = (profile / "install-termux.sh").read_text(encoding="utf-8")
        boot = (profile / "termux-boot-new-gym.sh").read_text(encoding="utf-8")
        routes = (profile / "CLOUDFLARE_ROUTES.md").read_text(encoding="utf-8")

        self.assertIn("GRAVITY_PORT=8897", example)
        self.assertIn("NEW_GYM_MEMBER_GATEWAY_PORT=8898", example)
        self.assertIn("NEW_GYM_PUBLIC_PORT=8899", example)
        self.assertIn(".config/new-gym", example)
        self.assertIn(".local/share/new-gym", example)
        self.assertNotIn(".config/gravity", example)
        self.assertNotIn(".local/share/gravity", example)

        for service in ("new-gym-admin", "new-gym-member", "new-gym-web"):
            runner = (profile / "services" / service / "run").read_text(encoding="utf-8")
            self.assertIn("127.0.0.1", runner, service)
            self.assertNotIn("0.0.0.0", runner, service)

        for name in (
            "new-gym-admin", "new-gym-member", "new-gym-web",
            "new-gym-health", "new-gym-notifications",
        ):
            self.assertIn(name, installer)
            self.assertIn(name, boot)
        self.assertIn("Refusing to replace existing service", installer)
        self.assertIn(".new-gym-managed", installer)
        self.assertIn("http://127.0.0.1:8897", routes)
        self.assertIn("http://127.0.0.1:8898", routes)
        self.assertIn("http://127.0.0.1:8899", routes)

    def test_new_gym_launch_preflight_is_fail_closed_and_secret_safe(self) -> None:
        spec = importlib.util.spec_from_file_location("new_gym_preflight", NEW_GYM_PREFLIGHT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        install_values = {
            "GRAVITY_ENV": "production",
            "GRAVITY_HOST": "127.0.0.1",
            "GRAVITY_PORT": "8897",
            "NEW_GYM_MEMBER_GATEWAY_PORT": "8898",
            "NEW_GYM_PUBLIC_PORT": "8899",
            "NEW_GYM_MEMBER_BACKEND": "http://127.0.0.1:8897",
            "GRAVITY_DATA_DIR": "/home/u/.local/share/new-gym/data",
            "GRAVITY_LOG_DIR": "/home/u/.local/state/new-gym/logs",
            "GRAVITY_BACKUP_DIR": "/home/u/.local/share/new-gym/backups",
            "SECRET_KEY": "x" * 40,
            "APP_BASE_URL": "https://admin.example.org",
        }
        install = module.validate(install_values, stage="install")
        self.assertTrue(install["ready"])

        launch_values = {
            **install_values,
            "BUSINESS_NAME": "Verified Fitness Club",
            "BUSINESS_ADDRESS": "Verified address",
            "OWNER_PHONE": "+919876543210",
            "NEW_GYM_MEMBER_ALLOWED_ORIGINS": "https://gym.example.org",
            "NEW_GYM_MEMBERSHIP_PRICING_CONFIRMED": "true",
            "NEW_GYM_POOL_RATES_CONFIRMED": "true",
            "NEW_GYM_KITCHEN_SETUP_CONFIRMED": "true",
            "FIREBASE_PROJECT_ID": "new-gym-auth",
            "FIREBASE_WEB_API_KEY": "public-web-key",
            "FIREBASE_AUTH_DOMAIN": "new-gym-auth.firebaseapp.com",
            "FIREBASE_APP_ID": "1:123:web:newgym",
            "FIREBASE_SERVICE_ACCOUNT_PATH": "/private/firebase.json",
            "CLOUDFLARED_TOKEN_FILE": "/private/cloudflare.token",
            "NEW_GYM_BACKUP_REMOTE": "new-gym-backup:daily",
            "NEW_GYM_REQUIRE_OFFDEVICE_BACKUP": "true",
        }
        customer_config = """
        name: 'Verified Fitness Club',
        phoneDisplay: '+91 98765 43210',
        whatsappNumber: '919876543210',
        address: 'Verified address',
        memberGatewayBase: 'https://gym.example.org',
        projectId: 'new-gym-auth',
        """
        ready_database = {
            "exists": True,
            "schemaVersion": 19,
            "integrityOk": True,
            "foreignKeysOk": True,
            "legacyPlanDrafts": 0,
            "activePlans": 2,
            "invalidActivePlans": 0,
            "poolTables": 3,
            "poolTablesMissingRates": 0,
            "availableMenuItems": 4,
            "activeInventoryItems": 6,
            "invalidRecipes": 0,
        }
        ready_backup = {
            "exists": True,
            "valid": True,
            "fresh": True,
            "remoteMatches": True,
        }
        launch = module.validate(
            launch_values,
            stage="launch",
            customer_config_text=customer_config,
            path_exists=lambda _value: True,
            database_state=ready_database,
            backup_state=ready_backup,
        )
        self.assertTrue(launch["ready"])

        blocked = module.validate(
            {**launch_values, "BUSINESS_NAME": "New Gym", "NEW_GYM_MEMBERSHIP_PRICING_CONFIRMED": "false"},
            stage="launch",
            customer_config_text="name: 'New Gym', phoneDisplay: '', projectId: ''",
            path_exists=lambda _value: True,
            database_state=ready_database,
            backup_state=ready_backup,
        )
        self.assertFalse(blocked["ready"])
        self.assertIn("business_name", blocked["blockers"])
        self.assertIn("membership_pricing_confirmed", blocked["blockers"])
        self.assertIn("customer_runtime_config", blocked["blockers"])

        serialized = __import__("json").dumps(blocked)
        self.assertNotIn(launch_values["SECRET_KEY"], serialized)

    def test_new_gym_database_preflight_detects_legacy_unconfigured_defaults(self) -> None:
        spec = importlib.util.spec_from_file_location("new_gym_preflight_db", NEW_GYM_PREFLIGHT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "new-gym.sqlite3"
            database = Database(path, ROOT / "server" / "migrations")
            database.migrate()
            state = module.inspect_database(path)

        self.assertTrue(state["exists"])
        self.assertGreaterEqual(state["schemaVersion"], 19)
        self.assertTrue(state["integrityOk"])
        self.assertTrue(state["foreignKeysOk"])
        self.assertEqual(state["legacyPlanDrafts"], 3)
        self.assertEqual(state["activePlans"], 3)
        self.assertEqual(state["invalidActivePlans"], 0)
        self.assertEqual(state["poolTables"], 3)
        self.assertEqual(state["poolTablesMissingRates"], 3)
        self.assertEqual(state["availableMenuItems"], 0)
        self.assertEqual(state["activeInventoryItems"], 0)

    def test_new_gym_backup_marker_requires_fresh_verified_matching_remote(self) -> None:
        spec = importlib.util.spec_from_file_location("new_gym_preflight_backup", NEW_GYM_PREFLIGHT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with TemporaryDirectory() as temporary:
            marker = Path(temporary) / "offdevice-backup.json"
            marker.write_text(
                __import__("json").dumps({
                    "verifiedAt": 1_900_000_000,
                    "archiveName": "new-gym-backup.tar.gz",
                    "archiveSha256": "a" * 64,
                    "remotePath": "new-gym-backup:daily/new-gym-backup.tar.gz",
                }),
                encoding="utf-8",
            )
            fresh = module.inspect_backup_marker(
                marker,
                expected_remote="new-gym-backup:daily",
                max_age_seconds=86400,
                now=1_900_000_100,
            )
            stale = module.inspect_backup_marker(
                marker,
                expected_remote="new-gym-backup:daily",
                max_age_seconds=60,
                now=1_900_000_100,
            )
            mismatch = module.inspect_backup_marker(
                marker,
                expected_remote="other-remote:daily",
                max_age_seconds=86400,
                now=1_900_000_100,
            )

        self.assertTrue(fresh["valid"])
        self.assertTrue(fresh["fresh"])
        self.assertTrue(fresh["remoteMatches"])
        self.assertFalse(stale["fresh"])
        self.assertFalse(mismatch["remoteMatches"])

    def test_new_gym_customer_config_renderer_uses_protected_env_and_live_prices(self) -> None:
        spec = importlib.util.spec_from_file_location("new_gym_customer_renderer", NEW_GYM_CUSTOMER_RENDERER)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            database_path = root / "new-gym.sqlite3"
            database = Database(database_path, ROOT / "server" / "migrations")
            database.migrate()
            with database.session() as connection:
                connection.execute(
                    "UPDATE membership_plans SET price_paise=150000,status='active' WHERE id='plan-basic-monthly'"
                )
                connection.execute(
                    "UPDATE membership_plans SET price_paise=390000,status='active' WHERE id='plan-pro-monthly'"
                )
                connection.execute(
                    "UPDATE membership_plans SET price_paise=1200000,status='active' WHERE id='plan-elite-monthly'"
                )
                connection.commit()

            values = {
                "BUSINESS_NAME": "Verified Fitness Club",
                "BUSINESS_SHORT_NAME": "VFC",
                "BUSINESS_CITY": "Neemuch",
                "BUSINESS_ADDRESS": "Verified address",
                "BUSINESS_OPENING_HOURS": "6 AM - 10 PM",
                "OWNER_PHONE": "+91 98765 43210",
                "OWNER_WHATSAPP": "919876543210",
                "BUSINESS_INSTAGRAM": "https://instagram.com/verifiedfitness",
                "BUSINESS_MAP_URL": "https://maps.google.com/?q=verified",
                "BUSINESS_MAP_EMBED_URL": "https://www.google.com/maps/embed?pb=verified",
                "NEW_GYM_PUBLIC_SITE_URL": "https://gym.example.org",
                "NEW_GYM_MEMBER_ALLOWED_ORIGINS": "https://gym.example.org",
                "FIREBASE_PROJECT_ID": "new-gym-auth",
                "FIREBASE_WEB_API_KEY": "public-web-key",
                "FIREBASE_AUTH_DOMAIN": "new-gym-auth.firebaseapp.com",
                "FIREBASE_APP_ID": "1:123:web:newgym",
            }
            prices = module.load_membership_prices(database_path)
            config = module.build_config(values, prices)

        self.assertEqual(config["name"], "Verified Fitness Club")
        self.assertEqual(config["shortName"], "VFC")
        self.assertEqual(config["city"], "Neemuch")
        self.assertEqual(config["phoneHref"], "tel:+919876543210")
        self.assertEqual(config["whatsappNumber"], "919876543210")
        self.assertEqual(config["memberGatewayBase"], "https://gym.example.org")
        self.assertEqual(
            config["membershipPricesPaise"],
            {
                "trial": None,
                "oneMonth": 150000,
                "threeMonths": 390000,
                "oneYear": 1200000,
            },
        )
        self.assertEqual(module.validate_complete(config), [])
        rendered = module.render(config)
        self.assertIn("Verified Fitness Club", rendered)
        self.assertIn('"oneMonth": 150000', rendered)
        for marker in ("gravityfitnessnmh", "gravity-authe", "917999526112"):
            self.assertNotIn(marker, rendered)

        incomplete = module.build_config(
            {
                "BUSINESS_NAME": "New Gym",
                "NEW_GYM_MEMBER_ALLOWED_ORIGINS": "https://www.new-gym.example",
            },
            {"trial": None, "oneMonth": None, "threeMonths": None, "oneYear": None},
        )
        blockers = module.validate_complete(incomplete)
        self.assertIn("business_name", blockers)
        self.assertIn("city", blockers)
        self.assertIn("membership_oneMonth", blockers)
        self.assertIn("firebase_projectId", blockers)

    def test_new_gym_public_release_verifier_rejects_tampering_and_gravity_values(self) -> None:
        spec = importlib.util.spec_from_file_location("new_gym_release_verifier", NEW_GYM_PUBLIC_RELEASE_VERIFIER)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        import hashlib
        import json

        with TemporaryDirectory() as temporary:
            release = Path(temporary) / "20260925T100000Z-abcdef123456"
            (release / "js").mkdir(parents=True)
            (release / "index.html").write_text("<html>New Gym</html>", encoding="utf-8")
            config = release / "js" / "gym-config.js"
            config.write_text("window.NEW_GYM_CONFIG={name:'Verified Fitness Club'};\n", encoding="utf-8")
            digest = hashlib.sha256(config.read_bytes()).hexdigest()
            manifest = {
                "releaseId": release.name,
                "gitCommit": "abcdef123456",
                "createdAt": 1900000000,
                "customerConfigSha256": digest,
                "complete": True,
            }
            (release / ".new-gym-release.json").write_text(json.dumps(manifest), encoding="utf-8")

            verified = module.verify_release(release, expected_release_id=release.name)
            self.assertTrue(verified["ready"])
            self.assertEqual(verified["gitCommit"], "abcdef123456")

            config.write_text("window.NEW_GYM_CONFIG={name:'Changed'};\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                module.verify_release(release, expected_release_id=release.name)

            config.write_text("window.NEW_GYM_CONFIG={projectId:'gravity-authe'};\n", encoding="utf-8")
            manifest["customerConfigSha256"] = hashlib.sha256(config.read_bytes()).hexdigest()
            (release / ".new-gym-release.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Gravity live values"):
                module.verify_release(release, expected_release_id=release.name)

    def test_need_for_strength_owner_demo_seed_and_production_blocker(self) -> None:
        seed_spec = importlib.util.spec_from_file_location("owner_demo_seed", OWNER_DEMO_SEED)
        self.assertIsNotNone(seed_spec)
        self.assertIsNotNone(seed_spec.loader)
        seed_module = importlib.util.module_from_spec(seed_spec)
        seed_spec.loader.exec_module(seed_module)

        preflight_spec = importlib.util.spec_from_file_location("new_gym_preflight_demo", NEW_GYM_PREFLIGHT)
        self.assertIsNotNone(preflight_spec)
        self.assertIsNotNone(preflight_spec.loader)
        preflight = importlib.util.module_from_spec(preflight_spec)
        preflight_spec.loader.exec_module(preflight)

        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "owner-demo.sqlite3"
            database = Database(path, ROOT / "server" / "migrations")
            result = seed_module.seed(database)
            state = preflight.inspect_database(path)
            with database.session() as connection:
                private_rate = connection.execute(
                    "SELECT default_rate_paise FROM pool_tables WHERE id='pool-private-1'"
                ).fetchone()[0]
                common_rates = [
                    row[0]
                    for row in connection.execute(
                        "SELECT default_rate_paise FROM pool_tables "
                        "WHERE id IN ('pool-common-1','pool-common-2') ORDER BY id"
                    ).fetchall()
                ]
                demo_plan_count = connection.execute(
                    "SELECT COUNT(*) FROM membership_plans WHERE id LIKE 'demo-%'"
                ).fetchone()[0]
                legacy_plan_count = connection.execute(
                    "SELECT COUNT(*) FROM membership_plans "
                    "WHERE id IN ('plan-basic-monthly','plan-pro-monthly','plan-elite-monthly')"
                ).fetchone()[0]
                total_plan_count = connection.execute(
                    "SELECT COUNT(*) FROM membership_plans"
                ).fetchone()[0]
                demo_menu_count = connection.execute(
                    "SELECT COUNT(*) FROM kitchen_menu_items WHERE id LIKE 'demo-%'"
                ).fetchone()[0]

        self.assertTrue(result["ownerDemoMode"])
        self.assertTrue(state["ownerDemoMode"])
        self.assertEqual(private_rate, 30000)
        self.assertEqual(common_rates, [20000, 20000])
        self.assertEqual(demo_plan_count, len(seed_module.DEMO_PLANS))
        self.assertEqual(total_plan_count, len(seed_module.DEMO_PLANS))
        self.assertEqual(legacy_plan_count, 0)
        self.assertEqual(demo_menu_count, len(seed_module.DEMO_MENU))

        blocked = preflight.validate(
            {
                "GRAVITY_ENV": "production",
                "GRAVITY_HOST": "127.0.0.1",
                "GRAVITY_PORT": "8897",
                "NEW_GYM_MEMBER_GATEWAY_PORT": "8898",
                "NEW_GYM_PUBLIC_PORT": "8899",
                "NEW_GYM_MEMBER_BACKEND": "http://127.0.0.1:8897",
                "GRAVITY_DATA_DIR": "/home/u/.local/share/new-gym/data",
                "GRAVITY_LOG_DIR": "/home/u/.local/state/new-gym/logs",
                "GRAVITY_BACKUP_DIR": "/home/u/.local/share/new-gym/backups",
                "SECRET_KEY": "x" * 40,
                "APP_BASE_URL": "https://admin.example.org",
                "BUSINESS_NAME": "Need For Strength",
                "BUSINESS_ADDRESS": "Verified address",
                "OWNER_PHONE": "+919893704372",
                "NEW_GYM_MEMBER_ALLOWED_ORIGINS": "https://gym.example.org",
                "NEW_GYM_MEMBERSHIP_PRICING_CONFIRMED": "true",
                "NEW_GYM_POOL_RATES_CONFIRMED": "true",
                "NEW_GYM_KITCHEN_SETUP_CONFIRMED": "true",
                "FIREBASE_PROJECT_ID": "need-for-strength-auth",
                "FIREBASE_WEB_API_KEY": "public-web-key",
                "FIREBASE_AUTH_DOMAIN": "need-for-strength-auth.firebaseapp.com",
                "FIREBASE_APP_ID": "1:123:web:nfs",
                "FIREBASE_SERVICE_ACCOUNT_PATH": "/private/firebase.json",
                "CLOUDFLARED_TOKEN_FILE": "/private/cloudflare.token",
                "NEW_GYM_BACKUP_REMOTE": "nfs-backup:daily",
                "NEW_GYM_REQUIRE_OFFDEVICE_BACKUP": "false",
            },
            stage="launch",
            customer_config_text=(
                "name: 'Need For Strength', phoneDisplay: '+91 98937 04372', "
                "whatsappNumber: '919893704372', address: 'Verified address', "
                "memberGatewayBase: 'https://gym.example.org', projectId: 'need-for-strength-auth'"
            ),
            path_exists=lambda _value: True,
            database_state=state,
        )
        self.assertFalse(blocked["ready"])
        self.assertIn("owner_demo_data_removed", blocked["blockers"])

    def test_need_for_strength_owner_demo_routes_one_ngrok_url_safely(self) -> None:
        edge_spec = importlib.util.spec_from_file_location("owner_demo_edge", OWNER_DEMO_EDGE)
        self.assertIsNotNone(edge_spec)
        self.assertIsNotNone(edge_spec.loader)
        edge = importlib.util.module_from_spec(edge_spec)
        edge_spec.loader.exec_module(edge)

        self.assertEqual(edge.target_port("/"), 8899)
        self.assertEqual(edge.target_port("/pages/member-login.html"), 8899)
        self.assertEqual(edge.target_port("/api/member/eligibility"), 8898)
        self.assertEqual(edge.target_port("/admin"), 8897)
        self.assertEqual(edge.target_port("/api/admin/session"), 8897)
        self.assertEqual(edge.target_port("/css/admin.css"), 8897)
        self.assertEqual(edge.target_port("/js/admin-pool.js"), 8897)
        self.assertEqual(edge.target_port("/assets/icons/favicon-32.png"), 8897)

        sync_spec = importlib.util.spec_from_file_location("owner_demo_sync", OWNER_DEMO_SYNC)
        self.assertIsNotNone(sync_spec)
        self.assertIsNotNone(sync_spec.loader)
        sync = importlib.util.module_from_spec(sync_spec)
        sync_spec.loader.exec_module(sync)
        with TemporaryDirectory() as temporary:
            config = Path(temporary) / "demo.env"
            config.write_text(
                "APP_BASE_URL=https://owner-demo.invalid\n"
                "NEW_GYM_PUBLIC_SITE_URL=https://owner-demo.invalid\n"
                "NEW_GYM_MEMBER_ALLOWED_ORIGINS=https://owner-demo.invalid\n"
                "SECRET_KEY=do-not-change-me\n",
                encoding="utf-8",
            )
            sync.update_env(config, "https://temporary-demo.ngrok-free.app")
            text = config.read_text(encoding="utf-8")
        self.assertIn("APP_BASE_URL=https://temporary-demo.ngrok-free.app", text)
        self.assertIn("NEW_GYM_PUBLIC_SITE_URL=https://temporary-demo.ngrok-free.app", text)
        self.assertIn("NEW_GYM_MEMBER_ALLOWED_ORIGINS=https://temporary-demo.ngrok-free.app", text)
        self.assertIn("SECRET_KEY=do-not-change-me", text)

        installer = (OWNER_DEMO_ROOT / "install-owner-demo.sh").read_text(encoding="utf-8")
        example = (OWNER_DEMO_ROOT / "owner-demo.env.example").read_text(encoding="utf-8")
        self.assertIn("ngrok config check", installer)
        self.assertIn("sync-ngrok-url.py", installer)
        self.assertIn("nfs-demo-edge", installer)
        self.assertIn("nfs-demo-ngrok", installer)
        self.assertIn("Need For Strength", example)
        self.assertIn("POOL_NAME=The Cue Master", example)
        self.assertIn("OWNER_DEMO_MODE=true", example)
        self.assertNotIn("CLOUDFLARED_TOKEN", example)
        self.assertNotIn("NGROK_AUTHTOKEN", example)

    def test_need_for_strength_owner_demo_lightweight_runtime_skips_firebase_extra(self) -> None:
        runtime = OWNER_DEMO_RUNTIME.read_text(encoding="utf-8")
        standalone = OWNER_DEMO_STANDALONE.read_text(encoding="utf-8")
        preflight = OWNER_DEMO_USB_PREFLIGHT.read_text(encoding="utf-8")

        self.assertIn('export PYTHONPATH="$REPO', runtime)
        self.assertIn("OWNER_DEMO_PYTHON", runtime)
        self.assertIn('importlib.import_module(name)', runtime)
        self.assertIn('("cryptography", "server.gravity")', runtime)
        self.assertIn("OWNER_DEMO_FIREBASE_ADMIN_PRESENT", runtime)
        self.assertNotIn("[firebase]", runtime)
        self.assertNotIn("pip install", runtime)
        self.assertNotIn("python3 -m venv", runtime)
        self.assertNotIn("setuptools", runtime)

        self.assertIn("prepare-owner-demo-runtime.sh", standalone)
        self.assertIn('export PYTHONPATH="$REPO', standalone)
        self.assertIn('PYTHON="${PYTHON:-$(command -v python3)}"', standalone)
        self.assertNotIn("prepare-python-runtime.sh", standalone)
        self.assertNotIn("[firebase]", standalone)
        self.assertNotIn(".venv/bin/python", standalone)
        self.assertIn('CLOUDFLARED="$(command -v cloudflared || true)"', standalone)
        self.assertIn("cloudflared is required for the isolated owner demo tunnel", standalone)
        self.assertIn("cloudflared tunnel --url http://127.0.0.1:8900", standalone)
        self.assertIn("trycloudflare.com", standalone)
        self.assertIn('--public-url "$public_url"', standalone)
        self.assertNotIn("wait_port_free", standalone)
        self.assertEqual(standalone.count("start_component admin server.gravity"), 1)
        self.assertEqual(standalone.count("start_component member member_gateway.py"), 1)
        web_start = standalone.index("start_component web http.server")
        edge_start = standalone.index("start_component edge demo-edge.py")
        origin_sync = standalone.index('--public-url "$public_url"')
        admin_start = standalone.index("start_component admin server.gravity")
        member_start = standalone.index("start_component member member_gateway.py")
        self.assertLess(web_start, origin_sync)
        self.assertLess(edge_start, origin_sync)
        self.assertLess(origin_sync, admin_start)
        self.assertLess(origin_sync, member_start)
        self.assertNotIn("NGROK_API", standalone)
        self.assertNotIn("nfs-owner-demo", standalone)

        self.assertIn("ownerDemoTunnelProvider", preflight)
        self.assertIn("cloudflare-quick-tunnel", preflight)
        self.assertIn("cloudflared", preflight)
        self.assertNotIn("ngrokAgentApi", preflight)
        self.assertIn("pythonCryptography", preflight)
        self.assertNotIn("pythonPackageIndex", preflight)
        self.assertNotIn("pythonVenv", preflight)
        self.assertIn('add_blocker "port_${port}_busy"', preflight)
        self.assertNotIn("ngrok config check", preflight)
        self.assertNotIn("command_sv", preflight)

    def test_need_for_strength_owner_demo_pc_deployer_is_fail_closed(self) -> None:
        script = OWNER_DEMO_PC_DEPLOYER.read_text(encoding="utf-8")
        self.assertIn("Get-CleanCommit", script)
        self.assertIn("git status --porcelain", script)
        self.assertIn("-o BatchMode=yes", script)
        self.assertIn("-o ConnectTimeout=8", script)
        self.assertIn("expected Termux user u0_a304", script)
        self.assertIn("expected Redmi model 23124RN87I", script)
        self.assertIn("usb-termux-preflight.sh", script)
        self.assertIn("usb-bootstrap-owner-demo.sh", script)
        self.assertIn("git archive --format=tar.gz", script)
        self.assertIn("Get-FileHash -Algorithm SHA256", script)
        self.assertIn("OWNER_DEMO_DEPLOYMENT=PASS", script)
        self.assertNotIn("install-owner-demo.sh", script)
        self.assertNotIn("ngrok config check", script)
        self.assertNotIn("nfs-demo-ngrok", script)
        self.assertNotIn("NGROK_AUTHTOKEN=", script)
        self.assertNotIn("CLOUDFLARED_TOKEN=", script)

    def test_need_for_strength_usb_bootstrap_preserves_existing_ngrok_tunnels(self) -> None:
        bootstrap = OWNER_DEMO_USB_BOOTSTRAP.read_text(encoding="utf-8")
        stopper = OWNER_DEMO_STOP_STANDALONE.read_text(encoding="utf-8")

        self.assertIn('EXPECTED_USER="u0_a304"', bootstrap)
        self.assertIn('EXPECTED_MODEL="23124RN87I"', bootstrap)
        self.assertIn("archive SHA-256 mismatch", bootstrap)
        self.assertIn("less than 512 MB free storage", bootstrap)
        self.assertIn("cloudflared", bootstrap)
        for port in ("8897", "8898", "8899", "8900"):
            self.assertIn(port, bootstrap)
        self.assertIn("stop-owner-demo-standalone.sh", bootstrap)
        self.assertIn("OWNER_DEMO_BOOTSTRAP=PASS", bootstrap)
        self.assertIn("SAFE_RESIDUAL_RELEASES=", bootstrap)
        self.assertIn(".nfs-owner-demo-release", bootstrap)
        self.assertIn("owner-demo app root contains unmanaged or malformed content", bootstrap)
        self.assertIn("cleanup_orphan_components", bootstrap)
        self.assertIn('*"$APP_ROOT/"*"member_gateway.py"*' , bootstrap)
        self.assertIn('*"$APP_ROOT/"*"demo-edge.py"*' , bootstrap)
        self.assertIn('*"$APP_ROOT/"*"http.server 8899"*' , bootstrap)
        self.assertIn('*"$APP_ROOT/"*"server.gravity"*' , bootstrap)
        self.assertNotIn("NGROK_API", bootstrap)
        self.assertNotIn('/api/tunnels', bootstrap)
        self.assertNotIn('DELETE "$NGROK_API', bootstrap)
        self.assertNotIn("/tmp/", bootstrap)
        self.assertNotIn("/tmp/", OWNER_DEMO_USB_PREFLIGHT.read_text(encoding="utf-8"))

        self.assertIn('TUNNEL_UPSTREAM="http://127.0.0.1:8900"', stopper)
        self.assertIn("stop_orphaned_components", stopper)
        self.assertIn('*"$APP_ROOT/"*', stopper)
        self.assertIn('cwd="$(readlink "/proc/$pid/cwd"', stopper)
        self.assertIn('case "$cwd" in "$APP_ROOT"/*)', stopper)
        self.assertIn('*"$marker"*', stopper)
        self.assertIn('stop_owned_pid_file web "http.server 8899"', stopper)
        self.assertIn("cloudflared", stopper)
        self.assertNotIn("NGROK_API", stopper)
        self.assertNotIn("command_line", stopper)
        self.assertNotIn("universal-gym-saas", stopper)
        self.assertNotIn("local-store-track", stopper)
        self.assertNotIn("universal-gym-saas", bootstrap)
        self.assertNotIn("local-store-track", bootstrap)

    def test_new_gym_local_acceptance_requires_loopback_services_and_tunnel_down(self) -> None:
        spec = importlib.util.spec_from_file_location("new_gym_acceptance", NEW_GYM_ACCEPTANCE)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        values = {
            "GRAVITY_PORT": "8897",
            "NEW_GYM_MEMBER_GATEWAY_PORT": "8898",
            "NEW_GYM_PUBLIC_PORT": "8899",
        }

        def good_runner(args, **_kwargs):
            if args[:2] == ["sv", "status"] and args[-1] == "new-gym-tunnel":
                return subprocess.CompletedProcess(args, 0, stdout="down: /service/new-gym-tunnel: 1s\n", stderr="")
            if args[:2] == ["sv", "status"]:
                stdout = "\n".join(
                    f"run: /service/{name}: (pid 100) 10s"
                    for name in (
                        "new-gym-admin",
                        "new-gym-member",
                        "new-gym-web",
                        "new-gym-health",
                        "new-gym-notifications",
                    )
                )
                return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")
            if args[:2] == ["ss", "-ltnH"]:
                return subprocess.CompletedProcess(
                    args,
                    0,
                    stdout=(
                        "LISTEN 0 5 127.0.0.1:8897 0.0.0.0:*\n"
                        "LISTEN 0 5 127.0.0.1:8898 0.0.0.0:*\n"
                        "LISTEN 0 5 127.0.0.1:8899 0.0.0.0:*\n"
                    ),
                    stderr="",
                )
            raise AssertionError(args)

        def good_probe(_url, **_kwargs):
            return True, "HTTP expected"

        good = module.run_acceptance(values, command_runner=good_runner, probe=good_probe)
        self.assertTrue(good["ready"])
        self.assertEqual(good["blockers"], [])

        def bad_runner(args, **kwargs):
            result = good_runner(args, **kwargs)
            if args[:2] == ["sv", "status"] and args[-1] == "new-gym-tunnel":
                return subprocess.CompletedProcess(args, 0, stdout="run: /service/new-gym-tunnel: (pid 1) 10s\n", stderr="")
            if args[:2] == ["ss", "-ltnH"]:
                return subprocess.CompletedProcess(
                    args,
                    0,
                    stdout=(
                        "LISTEN 0 5 0.0.0.0:8897 0.0.0.0:*\n"
                        "LISTEN 0 5 127.0.0.1:8898 0.0.0.0:*\n"
                        "LISTEN 0 5 127.0.0.1:8899 0.0.0.0:*\n"
                    ),
                    stderr="",
                )
            return result

        blocked = module.run_acceptance(values, command_runner=bad_runner, probe=good_probe)
        self.assertFalse(blocked["ready"])
        self.assertIn("tunnel_disabled", blocked["blockers"])
        self.assertIn("admin_loopback_listener", blocked["blockers"])

    def test_new_gym_installer_requires_staged_preflight_before_tunnel(self) -> None:
        profile = ROOT / "deploy" / "new-gym-termux"
        installer = (profile / "install-termux.sh").read_text(encoding="utf-8")
        backup = (profile / "backup-offdevice.sh").read_text(encoding="utf-8")
        runtime = (profile / "prepare-python-runtime.sh").read_text(encoding="utf-8")
        renderer = (profile / "render-customer-config.py").read_text(encoding="utf-8")
        verifier = (profile / "verify-public-release.py").read_text(encoding="utf-8")
        rollback = (profile / "rollback-public-site.sh").read_text(encoding="utf-8")
        web_service = (profile / "services" / "new-gym-web" / "run").read_text(encoding="utf-8")
        preflight = (profile / "preflight-new-gym.py").read_text(encoding="utf-8")
        example = (profile / "new-gym.env.example").read_text(encoding="utf-8")
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("preflight-new-gym.py", installer)
        self.assertIn("--stage install", installer)
        self.assertIn("--stage launch", installer)
        self.assertIn("acceptance-new-gym.py", installer)
        self.assertLess(installer.index("--stage launch"), installer.index("acceptance-new-gym.py"))
        self.assertLess(installer.index("acceptance-new-gym.py"), installer.index("sv-enable new-gym-tunnel"))
        self.assertIn("prepare-python-runtime.sh", installer)
        self.assertIn("python-cryptography", installer)
        self.assertIn("python3 -m venv --system-site-packages", runtime)
        self.assertIn('pip install --upgrade -e "$REPO[firebase]"', runtime)
        self.assertIn('"firebase_admin"', runtime)
        self.assertIn('"server.gravity"', runtime)
        self.assertLess(installer.index("prepare-python-runtime.sh"), installer.index("install_service()"))
        self.assertIn('GRAVITY_PYTHON=', example)
        self.assertNotIn('GRAVITY_PYTHON=/data/data/', example)
        self.assertIn('name = "new-gym-platform"', pyproject)
        self.assertIn("prepare_public_release", installer)
        self.assertIn("render-customer-config.py", installer)
        self.assertIn("--require-complete", installer)
        self.assertLess(installer.index("prepare_public_release true"), installer.index("--stage launch"))
        self.assertIn("NEW_GYM_PUBLIC_ROOT", web_service)
        self.assertIn(".local/share/new-gym/", web_service)
        self.assertNotIn("customer-website/web", web_service)
        self.assertIn("NEW_GYM_PUBLIC_CONFIG_PATH", preflight)
        self.assertIn("membershipPricesPaise", renderer)
        self.assertIn(".new-gym-release.json", installer)
        self.assertIn("verify-public-release.py", installer)
        self.assertIn("customerConfigSha256", verifier)
        self.assertIn("GRAVITY_MARKERS", verifier)
        self.assertIn("verify-public-release.py", rollback)
        self.assertIn("sv restart new-gym-web", rollback)
        self.assertIn('case "$release_id"', rollback)
        for key in (
            "NEW_GYM_MEMBERSHIP_PRICING_CONFIRMED=false",
            "NEW_GYM_POOL_RATES_CONFIRMED=false",
            "NEW_GYM_KITCHEN_SETUP_CONFIRMED=false",
            "NEW_GYM_OFFDEVICE_BACKUP_MARKER=",
            "NEW_GYM_BACKUP_MAX_AGE_SECONDS=86400",
            "NEW_GYM_PUBLIC_SITE_URL=",
            "NEW_GYM_PUBLIC_ROOT=",
            "NEW_GYM_PUBLIC_CONFIG_PATH=",
            "BUSINESS_CITY=",
            "BUSINESS_OPENING_HOURS=",
        ):
            self.assertIn(key, example)
        self.assertIn("rclone check", backup)
        self.assertIn("archiveSha256", backup)
        self.assertIn("offdeviceMarker=", backup)
        self.assertLess(backup.index("rclone check"), backup.index("offdeviceMarker="))

    def test_new_gym_firebase_aliases_are_not_bound_to_gravity(self) -> None:
        for path in (ROOT / ".firebaserc", ROOT.parent / "customer-website" / ".firebaserc"):
            text = path.read_text(encoding="utf-8")
            self.assertIn('"projects": {}', text, path)
            for marker in ("gravityfitnessnmh", "gravity-authe"):
                self.assertNotIn(marker, text, path)

    def test_new_gym_member_gateway_has_no_gravity_live_endpoints(self) -> None:
        gateway = (ROOT.parent / "customer-website" / "gateway" / "member_gateway.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("NEW_GYM_MEMBER_GATEWAY_PORT", gateway)
        self.assertIn("NEW_GYM_MEMBER_ALLOWED_ORIGINS", gateway)
        self.assertIn("http://127.0.0.1:8897", gateway)
        for marker in (
            "gravityfitnessnmh",
            "gravity-authe",
            "917999526112",
            "foyer-amenity-staff.ngrok-free.dev",
        ):
            self.assertNotIn(marker, gateway)


if __name__ == "__main__":
    unittest.main()
