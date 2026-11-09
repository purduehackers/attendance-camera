import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'src' / 'render_config.py'
spec = importlib.util.spec_from_file_location('render_config', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConfigurationTests(unittest.TestCase):
    def test_rejects_non_tailnet_bindings(self):
        for address in ('0.0.0.0', '127.0.0.1', '192.168.1.2', '8.8.8.8', '::', '100.63.255.255', '100.128.0.0'):
            with self.subTest(address=address), self.assertRaises(ValueError):
                module.render(address, 'camera')

    def test_rejects_service_unit_injection(self):
        for user in ('camera\nExecStart=/bin/sh', '../root', 'camera;id', ''):
            with self.subTest(user=user), self.assertRaises(ValueError):
                module.render('100.64.0.2', user)

    def test_private_read_only_feed(self):
        files = module.render('100.64.0.2', 'camera')
        config = files['mediamtx.yml']
        for binding in ('rtspAddress: 100.64.0.2:8554', 'webrtcAddress: 100.64.0.2:8889', 'webrtcLocalUDPAddress: 100.64.0.2:8189', 'webrtcLocalTCPAddress: 100.64.0.2:8189'):
            self.assertIn(binding, config)
        self.assertIn('ips: [100.64.0.0/10]', config)
        self.assertIn('action: read', config)
        self.assertNotIn('action: publish', config)
        self.assertIn('record: false', config)
        self.assertIn('rpiCameraCodec: hardwareH264', config)
        self.assertIn('User=camera', files['camera-feed.service'])
        self.assertIn('100.64.0.2/', files['camera-feed.service'])
        self.assertTrue(all('__TAILSCALE_IP__' not in value and '__SERVICE_USER__' not in value for value in files.values()))


if __name__ == '__main__':
    unittest.main()
