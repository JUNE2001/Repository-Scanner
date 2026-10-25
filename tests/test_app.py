import unittest
from unittest.mock import patch

from repository_scanner import code_regex, parse_repository_url
from app import app


class HubGitTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_main_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'HUB Repository Search', response.data)
        self.assertIn(b'detect_percent < 0.1', response.data)

    def test_repository_url_validation(self):
        self.assertEqual(parse_repository_url('https://github.com/openai/openai-python'), ('openai', 'openai-python'))
        with self.assertRaises(ValueError):
            parse_repository_url('http://localhost/private')

    def test_regex_detection_keeps_file_path(self):
        data, detected, count = code_regex([['phone=010-1234-5678', 'ip=127.0.0.1']], ['config.py'])
        self.assertEqual(data['call'][0][1], 'config.py')
        self.assertEqual(data['ip'][0][1], 'config.py')
        self.assertEqual((detected, count), (2, 2))

    def test_phone_detection_rejects_invalid_separators(self):
        samples = [['010A1234B5678', '2010-1234-5678', '010-12-3456', '010.1234.5678']]
        data, detected, _ = code_regex(samples, ['invalid.txt'])
        self.assertEqual(data['call'], [])
        self.assertEqual(detected, 0)

    def test_phone_detection_returns_only_phone_number(self):
        data, detected, _ = code_regex([['phone="010-2468-1357"', 'backup=01024681357']], ['customer.py'])
        self.assertEqual(data['call'], [['010-2468-1357', 'customer.py'], ['01024681357', 'customer.py']])
        self.assertEqual(detected, 2)

    def test_resident_number_uses_six_and_seven_digit_rule(self):
        data, detected, _ = code_regex([['id=123456-1234567', 'short=12345-1234567']], ['customer.py'])
        self.assertEqual(data['reg'], [['id=123456-1234567', 'customer.py']])
        self.assertEqual(detected, 1)

    def test_ssh_private_key_detection(self):
        data, detected, _ = code_regex([['-----BEGINOPENSSHPRIVATEKEY-----']], ['id_ed25519'])
        self.assertEqual(data['ssh_private_key'], [['-----BEGINOPENSSHPRIVATEKEY-----', 'id_ed25519']])
        self.assertEqual(detected, 1)

    def test_openai_api_key_detection_is_masked(self):
        key = 'sk-proj-abcdefghijklmnopqrstuvwxyz123456'
        data, detected, _ = code_regex([[f'OPENAI_API_KEY={key}']], ['.env'])
        displayed = data['openai_api_key'][0][0]
        self.assertEqual(data['openai_api_key'][0][1], '.env')
        self.assertNotIn(key, displayed)
        self.assertTrue(displayed.startswith('sk-proj-'))
        self.assertTrue(displayed.endswith('3456'))
        self.assertEqual(detected, 1)

    @patch('app.code_regex', return_value=({'reg': [], 'call': [], 'ip': [], 'ssh_private_key': [], 'openai_api_key': []}, 0, 1))
    @patch('app.code_parser', return_value=[['safe']])
    @patch('app.git_parser', return_value=['README.md'])
    @patch('app.repository_info', return_value=('owner', 'repo', 'main'))
    def test_post_success(self, *_):
        response = self.client.post('/post', data={'userURL': 'https://github.com/owner/repo'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'owner', response.data)

    def test_post_rejects_non_github_url(self):
        response = self.client.post('/post', data={'userURL': 'http://localhost/repo'})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
