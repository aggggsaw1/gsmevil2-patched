import sys
from unittest.mock import MagicMock

# Mocking modules that are not available
mock_pyshark = MagicMock()
sys.modules['pyshark'] = mock_pyshark

mock_flask = MagicMock()
sys.modules['flask'] = mock_flask

mock_flask_socketio = MagicMock()
sys.modules['flask_socketio'] = mock_flask_socketio

# Mock Flask class and SocketIO
mock_flask.Flask = MagicMock()
mock_flask_socketio.SocketIO = MagicMock()

# Now we can import GsmEvil
import GsmEvil
import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import os

class TestImsiEvil(unittest.TestCase):
    def setUp(self):
        self.imsi_evil = GsmEvil.ImsiEvil()
        self.imsi_evil.imsi = "123456789012345"
        self.imsi_evil.tmsi = "0x12345678"
        self.imsi_evil.mcc = 250
        self.imsi_evil.mnc = 1
        GsmEvil.lac = 1234
        GsmEvil.ci = 5678
        GsmEvil.imsi_live_db = {}

    def test_sql_db(self):
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            self.imsi_evil.sql_db()
            mock_connect.assert_called_with('database/imsi.db')
            mock_conn.execute.assert_called()

    def test_save_data(self):
        real_conn = sqlite3.connect(':memory:')
        with patch('sqlite3.connect', return_value=real_conn):
            self.imsi_evil.sql_db()
            self.imsi_evil.save_data()

        cursor = real_conn.cursor()
        cursor.execute("SELECT imsi, tmsi, mcc, mnc FROM imsi_data")
        row = cursor.fetchone()
        self.assertEqual(row[0], self.imsi_evil.imsi)
        self.assertEqual(row[1], self.imsi_evil.tmsi)
        self.assertEqual(row[2], self.imsi_evil.mcc)
        self.assertEqual(row[3], self.imsi_evil.mnc)

    def test_filter_imsi_new(self):
        real_conn = sqlite3.connect(':memory:')
        with patch('sqlite3.connect', return_value=real_conn):
            with patch.object(self.imsi_evil, 'output'):
                self.imsi_evil.filter_imsi()

        self.assertIn(self.imsi_evil.imsi, GsmEvil.imsi_live_db)
        self.assertEqual(GsmEvil.imsi_live_db[self.imsi_evil.imsi]['tmsi'], self.imsi_evil.tmsi)

    def test_get_imsi(self):
        real_conn = sqlite3.connect(':memory:')
        with patch('sqlite3.connect', return_value=real_conn):
            mock_packet = MagicMock()
            mock_layer = MagicMock()
            mock_layer.layer_name = 'gsm_a.ccch'
            mock_layer.gsm_a_bssmap_cell_ci = '162e' # 5678 in hex
            mock_layer.gsm_a_lac = '04d2' # 1234 in hex
            mock_layer.e212_imsi = '123456789012345'
            mock_layer.e212_mcc = '250'
            mock_layer.e212_mnc = '01'
            mock_layer.gsm_a_rr_tmsi_ptmsi = '0x12345678'

            mock_packet.layers = [mock_layer]

            with patch.object(self.imsi_evil, 'filter_imsi'):
                self.imsi_evil.get_imsi(mock_packet)

        self.assertEqual(self.imsi_evil.imsi, '123456789012345')
        self.assertEqual(self.imsi_evil.mcc, '250')
        self.assertEqual(GsmEvil.ci, 5678)
        self.assertEqual(GsmEvil.lac, 1234)

class TestSmsEvil(unittest.TestCase):
    def setUp(self):
        self.sms_evil = GsmEvil.SmsEvil()
        self.sms_evil.text = "Hello World"
        self.sms_evil.sender = "12345"
        self.sms_evil.receiver = "67890"
        self.sms_evil.time = "12:00:00"
        self.sms_evil.date = "01/01/2023"

    def test_save_data(self):
        real_conn = sqlite3.connect(':memory:')
        with patch('sqlite3.connect', return_value=real_conn):
            self.sms_evil.sql_db()
            self.sms_evil.save_data()

        cursor = real_conn.cursor()
        cursor.execute("SELECT text, sender, receiver FROM sms_data")
        row = cursor.fetchone()
        self.assertEqual(row[0], self.sms_evil.text)
        self.assertEqual(row[1], self.sms_evil.sender)
        self.assertEqual(row[2], self.sms_evil.receiver)

    def test_get_sms(self):
        real_conn = sqlite3.connect(':memory:')
        with patch('sqlite3.connect', return_value=real_conn):
            mock_packet = MagicMock()
            mock_packet.gsm_sms = MagicMock()
            mock_packet.gsm_sms.sms_text = "Test SMS"
            mock_packet.gsm_sms.scts_hour = "14"
            mock_packet.gsm_sms.scts_minutes = "30"
            mock_packet.gsm_sms.scts_seconds = "05"
            mock_packet.gsm_sms.scts_day = "07"
            mock_packet.gsm_sms.scts_month = "03"
            mock_packet.gsm_sms.scts_year = "2023"
            mock_packet.gsm_sms.tp_oa = "SenderID"

            mock_layer = MagicMock()
            mock_layer.gsm_a_dtap_cld_party_bcd_num = "ReceiverID"
            mock_packet.layers = [mock_layer]

            with patch.object(self.sms_evil, 'output'):
                self.sms_evil.get_sms(mock_packet)

        self.assertEqual(self.sms_evil.text, "Test SMS")
        self.assertEqual(self.sms_evil.sender, "SenderID")
        self.assertEqual(self.sms_evil.receiver, "ReceiverID")

if __name__ == '__main__':
    unittest.main()
