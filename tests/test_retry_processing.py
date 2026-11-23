from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import imagecodecs
import numpy as np
import pytest

import src.converter as converter_module
from src.config import attach_file_logger
from src.converter import ProcessRunner, convert_sdr
from src.models import AppSettings
from src.results import (
    ImageConversionResult,
    ImageStatus,
    OutputResult,
    OutputStatus,
    ProcessingOutcome,
    ProcessingSummary,
    StepResult,
    StepStatus,
)
from src.worker import ProcessingWorker


ALL_TOOLS = {
    "imagecodecs_python": True,
    "pillow_heif_python": True,
    "openexr_python": True,
    "cjxl": True,
    "avifgainmaputil": True,
}


def _write_tiny_png(path: Path) -> Path:
    arr = np.full((8, 8, 3), 128, dtype=np.uint8)
    path.write_bytes(imagecodecs.png_encode(arr))
    return path


@pytest.fixture
def test_logger():
    logger = logging.Logger("retry-processing-tests", level=logging.DEBUG)
    logger.propagate = False
    logger.addHandler(logging.NullHandler())
    yield logger
    for handler in list(logger.handlers):
        handler.flush()
        logger.removeHandler(handler)
        handler.close()


def _failure(stderr: str, return_code: int = 1) -> subprocess.CalledProcessError:
    return subprocess.CalledProcessError(
        return_code,
        ["fake-encoder"],
        output=b"",
        stderr=stderr.encode("utf-8"),
    )


def _settings(*enabled_codecs: str) -> AppSettings:
    settings = AppSettings()
    settings.rename_enabled = False
    settings.codec_enabled = {
        codec: codec in enabled_codecs
        for codec in ("jpeg", "jpegxl", "heic", "avif", "exr")
    }
    return settings


def _output_by_codec(result: ImageConversionResult) -> Dict[str, OutputResult]:
    return {output.codec: output for output in result.outputs}


def _flush_logger(logger: logging.Logger) -> None:
    for handler in logger.handlers:
        handler.flush()


