from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.config import get_retrieval_cache_settings
from app.dataset_adapter import EXPECTED_FILES
from app.dataset_normalization import NORMALIZATION_VERSION, normalize_index_text
from app.schemas import DatasetCacheMetadata


CACHE_SCHEMA_VERSION = "2026-07-09"
INDEX_SCORING_VERSION = "2026-07-09"


@dataclass(frozen=True)
class CacheSourceSnapshot:
    fingerprint: str
    safe_key: str
    file_fingerprint: str
    dataset_key: str
    record_limit: int
    cache_enabled: bool
    cache_entry_count: int
    cache_max_entries: int
    cache_ttl_seconds: int | None
    cache_invalidated_reason: str | None = None


@dataclass(frozen=True)
class CacheValue:
    value: Any
    created_at: float
    fingerprint: str


class RetrievalCacheStore:
    def __init__(self) -> None:
        self._index_cache: OrderedDict[str, CacheValue] = OrderedDict()
        self._retrieval_cache: OrderedDict[str, CacheValue] = OrderedDict()
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._index_cache.clear()
            self._retrieval_cache.clear()

    def get_or_build_dataset_index(
        self,
        *,
        dataset_dir: str | Path | None,
        record_limit: int,
        build_fn: Callable[[], Any],
    ) -> tuple[Any, DatasetCacheMetadata, str]:
        settings = get_retrieval_cache_settings()
        source = describe_dataset_source(dataset_dir, record_limit)
        cache_key = _fingerprint(
            {
                "schema": CACHE_SCHEMA_VERSION,
                "kind": "dataset-index",
                "source": source.fingerprint,
                "normalization_version": NORMALIZATION_VERSION,
                "scoring_version": INDEX_SCORING_VERSION,
            }
        )
        if not settings.enabled:
            return (
                build_fn(),
                _cache_metadata(
                    cache_enabled=False,
                    index_cache_hit=False,
                    index_cache_key=_safe_cache_key(cache_key),
                    cache_entry_count=self.entry_count,
                    cache_max_entries=settings.max_entries,
                    cache_ttl_seconds=settings.ttl_seconds,
                    cache_invalidated_reason="cache_disabled",
                ),
                _safe_cache_key(cache_key),
            )

        with self._lock:
            entry = self._index_cache.get(cache_key)
            if entry is not None and not _expired(entry, settings.ttl_seconds):
                self._index_cache.move_to_end(cache_key)
                entry_count = self._entry_count_unlocked()
                return (
                    entry.value,
                    _cache_metadata(
                        cache_enabled=True,
                        index_cache_hit=True,
                        index_cache_key=_safe_cache_key(cache_key),
                        cache_entry_count=entry_count,
                        cache_max_entries=settings.max_entries,
                        cache_ttl_seconds=settings.ttl_seconds,
                    ),
                    _safe_cache_key(cache_key),
                )
            if entry is not None:
                del self._index_cache[cache_key]

        value = build_fn()
        with self._lock:
            self._index_cache[cache_key] = CacheValue(value=value, created_at=time.monotonic(), fingerprint=cache_key)
            self._index_cache.move_to_end(cache_key)
            self._evict_if_needed(self._index_cache, settings.max_entries)
        return (
            value,
            _cache_metadata(
                cache_enabled=True,
                index_cache_hit=False,
                index_cache_key=_safe_cache_key(cache_key),
                cache_entry_count=self.entry_count,
                cache_max_entries=settings.max_entries,
                cache_ttl_seconds=settings.ttl_seconds,
                cache_invalidated_reason="cache_miss",
            ),
            _safe_cache_key(cache_key),
        )

    def get_or_build_retrieval_results(
        self,
        *,
        index_cache_key: str,
        query: str,
        limit: int,
        build_fn: Callable[[], Any],
    ) -> tuple[Any, DatasetCacheMetadata, str]:
        settings = get_retrieval_cache_settings()
        normalized_query = normalize_index_text(query)
        cache_key = _fingerprint(
            {
                "schema": CACHE_SCHEMA_VERSION,
                "kind": "retrieval-results",
                "index_cache_key": index_cache_key,
                "query": normalized_query.normalized,
                "query_tokens": normalized_query.tokens,
                "query_phrases": normalized_query.phrases,
                "limit": limit,
                "normalization_version": NORMALIZATION_VERSION,
                "scoring_version": INDEX_SCORING_VERSION,
            }
        )
        if not settings.enabled:
            return (
                build_fn(),
                _cache_metadata(
                    cache_enabled=False,
                    retrieval_cache_hit=False,
                    retrieval_cache_key=_safe_cache_key(cache_key),
                    cache_entry_count=self.entry_count,
                    cache_max_entries=settings.max_entries,
                    cache_ttl_seconds=settings.ttl_seconds,
                    cache_invalidated_reason="cache_disabled",
                ),
                _safe_cache_key(cache_key),
            )

        with self._lock:
            entry = self._retrieval_cache.get(cache_key)
            if entry is not None and not _expired(entry, settings.ttl_seconds):
                self._retrieval_cache.move_to_end(cache_key)
                entry_count = self._entry_count_unlocked()
                return (
                    entry.value,
                    _cache_metadata(
                        cache_enabled=True,
                        retrieval_cache_hit=True,
                        retrieval_cache_key=_safe_cache_key(cache_key),
                        cache_entry_count=entry_count,
                        cache_max_entries=settings.max_entries,
                        cache_ttl_seconds=settings.ttl_seconds,
                    ),
                    _safe_cache_key(cache_key),
                )
            if entry is not None:
                del self._retrieval_cache[cache_key]

        value = build_fn()
        with self._lock:
            self._retrieval_cache[cache_key] = CacheValue(value=value, created_at=time.monotonic(), fingerprint=cache_key)
            self._retrieval_cache.move_to_end(cache_key)
            self._evict_if_needed(self._retrieval_cache, settings.max_entries)
        return (
            value,
            _cache_metadata(
                cache_enabled=True,
                retrieval_cache_hit=False,
                retrieval_cache_key=_safe_cache_key(cache_key),
                cache_entry_count=self.entry_count,
                cache_max_entries=settings.max_entries,
                cache_ttl_seconds=settings.ttl_seconds,
                cache_invalidated_reason="cache_miss",
            ),
            _safe_cache_key(cache_key),
        )

    @property
    def entry_count(self) -> int:
        with self._lock:
            return self._entry_count_unlocked()

    def _entry_count_unlocked(self) -> int:
        return len(self._index_cache) + len(self._retrieval_cache)

    def _evict_if_needed(self, cache: OrderedDict[str, CacheValue], max_entries: int) -> None:
        while len(cache) > max_entries:
            cache.popitem(last=False)


