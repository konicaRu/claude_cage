import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import Mock, patch

SOURCE = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'microphone_bridge.py'
spec = importlib.util.spec_from_file_location('microphone_bridge', SOURCE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.controller = bridge.Controller(pathlib.Path(self.temp.name), Mock())

    def test_stop_terminates_every_child_even_when_one_is_already_dead(self):
        alive, dead = Mock(), Mock()
        alive.poll.return_value = None
        dead.poll.return_value = 0
        self.controller.children = [alive, dead]
        self.controller.stop_children()
        alive.terminate.assert_called_once()
        alive.wait.assert_called_once()
        dead.terminate.assert_not_called()
        self.assertEqual(self.controller.children, [])

    def test_hung_child_is_killed_and_reaped(self):
        import subprocess
        child = Mock()
        child.poll.return_value = None
        child.wait.side_effect = [subprocess.TimeoutExpired('child', 3), 0]
        self.controller.children = [child]
        self.controller.stop_children()
        child.kill.assert_called_once()
        self.assertEqual(child.wait.call_count, 2)

    def test_cleanup_uses_owner_to_avoid_touching_another_bridge(self):
        self.controller.owner = 'test-owner'
        self.controller.cleanup()
        script = self.controller.guest.call_args.args[0]
        self.assertIn('test-owner', script)
        self.assertIn('/run/cage-mic-bridge/owner', script)

    def test_setup_keeps_original_audio_configuration_and_watchdog(self):
        script = bridge.setup_script('owner123')
        self.assertIn('.include /etc/claude-cage/audio.pa', script)
        self.assertIn('module-pipe-source', script)
        self.assertIn('--on-unit-active=30s', script)
        self.assertIn('90', bridge.WATCHDOG)
        self.assertIn('test ! -e /run/cage-mic-bridge', script)
        self.assertNotIn('tee /etc/', script)

    def test_runtime_lease_renewal_rejects_missing_owner(self):
        script = bridge.heartbeat_script('owner123')
        self.assertIn('owner123', script)
        self.assertIn('set -eu', script)
        self.assertIn('date +%s', script)
        self.assertIn('sudo mv /run/cage-mic-bridge/lease.new /run/cage-mic-bridge/lease', script)

    def test_duplicate_lock_does_not_modify_existing_stop_request(self):
        lock = bridge.InstanceLock(pathlib.Path(self.temp.name) / 'lock')
        second = bridge.InstanceLock(pathlib.Path(self.temp.name) / 'lock')
        with lock:
            with self.assertRaises(bridge.AlreadyRunning):
                with second:
                    pass

    def test_stop_kills_capture_job_without_waiting_for_guest_command(self):
        self.controller.job = Mock()
        self.controller.request_stop()
        self.assertTrue(self.controller.stop_event.is_set())
        self.controller.job.close.assert_called_once()

    def test_cancellation_prevents_new_microphone_process(self):
        self.controller.stop_event.set()
        with patch.object(bridge.subprocess, 'Popen') as popen:
            with self.assertRaises(bridge.StopRequested):
                self.controller.spawn(['ffmpeg'])
            popen.assert_not_called()


class AutomaticTests(unittest.TestCase):
    def setUp(self):
        self.factory = Mock()
        self.thread_factory = Mock()
        self.thread_factory.return_value.is_alive.return_value = True
        self.auto = bridge.AutomaticBridge(self.factory, self.thread_factory)

    def test_waits_for_both_cage_and_linux(self):
        self.auto.update(False, True)
        self.auto.update(True, False)
        self.factory.assert_not_called()

    def test_starts_once_when_cage_and_linux_are_ready(self):
        self.auto.update(True, True)
        self.auto.update(True, True)
        self.factory.assert_called_once()
        self.thread_factory.return_value.start.assert_called_once()

    def test_stops_capture_when_cage_exits_or_guest_stops(self):
        for app, guest in ((False, True), (True, False)):
            self.factory.reset_mock()
            auto = bridge.AutomaticBridge(self.factory, self.thread_factory)
            auto.update(True, True)
            auto.update(app, guest)
            self.factory.return_value.request_stop.assert_called_once()

    def test_does_not_restart_while_previous_controller_is_stopping(self):
        self.auto.update(True, True)
        self.auto.update(False, True)
        self.auto.update(True, True)
        self.factory.assert_called_once()

    def test_completed_attempt_waits_before_retrying(self):
        self.auto.update(True, True)
        self.thread_factory.return_value.is_alive.return_value = False
        self.auto.update(True, True)
        self.auto.update(True, True)
        self.factory.assert_called_once()

    def test_microphone_preflight_failure_leaves_guest_audio_untouched(self):
        controller = bridge.Controller(guest=Mock())
        process = Mock()
        process.communicate.return_value = (b'', b'device unavailable')
        process.returncode = 1
        with patch.object(controller, 'spawn', return_value=process):
            with self.assertRaisesRegex(RuntimeError, 'Realtek'):
                controller.preflight('ffmpeg')
        controller.guest.assert_not_called()


if __name__ == '__main__':
    unittest.main()
