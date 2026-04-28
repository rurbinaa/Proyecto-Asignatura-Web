# Mockups Directory

Place garment mockup images here. The backend serves them via the `/api/v1/mockups/` endpoint.

## Expected files

| Filename | Side | Garment |
|----------|------|---------|
| `shirt_front.png` | FRONT | Shirt |
| `shirt_back.png` | BACK | Shirt |
| `pants_front.png` | FRONT | Pants |
| `pants_back.png` | BACK | Pants |

## Format

- PNG or SVG recommended
- Transparent background preferred
- Consistent dimensions for front/back pairs

## How to register

Upload via Django admin at `/admin/media_data/mockup/` or use the API:

```bash
POST /api/v1/mockups/
{
  "name": "shirt",
  "side": "FRONT",
  "image": "<file>",
  "width": 1024,
  "height": 768
}
```
