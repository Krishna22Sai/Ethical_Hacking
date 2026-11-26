"""
Comprehensive End-to-End Verification of PhishAwareLab Event Connections
Traces every event: UI Action -> JS Request -> Flask Route -> Data Update -> JSON Persistence -> Dashboard Refresh.
Confirms independent telemetry, duplicate rejection, and data integrity.
Preserves and restores original data.json at start and end.
"""
import os
import json
import time
import unittest
from app import app, DATA_FILE

class TestPhishAwareLabEventConnections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            cls.original_data_backup = f.read()

    @classmethod
    def tearDownClass(cls):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            f.write(cls.original_data_backup)
        print("\n[INFO] Preserved original data.json successfully restored.")

    def setUp(self):
        self.client = app.test_client()
        # Reset baseline for clean assertion arithmetic: 30, 22, 14, 8
        self.client.post('/api/reset-demo')

    def test_01_sent_via_dashboard_and_invite_endpoints(self):
        """Test Sent: Dashboard control & Invite dispatch increment ONLY Sent."""
        stats_start = self.client.get('/api/stats').get_json()['stats']

        # 1. Dashboard Generate Sent Event (POST /api/event/sent)
        res_btn = self.client.post('/api/event/sent', json={'type': 'sent'})
        self.assertEqual(res_btn.status_code, 200)
        self.assertTrue(res_btn.get_json()['success'])

        stats_1 = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_1['sent'], stats_start['sent'] + 1)
        self.assertEqual(stats_1['opened'], stats_start['opened'])
        self.assertEqual(stats_1['clicked'], stats_start['clicked'])
        self.assertEqual(stats_1['submitted'], stats_start['submitted'])

        # 2. Email Invite Dispatch (POST /api/invite/send with dry_run)
        res_invite = self.client.post('/api/invite/send', json={
            'recipient_email': 'volunteer_flow_test@example.com',
            'custom_note': 'Audit verification',
            'dry_run': True
        })
        self.assertEqual(res_invite.status_code, 200)
        self.assertTrue(res_invite.get_json()['dry_run'])

        stats_2 = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_2['sent'], stats_1['sent'] + 1)
        self.assertEqual(stats_2['opened'], stats_start['opened'])
        self.assertEqual(stats_2['clicked'], stats_start['clicked'])
        self.assertEqual(stats_2['submitted'], stats_start['submitted'])
        print(f"✓ Event 1 (Sent) Verified: Incremented Sent ({stats_start['sent']} -> {stats_2['sent']}), all others unchanged.")

    def test_02_opened_via_independent_demo_control(self):
        """Test Opened: Disclosed manual/demo control increments ONLY Opened."""
        stats_start = self.client.get('/api/stats').get_json()['stats']

        # Trigger Opened demo control (POST /api/event/opened)
        res = self.client.post('/api/event/opened', json={'type': 'opened'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn("Demo/Manual", data['event']['action'])

        stats_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_after['opened'], stats_start['opened'] + 1)
        self.assertEqual(stats_after['sent'], stats_start['sent'])
        self.assertEqual(stats_after['clicked'], stats_start['clicked'])
        self.assertEqual(stats_after['submitted'], stats_start['submitted'])
        print(f"✓ Event 2 (Opened) Verified: Incremented Opened ({stats_start['opened']} -> {stats_after['opened']}), all others unchanged.")

    def test_03_clicked_via_disclosed_training_link(self):
        """Test Clicked: Disclosed training link arrival increments ONLY Clicked."""
        stats_start = self.client.get('/api/stats').get_json()['stats']

        # Disclosed training portal link arrival (POST /api/training/event with type: 'clicked')
        res_link = self.client.post('/api/training/event', json={
            'type': 'clicked',
            'volunteer_id': 'Volunteer FlowClick'
        })
        self.assertEqual(res_link.status_code, 200)
        data_link = res_link.get_json()
        self.assertTrue(data_link['success'])
        self.assertFalse(data_link['duplicate'])

        stats_1 = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_1['clicked'], stats_start['clicked'] + 1)
        self.assertEqual(stats_1['sent'], stats_start['sent'])
        self.assertEqual(stats_1['opened'], stats_start['opened'])
        self.assertEqual(stats_1['submitted'], stats_start['submitted'])

        # Dashboard Generate Clicked Event (POST /api/event/clicked)
        res_dash = self.client.post('/api/event/clicked', json={'type': 'clicked'})
        self.assertEqual(res_dash.status_code, 200)
        self.assertTrue(res_dash.get_json()['success'])

        stats_2 = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_2['clicked'], stats_1['clicked'] + 1)
        self.assertEqual(stats_2['sent'], stats_start['sent'])
        self.assertEqual(stats_2['opened'], stats_start['opened'])
        self.assertEqual(stats_2['submitted'], stats_start['submitted'])
        print(f"✓ Event 3 (Clicked) Verified: Incremented Clicked ({stats_start['clicked']} -> {stats_2['clicked']}), all others unchanged.")

    def test_04_completed_via_training_activity_completion(self):
        """Test Completed: Voluntary red-flag training completion increments ONLY Completed."""
        stats_start = self.client.get('/api/stats').get_json()['stats']

        # Voluntary training completion (POST /api/training/event with type: 'complete')
        res_comp = self.client.post('/api/training/event', json={
            'type': 'complete',
            'volunteer_id': 'Volunteer FlowComplete'
        })
        self.assertEqual(res_comp.status_code, 200)
        data_comp = res_comp.get_json()
        self.assertTrue(data_comp['success'])
        self.assertFalse(data_comp['duplicate'])

        stats_1 = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_1['submitted'], stats_start['submitted'] + 1)
        self.assertEqual(stats_1['sent'], stats_start['sent'])
        self.assertEqual(stats_1['opened'], stats_start['opened'])
        self.assertEqual(stats_1['clicked'], stats_start['clicked'])

        # Dashboard Generate Completed Event (POST /api/event/completed)
        res_dash = self.client.post('/api/event/completed', json={'type': 'completed'})
        self.assertEqual(res_dash.status_code, 200)
        self.assertTrue(res_dash.get_json()['success'])

        stats_2 = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_2['submitted'], stats_1['submitted'] + 1)
        self.assertEqual(stats_2['sent'], stats_start['sent'])
        self.assertEqual(stats_2['opened'], stats_start['opened'])
        self.assertEqual(stats_2['clicked'], stats_start['clicked'])
        print(f"✓ Event 4 (Completed) Verified: Incremented Completed ({stats_start['submitted']} -> {stats_2['submitted']}), all others unchanged.")

    def test_05_recent_activity_and_json_persistence(self):
        """Test Persistence & Activity Log: events are persisted to data.json with full metadata."""
        self.client.post('/api/event/sent', json={'type': 'sent'})
        self.client.post('/api/event/opened', json={'type': 'opened'})
        self.client.post('/api/training/event', json={'type': 'clicked', 'volunteer_id': 'Volunteer FlowAudit'})
        self.client.post('/api/training/event', json={'type': 'complete', 'volunteer_id': 'Volunteer FlowAudit2'})

        # Verify disk persistence directly from file
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            disk_data = json.load(f)

        stats = disk_data['stats']
        self.assertEqual(stats['sent'], 31)
        self.assertEqual(stats['opened'], 23)
        self.assertEqual(stats['clicked'], 15)
        self.assertEqual(stats['submitted'], 9)

        recent = disk_data['recent_activity']
        types_logged = [item['type'] for item in recent[:4]]
        self.assertIn('completed', types_logged)
        self.assertIn('clicked', types_logged)
        self.assertIn('opened', types_logged)
        self.assertIn('sent', types_logged)
        print("✓ Persistence & Activity Feed Verified: data.json contains accurate counts and recent activities.")

    def test_06_polling_and_page_refreshes_produce_zero_drift(self):
        """Test Zero Drift: polling and navigating pages do not create phantom events."""
        stats_initial = self.client.get('/api/stats').get_json()['stats']

        # Load all pages multiple times
        for _ in range(5):
            self.assertEqual(self.client.get('/').status_code, 200)
            self.assertEqual(self.client.get('/training').status_code, 200)
            self.assertEqual(self.client.get('/invite').status_code, 200)

        # 15 polling cycles
        for _ in range(15):
            self.assertEqual(self.client.get('/api/stats').status_code, 200)

        stats_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_initial, stats_after)
        print("✓ Zero Drift Verified: 15 polling cycles and 15 page reloads produced zero count changes.")

    def test_07_duplicate_prevention(self):
        """Test Deduplication: immediate duplicate submission does not increment counter."""
        res1 = self.client.post('/api/training/event', json={'type': 'complete', 'volunteer_id': 'Volunteer DedupCheck'})
        self.assertEqual(res1.status_code, 200)
        self.assertFalse(res1.get_json()['duplicate'])
        count_1 = res1.get_json()['stats']['submitted']

        res2 = self.client.post('/api/training/event', json={'type': 'complete', 'volunteer_id': 'Volunteer DedupCheck'})
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.get_json()['duplicate'])
        count_2 = res2.get_json()['stats']['submitted']
        self.assertEqual(count_1, count_2)
        print(f"✓ Deduplication Verified: Duplicate event detected and counter was not double-incremented ({count_1}).")

if __name__ == '__main__':
    unittest.main()
