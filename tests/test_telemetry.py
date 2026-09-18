# Created by 11hopem (11 Hopem Software Ltd. Şti.)
# Copyright (c) 2026 11hopem. All rights reserved.
# Licensed under 11 Hopem Software Proprietary License.

import unittest
import tempfile
import os
import json
import sys

# Ensure root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry.firebase_config import FIREBASE_ECOSYSTEM_CONFIG
from telemetry.logger import TelemetryLogger

class TestTelemetryLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.logger = TelemetryLogger(
            app_name="iphone-bot-test",
            app_version="1.0.0",
            log_dir=self.temp_dir.name
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_firebase_config(self):
        self.assertEqual(FIREBASE_ECOSYSTEM_CONFIG["account"], "umutocgdr@gmail.com")
        self.assertEqual(FIREBASE_ECOSYSTEM_CONFIG["project_id"], "hopem-software-cloud")

    def test_log_writing_and_local_custody(self):
        entry = self.logger.info("Bot automation started", {"target": "bonusflas"})
        self.assertEqual(entry["level"], "INFO")
        self.assertEqual(entry["app_name"], "iphone-bot-test")
        self.assertEqual(entry["context"]["target"], "bonusflas")

        error_entry = self.logger.error("OCR recognition failure", {"attempt": 2})
        self.assertEqual(error_entry["level"], "ERROR")

        # Verify JSONL file exists and is populated
        self.assertTrue(os.path.exists(self.logger.log_file))
        with open(self.logger.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)
            parsed = json.loads(lines[0])
            self.assertEqual(parsed["message"], "Bot automation started")

    def test_zero_crash_guarantee(self):
        res1 = self.logger.log(None, None)
        self.assertIsNotNone(res1)
        res2 = self.logger.error(Exception("Test exception"))
        self.assertIsNotNone(res2)

if __name__ == "__main__":
    unittest.main()
