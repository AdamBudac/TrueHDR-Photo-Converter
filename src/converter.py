"""Image converter – encodes SDR and HDR images using native Python libraries
(``imagecodecs``, ``pillow-heif``, ``OpenEXR``) and optional ``avifgainmaputil``
for ISO 21496-1 AVIF Gain Map outputs.

All functions are **stateless**; they receive everything they need as arguments.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
import threading
import traceback
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple
from uuid import uuid4

from src.exr_encoder import encode_hdr_rgb16_to_exr
from src.models import AppSettings, TOOLS_FOR_CODECS, TOOLS_FOR_GAINMAP
from src.python_encoders import (
    encode_hdr_gm_jpeg,
    encode_hdr_pq_avif,
    encode_hdr_pq_heic,
    encode_hdr_pq_jxl,
    encode_sdr_avif,
    encode_sdr_heic,
    encode_sdr_jpeg,
    encode_sdr_jxl,
    load_hdr_png,
    load_sdr_png,
)
from src.results import (
    CommandAttemptFailure,
    ImageConversionResult,
    OutputResult,
    OutputStatus,
    StepResult,
    StepStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HDR_SUFFIX_RE = re.compile(r"_HDR(?=(?:_Duplicate\d+)?$)", re.IGNORECASE)


def required_tools_missing(codec: str, tool_map: Dict[str, bool]) -> List[str]:
    """Return the list of tools required by *codec* that are **not** available."""
    required = TOOLS_FOR_CODECS.get(codec, [])
    return [t for t in required if not tool_map.get(t, False)]


def required_tools_missing_gainmap(
    codec: str, tool_map: Dict[str, bool], has_sdr: bool
) -> List[str]:
    """Return missing tools required for HDR/GainMap encoding of *codec*."""
    required = list(TOOLS_FOR_GAINMAP.get(codec, []))
    if codec == "avif" and not has_sdr and "imagecodecs_python" not in required:
        required.append("imagecodecs_python")
    return [t for t in required if not tool_map.get(t, False)]


def hdr_output_stem(png_file: Path, variant: str) -> Path:
    """Derive an HDR output stem replacing ``_HDR`` with ``_HDR-PQ`` or ``_HDR-GM``."""
    stem_name = png_file.stem
    if _HDR_SUFFIX_RE.search(stem_name):
        new_name = _HDR_SUFFIX_RE.sub(f"_{variant}", stem_name, count=1)
    else:
        new_name = f"{stem_name}_{variant}"
    return png_file.with_name(new_name)


class ProcessRunner:
    """Manages execution of subprocesses and cooperative cancellation."""

    def __init__(self):
        self._active_process: Optional[subprocess.Popen] = None
        self._cancelled = False
        self._lock = threading.Lock()

    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def cancel(self) -> None:
        """Mark as cancelled and kill the currently running process if any."""
        with self._lock:
            self._cancelled = True
            if self._active_process is not None:
                try:
                    self._active_process.kill()
                except Exception:
                    pass

    def run_cmd(self, command: List[str], logger: logging.Logger) -> None:
        """Execute one command attempt as a subprocess."""
        with self._lock:
            if self._cancelled:
                raise InterruptedError("Cancelled by user")

        logger.info("Running: %s", format_command(command))
        creationflags = 0
        startupinfo = None
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
            startupinfo=startupinfo,
        )

        with self._lock:
            self._active_process = proc
            cancel_after_start = self._cancelled

        if cancel_after_start:
            try:
                proc.kill()
            except Exception:
                pass

        try:
            stdout, stderr = proc.communicate()
        finally:
            with self._lock:
                if self._active_process is proc:
                    self._active_process = None

        with self._lock:
            if self._cancelled:
                raise InterruptedError("Cancelled by user")

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, command, stdout, stderr)


# ---------------------------------------------------------------------------
# Command & Python encoder execution helpers (retry + diagnostics)
# ---------------------------------------------------------------------------

MAX_COMMAND_ATTEMPTS = 2
MAX_DIAGNOSTIC_CHARS = 64 * 1024


class MissingCommandOutputError(RuntimeError):
    """Raised when an encoder step completed without creating a usable output."""


def format_command(command: Sequence[str]) -> str:
    """Return a copy/paste-friendly representation of *command*."""
    if os.name == "nt":
        return subprocess.list2cmdline(list(command))
    return shlex.join(command)


def _decode_output(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode(errors="replace")
    else:
        text = str(value)
    if len(text) <= MAX_DIAGNOSTIC_CHARS:
        return text
    omitted = len(text) - MAX_DIAGNOSTIC_CHARS
    return f"{text[:MAX_DIAGNOSTIC_CHARS]}\n... [{omitted} characters truncated]"


def _capture_attempt_failure(
    attempt: int, exc: BaseException
) -> CommandAttemptFailure:
    return_code = None
    stdout = ""
    stderr = ""
    if isinstance(exc, subprocess.CalledProcessError):
        return_code = exc.returncode
        stdout = _decode_output(exc.stdout)
        stderr = _decode_output(exc.stderr)
    return CommandAttemptFailure(
        attempt=attempt,
        error_type=type(exc).__name__,
        message=str(exc),
        return_code=return_code,
        stdout=stdout,
        stderr=stderr,
        traceback_text=traceback.format_exc(),
    )


def _last_nonempty_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _log_final_command_failure(
    logger: logging.Logger,
    image_path: Path,
    codec: str,
    stage: str,
    command: Sequence[str],
    failures: Sequence[CommandAttemptFailure],
    dependent_step: Optional[str] = None,
) -> None:
    lines = [
        "COMMAND_FAILED",
        f"Image: {image_path}",
        f"Codec: {codec}",
        f"Stage: {stage}",
        f"Command: {format_command(command)}",
        f"Attempts: {len(failures)}/{MAX_COMMAND_ATTEMPTS}",
    ]
    if failures and failures[-1].return_code is not None:
        lines.append(f"Return code: {failures[-1].return_code}")
    if dependent_step:
        lines.append(f"Dependent step skipped: {dependent_step}")

    for failure in failures:
        lines.extend(
            [
                "",
                f"Attempt {failure.attempt} error: "
                f"{failure.error_type}: {failure.message}",
            ]
        )
        if failure.stdout:
            lines.extend([f"Attempt {failure.attempt} stdout:", failure.stdout])
        if failure.stderr:
            lines.extend([f"Attempt {failure.attempt} stderr:", failure.stderr])

    if failures:
        lines.extend(["", "Final traceback:", failures[-1].traceback_text])
    lines.extend(["", "-" * 80])
    logger.error("\n".join(lines), extra={"error_log": True})


def log_operation_failure(
    logger: logging.Logger,
    image_path: Path,
    operation: str,
    exc: BaseException,
    details: Optional[str] = None,
) -> None:
    """Write one non-command, image-level failure to both run logs."""
    lines = [
        "OPERATION_FAILED",
        f"Image: {image_path}",
        f"Operation: {operation}",
    ]
    if details:
        lines.append(f"Details: {details}")
    lines.extend(
        [
            f"Error: {type(exc).__name__}: {exc}",
            "",
            "Traceback:",
            traceback.format_exc(),
            "",
            "-" * 80,
        ]
    )
    logger.error("\n".join(lines), extra={"error_log": True})


def _remove_partial_output(path: Path) -> None:
    path.unlink(missing_ok=True)


def _check_runner_cancelled(runner: ProcessRunner) -> None:
    if hasattr(runner, "is_cancelled"):
        if runner.is_cancelled():
            raise InterruptedError("Cancelled by user")
    elif getattr(runner, "_cancelled", False):
        raise InterruptedError("Cancelled by user")


def _run_step_with_retry(
    *,
    action: Callable[[], None],
    command_descriptor: Sequence[str],
    expected_output: Path,
    image_path: Path,
    codec: str,
    stage: str,
    runner: ProcessRunner,
    logger: logging.Logger,
    dependent_step: Optional[str] = None,
) -> StepResult:
    """Run an encoding action (subprocess or Python callable) at most twice."""
    failures: List[CommandAttemptFailure] = []
    cmd_tuple = tuple(command_descriptor)

    for attempt in range(1, MAX_COMMAND_ATTEMPTS + 1):
        _check_runner_cancelled(runner)
        try:
            _remove_partial_output(expected_output)
        except InterruptedError:
            raise
        except OSError as exc:
            failure = _capture_attempt_failure(attempt, exc)
            log_operation_failure(
                logger,
                image_path,
                f"prepare_{stage}",
                exc,
                f"Could not remove partial output before attempt {attempt}: "
                f"{expected_output}",
            )
            return StepResult(
                name=f"prepare_{stage}",
                status=StepStatus.FAILED,
                attempts=0,
                failures=[failure],
                reason=str(exc),
            )

        try:
            logger.info(
                "Encode attempt %s/%s for %s (%s: %s)",
                attempt,
                MAX_COMMAND_ATTEMPTS,
                image_path.name,
                codec,
                stage,
            )
            action()
            _check_runner_cancelled(runner)
            if (
                not expected_output.is_file()
                or expected_output.stat().st_size <= 0
            ):
                raise MissingCommandOutputError(
                    f"Encoder completed without a usable output: {expected_output}"
                )
            if attempt > 1:
                logger.info(
                    "Encoder recovered on attempt %s/%s for %s (%s: %s)",
                    attempt,
                    MAX_COMMAND_ATTEMPTS,
                    image_path.name,
                    codec,
                    stage,
                )
            return StepResult(
                name=stage,
                status=StepStatus.SUCCESS,
                command=cmd_tuple,
                attempts=attempt,
                failures=failures,
            )
        except InterruptedError:
            raise
        except Exception as exc:
            failure = _capture_attempt_failure(attempt, exc)
            failures.append(failure)
            diagnostic = _last_nonempty_line(failure.stderr) or failure.message
            if attempt < MAX_COMMAND_ATTEMPTS:
                logger.warning(
                    "Encoder failed for %s (%s: %s), attempt %s/%s: %s. Retrying.",
                    image_path.name,
                    codec,
                    stage,
                    attempt,
                    MAX_COMMAND_ATTEMPTS,
                    diagnostic,
                )
                continue

            _log_final_command_failure(
                logger,
                image_path,
                codec,
                stage,
                cmd_tuple,
                failures,
                dependent_step,
            )
            try:
                _remove_partial_output(expected_output)
            except OSError as cleanup_exc:
                logger.warning(
                    "Failed to remove partial output %s: %s",
                    expected_output,
                    cleanup_exc,
                )
            return StepResult(
                name=stage,
                status=StepStatus.FAILED,
                command=cmd_tuple,
                attempts=attempt,
                failures=failures,
                reason=diagnostic,
            )

    raise AssertionError("Retry loop terminated unexpectedly")


def _run_command_with_retry(
    *,
    command: List[str],
    expected_output: Path,
    image_path: Path,
    codec: str,
    stage: str,
    runner: ProcessRunner,
    logger: logging.Logger,
    dependent_step: Optional[str] = None,
) -> StepResult:
    """Run one external CLI command at most twice and return a structured result."""
    return _run_step_with_retry(
        action=lambda: runner.run_cmd(command, logger),
        command_descriptor=command,
        expected_output=expected_output,
        image_path=image_path,
        codec=codec,
        stage=stage,
        runner=runner,
        logger=logger,
        dependent_step=dependent_step,
    )


def _publish_output(
    *,
    temp_path: Path,
    final_path: Path,
    image_path: Path,
    codec: str,
    logger: logging.Logger,
) -> StepResult:
    stage = f"publish_{codec}"
    try:
        temp_path.replace(final_path)
        return StepResult(name=stage, status=StepStatus.SUCCESS)
    except OSError as exc:
        failure = _capture_attempt_failure(1, exc)
        log_operation_failure(
            logger,
            image_path,
            stage,
            exc,
            f"{temp_path} -> {final_path}",
        )
        return StepResult(
            name=stage,
            status=StepStatus.FAILED,
            attempts=1,
            failures=[failure],
            reason=str(exc),
        )


def _direct_output(
    *,
    codec: str,
    stage: str,
    command: List[str],
    temp_path: Path,
    final_path: Path,
    image_path: Path,
    runner: ProcessRunner,
    logger: logging.Logger,
) -> OutputResult:
    command_result = _run_command_with_retry(
        command=command,
        expected_output=temp_path,
        image_path=image_path,
        codec=codec,
        stage=stage,
        runner=runner,
        logger=logger,
    )
    steps = [command_result]
    if command_result.status == StepStatus.FAILED:
        return OutputResult(
            codec=codec,
            status=OutputStatus.FAILED,
            output_path=final_path,
            steps=steps,
            reason=command_result.reason,
        )

    publish_result = _publish_output(
        temp_path=temp_path,
        final_path=final_path,
        image_path=image_path,
        codec=codec,
        logger=logger,
    )
    steps.append(publish_result)
    return OutputResult(
        codec=codec,
        status=(
            OutputStatus.SUCCESS
            if publish_result.status == StepStatus.SUCCESS
            else OutputStatus.FAILED
        ),
        output_path=final_path,
        steps=steps,
        reason=publish_result.reason,
    )


def _python_output(
    *,
    codec: str,
    stage: str,
    descriptor: Sequence[str],
    action: Callable[[], None],
    temp_path: Path,
    final_path: Path,
    image_path: Path,
    runner: ProcessRunner,
    logger: logging.Logger,
) -> OutputResult:
    step_result = _run_step_with_retry(
        action=action,
        command_descriptor=descriptor,
        expected_output=temp_path,
        image_path=image_path,
        codec=codec,
        stage=stage,
        runner=runner,
        logger=logger,
    )
    steps = [step_result]
    if step_result.status == StepStatus.FAILED:
        return OutputResult(
            codec=codec,
            status=OutputStatus.FAILED,
            output_path=final_path,
            steps=steps,
            reason=step_result.reason,
        )

    publish_result = _publish_output(
        temp_path=temp_path,
        final_path=final_path,
        image_path=image_path,
        codec=codec,
        logger=logger,
    )
    steps.append(publish_result)
    return OutputResult(
        codec=codec,
        status=(
            OutputStatus.SUCCESS
            if publish_result.status == StepStatus.SUCCESS
            else OutputStatus.FAILED
        ),
        output_path=final_path,
        steps=steps,
        reason=publish_result.reason,
    )


def _unavailable_output(
    codec: str, image_path: Path, missing_tools: Sequence[str], logger: logging.Logger
) -> OutputResult:
    reason = f"Missing tools: {', '.join(missing_tools)}"
    logger.warning("Skipping %s for %s – %s", codec, image_path.name, reason)
    return OutputResult(codec=codec, status=OutputStatus.SKIPPED, reason=reason)


def _cleanup_temp_files(paths: Sequence[Path], logger: logging.Logger) -> None:
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Failed to clean temporary file %s: %s", path, exc)


# ---------------------------------------------------------------------------
# SDR conversion (native Python: imagecodecs + pillow-heif)
# ---------------------------------------------------------------------------

def convert_sdr(
    png_file: Path,
    settings: AppSettings,
    tool_map: Dict[str, bool],
    runner: ProcessRunner,
    logger: logging.Logger,
) -> ImageConversionResult:
    """Convert one SDR PNG while isolating failures between codec outputs."""
    result = ImageConversionResult(source_path=png_file)
    stem = png_file.with_suffix("")
    temp_base = png_file.with_name(f"Tempfile_{uuid4().hex}")
    temp_jpg = temp_base.with_suffix(".jpg")
    temp_jxl = temp_base.with_suffix(".jxl")
    temp_heic = temp_base.with_suffix(".heic")
    temp_avif = temp_base.with_suffix(".avif")
    temp_files = [temp_jpg, temp_jxl, temp_heic, temp_avif]
    _cleanup_temp_files(temp_files, logger)

    sdr_cache: Optional[Tuple[object, Optional[bytes]]] = None

    def _get_sdr_data() -> Tuple[object, Optional[bytes]]:
        nonlocal sdr_cache
        if sdr_cache is None:
            sdr_cache = load_sdr_png(png_file)
        return sdr_cache

    try:
        if settings.codec_enabled.get("jpeg"):
            missing = required_tools_missing("jpeg", tool_map)
            if missing:
                result.outputs.append(
                    _unavailable_output("jpeg", png_file, missing, logger)
                )
            else:
                q = settings.codec_quality["jpeg"]
                result.outputs.append(
                    _python_output(
                        codec="jpeg",
                        stage="png_to_jpeg",
                        descriptor=["imagecodecs.jpeg8_encode", f"quality={q}", str(png_file)],
                        action=lambda: encode_sdr_jpeg(*_get_sdr_data(), temp_jpg, q),
                        temp_path=temp_jpg,
                        final_path=stem.with_suffix(".jpg"),
                        image_path=png_file,
                        runner=runner,
                        logger=logger,
                    )
                )

        if settings.codec_enabled.get("jpegxl"):
            missing = required_tools_missing("jpegxl", tool_map)
            if missing:
                result.outputs.append(
                    _unavailable_output("jpegxl", png_file, missing, logger)
                )
            else:
                result.outputs.append(
                    _direct_output(
                        codec="jpegxl",
                        stage="png_to_jpegxl",
                        command=[
                            "cjxl",
                            str(png_file),
                            str(temp_jxl),
                            "--quality",
                            str(settings.codec_quality["jpegxl"]),
                            "--modular",
                            "0",
                            "--effort",
                            "7",
                            "--brotli_effort",
                            "11",
                            "--num_threads",
                            "-1",
                            "--gaborish",
                            "1",
                        ],
                        temp_path=temp_jxl,
                        final_path=stem.with_suffix(".jxl"),
                        image_path=png_file,
                        runner=runner,
                        logger=logger,
                    )
                )

        if settings.codec_enabled.get("heic"):
            missing = required_tools_missing("heic", tool_map)
            if missing:
                result.outputs.append(
                    _unavailable_output("heic", png_file, missing, logger)
                )
            else:
                q = settings.codec_quality["heic"]
                result.outputs.append(
                    _python_output(
                        codec="heic",
                        stage="png_to_heic",
                        descriptor=["pillow_heif.save", f"quality={q}", "420", str(png_file)],
                        action=lambda: encode_sdr_heic(*_get_sdr_data(), temp_heic, q),
                        temp_path=temp_heic,
                        final_path=stem.with_suffix(".heic"),
                        image_path=png_file,
                        runner=runner,
                        logger=logger,
                    )
                )

        if settings.codec_enabled.get("avif"):
            missing = required_tools_missing("avif", tool_map)
            if missing:
                result.outputs.append(
                    _unavailable_output("avif", png_file, missing, logger)
                )
            else:
                q = settings.codec_quality["avif"]
                result.outputs.append(
                    _python_output(
                        codec="avif",
                        stage="png_to_avif",
                        descriptor=["imagecodecs.avif_encode", f"quality={q}", "8bit", str(png_file)],
                        action=lambda: encode_sdr_avif(*_get_sdr_data(), temp_avif, q),
                        temp_path=temp_avif,
                        final_path=stem.with_suffix(".avif"),
                        image_path=png_file,
                        runner=runner,
                        logger=logger,
                    )
                )
    finally:
        _cleanup_temp_files(temp_files, logger)

    return result


# ---------------------------------------------------------------------------
# HDR conversion (HDR/PQ, HDR/GainMap, and independent linear HDR EXR)
# ---------------------------------------------------------------------------

def _encode_hdr_gm_avif(
    *,
    png_file: Path,
    sdr_file: Optional[Path],
    gm_stem: Path,
    existing_sc0_jpg: Optional[Path],
    get_hdr_data: Callable[[], Tuple[object, Optional[bytes]]],
    temp_sc0_jpg: Path,
    temp_avif_gm: Path,
    settings: AppSettings,
    tool_map: Dict[str, bool],
    runner: ProcessRunner,
    logger: logging.Logger,
) -> OutputResult:
    """Encode ISO 21496-1 AVIF Gain Map via ``avifgainmaputil combine``.

    Uses the paired SDR PNG directly when available; otherwise generates an
    auto tone-mapped SDR JPEG via native Python ``imagecodecs.ultrahdr_encode``
    (Scenario 0) with zero ``ffmpeg`` / ``ultrahdr_app`` CLI dependency.
    """
    has_sdr = sdr_file is not None and sdr_file.is_file()
    missing = required_tools_missing_gainmap("avif", tool_map, has_sdr=has_sdr)
    if missing:
        return _unavailable_output("avif_gm", png_file, missing, logger)

    final_path = gm_stem.with_suffix(".avif")
    steps: List[StepResult] = []
    q = str(settings.codec_quality["avif"])

    base_input: Path
    cicp_base = "1/13/1"
    if has_sdr and sdr_file is not None:
        base_input = sdr_file
    elif existing_sc0_jpg is not None and existing_sc0_jpg.is_file():
        base_input = existing_sc0_jpg
        cicp_base = "12/13/1"
    else:
        logger.info(
            "No paired SDR PNG for %s – generating auto SDR base via Python libultrahdr for AVIF GainMap",
            png_file.name,
        )
        sc0_step = _run_step_with_retry(
            action=lambda: encode_hdr_gm_jpeg(get_hdr_data()[0], None, temp_sc0_jpg, 95),
            command_descriptor=["imagecodecs.ultrahdr_encode", "scenario=0", str(png_file)],
            expected_output=temp_sc0_jpg,
            image_path=png_file,
            codec="avif_gm",
            stage="ultrahdr_auto_sdr",
            runner=runner,
            logger=logger,
            dependent_step="avif_gainmap_combine",
        )
        steps.append(sc0_step)
        if sc0_step.status == StepStatus.FAILED:
            steps.append(
                StepResult(
                    name="avif_gainmap_combine",
                    status=StepStatus.SKIPPED_DEPENDENCY,
                    command=("avifgainmaputil",),
                    reason="Skipped because ultrahdr_auto_sdr failed",
                )
            )
            return OutputResult(
                codec="avif_gm",
                status=OutputStatus.FAILED,
                output_path=final_path,
                steps=steps,
                reason=sc0_step.reason,
            )
        base_input = temp_sc0_jpg
        cicp_base = "12/13/1"

    combine_step = _run_command_with_retry(
        command=[
            "avifgainmaputil",
            "combine",
            str(base_input),
            str(png_file),
            str(temp_avif_gm),
            "--ignore-profile",
            "--cicp-base",
            cicp_base,
            "--cicp-alternate",
            "9/16/9",
            "-y",
            "420",
            "-d",
            "8",
            "--yuv-gain-map",
            "420",
            "--depth-gain-map",
            "8",
            "-q",
            q,
            "--qgain-map",
            q,
            "-s",
            "6",
            "-j",
            "all",
        ],
        expected_output=temp_avif_gm,
        image_path=png_file,
        codec="avif_gm",
        stage="avif_gainmap_combine",
        runner=runner,
        logger=logger,
    )
    steps.append(combine_step)
    if combine_step.status == StepStatus.FAILED:
        return OutputResult(
            codec="avif_gm",
            status=OutputStatus.FAILED,
            output_path=final_path,
            steps=steps,
            reason=combine_step.reason,
        )

    publish_result = _publish_output(
        temp_path=temp_avif_gm,
        final_path=final_path,
        image_path=png_file,
        codec="avif_gm",
        logger=logger,
    )
    steps.append(publish_result)
    return OutputResult(
        codec="avif_gm",
        status=(
            OutputStatus.SUCCESS
            if publish_result.status == StepStatus.SUCCESS
            else OutputStatus.FAILED
        ),
        output_path=final_path,
        steps=steps,
        reason=publish_result.reason,
    )


def convert_hdr(
    png_file: Path,
    settings: AppSettings,
    tool_map: Dict[str, bool],
    runner: ProcessRunner,
    logger: logging.Logger,
    sdr_file: Optional[Path] = None,
) -> ImageConversionResult:
    """Convert one HDR PNG to HDR-PQ, HDR-GainMap, and/or linear HDR EXR outputs."""
    result = ImageConversionResult(source_path=png_file)
    any_hdr_enabled = bool(settings.hdr_pq_enabled or settings.hdr_gm_enabled)
    pq_stem = hdr_output_stem(png_file, "HDR-PQ")
    gm_stem = hdr_output_stem(png_file, "HDR-GM")
    temp_base = png_file.with_name(f"Tempfile_{uuid4().hex}")
    temp_jxl = temp_base.with_suffix(".jxl")
    temp_heic = temp_base.with_suffix(".heic")
    temp_avif = temp_base.with_suffix(".avif")
    temp_exr = temp_base.with_suffix(".exr")
    temp_uhdr_jpg = temp_base.with_name(f"{temp_base.name}_gm.jpg")
    temp_sc0_jpg = temp_base.with_name(f"{temp_base.name}_sc0.jpg")
    temp_avif_gm = temp_base.with_name(f"{temp_base.name}_gm.avif")
    temp_files = [
        temp_jxl,
        temp_heic,
        temp_avif,
        temp_exr,
        temp_uhdr_jpg,
        temp_sc0_jpg,
        temp_avif_gm,
    ]
    _cleanup_temp_files(temp_files, logger)

    hdr_cache: Optional[Tuple[object, Optional[bytes]]] = None
    sdr_cache: Tuple[Optional[object], Optional[bytes]] = (None, None)
    sdr_loaded = False

    def _get_hdr_data() -> Tuple[object, Optional[bytes]]:
        nonlocal hdr_cache
        if hdr_cache is None:
            hdr_cache = load_hdr_png(png_file)
        return hdr_cache

    def _get_sdr_data() -> Tuple[Optional[object], Optional[bytes]]:
        nonlocal sdr_cache, sdr_loaded
        if not sdr_loaded:
            sdr_loaded = True
            if sdr_file is not None and sdr_file.is_file():
                sdr_cache = load_sdr_png(sdr_file)
        return sdr_cache

    try:
        # --- Single-variant HDR codecs (run once if EITHER HDR/PQ or HDR/GM is checked) ---
        if any_hdr_enabled:
            # JXL currently has no CLI GainMap support: always emit once as *_HDR-PQ.jxl
            if settings.codec_enabled.get("jpegxl"):
                missing = required_tools_missing("jpegxl", tool_map)
                if missing:
                    result.outputs.append(
                        _unavailable_output("jpegxl", png_file, missing, logger)
                    )
                else:
                    result.outputs.append(
                        _direct_output(
                            codec="jpegxl",
                            stage="png_to_jpegxl_hdr_pq",
                            command=[
                                "cjxl",
                                str(png_file),
                                str(temp_jxl),
                                "--quality",
                                str(settings.codec_quality["jpegxl"]),
                                "--modular",
                                "0",
                                "--effort",
                                "7",
                                "--brotli_effort",
                                "11",
                                "--num_threads",
                                "-1",
                                "--gaborish",
                                "1",
                                "-x",
                                "color_space=RGB_D65_202_Rel_PeQ",
                            ],
                            temp_path=temp_jxl,
                            final_path=pq_stem.with_suffix(".jxl"),
                            image_path=png_file,
                            runner=runner,
                            logger=logger,
                        )
                    )

            # HEIC currently has no Windows ISO 21496-1 GainMap support:
            # always emit once as *_HDR-PQ.heic
            if settings.codec_enabled.get("heic"):
                missing = required_tools_missing("heic", tool_map)
                if missing:
                    result.outputs.append(
                        _unavailable_output("heic", png_file, missing, logger)
                    )
                else:
                    q = settings.codec_quality["heic"]
                    result.outputs.append(
                        _python_output(
                            codec="heic",
                            stage="png_to_heic_hdr_pq",
                            descriptor=["pillow_heif.save", f"quality={q}", "10bit_pq", str(png_file)],
                            action=lambda: encode_hdr_pq_heic(*_get_hdr_data(), temp_heic, q),
                            temp_path=temp_heic,
                            final_path=pq_stem.with_suffix(".heic"),
                            image_path=png_file,
                            runner=runner,
                            logger=logger,
                        )
                    )

        # --- Linear HDR EXR (*_HDR.exr, independent of HDR/PQ & HDR/GM) -----
        if settings.codec_enabled.get("exr"):
            missing = required_tools_missing("exr", tool_map)
            if missing:
                result.outputs.append(
                    _unavailable_output("exr", png_file, missing, logger)
                )
            else:
                comp = settings.exr_compression
                result.outputs.append(
                    _python_output(
                        codec="exr",
                        stage="png_to_exr_hdr_python",
                        descriptor=["OpenEXR.File", f"compression={comp}", "rec2020_linear", str(png_file)],
                        action=lambda: encode_hdr_rgb16_to_exr(
                            _get_hdr_data()[0], temp_exr, compression=comp
                        ),
                        temp_path=temp_exr,
                        final_path=png_file.with_suffix(".exr"),
                        image_path=png_file,
                        runner=runner,
                        logger=logger,
                    )
                )

        # --- HDR/PQ outputs (*_HDR-PQ.*) ------------------------------------
        if settings.hdr_pq_enabled:
            if settings.codec_enabled.get("avif"):
                missing = required_tools_missing("avif", tool_map)
                if missing:
                    result.outputs.append(
                        _unavailable_output("avif", png_file, missing, logger)
                    )
                else:
                    q = settings.codec_quality["avif"]
                    result.outputs.append(
                        _python_output(
                            codec="avif",
                            stage="png_to_avif_hdr_pq",
                            descriptor=["imagecodecs.avif_encode", f"quality={q}", "10bit_pq", str(png_file)],
                            action=lambda: encode_hdr_pq_avif(*_get_hdr_data(), temp_avif, q),
                            temp_path=temp_avif,
                            final_path=pq_stem.with_suffix(".avif"),
                            image_path=png_file,
                            runner=runner,
                            logger=logger,
                        )
                    )

        # --- HDR/GainMap outputs (*_HDR-GM.*) -------------------------------
        if settings.hdr_gm_enabled:
            produced_sc0_jpg: Optional[Path] = None

            if settings.codec_enabled.get("jpeg"):
                has_sdr = sdr_file is not None and sdr_file.is_file()
                missing = required_tools_missing_gainmap("jpeg", tool_map, has_sdr=has_sdr)
                if missing:
                    result.outputs.append(
                        _unavailable_output("jpeg_gm", png_file, missing, logger)
                    )
                else:
                    q = settings.codec_quality["jpeg"]
                    scenario_label = "paired_sdr" if has_sdr else "auto_sdr"
                    gm_jpeg_res = _python_output(
                        codec="jpeg_gm",
                        stage="ultrahdr_encode",
                        descriptor=["imagecodecs.ultrahdr_encode", f"quality={q}", scenario_label, str(png_file)],
                        action=lambda: encode_hdr_gm_jpeg(
                            _get_hdr_data()[0],
                            _get_sdr_data()[0],
                            temp_uhdr_jpg,
                            q,
                            sdr_icc=_get_sdr_data()[1],
                        ),
                        temp_path=temp_uhdr_jpg,
                        final_path=gm_stem.with_suffix(".jpg"),
                        image_path=png_file,
                        runner=runner,
                        logger=logger,
                    )
                    result.outputs.append(gm_jpeg_res)
                    if (
                        not has_sdr
                        and gm_jpeg_res.status == OutputStatus.SUCCESS
                        and gm_jpeg_res.output_path is not None
                    ):
                        produced_sc0_jpg = gm_jpeg_res.output_path

            if settings.codec_enabled.get("avif"):
                gm_avif_res = _encode_hdr_gm_avif(
                    png_file=png_file,
                    sdr_file=sdr_file,
                    gm_stem=gm_stem,
                    existing_sc0_jpg=produced_sc0_jpg,
                    get_hdr_data=_get_hdr_data,
                    temp_sc0_jpg=temp_sc0_jpg,
                    temp_avif_gm=temp_avif_gm,
                    settings=settings,
                    tool_map=tool_map,
                    runner=runner,
                    logger=logger,
                )
                result.outputs.append(gm_avif_res)
    finally:
        _cleanup_temp_files(temp_files, logger)

    return result
