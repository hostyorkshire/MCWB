#!/usr/bin/env python3
"""
Test USB port detection functionality
"""

import sys
import unittest
from unittest.mock import MagicMock, patch, Mock
from meshcore import find_serial_ports, MeshCore, SERIAL_AVAILABLE


class TestUSBPortDetection(unittest.TestCase):
    """Test USB port detection"""

    @patch('meshcore.SERIAL_AVAILABLE', True)
    @patch('meshcore.list_ports')
    def test_find_serial_ports_with_usb_devices(self, mock_list_ports):
        """Test finding USB serial ports"""
        # Mock serial port objects
        port1 = MagicMock()
        port1.device = '/dev/ttyUSB0'
        port1.description = 'USB Serial Device'
        
        port2 = MagicMock()
        port2.device = '/dev/ttyUSB1'
        port2.description = 'FTDI USB Serial'
        
        port3 = MagicMock()
        port3.device = '/dev/ttyACM0'
        port3.description = 'Arduino Uno'
        
        # Mock should return these ports
        mock_list_ports.comports.return_value = [port1, port2, port3]
        
        # Test the function
        ports = find_serial_ports(debug=False)
        
        # Should find all USB ports
        self.assertEqual(len(ports), 3)
        self.assertIn('/dev/ttyUSB0', ports)
        self.assertIn('/dev/ttyUSB1', ports)
        self.assertIn('/dev/ttyACM0', ports)

    @patch('meshcore.SERIAL_AVAILABLE', True)
    @patch('meshcore.list_ports')
    def test_find_serial_ports_filters_non_usb(self, mock_list_ports):
        """Test that non-USB ports are filtered out"""
        # Mock serial port objects
        port1 = MagicMock()
        port1.device = '/dev/ttyUSB0'
        port1.description = 'USB Serial Device'
        
        port2 = MagicMock()
        port2.device = '/dev/ttyS0'
        port2.description = 'Built-in Serial Port'
        
        mock_list_ports.comports.return_value = [port1, port2]
        
        # Test the function
        ports = find_serial_ports(debug=False)
        
        # Should only find USB port, not ttyS0
        self.assertEqual(len(ports), 1)
        self.assertIn('/dev/ttyUSB0', ports)
        self.assertNotIn('/dev/ttyS0', ports)

    @patch('meshcore.SERIAL_AVAILABLE', True)
    @patch('meshcore.list_ports')
    def test_find_serial_ports_empty(self, mock_list_ports):
        """Test when no serial ports are available"""
        mock_list_ports.comports.return_value = []
        
        ports = find_serial_ports(debug=False)
        
        self.assertEqual(len(ports), 0)

    @patch('meshcore.SERIAL_AVAILABLE', False)
    def test_find_serial_ports_no_pyserial(self):
        """Test when pyserial is not installed"""
        ports = find_serial_ports(debug=False)
        
        self.assertEqual(len(ports), 0)

    @patch('meshcore.SERIAL_AVAILABLE', True)
    @patch('meshcore.list_ports')
    def test_find_serial_ports_sorted_order(self, mock_list_ports):
        """Test that ports are returned in sorted order"""
        # Mock serial port objects in random order
        port1 = MagicMock()
        port1.device = '/dev/ttyUSB2'
        port1.description = 'USB Serial 2'
        
        port2 = MagicMock()
        port2.device = '/dev/ttyUSB0'
        port2.description = 'USB Serial 0'
        
        port3 = MagicMock()
        port3.device = '/dev/ttyUSB1'
        port3.description = 'USB Serial 1'
        
        mock_list_ports.comports.return_value = [port1, port2, port3]
        
        # Test the function
        ports = find_serial_ports(debug=False)
        
        # Should be sorted
        self.assertEqual(ports, ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2'])

    @patch('meshcore.find_serial_ports')
    @patch('meshcore.serial.Serial')
    @patch('meshcore.SERIAL_AVAILABLE', True)
    def test_meshcore_auto_detect_on_failure(self, mock_serial_class, mock_find_ports):
        """Test that MeshCore auto-detects ports when specified port fails"""
        from meshcore import SerialException
        
        # Set up the mock
        mock_find_ports.return_value = ['/dev/ttyUSB0', '/dev/ttyUSB1']
        
        # First call fails (original port), second call succeeds (auto-detected port)
        mock_serial_instance = MagicMock()
        mock_serial_instance.is_open = True
        
        mock_serial_class.side_effect = [
            SerialException("Port not found"),  # First attempt fails
            mock_serial_instance  # Second attempt succeeds
        ]
        
        # Create MeshCore with a port that doesn't exist
        mesh = MeshCore("test_node", debug=True, serial_port="/dev/ttyUSB999", baud_rate=9600)
        mesh._connect_serial()
        
        # Should have tried the specified port, then auto-detected
        self.assertEqual(mock_serial_class.call_count, 2)
        
        # Should have updated to the working port
        self.assertEqual(mesh.serial_port, '/dev/ttyUSB0')
        
        # Should have found ports
        mock_find_ports.assert_called_once()


def run_tests():
    """Run all tests"""
    print("Testing USB port detection functionality...")
    print()
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUSBPortDetection)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✓ All USB port detection tests passed!")
        return 0
    else:
        print(f"\n✗ {len(result.failures)} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
