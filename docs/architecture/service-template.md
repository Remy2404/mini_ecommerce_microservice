# Service Template

Use this layout for new services:

```text
apps/<service_name>
├─ app
│  ├─ api/
│  ├─ application/
│  │  └─ services.py
│  ├─ domain/
│  │  ├─ entities.py
│  │  ├─ exceptions.py
│  │  └─ policies.py
│  ├─ infrastructure/
│  ├─ schemas/
│  └─ main.py
├─ workers/
├─ tests/
└─ Dockerfile
```

Keep route handlers thin. Put business orchestration in `application`, external
tools in `infrastructure`, and request/response DTOs in `schemas`.

Keep the service tree flat by default. Add extra subpackages only when a layer
has enough real code to justify them. Do not create `use_cases/`, `entities/`,
or similar nested folders just because they sound tidy.
