import json
import unittest

from utils import create_presence, process_ans, process_client_message, get_message, send_message


class TestClient(unittest.TestCase):
    def test_def_presense(self):
        test = create_presence()
        test['time'] = 1.1
        self.assertEqual(test, {'action': 'presence', 'time': 1.1, 'type': 'status', 'user': {'account_name': 'User', 'status': 'Yep, I am here!'}})

    def test_200_ans(self):
        self.assertEqual(process_ans({'response': 200}), '200 : OK')

    def test_400_ans(self):
        self.assertEqual(process_ans({'response': 400, 'error': 'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        self.assertRaises(ValueError, process_ans, {'error': 'Bad Request'})


class TestServer(unittest.TestCase):
    error_dict = {
        'response': 400,
        'error': 'Bad Request'
    }
    ok_dict = {'response': 200}

    def test_no_action(self):
        self.assertEqual(process_client_message({'time': '1.1'}), self.error_dict)

    def test_wrong_action(self):
        self.assertEqual(process_client_message(
            {'action': 'Wrong', 'time': '1.1', 'user': {'account_name': 'User'}}), self.error_dict)

    def test_ok_check(self):
        self.assertEqual(process_client_message(
            {'action': 'presence', 'time': '1.1', 'user': {'account_name': 'User'}}), self.ok_dict)


class TestSocket:
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.receved_message = None

    def send(self, message_to_send):

        json_test_message = json.dumps(self.test_dict)
        # кодирует сообщение
        self.encoded_message = json_test_message.encode('utf-8')
        # сохраняем что должно было отправлено в сокет
        self.receved_message = message_to_send

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode('utf-8')


class Tests(unittest.TestCase):
    test_dict_send = {
        'action': 'presense',
        'time': 1.1,
        'user': {
            'account_name': 'test'
        }
    }
    error_dict = {
        'response': 400,
        'error': 'Bad Request'
    }
    ok_dict = {'response': 200}

    def test_send_message(self):
        test_socket = TestSocket(self.test_dict_send)
        send_message(test_socket, self.test_dict_send)
        self.assertEqual(test_socket.encoded_message, test_socket.receved_message)
        with self.assertRaises(Exception):
            send_message(test_socket, test_socket)

    def test_get_message(self):
        test_sock_ok = TestSocket(self.ok_dict)
        test_sock_err = TestSocket(self.error_dict)
        self.assertEqual(get_message(test_sock_ok), self.ok_dict)
        self.assertEqual(get_message(test_sock_err), self.error_dict)


if __name__ == '__main__':
    unittest.main()
