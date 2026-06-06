"""Tests for REST API call tool."""

import json
import pytest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

from tools.rest_api_call import rest_api_call, check_rest_api_call_requirements


class TestRestApiCall:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.valid_url = 'https://api.example.com/data'

    def test_check_requirements_always_available(self):
        assert check_rest_api_call_requirements() is True

    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_get_request_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"result": "success"}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = json.loads(rest_api_call('https://api.example.com/get'))
        assert result['success'] is True
        assert result['status_code'] == 200

    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_post_request_with_body(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.read.return_value = b'{"id": 123}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = json.loads(rest_api_call(
            'https://api.example.com/create',
            method='POST',
            body={'name': 'test'}
        ))
        assert result['success'] is True
        assert result['status_code'] == 201

    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_put_request(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"updated": true}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = json.loads(rest_api_call(
            'https://api.example.com/update/1',
            method='PUT',
            body={'name': 'updated'}
        ))
        assert result['success'] is True

    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_delete_request(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.read.return_value = b''
        mock_response.headers = {}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = json.loads(rest_api_call(
            'https://api.example.com/delete/1',
            method='DELETE'
        ))
        assert result['success'] is True
        assert result['status_code'] == 204

    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_http_error_404(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            'https://api.example.com/notfound',
            404,
            'Not Found',
            {},
            None
        )

        result = json.loads(rest_api_call('https://api.example.com/notfound'))
        assert result['success'] is False
        assert result['status_code'] == 404
        assert 'error' in result

    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_http_error_500(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            'https://api.example.com/error',
            500,
            'Internal Server Error',
            {},
            None
        )

        result = json.loads(rest_api_call('https://api.example.com/error'))
        assert result['success'] is False
        assert result['status_code'] == 500

    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_custom_headers(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"data": "ok"}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = json.loads(rest_api_call(
            'https://api.example.com/secure',
            headers={'Authorization': 'Bearer token123'}
        ))
        assert result['success'] is True
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert req.get_header('Authorization') == 'Bearer token123'

    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_timeout_parameter(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        rest_api_call('https://api.example.com/test', timeout=60)
        call_args = mock_urlopen.call_args
        assert call_args[1]['timeout'] == 60

    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_non_json_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'plain text response'
        mock_response.headers = {'Content-Type': 'text/plain'}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = json.loads(rest_api_call('https://api.example.com/text'))
        assert result['success'] is True
        assert 'body' in result


class TestRestApiCallMethods:
    @patch('tools.rest_api_call.urllib.request.urlopen')
    def test_all_methods(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{}'
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_urlopen.return_value.__enter__.return_value = mock_response

        for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            result = json.loads(rest_api_call('https://api.example.com/test', method=method))
            assert result['success'] is True