def test_first_attempt_fails_and_second_attempt_succeeds(
    tmp_path: Path, test_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _write_tiny_png(tmp_path / "photo.png")
    outcomes: List[Optional[BaseException]] = [_failure("temporary encoder failure"), None]
    calls = []

    def fake_jpeg(rgb8, icc, out_path: Path, quality: int) -> Path:
        calls.append(("jpeg", quality))
        outcome = outcomes.pop(0) if outcomes else None
        if outcome is not None:
            raise outcome
        out_path.write_bytes(b"fake output")
        return out_path

    monkeypatch.setattr(converter_module, "encode_sdr_jpeg", fake_jpeg)

    result = convert_sdr(
        source,
        _settings("jpeg"),
        ALL_TOOLS,
        ProcessRunner(),
        test_logger,
    )

    jpeg = _output_by_codec(result)["jpeg"]
    assert jpeg.status == OutputStatus.SUCCESS
    assert jpeg.steps[0].status == StepStatus.SUCCESS
    assert jpeg.steps[0].attempts == 2
    assert len(jpeg.steps[0].failures) == 1
    assert len(calls) == 2
    assert source.with_suffix(".jpg").read_bytes() == b"fake output"


def test_partial_output_is_removed_before_retry(
    tmp_path: Path, test_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _write_tiny_png(tmp_path / "photo.png")
    attempts = 0

    def partial_jpeg(rgb8, icc, out_path: Path, quality: int) -> Path:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            out_path.write_bytes(b"partial")
            raise _failure("failed after writing a partial JPEG")
        assert not out_path.exists()
        out_path.write_bytes(b"complete JPEG")
        return out_path

    monkeypatch.setattr(converter_module, "encode_sdr_jpeg", partial_jpeg)

    result = convert_sdr(
        source,
        _settings("jpeg"),
        ALL_TOOLS,
        ProcessRunner(),
        test_logger,
    )

    jpeg = _output_by_codec(result)["jpeg"]
    assert jpeg.status == OutputStatus.SUCCESS
    assert jpeg.steps[0].attempts == 2
    assert source.with_suffix(".jpg").read_bytes() == b"complete JPEG"
    assert not list(tmp_path.glob("Tempfile_*"))


def test_native_sdr_jpeg_encodes_real_bytes(
    tmp_path: Path, test_logger: logging.Logger
) -> None:
    source = _write_tiny_png(tmp_path / "photo.png")

    result = convert_sdr(
        source,
        _settings("jpeg"),
        ALL_TOOLS,
        ProcessRunner(),
        test_logger,
    )

    jpeg = _output_by_codec(result)["jpeg"]
    assert jpeg.status == OutputStatus.SUCCESS
    assert source.with_suffix(".jpg").read_bytes()[:2] == b"\xff\xd8"


def test_failed_jpeg_continues_with_next_codec(
    tmp_path: Path, test_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _write_tiny_png(tmp_path / "photo.png")
    calls: List[str] = []

    def failing_jpeg(rgb8, icc, out_path: Path, quality: int) -> Path:
        calls.append("jpeg")
        raise _failure("jpeg encoder failure")

    class FakeCjxlRunner(ProcessRunner):
        def run_cmd(self, command: List[str], logger: logging.Logger) -> None:
            calls.append(command[0])
            Path(command[2]).write_bytes(b"jxl ok")

    monkeypatch.setattr(converter_module, "encode_sdr_jpeg", failing_jpeg)

    result = convert_sdr(
        source,
        _settings("jpeg", "jpegxl"),
        ALL_TOOLS,
        FakeCjxlRunner(),
        test_logger,
    )

    outputs = _output_by_codec(result)
    assert outputs["jpeg"].status == OutputStatus.FAILED
    assert outputs["jpeg"].steps[0].status == StepStatus.FAILED
    assert outputs["jpeg"].steps[0].attempts == 2
    assert outputs["jpegxl"].status == OutputStatus.SUCCESS
    assert calls == ["jpeg", "jpeg", "cjxl"]
    assert not source.with_suffix(".jpg").exists()
    assert source.with_suffix(".jxl").exists()


def test_interrupted_error_is_not_retried(
    tmp_path: Path, test_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _write_tiny_png(tmp_path / "photo.png")
    calls: List[str] = []

    def interrupted_jpeg(rgb8, icc, out_path: Path, quality: int) -> Path:
        calls.append("jpeg")
        raise InterruptedError("cancelled by test")

    monkeypatch.setattr(converter_module, "encode_sdr_jpeg", interrupted_jpeg)

    with pytest.raises(InterruptedError, match="cancelled by test"):
        convert_sdr(
            source,
            _settings("jpeg", "jpegxl"),
            ALL_TOOLS,
            ProcessRunner(),
            test_logger,
        )

    assert calls == ["jpeg"]
    assert not list(tmp_path.glob("Tempfile_*"))


def test_errors_log_contains_only_final_failures_with_command_and_stderr(
    tmp_path: Path, test_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _write_tiny_png(tmp_path / "photo.png")
    logging_log = tmp_path / "logging.log"
    errors_log = tmp_path / "errors.log"
    attach_file_logger(test_logger, logging_log, errors_log)
    errs = [_failure("final encoder failure one"), _failure("final encoder failure two")]

    def failing_jpeg(rgb8, icc, out_path: Path, quality: int) -> Path:
        raise errs.pop(0)

    monkeypatch.setattr(converter_module, "encode_sdr_jpeg", failing_jpeg)

    convert_sdr(
        source,
        _settings("jpeg"),
        ALL_TOOLS,
        ProcessRunner(),
        test_logger,
    )
    _flush_logger(test_logger)

    main_content = logging_log.read_text(encoding="utf-8")
    error_content = errors_log.read_text(encoding="utf-8")
    assert "final encoder failure one" in main_content
    assert "final encoder failure two" in main_content
    assert "COMMAND_FAILED" in error_content
    assert "Stage: png_to_jpeg" in error_content
    assert "Command: imagecodecs.jpeg8_encode" in error_content
    assert "Attempt 1 stderr:\nfinal encoder failure one" in error_content
    assert "Attempt 2 stderr:\nfinal encoder failure two" in error_content


def test_recovered_command_leaves_errors_log_empty(
    tmp_path: Path, test_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _write_tiny_png(tmp_path / "photo.png")
    logging_log = tmp_path / "logging.log"
    errors_log = tmp_path / "errors.log"
    attach_file_logger(test_logger, logging_log, errors_log)
    outcomes: List[Optional[BaseException]] = [_failure("transient encoder failure"), None]

    def flaky_jpeg(rgb8, icc, out_path: Path, quality: int) -> Path:
        exc = outcomes.pop(0) if outcomes else None
        if exc is not None:
            raise exc
        out_path.write_bytes(b"recovered")
        return out_path

    monkeypatch.setattr(converter_module, "encode_sdr_jpeg", flaky_jpeg)

    result = convert_sdr(
        source,
        _settings("jpeg"),
        ALL_TOOLS,
        ProcessRunner(),
        test_logger,
    )
    _flush_logger(test_logger)

    assert result.status == ImageStatus.SUCCESS
    assert errors_log.exists()
    assert errors_log.read_text(encoding="utf-8") == ""


def test_processing_summary_counters_and_outcomes(tmp_path: Path) -> None:
    summary = ProcessingSummary(
        output_dir=tmp_path,
        logging_log_path=tmp_path / "logging.log",
        rename_log_path=tmp_path / "rename.log",
        errors_log_path=tmp_path / "errors.log",
        discovered_images=4,
    )
    recovered = ImageConversionResult(
        source_path=tmp_path / "recovered.png",
        outputs=[
            OutputResult(
                codec="jpeg",
                status=OutputStatus.SUCCESS,
                steps=[
                    StepResult(
                        name="png_to_jpeg",
                        status=StepStatus.SUCCESS,
                        command=("imagecodecs.jpeg8_encode",),
                        attempts=2,
                    )
                ],
            )
        ],
    )
    partial = ImageConversionResult(
        source_path=tmp_path / "partial.png",
        outputs=[
            OutputResult(
                codec="jpeg",
                status=OutputStatus.FAILED,
                steps=[
                    StepResult(
                        name="png_to_jpeg",
                        status=StepStatus.FAILED,
                        command=("imagecodecs.jpeg8_encode",),
                        attempts=2,
                    )
                ],
            ),
            OutputResult(
                codec="jpegxl",
                status=OutputStatus.SUCCESS,
                steps=[
                    StepResult(
                        name="png_to_jpegxl",
                        status=StepStatus.SUCCESS,
                        command=("imagecodecs.jpegxl_encode",),
                        attempts=1,
                    )
                ],
            ),
        ],
    )
    failed = ImageConversionResult(
        source_path=tmp_path / "failed.png",
        outputs=[
            OutputResult(
                codec="avif",
                status=OutputStatus.FAILED,
                steps=[
                    StepResult(
                        name="png_to_avif",
                        status=StepStatus.FAILED,
                        command=("imagecodecs.avif_encode",),
                        attempts=1,
                    )
                ],
            )
        ],
    )
    skipped = ImageConversionResult(
        source_path=tmp_path / "skipped.png",
        outputs=[
            OutputResult(codec="heic", status=OutputStatus.SKIPPED)
        ],
        skipped_reason="HEIC tool unavailable",
    )

    summary.add_image_result(recovered)
    assert summary.outcome == ProcessingOutcome.RECOVERED
    summary.add_image_result(partial)
    summary.add_image_result(failed)
    summary.add_image_result(skipped)

    assert summary.processed_images == 3
    assert summary.successful_images == 1
    assert summary.partially_successful_images == 1
    assert summary.failed_images == 1
    assert summary.skipped_images == 1
    assert summary.successful_outputs == 2
    assert summary.failed_outputs == 2
    assert summary.skipped_outputs == 1
    assert summary.successful_commands == 2
    assert summary.failed_commands == 2
    assert summary.retried_commands == 2
    assert summary.recovered_commands == 1
    assert summary.dependency_skipped_commands == 0
    assert summary.not_processed_images == 0
    assert summary.outcome == ProcessingOutcome.PARTIAL


def test_worker_continues_with_next_image_and_reaches_total_progress(
    tmp_path: Path, test_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_tiny_png(tmp_path / "a.png")
    _write_tiny_png(tmp_path / "b.png")
    outcomes: List[Optional[BaseException]] = [
        _failure("a failed once"),
        _failure("a failed twice"),
        None,
    ]
    calls: List[str] = []

    def scripted_jpeg(rgb8, icc, out_path: Path, quality: int) -> Path:
        calls.append("jpeg")
        exc = outcomes.pop(0) if outcomes else None
        if exc is not None:
            raise exc
        out_path.write_bytes(b"ok jpg")
        return out_path

    monkeypatch.setattr(converter_module, "encode_sdr_jpeg", scripted_jpeg)

    worker = ProcessingWorker(
        tmp_path,
        _settings("jpeg"),
        ALL_TOOLS,
        test_logger,
    )
    progress_updates = []

    def record_progress(current: int, total: int) -> None:
        progress_updates.append((current, total))

    worker.progress.connect(record_progress)
    summary = worker.process()

    assert calls == ["jpeg", "jpeg", "jpeg"]
    assert summary.discovered_images == 2
    assert summary.processed_images == 2
    assert summary.successful_images == 1
    assert summary.failed_images == 1
    assert summary.failed_commands == 1
    assert summary.dependency_skipped_commands == 0
    assert progress_updates == [(1, 2), (2, 2)]
    assert summary.outcome == ProcessingOutcome.PARTIAL
    assert not (tmp_path / "output" / "a.jpg").exists()
    assert (tmp_path / "output" / "b.jpg").exists()