def describe_dataset_source(dataset_dir: str | Path | None, record_limit: int) -> CacheSourceSnapshot:
    settings = get_retrieval_cache_settings()
    root = Path(dataset_dir or ".").expanduser().resolve(strict=False)
    root_fingerprint = _safe_cache_key(str(root))
    file_parts: list[dict[str, Any]] = []
    for name in EXPECTED_FILES:
        path = root / name
        try:
            stat = path.stat()
        except OSError:
            file_parts.append({"name": name, "present": False})
            continue
        file_parts.append(
            {
                "name": name,
                "present": True,
                "size_bytes": stat.st_size,
                "modified_ns": stat.st_mtime_ns,
            }
        )
    file_fingerprint = _fingerprint({"root": root_fingerprint, "files": file_parts})
    fingerprint = _fingerprint(
        {
            "schema": CACHE_SCHEMA_VERSION,
            "dataset_root": root_fingerprint,
            "file_fingerprint": file_fingerprint,
            "record_limit": record_limit,
            "normalization_version": NORMALIZATION_VERSION,
            "scoring_version": INDEX_SCORING_VERSION,
        }
    )
    return CacheSourceSnapshot(
        fingerprint=fingerprint,
        safe_key=_safe_cache_key(fingerprint),
        file_fingerprint=_safe_cache_key(file_fingerprint),
        dataset_key=root_fingerprint,
        record_limit=record_limit,
        cache_enabled=settings.enabled,
        cache_entry_count=_CACHE.entry_count,
        cache_max_entries=settings.max_entries,
        cache_ttl_seconds=settings.ttl_seconds,
    )


