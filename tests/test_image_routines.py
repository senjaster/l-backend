"""Unit tests for fetch_images_background and ImageBackgroundFetcher"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4

from app.models.image import Image, ImageType, ImageUploadStatus
from app.utils.image_routines import ImageBackgroundFetcher, fetch_images_background


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_image(
    upload_status: ImageUploadStatus = ImageUploadStatus.UNKNOWN,
    server_uploaded_at: datetime | None = None,
) -> Image:
    return Image(
        id=uuid4(),
        plant_id=uuid4(),
        original_file_name="test.jpg",
        image_type=ImageType.VISUAL,
        is_deleted=False,
        server_modified_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        upload_status=upload_status,
        server_uploaded_at=server_uploaded_at,
    )


def _make_fetcher(base_url: str = "http://localhost:8000", s3_service=None) -> ImageBackgroundFetcher:
    if s3_service is None:
        s3_service = MagicMock()
        s3_service.get_metadata = AsyncMock(return_value=None)
    return ImageBackgroundFetcher(base_url=base_url, batch_size=10, s3_service=s3_service)


# ── ImageBackgroundFetcher.fetch_all_images ───────────────────────────────────


async def test_fetch_all_images_returns_images_from_repo():
    """fetch_all_images delegates to image_repo.get_all and returns the result."""
    images = [_make_image(), _make_image()]
    mock_conn = MagicMock()
    fetcher = _make_fetcher()

    with patch("app.utils.image_routines.image_repo") as mock_repo:
        mock_repo.get_all = AsyncMock(return_value=images)
        result = await fetcher.fetch_all_images(mock_conn)

    assert result == images
    mock_repo.get_all.assert_awaited_once()


async def test_fetch_all_images_passes_filters_to_repo():
    """fetch_all_images forwards upload_status, modified_since, uploaded_since, limit."""
    mock_conn = MagicMock()
    fetcher = _make_fetcher()
    modified_since = datetime(2024, 6, 1, tzinfo=timezone.utc)
    uploaded_since = datetime(2024, 5, 1, tzinfo=timezone.utc)

    with patch("app.utils.image_routines.image_repo") as mock_repo:
        mock_repo.get_all = AsyncMock(return_value=[])
        await fetcher.fetch_all_images(
            mock_conn,
            upload_status=ImageUploadStatus.UNKNOWN,
            modified_since=modified_since,
            uploaded_since=uploaded_since,
            limit=50,
        )

    mock_repo.get_all.assert_awaited_once_with(
        mock_conn,
        upload_status=ImageUploadStatus.UNKNOWN.value,
        modified_since=modified_since,
        uploaded_since=uploaded_since,
        limit=50,
    )


async def test_fetch_all_images_uses_default_dates_when_none_given():
    """When modified_since/uploaded_since are None, defaults to 2020-01-01."""
    mock_conn = MagicMock()
    fetcher = _make_fetcher()

    with patch("app.utils.image_routines.image_repo") as mock_repo:
        mock_repo.get_all = AsyncMock(return_value=[])
        await fetcher.fetch_all_images(mock_conn)

    _, kwargs = mock_repo.get_all.call_args
    assert kwargs["modified_since"] == datetime(2020, 1, 1)
    assert kwargs["uploaded_since"] == datetime(2020, 1, 1)


async def test_fetch_all_images_propagates_repo_exception():
    """fetch_all_images re-raises exceptions from the repository."""
    mock_conn = MagicMock()
    fetcher = _make_fetcher()

    with patch("app.utils.image_routines.image_repo") as mock_repo:
        mock_repo.get_all = AsyncMock(side_effect=RuntimeError("db error"))
        with pytest.raises(RuntimeError, match="db error"):
            await fetcher.fetch_all_images(mock_conn)


# ── ImageBackgroundFetcher._determine_image_status ────────────────────────────


async def test_determine_image_status_returns_uploaded_when_metadata_present():
    """_determine_image_status returns UPLOADED when S3 metadata exists."""
    s3_service = MagicMock()
    s3_service.get_metadata = AsyncMock(return_value={"last_modified": None})
    fetcher = _make_fetcher(s3_service=s3_service)
    image = _make_image()

    status, _ = await fetcher._determine_image_status(image)

    assert status == ImageUploadStatus.UPLOADED


async def test_determine_image_status_returns_missing_when_no_metadata():
    """_determine_image_status returns MISSING when S3 returns no metadata."""
    s3_service = MagicMock()
    s3_service.get_metadata = AsyncMock(return_value=None)
    fetcher = _make_fetcher(s3_service=s3_service)
    image = _make_image()

    status, _ = await fetcher._determine_image_status(image)

    assert status == ImageUploadStatus.MISSING


async def test_determine_image_status_uses_s3_last_modified_when_newer():
    """server_uploaded_at is set to S3 last_modified when it is newer than server_modified_at."""
    s3_last_modified = datetime(2025, 1, 1, tzinfo=timezone.utc)
    s3_service = MagicMock()
    s3_service.get_metadata = AsyncMock(return_value={"last_modified": s3_last_modified})
    fetcher = _make_fetcher(s3_service=s3_service)
    image = _make_image()  # server_modified_at = 2024-01-01

    _, server_uploaded_at = await fetcher._determine_image_status(image)

    assert server_uploaded_at == s3_last_modified


async def test_determine_image_status_falls_back_to_server_modified_at_when_s3_older():
    """server_uploaded_at falls back to image.server_modified_at when S3 date is older."""
    s3_last_modified = datetime(2023, 1, 1, tzinfo=timezone.utc)  # older than image
    s3_service = MagicMock()
    s3_service.get_metadata = AsyncMock(return_value={"last_modified": s3_last_modified})
    fetcher = _make_fetcher(s3_service=s3_service)
    image = _make_image()  # server_modified_at = 2024-01-01

    _, server_uploaded_at = await fetcher._determine_image_status(image)

    assert server_uploaded_at == image.server_modified_at


# ── ImageBackgroundFetcher.get_images_statuses_from_s3 ────────────────────────


async def test_get_images_statuses_from_s3_returns_updated_images():
    """get_images_statuses_from_s3 returns one updated Image per input image."""
    s3_service = MagicMock()
    s3_service.get_metadata = AsyncMock(return_value={"last_modified": None})
    fetcher = _make_fetcher(s3_service=s3_service)
    images = [_make_image(), _make_image()]

    result = await fetcher.get_images_statuses_from_s3(images)

    assert len(result) == len(images)
    assert all(img.upload_status == ImageUploadStatus.UPLOADED for img in result)


async def test_get_images_statuses_from_s3_empty_list():
    """get_images_statuses_from_s3 handles an empty image list gracefully."""
    fetcher = _make_fetcher()
    result = await fetcher.get_images_statuses_from_s3([])
    assert result == []


async def test_get_images_statuses_from_s3_does_not_mutate_originals():
    """get_images_statuses_from_s3 returns copies; originals are unchanged."""
    s3_service = MagicMock()
    s3_service.get_metadata = AsyncMock(return_value={"last_modified": None})
    fetcher = _make_fetcher(s3_service=s3_service)
    image = _make_image(upload_status=ImageUploadStatus.UNKNOWN)
    original_status = image.upload_status

    result = await fetcher.get_images_statuses_from_s3([image])

    assert image.upload_status == original_status  # original unchanged
    assert result[0].upload_status == ImageUploadStatus.UPLOADED


async def test_get_images_statuses_from_s3_marks_missing_when_not_in_s3():
    """Images absent from S3 are marked MISSING."""
    s3_service = MagicMock()
    s3_service.get_metadata = AsyncMock(return_value=None)
    fetcher = _make_fetcher(s3_service=s3_service)
    images = [_make_image()]

    result = await fetcher.get_images_statuses_from_s3(images)

    assert result[0].upload_status == ImageUploadStatus.MISSING


# ── fetch_images_background ───────────────────────────────────────────────────


async def test_fetch_images_background_returns_empty_when_server_unavailable():
    """fetch_images_background returns [] immediately when server is unreachable."""
    with patch(
        "app.utils.image_routines.check_server_availability",
        new=AsyncMock(return_value=False),
    ):
        result = await fetch_images_background(base_url="http://unreachable")

    assert result == []


async def test_fetch_images_background_fetches_and_updates_statuses():
    """
    Happy-path: server available → images fetched → S3 statuses resolved →
    update_upload_status called for each image.
    """
    images = [_make_image(), _make_image()]
    updated_images = [
        img.model_copy(update={"upload_status": ImageUploadStatus.UPLOADED})
        for img in images
    ]

    mock_conn = MagicMock()

    async def _fake_get_db():
        yield mock_conn

    mock_s3 = MagicMock()
    mock_s3.get_metadata = AsyncMock(return_value={"last_modified": None})

    mock_s3_ctx = MagicMock()
    mock_s3_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_s3_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.utils.image_routines.check_server_availability", new=AsyncMock(return_value=True)),
        patch("app.utils.image_routines.get_db_connection", side_effect=_fake_get_db),
        patch("app.utils.image_routines.s3_objects_service_ctx", return_value=mock_s3_ctx),
        patch("app.utils.image_routines.image_repo") as mock_repo,
    ):
        mock_repo.get_all = AsyncMock(return_value=images)
        mock_repo.get_by_id = AsyncMock(side_effect=lambda conn, image_id: next(
            (img for img in images if img.id == image_id), None
        ))
        mock_repo.save = AsyncMock(side_effect=lambda conn, img, force=False: img)

        result = await fetch_images_background(base_url="http://localhost:8000")

    # save must be called once per image (via update_image_upload_status_in_db)
    assert mock_repo.save.await_count == len(images)


async def test_fetch_images_background_skips_update_when_no_images():
    """When the DB returns no images, update_upload_status is never called."""
    mock_conn = MagicMock()

    async def _fake_get_db():
        yield mock_conn

    mock_s3 = MagicMock()

    mock_s3_ctx = MagicMock()
    mock_s3_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_s3_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.utils.image_routines.check_server_availability", new=AsyncMock(return_value=True)),
        patch("app.utils.image_routines.get_db_connection", side_effect=_fake_get_db),
        patch("app.utils.image_routines.s3_objects_service_ctx", return_value=mock_s3_ctx),
        patch("app.utils.image_routines.image_repo") as mock_repo,
    ):
        mock_repo.get_all = AsyncMock(return_value=[])
        mock_repo.get_by_id = AsyncMock(return_value=None)
        mock_repo.save = AsyncMock()

        await fetch_images_background(base_url="http://localhost:8000")

    mock_repo.save.assert_not_awaited()


async def test_fetch_images_background_passes_filters_to_fetcher():
    """Query parameters are forwarded to fetch_all_images."""
    mock_conn = MagicMock()

    async def _fake_get_db():
        yield mock_conn

    mock_s3 = MagicMock()
    mock_s3.get_metadata = AsyncMock(return_value=None)

    modified_since = datetime(2024, 3, 1, tzinfo=timezone.utc)
    uploaded_since = datetime(2024, 2, 1, tzinfo=timezone.utc)

    mock_s3_ctx = MagicMock()
    mock_s3_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_s3_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.utils.image_routines.check_server_availability", new=AsyncMock(return_value=True)),
        patch("app.utils.image_routines.get_db_connection", side_effect=_fake_get_db),
        patch("app.utils.image_routines.s3_objects_service_ctx", return_value=mock_s3_ctx),
        patch("app.utils.image_routines.image_repo") as mock_repo,
    ):
        mock_repo.get_all = AsyncMock(return_value=[])
        mock_repo.update_upload_status = AsyncMock()

        await fetch_images_background(
            base_url="http://localhost:8000",
            upload_status=ImageUploadStatus.UNKNOWN,
            modified_since=modified_since,
            uploaded_since=uploaded_since,
            batch_size=25,
            limit=100,
        )

    _, kwargs = mock_repo.get_all.call_args
    assert kwargs["upload_status"] == ImageUploadStatus.UNKNOWN.value
    assert kwargs["modified_since"] == modified_since
    assert kwargs["uploaded_since"] == uploaded_since
    assert kwargs["limit"] == 100


async def test_fetch_images_background_logs_error_on_exception(caplog):
    """Exceptions inside the DB block are caught and logged; function does not raise."""
    import logging

    mock_conn = MagicMock()

    async def _fake_get_db():
        yield mock_conn

    mock_s3 = MagicMock()

    mock_s3_ctx = MagicMock()
    mock_s3_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_s3_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.utils.image_routines.check_server_availability", new=AsyncMock(return_value=True)),
        patch("app.utils.image_routines.get_db_connection", side_effect=_fake_get_db),
        patch("app.utils.image_routines.s3_objects_service_ctx", return_value=mock_s3_ctx),
        patch("app.utils.image_routines.image_repo") as mock_repo,
        caplog.at_level(logging.ERROR, logger="app.utils.image_routines"),
    ):
        mock_repo.get_all = AsyncMock(side_effect=RuntimeError("boom"))

        # Should not raise
        await fetch_images_background(base_url="http://localhost:8000")

    assert any("boom" in record.message for record in caplog.records)


async def test_fetch_images_background_update_called_with_correct_args():
    """update_image_upload_status_in_db receives the image id and resolved status."""
    image = _make_image(upload_status=ImageUploadStatus.UNKNOWN)
    mock_conn = MagicMock()

    async def _fake_get_db():
        yield mock_conn

    mock_s3 = MagicMock()
    # S3 has the object → UPLOADED
    mock_s3.get_metadata = AsyncMock(return_value={"last_modified": None})

    mock_s3_ctx = MagicMock()
    mock_s3_ctx.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_s3_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.utils.image_routines.check_server_availability", new=AsyncMock(return_value=True)),
        patch("app.utils.image_routines.get_db_connection", side_effect=_fake_get_db),
        patch("app.utils.image_routines.s3_objects_service_ctx", return_value=mock_s3_ctx),
        patch("app.utils.image_routines.image_repo") as mock_repo,
    ):
        mock_repo.get_all = AsyncMock(return_value=[image])
        mock_repo.get_by_id = AsyncMock(return_value=image)
        mock_repo.save = AsyncMock(return_value=image)

        await fetch_images_background(base_url="http://localhost:8000")

    mock_repo.save.assert_awaited_once()
    saved_image = mock_repo.save.call_args[0][1]  # positional arg: (conn, image, ...)
    assert saved_image.id == image.id
    assert saved_image.upload_status == ImageUploadStatus.UPLOADED
