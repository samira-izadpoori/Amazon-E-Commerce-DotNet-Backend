"""Copy existing Node catalog into PostgreSQL without changing source or existing rows.
Usage: python3 scripts/import_store_catalog.py /absolute/path/to/prisma/dev.db
"""
import datetime
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    rows = [dict(row) for row in db.execute('SELECT * FROM Product ORDER BY createdAt DESC, id')]
assert rows, 'Source catalog is empty; nothing imported.'

def timestamp(value):
    return datetime.datetime.fromtimestamp(value / 1000, datetime.timezone.utc).isoformat()

products = [dict(Id=p['id'], Name=p['title'], Description=p['description'],
                 Price=p['price'], Stock=p['stock'], ImageUrl=p['image'], Category=p['category'],
                 CreatedAt=timestamp(p['createdAt']), UpdatedAt=timestamp(p['updatedAt'])) for p in rows]
for p in products:
    assert len(p['Name']) <= 200 and len(p['Description']) <= 5000
    assert len(p['ImageUrl']) <= 2048 and len(p['Category']) <= 100
    assert p['Price'] >= 0 and p['Stock'] >= 0
root = Path(__file__).resolve().parents[1]
connection = os.environ.get('ConnectionStrings__DefaultConnection') or json.loads((root/'appsettings.json').read_text())['ConnectionStrings']['DefaultConnection']
parts = {k.lower(): v for k,v in (part.split('=',1) for part in connection.split(';') if '=' in part)}
env = os.environ.copy()
env['PGPASSWORD'] = parts.get('password', '')
# SQL string-literal quoting; JSON remains data, never executable SQL.
payload = json.dumps(products, ensure_ascii=False).replace("'", "''")
sql = '''BEGIN;
SET LOCAL standard_conforming_strings = on;
INSERT INTO "StoreProducts" ("Id","Name","Description","Price","Stock","ImageUrl","Category","CreatedAt","UpdatedAt")
SELECT "Id","Name","Description","Price","Stock","ImageUrl","Category","CreatedAt","UpdatedAt"
FROM json_to_recordset(''' + "'" + payload + "'" + ''') AS p(
"Id" text, "Name" text, "Description" text, "Price" numeric, "Stock" integer,
"ImageUrl" text, "Category" text, "CreatedAt" timestamptz, "UpdatedAt" timestamptz)
ON CONFLICT ("Id") DO NOTHING;
COMMIT;
'''
subprocess.run(['psql', '-X', '-v', 'ON_ERROR_STOP=1', '-q', '-h', parts.get('host','localhost'),
                '-p', parts.get('port','5432'), '-U', parts['username'], '-d', parts['database']],
               input=sql, text=True, env=env, check=True, capture_output=True)
print(f'Imported {len(products)} source products (existing matching IDs left untouched).')
