from fastapi.testclient import TestClient
from main import app
from google.genai.errors import ClientError
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_google_genai.chat_models import GoogleRateLimitError
import pytest

client = TestClient(app)


def test_demo_generation():
    response = client.post('/api/generate', json={'topic': 'Better daily habits', 'demo': True})
    assert response.status_code == 200
    assert response.json()['content'].startswith('# Better daily habits')
    assert response.json()['demo'] is True
    assert response.json()['words'] > 100


def test_blank_topic():
    assert client.post('/api/generate', json={'topic': '   '}).status_code == 422


def test_ai_requires_key(monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    assert client.post('/api/generate', json={'topic': 'Daily habits', 'demo': False}).status_code == 503


def test_gemini_chain_uses_brief(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only-key')
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    seen = {}

    def fake_model(**kwargs):
        seen.update(kwargs)

        def respond(prompt):
            seen['prompt'] = prompt.to_string()
            return AIMessage(content='# A better habit\n\nRead a page each day.')

        return RunnableLambda(respond)

    monkeypatch.setattr('main.ChatGoogleGenerativeAI', fake_model)
    response = client.post('/api/generate', json={'topic': 'Daily habits', 'tone': 'Educational', 'length': 'Short', 'keywords': 'reading', 'demo': False})
    assert response.status_code == 200
    assert response.json()['demo'] is False
    assert response.json()['content'].startswith('# A better habit')
    assert seen['model'] == 'gemini-3.5-flash-lite'
    assert seen['api_key'] == 'test-only-key'
    assert seen['vertexai'] is False
    assert 'Educational' in seen['prompt']
    assert '400' in seen['prompt']
    assert 'reading' in seen['prompt']


def test_quota_error_does_not_leak_provider_details(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only-key')

    def fail(**kwargs):
        def respond(prompt):
            try:
                raise ClientError(429, {'error': {'code': 429, 'message': 'secret-provider-detail', 'status': 'RESOURCE_EXHAUSTED'}})
            except ClientError as error:
                raise GoogleRateLimitError('secret-provider-detail') from error
        return RunnableLambda(respond)

    monkeypatch.setattr('main.ChatGoogleGenerativeAI', fail)
    response = client.post('/api/generate', json={'topic': 'Daily habits', 'demo': False})
    assert response.status_code == 429
    assert 'quota' in response.json()['detail']
    assert 'secret-provider-detail' not in response.text


def test_health_never_returns_key(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only-key')
    response = client.get('/api/health')
    assert response.json()['ai_configured'] is True
    assert response.json()['provider'] == 'gemini'
    assert 'test-only-key' not in response.text


@pytest.mark.parametrize('code,expected', [(403, 'rejected'), (404, 'unavailable'), (503, 'temporarily unavailable')])
def test_provider_failure(monkeypatch, code, expected):
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only-key')

    def fail(**kwargs):
        def respond(prompt):
            raise ClientError(code, {'error': {'code': code, 'message': 'private-provider-detail'}})
        return RunnableLambda(respond)

    monkeypatch.setattr('main.ChatGoogleGenerativeAI', fail)
    response = client.post('/api/generate', json={'topic': 'Daily habits', 'demo': False})
    assert response.status_code == 502
    assert expected in response.json()['detail']
    assert 'private-provider-detail' not in response.text
