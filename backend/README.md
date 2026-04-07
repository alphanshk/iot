# Raspberry Pi Flask Backend

## Run

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## APIs

- `POST /register` with `name`, `phone`, `password`
- `POST /login` with `phone`, `password`
- `POST /mark_api` with `employee_id`, `image_base64`
- `GET /attendance` (optional `?employee_id=1`)

Default user auto-created:
- Name: Alphan
- Phone: 7385520906
- Password: admin123

Images are stored in `data/saved_faces/` as `employeeId_timestamp.jpg`.
