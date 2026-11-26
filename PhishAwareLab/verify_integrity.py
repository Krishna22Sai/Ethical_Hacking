"""
Verification script for PhishAwareLab Event Tracking and Data Integrity
Tests 1 through 12 exactly as specified in requirements.
"""
import os
import json
import time
import unittest
from app import app, DATA_FILE, DEFAULT_DATA, reset_demo

class TestPhishAwareLabIntegrity(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Reset to baseline before running test suite
        with app.app_context():
            self.client.post('/api/reset-demo')

    def tearDown(self):
        # Restore clean baseline after tests
        with app.app_context():
            self.client.post('/api/reset-demo')

    def test_01_baseline_statistics_load_correctly(self):
        """Test 1: Baseline statistics load correctly (30, 22, 14, 8)."""
        res = self.client.get('/api/stats')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        stats = data['stats']
        self.assertEqual(stats['sent'], 30, f"Expected 30 sent, got {stats['sent']}")
        self.assertEqual(stats['opened'], 22, f"Expected 22 opened, got {stats['opened']}")
        self.assertEqual(stats['clicked'], 14, f"Expected 14 clicked, got {stats['clicked']}")
        self.assertEqual(stats['submitted'], 8, f"Expected 8 submitted, got {stats['submitted']}")
        print("✓ Test 1 Passed: Baseline statistics are (30, 22, 14, 8)")

    def test_02_generate_sent_event(self):
        """Test 2: Generate a Sent event -> Sent increases by exactly 1."""
        res_before = self.client.get('/api/stats').get_json()['stats']
        res = self.client.post('/api/event/sent')
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body['success'])
        
        res_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(res_after['sent'], res_before['sent'] + 1)
        self.assertEqual(res_after['opened'], res_before['opened'])
        self.assertEqual(res_after['clicked'], res_before['clicked'])
        self.assertEqual(res_after['submitted'], res_before['submitted'])
        print(f"✓ Test 2 Passed: Sent increased from {res_before['sent']} to {res_after['sent']}")

    def test_03_generate_opened_event(self):
        """Test 3: Generate an Opened event -> Opened increases by exactly 1."""
        res_before = self.client.get('/api/stats').get_json()['stats']
        res = self.client.post('/api/event/opened')
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body['success'])
        
        res_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(res_after['opened'], res_before['opened'] + 1)
        self.assertEqual(res_after['sent'], res_before['sent'])
        self.assertEqual(res_after['clicked'], res_before['clicked'])
        self.assertEqual(res_after['submitted'], res_before['submitted'])
        print(f"✓ Test 3 Passed: Opened increased from {res_before['opened']} to {res_after['opened']}")

    def test_04_generate_clicked_event(self):
        """Test 4: Generate a Clicked demo event -> Clicked increases by exactly 1."""
        res_before = self.client.get('/api/stats').get_json()['stats']
        res = self.client.post('/api/event/clicked')
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body['success'])
        
        res_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(res_after['clicked'], res_before['clicked'] + 1)
        self.assertEqual(res_after['sent'], res_before['sent'])
        self.assertEqual(res_after['opened'], res_before['opened'])
        self.assertEqual(res_after['submitted'], res_before['submitted'])
        print(f"✓ Test 4 Passed: Clicked increased from {res_before['clicked']} to {res_after['clicked']}")

    def test_05_complete_training_activity(self):
        """Test 5: Complete the training activity -> Simulated Submissions increases by exactly 1."""
        res_before = self.client.get('/api/stats').get_json()['stats']
        res = self.client.post('/api/training/event', json={
            'type': 'complete',
            'volunteer_id': 'Volunteer 77'
        })
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body['success'])
        self.assertFalse(body.get('duplicate', False))
        
        res_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(res_after['submitted'], res_before['submitted'] + 1)
        print(f"✓ Test 5 Passed: Simulated Submissions increased from {res_before['submitted']} to {res_after['submitted']}")

    def test_06_recent_activity_records_each_event(self):
        """Test 6: Recent Activity records each event."""
        # Generate sent, opened, clicked, completed
        self.client.post('/api/event/sent')
        self.client.post('/api/event/opened')
        self.client.post('/api/event/clicked')
        self.client.post('/api/training/event', json={'type': 'complete', 'volunteer_id': 'Volunteer 88'})

        res = self.client.get('/api/stats')
        activities = res.get_json()['recent_activity']
        types_recorded = [a['type'] for a in activities[:4]]
        self.assertIn('completed', types_recorded)
        self.assertIn('clicked', types_recorded)
        self.assertIn('opened', types_recorded)
        self.assertIn('sent', types_recorded)
        
        # Verify fields in each record
        for act in activities[:4]:
            self.assertIn('id', act)
            self.assertIn('user', act)
            self.assertIn('action', act)
            self.assertIn('timestamp', act)
            self.assertIn('details', act)
        print("✓ Test 6 Passed: Recent Activity accurately recorded every event type with full metadata")

    def test_07_refresh_dashboard_counts_remain_unchanged(self):
        """Test 7: Refresh dashboard -> counts remain unchanged."""
        # Advance state
        self.client.post('/api/event/sent')
        self.client.post('/api/event/opened')
        stats_initial = self.client.get('/api/stats').get_json()['stats']
        
        # Simulate loading the dashboard page multiple times (GET /)
        for _ in range(5):
            page_res = self.client.get('/')
            self.assertEqual(page_res.status_code, 200)
        
        stats_refreshed = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_initial, stats_refreshed)
        print(f"✓ Test 7 Passed: Dashboard page refreshes did not alter counts: {stats_refreshed}")

    def test_08_restart_flask_saved_counts_remain_unchanged(self):
        """Test 8: Restart Flask -> saved counts remain unchanged."""
        # Modify stats and verify persistence in data.json
        self.client.post('/api/event/sent')
        self.client.post('/api/event/opened')
        self.client.post('/api/event/clicked')
        stats_before_restart = self.client.get('/api/stats').get_json()['stats']

        # Simulate fresh app startup by re-reading directly from data.json file
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            disk_data = json.load(f)
        
        self.assertEqual(disk_data['stats'], stats_before_restart)
        print(f"✓ Test 8 Passed: Data file on disk matches memory state: {disk_data['stats']}")

    def test_09_dashboard_polling_counts_do_not_increase(self):
        """Test 9: Dashboard polling for at least 20 cycles -> counts do not increase automatically."""
        stats_initial = self.client.get('/api/stats').get_json()['stats']
        for cycle in range(25):
            poll_res = self.client.get('/api/stats')
            self.assertEqual(poll_res.status_code, 200)
            stats_polled = poll_res.get_json()['stats']
            self.assertEqual(stats_initial, stats_polled)
        print(f"✓ Test 9 Passed: 25 polling cycles executed, counts remained exactly {stats_initial}")

    def test_10_duplicate_event_does_not_create_duplicate_count(self):
        """Test 10: Duplicate event -> does not create unintended duplicate count."""
        # Submit first completion
        res1 = self.client.post('/api/training/event', json={
            'type': 'complete',
            'volunteer_id': 'Volunteer 99'
        })
        self.assertEqual(res1.status_code, 200)
        self.assertFalse(res1.get_json().get('duplicate', False))
        submitted_count = res1.get_json()['stats']['submitted']

        # Submit immediate duplicate completion with same volunteer ID
        res2 = self.client.post('/api/training/event', json={
            'type': 'complete',
            'volunteer_id': 'Volunteer 99'
        })
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.get_json().get('duplicate', True))
        self.assertEqual(res2.get_json()['stats']['submitted'], submitted_count)

        # Check /api/stats
        stats_after = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats_after['submitted'], submitted_count)
        print(f"✓ Test 10 Passed: Duplicate event was detected and rejected from incrementing counter ({submitted_count})")

    def test_11_reset_demo_restores_baseline(self):
        """Test 11: Reset Demo -> restores intended clean demo state (30, 22, 14, 8)."""
        # Change stats
        self.client.post('/api/event/sent')
        self.client.post('/api/event/opened')
        self.client.post('/api/event/clicked')
        self.client.post('/api/event/completed')

        # Trigger Reset Demo
        res = self.client.post('/api/reset-demo')
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body['success'])

        stats = self.client.get('/api/stats').get_json()['stats']
        self.assertEqual(stats['sent'], 30)
        self.assertEqual(stats['opened'], 22)
        self.assertEqual(stats['clicked'], 14)
        self.assertEqual(stats['submitted'], 8)
        print("✓ Test 11 Passed: Reset demo cleanly restored baseline (30, 22, 14, 8)")

    def test_12_statistics_chart_and_records_remain_consistent(self):
        """Test 12: All statistics, chart values, and stored records remain consistent."""
        self.client.post('/api/event/sent')
        self.client.post('/api/event/opened')
        self.client.post('/api/event/clicked')
        self.client.post('/api/training/event', json={'type': 'complete', 'volunteer_id': 'Volunteer 50'})

        data = self.client.get('/api/stats').get_json()
        stats = data['stats']
        sent, opened, clicked, submitted = stats['sent'], stats['opened'], stats['clicked'], stats['submitted']

        # Rule: Sent >= Opened >= Clicked >= Submitted
        self.assertGreaterEqual(sent, opened)
        self.assertGreaterEqual(opened, clicked)
        self.assertGreaterEqual(clicked, submitted)

        # Rates calculation consistency
        expected_open_rate = round((opened / sent * 100), 1)
        expected_click_rate = round((clicked / sent * 100), 1)
        expected_submit_rate = round((submitted / sent * 100), 1)

        self.assertEqual(stats['open_rate'], expected_open_rate)
        self.assertEqual(stats['click_rate'], expected_click_rate)
        self.assertEqual(stats['submit_rate'], expected_submit_rate)

        # Check data.json on disk matches returned stats
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            disk_data = json.load(f)
        self.assertEqual(disk_data['stats'], stats)

        print(f"✓ Test 12 Passed: Funnel constraint {sent} >= {opened} >= {clicked} >= {submitted} and rates are consistent")

    def test_13_invalid_event_types_rejected(self):
        """Test 13: Invalid event types are rejected with 400."""
        res1 = self.client.post('/api/event/invalid_event_type')
        self.assertEqual(res1.status_code, 400)
        
        res2 = self.client.post('/api/training/event', json={'type': 'malicious_input'})
        self.assertEqual(res2.status_code, 400)
        print("✓ Test 13 Passed: Invalid event types correctly rejected with HTTP 400")

    def test_14_funnel_progression_with_high_volume(self):
        """Test 14: High volume events maintain Sent >= Opened >= Clicked >= Submitted."""
        for i in range(12):
            res = self.client.post('/api/training/event', json={'type': 'complete', 'volunteer_id': f'LoadVol {i}'})
            self.assertEqual(res.status_code, 200)

        stats = self.client.get('/api/stats').get_json()['stats']
        self.assertGreaterEqual(stats['sent'], stats['opened'])
        self.assertGreaterEqual(stats['opened'], stats['clicked'])
        self.assertGreaterEqual(stats['clicked'], stats['submitted'])
        self.assertEqual(stats['submitted'], 20)
        print(f"✓ Test 14 Passed: High volume completion maintained funnel hierarchy: {stats}")

if __name__ == '__main__':
    unittest.main()
