from functools import lru_cache

import valkey

from packages.config.settings import settings


@lru_cache
def get_valkey_client() -> valkey.Valkey:
    return valkey.from_url(
        settings.valkey_url,
        decode_responses=True,
    )
