# Service Template

Use this layout for new services:

```text
apps/<service_name>
├─ app
│  ├─ api
│  ├─ application
│  ├─ domain
│  ├─ infrastructure
│  ├─ schemas
│  └─ main.py
├─ workers
├─ tests
└─ Dockerfile
```

Keep route handlers thin. Put business orchestration in `application`, external
tools in `infrastructure`, and request/response DTOs in `schemas`.
