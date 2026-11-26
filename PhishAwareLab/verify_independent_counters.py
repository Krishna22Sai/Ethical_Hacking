"""
Verification Suite for PhishAwareLab Independent Counters & Telemetry Integrity
Tests independent event increments, absence of artificial progression,
duplicate rejection, polling safety, reset behavior, and data persistence.
Guarantees preservation and restoration of original user data.
"""
import os
import json
import time
import unittest
from app import app, DATA_FILE

class TestIndependentCounters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Save snapshot of actual data.json to restore at the very end
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            cls.original_data_backup = f.read()

    @classmethod
    def tearDownClass(cls):
        # Guarantee restoration of the exact user data
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            f.write(cls.original_data_backup)
        print("\n[INFO] Restored original data.json successfully.")

    def setUp(self):
        self.client = app.test_client()
        # Reset to known baseline (30, 22, 14, 8) for clean predictable assertions
        self.client.post('/api/reset-demo')

    def tearDown(self):
        pass

    def test_01_sent_changes_only_sent(self):
        """Test 1: Sent increments ONLY Sent (Opened, Clicked, Completed unchanged)."""
        res_before = self.client.get('/api/stats').get_json()['stats']
        
        # Test synthetic sent endpoint
        res = self.client.post('/api/event/sent')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])
        
        res_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(res_after['sent'], res_before['sent'] + 1, "Sent should increment by 1")
        self.assertEqual(res_after['opened'], res_before['opened'], "Opened must remain unchanged")
        self.assertEqual(res_after['clicked'], res_before['clicked'], "Clicked must remain unchanged")
        self.assertEqual(res_after['submitted'], res_before['submitted'], "Submitted must remain unchanged")
        print(f"✓ Test 1a Passed: Sent incremented ({res_before['sent']} -> {res_after['sent']}), all others unchanged")

        # Test dry-run invitation sent
        res_invite = self.client.post('/api/invite/send', json={
            'recipient_email': 'volunteer_test@example.com',
            'dry_run': True
        })
        self.assertEqual(res_invite.status_code, 200)
        body = res_invite.get_json()
        self.assertTrue(body['success'])
        self.assertTrue(body['dry_run'])
        self.assertIn("Test Mode", body['event']['details'])

        res_after_invite = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(res_after_invite['sent'], res_after['sent'] + 1)
        self.assertEqual(res_after_invite['opened'], res_before['opened'])
        self.assertEqual(res_after_invite['clicked'], res_before['clicked'])
        self.assertEqual(res_after_invite['submitted'], res_before['submitted'])
        print(f"✓ Test 1b Passed: Dry run invitation incremented Sent only ({res_after['sent']} -> {res_after_invite['sent']}) with Test Mode label")

    def test_02_opened_changes_only_opened(self):
        """Test 2: Opened increments ONLY Opened (Sent, Clicked, Completed unchanged)."""
        res_before = self.client.get('/api/stats').get_json()['stats']
        
        res = self.client.post('/api/event/opened')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])
        
        res_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(res_after['opened'], res_before['opened'] + 1, "Opened should increment by 1")
        self.assertEqual(res_after['sent'], res_before['sent'], "Sent must remain unchanged")
        self.assertEqual(res_after['clicked'], res_before['clicked'], "Clicked must remain unchanged")
        self.assertEqual(res_after['submitted'], res_before['submitted'], "Submitted must remain unchanged")
        print(f"✓ Test 2 Passed: Opened incremented ({res_before['opened']} -> {res_after['opened']}), all others unchanged")

    def test_03_clicked_changes_only_clicked(self):
        """Test 3: Clicked increments ONLY Clicked (Sent, Opened, Completed unchanged)."""
        res_before = self.client.get('/api/stats').get_json()['stats']
        
        res = self.client.post('/api/event/clicked')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])
        
        res_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(res_after['clicked'], res_before['clicked'] + 1, "Clicked should increment by 1")
        self.assertEqual(res_after['sent'], res_before['sent'], "Sent must remain unchanged")
        self.assertEqual(res_after['opened'], res_before['opened'], "Opened must remain unchanged")
        self.assertEqual(res_after['submitted'], res_before['submitted'], "Submitted must remain unchanged")
        print(f"✓ Test 3 Passed: Clicked incremented ({res_before['clicked']} -> {res_after['clicked']}), all others unchanged")

    def test_04_completed_changes_only_completed(self):
        """Test 4: Training completion increments ONLY Completed (Sent, Opened, Clicked unchanged)."""
        res_before = self.client.get('/api/stats').get_json()['stats']
        
        res = self.client.post('/api/training/event', json={
            'type': 'complete',
            'volunteer_id': 'Volunteer 101'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])
        
        res_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(res_after['submitted'], res_before['submitted'] + 1, "Completed/Submitted should increment by 1")
        self.assertEqual(res_after['sent'], res_before['sent'], "Sent must remain unchanged")
        self.assertEqual(res_after['opened'], res_before['opened'], "Opened must remain unchanged")
        self.assertEqual(res_after['clicked'], res_before['clicked'], "Clicked must remain unchanged")
        print(f"✓ Test 4 Passed: Completed incremented ({res_before['submitted']} -> {res_after['submitted']}), all others unchanged")

    def test_05_no_artificial_progression_even_when_completed_exceeds_others(self):
        """Test 5: Completed count can rise without artificially bumping Clicked, Opened, or Sent."""
        # Baseline is 30, 22, 14, 8.
        # Fire 10 completions in a row: Completed becomes 18, which is > Clicked (14).
        for i in range(10):
            res = self.client.post('/api/training/event', json={
                'type': 'complete',
                'volunteer_id': f'ProgressionTest_{i}'
            })
            self.assertEqual(res.status_code, 200)

        stats = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats['submitted'], 18, "Submitted should be exactly 8 + 10 = 18")
        self.assertEqual(stats['clicked'], 14, "Clicked must remain 14, NOT artificially bumped to 18")
        self.assertEqual(stats['opened'], 22, "Opened must remain 22")
        self.assertEqual(stats['sent'], 30, "Sent must remain 30")
        print(f"✓ Test 5 Passed: No artificial progression! Completed is {stats['submitted']} while Clicked is {stats['clicked']}")

    def test_06_refreshes_and_page_visits_do_not_alter_counts(self):
        """Test 6: Refreshing dashboard or training page does NOT fabricate events or increments."""
        stats_before = self.client.get('/api/stats').get_json()['stats']

        # Visit dashboard, training, and invite multiple times
        for _ in range(5):
            self.assertEqual(self.client.get('/').status_code, 200)
            self.assertEqual(self.client.get('/training').status_code, 200)
            self.assertEqual(self.client.get('/invite').status_code, 200)

        # Informational visit API call
        visit_res = self.client.post('/api/training/event', json={'type': 'visit', 'volunteer_id': 'Volunteer 55'})
        self.assertEqual(visit_res.status_code, 200)
        self.assertEqual(visit_res.get_json()['event_type'], 'visit')

        stats_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_before, stats_after, "Page loads and informational visits must not alter statistics")
        print(f"✓ Test 6 Passed: Refreshes and portal visits produced zero counter drift: {stats_after}")

    def test_07_polling_cycles_do_not_increase_counts(self):
        """Test 7: 20 polling cycles of /api/stats do not change counts."""
        stats_start = self.client.get('/api/stats').get_json()['stats']
        for _ in range(20):
            res = self.client.get('/api/stats')
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.get_json()['stats'], stats_start)
        print("✓ Test 7 Passed: 20 polling cycles completed with zero counter changes")

    def test_08_duplicate_event_rejection(self):
        """Test 8: Duplicate events within deduplication window are rejected."""
        res1 = self.client.post('/api/training/event', json={
            'type': 'complete',
            'volunteer_id': 'Volunteer DedupTest'
        })
        self.assertEqual(res1.status_code, 200)
        self.assertFalse(res1.get_json().get('duplicate', False))
        submitted_before = res1.get_json()['stats']['submitted']

        # Immediate repeat
        res2 = self.client.post('/api/training/event', json={
            'type': 'complete',
            'volunteer_id': 'Volunteer DedupTest'
        })
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.get_json().get('duplicate', False))
        self.assertEqual(res2.get_json()['stats']['submitted'], submitted_before)
        print("✓ Test 8 Passed: Rapid duplicate event correctly detected and counter was not double-incremented")

    def test_09_disk_persistence(self):
        """Test 9: Events persist accurately to data.json."""
        self.client.post('/api/event/sent')
        self.client.post('/api/event/opened')
        stats_api = self.client.get('/api/stats').get_json()['stats']

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            disk_data = json.load(f)

        self.assertEqual(disk_data['stats'], stats_api)
        print(f"✓ Test 9 Passed: Disk data matches API stats ({disk_data['stats']})")

    def test_10_reset_demo_restores_baseline(self):
        """Test 10: Reset Demo cleanly restores baseline (30, 22, 14, 8)."""
        self.client.post('/api/event/sent')
        self.client.post('/api/event/clicked')
        
        res = self.client.post('/api/reset-demo')
        self.assertEqual(res.status_code, 200)
        stats = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats['sent'], 30)
        self.assertEqual(stats['opened'], 22)
        self.assertEqual(stats['clicked'], 14)
        self.assertEqual(stats['submitted'], 8)
        print("✓ Test 10 Passed: Reset demo cleanly restores baseline (30, 22, 14, 8)")

    def test_11_invalid_event_types_rejected(self):
        """Test 11: Invalid event types return HTTP 400."""
        res = self.client.post('/api/event/unknown_hack')
        self.assertEqual(res.status_code, 400)
        res_train = self.client.post('/api/training/event', json={'type': 'corrupt_type'})
        self.assertEqual(res_train.status_code, 400)
        print("✓ Test 11 Passed: Invalid event requests correctly return HTTP 400")

if __name__ == '__main__':
    unittest.main()
