"""Run against the local ProductApi: python3 scripts/smoke_test.py.
Creates its own product and deletes only that product in finally.
"""
import json
import os
import urllib.request
import urllib.error
import uuid

BASE = os.environ.get('PRODUCT_API_URL', 'http://localhost:5105/api').rstrip('/')

def request(method, path, payload=None, headers=None):
    req = urllib.request.Request(BASE + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Content-Type': 'application/json', **(headers or {})}, method=method)
    try:
        response = urllib.request.urlopen(req, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        raw = response.read()
        return response.status, json.loads(raw) if raw else None, response.headers

name = 'Smoke-' + uuid.uuid4().hex
product = dict(name=name, description='Temporary test product', price=19.99,
               stock=3, imageUrl='', category='Testing')
product_id = None
try:
    status, existing, _ = request('GET', '/products')
    assert status == 200 and isinstance(existing, list)
    status, created, headers = request('POST', '/products', product)
    assert status == 201, (status, created)
    product_id = created['id']
    assert headers['Location'].endswith('/' + str(product_id))
    path = '/products/' + str(product_id)
    assert request('GET', path)[1] == created
    status, matches, _ = request('GET', '/products?search=' + name.lower())
    assert status == 200 and [p['id'] for p in matches] == [product_id]
    product.update(price=24.50, stock=7, description='Updated description')
    status, updated, _ = request('PUT', path, product)
    assert status == 200 and updated['price'] == 24.50 and updated['stock'] == 7
    assert request('GET', path)[1]['description'] == 'Updated description'
    for invalid in [dict(product, name=''), dict(product, price=-1), dict(product, stock=-1)]:
        assert request('POST', '/products', invalid)[0] == 400
    assert request('PUT', path, dict(product, stock=-1))[0] == 400
    status, _, headers = request('OPTIONS', '/products', headers={
        'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type'})
    assert status == 204 and headers['Access-Control-Allow-Origin'] == 'http://localhost:5173'
    _, _, headers = request('GET', '/products', headers={'Origin': 'https://untrusted.example'})
    assert headers.get('Access-Control-Allow-Origin') is None
    assert request('DELETE', path)[0] == 204
    assert request('GET', path)[0] == 404
    assert request('PUT', path, product)[0] == 404
    assert request('DELETE', path)[0] == 404
    product_id = None
    assert request('GET', '/products')[1] == existing
    print('PASS: CRUD, saved updates, search, validation, 404, CORS and unchanged existing products.')
finally:
    if product_id is not None:
        request('DELETE', '/products/' + str(product_id))
