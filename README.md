# ProductApi

Minimal ASP.NET Core 9 / EF Core 9 / PostgreSQL product backend for the existing React shop.

## Run locally

PostgreSQL must be running. The existing `DefaultConnection` in appsettings.json is used.
An environment variable named `ConnectionStrings__DefaultConnection` can override it.
Do not commit real database passwords.

```sh
DOTNET_USE_POLLING_FILE_WATCHER=1 dotnet ef database update
dotnet run --launch-profile http
```

API: http://localhost:5105/api/products
React: http://localhost:5173/products (run `npm run dev` in the frontend folder).
Port 5105 avoids the old API process already occupying 5104.
The launch profile enables polling to avoid file-watcher startup hangs in the restricted environment.

Frontend `VITE_PRODUCT_API_URL` defaults to `http://localhost:5105/api`.
CORS allows localhost and 127.0.0.1 on ports 5173 and 5174. Override `Cors:AllowedOrigins`
with a configuration array if the frontend uses another origin; restart the API.

## Endpoints

| Method | Route | Result |
| --- | --- | --- |
| GET | /api/products?search=phone | 200, product array; optional case-insensitive search |
| GET | /api/products/{id} | 200 or 404 |
| POST | /api/products | 201, created product and Location header |
| PUT | /api/products/{id} | 200, updated product, or 404 |
| DELETE | /api/products/{id} | 204 or 404 |

POST and PUT body (PUT replaces all editable fields):

```json
{
  "name": "Phone",
  "description": "Example product",
  "price": 600,
  "stock": 10,
  "imageUrl": "",
  "category": "Electronics"
}
```

New shop products receive server-generated string IDs. Imported products retain their original Node IDs. Name is required and at most 200 characters;
price and stock cannot be negative. Invalid input returns 400 automatically
through `[ApiController]` and model validation.

## Verify

```sh
dotnet build
python3 scripts/smoke_test.py
```

The smoke test creates and deletes its own temporary product. It checks CRUD,
persisted updates, search, validation, missing IDs, CORS and preservation of existing rows.
Frontend checks: `npm run build` and `npx vitest run`.

## Files and design

- `Models/StoreProduct.cs`: actual shop catalog, string IDs, timestamps and validation.
- `Models/Product.cs`: original teaching model retained without changing its IDs or table.
- `Models/Data/MyDatabaseContext.cs`: EF Core bridge to PostgreSQL; includes both original Products and new StoreProducts.
- `Controllers/ProductsController.cs`: async CRUD and search. Read-only lists use
  `AsNoTracking`; updates load a tracked row, change fields, then call `SaveChangesAsync`.
- `Program.cs`: existing Npgsql configuration plus CORS before controllers.
  Local Development can use HTTP; HTTPS redirection remains outside Development.
- `Migrations/*AddProductDetails*` and model snapshot: add description, stock,
  image URL and category, and constrain name length. Existing rows start with empty
  metadata and stock zero, so they appear out of stock until deliberately updated.
- `Properties/launchSettings.json`: local port and file-watcher setting.
- Frontend `src/api/products.ts`: separate Axios client for products; preserves original string IDs and timestamps, and maps
  `name` to `title` and `imageUrl` to `image`. Existing UI stays intact.
- Frontend `.env.example`: documents the configurable ProductApi URL.
- Frontend product-page tests: provide the Router required by existing search behavior.
- Frontend `tests/api/products.test.ts`: checks response mapping, search and error propagation.

Only the product flow uses this API. Existing authentication/order/dashboard calls
still use the original Node backend on port 4000. Checkout is not integrated with
ProductApi; Original catalog IDs now match, but future edits in one database are not automatically synchronized. No auth,
orders or cart persistence was added. The unauthenticated write endpoints are for
local development; authentication is a separate next step before public deployment.

## Original shop catalog correction

The API now serves `StoreProducts`, containing the same 20 products as the existing
Node/SQLite catalog. Images, prices, stock, descriptions, categories, IDs, timestamps
and ordering were compared against the original Node API. The original teaching
`Products` table remains intact and is not shown in the store.

`AddStoreCatalog` only creates a new table. Import the existing source without
re-seeding or changing it:

```sh
python3 scripts/import_store_catalog.py /absolute/path/to/Amazon-E-Commerce-Backend/prisma/dev.db
```

The importer reads SQLite in read-only mode, inserts in a PostgreSQL transaction,
and leaves existing destination IDs unchanged. This is a one-time copy, not ongoing
synchronization. Never run the old Node seed script for this migration: it replaces
the original catalog.