def merge_cache_metadata(index_cache: DatasetCacheMetadata | None, retrieval_cache: DatasetCacheMetadata | None) -> DatasetCacheMetadata:
    settings = get_retrieval_cache_settings()
    merged = DatasetCacheMetadata(
        cache_enabled=settings.enabled,
        index_cache_hit=index_cache.index_cache_hit if index_cache else None,
        retrieval_cache_hit=retrieval_cache.retrieval_cache_hit if retrieval_cache else None,
        index_cache_key=index_cache.index_cache_key if index_cache else None,
        retrieval_cache_key=retrieval_cache.retrieval_cache_key if retrieval_cache else None,
        cache_entry_count=_merged_entry_count(index_cache, retrieval_cache),
        cache_max_entries=settings.max_entries,
        cache_ttl_seconds=settings.ttl_seconds,
        cache_invalidated_reason=_first_reason(index_cache, retrieval_cache),
    )
    return merged


def cache_metadata_for_index(index_cache: DatasetCacheMetadata | None) -> DatasetCacheMetadata:
    settings = get_retrieval_cache_settings()
    if index_cache is None:
        return DatasetCacheMetadata(
            cache_enabled=settings.enabled,
            cache_entry_count=_CACHE.entry_count,
            cache_max_entries=settings.max_entries,
            cache_ttl_seconds=settings.ttl_seconds,
        )
    return DatasetCacheMetadata(
        cache_enabled=settings.enabled,
        index_cache_hit=index_cache.index_cache_hit,
        index_cache_key=index_cache.index_cache_key,
        cache_entry_count=_CACHE.entry_count,
        cache_max_entries=settings.max_entries,
        cache_ttl_seconds=settings.ttl_seconds,
        cache_invalidated_reason=index_cache.cache_invalidated_reason,
    )


def get_cached_dataset_index(
    *,
    dataset_dir: str | Path | None,
    record_limit: int,
    build_fn: Callable[[], Any],
) -> tuple[Any, DatasetCacheMetadata, str]:
    return _CACHE.get_or_build_dataset_index(dataset_dir=dataset_dir, record_limit=record_limit, build_fn=build_fn)


def get_cached_retrieval_results(
    *,
    index_cache_key: str,
    query: str,
    limit: int,
    build_fn: Callable[[], Any],
) -> tuple[Any, DatasetCacheMetadata, str]:
    return _CACHE.get_or_build_retrieval_results(index_cache_key=index_cache_key, query=query, limit=limit, build_fn=build_fn)


def reset_retrieval_cache() -> None:
    _CACHE.reset()


def _cache_metadata(**kwargs: Any) -> DatasetCacheMetadata:
    return DatasetCacheMetadata(**kwargs)


def _expired(entry: CacheValue, ttl_seconds: int) -> bool:
    if ttl_seconds <= 0:
        return True
    return (time.monotonic() - entry.created_at) > ttl_seconds


def _fingerprint(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_cache_key(value: str) -> str:
    return value[:12]


def _merged_entry_count(index_cache: DatasetCacheMetadata | None, retrieval_cache: DatasetCacheMetadata | None) -> int:
    values = [value for value in ((index_cache.cache_entry_count if index_cache else 0), (retrieval_cache.cache_entry_count if retrieval_cache else 0)) if value]
    return max(values, default=0)


def _first_reason(index_cache: DatasetCacheMetadata | None, retrieval_cache: DatasetCacheMetadata | None) -> str | None:
    for item in (index_cache, retrieval_cache):
        if item and item.cache_invalidated_reason:
            return item.cache_invalidated_reason
    return None


_CACHE = RetrievalCacheStore()
