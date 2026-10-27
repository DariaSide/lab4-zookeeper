#!/usr/bin/env python3
"""ZooKeeper-coordinated checkpointable calculation with epoch fencing."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import signal
import socket
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import BadVersionError, NodeExistsError
from kazoo.protocol.states import EventType


ROOT = "/skill-pairs"
ELECTION = f"{ROOT}/election"
EPOCH = f"{ROOT}/epoch"
CHECKPOINT = f"{ROOT}/checkpoint"
RESULT = f"{ROOT}/result"
PUBLICATIONS = f"{ROOT}/publications"


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


INSTANCE = os.getenv("INSTANCE_ID", socket.gethostname())
RUN_ID = os.getenv("RUN_ID", "manual")
FENCING = os.getenv("FENCING", "0") == "1"
SESSION_TIMEOUT = env_int("SESSION_TIMEOUT_MS", 10_000) / 1000
WORK_UNITS = env_int("WORK_UNITS", 120)
UNIT_DELAY = float(os.getenv("UNIT_DELAY_SECONDS", "0.25"))
EXPECTED_PAIRS = env_int("EXPECTED_PAIRS", 22_286)
DATA_FILE = Path(os.getenv("DATA_FILE", "/app/data/pairs.ndjson"))


def make_logger() -> logging.Logger:
    log_dir = Path(os.getenv("LOG_DIR", "/app/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(INSTANCE)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s.%(msecs)03dZ %(levelname)s " + INSTANCE + " %(message)s", "%Y-%m-%dT%H:%M:%S")
    formatter.converter = time.gmtime
    file_handler = logging.FileHandler(log_dir / f"{RUN_ID}-{INSTANCE}.log")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.handlers[:] = [file_handler, stream_handler]
    return logger


LOG = make_logger()


def encode(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def decode(value: bytes) -> dict:
    return json.loads(value.decode())


@dataclass(frozen=True)
class Dataset:
    count: int
    digest: str
    source: str


def load_dataset() -> Dataset:
    digest = hashlib.sha256()
    count = 0
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{DATA_FILE}:{number}: invalid JSON: {exc}") from exc
                digest.update(encode(item) + b"\n")
                count += 1
        source = str(DATA_FILE)
    else:
        # Reproducible stand-in: one canonical record per unique pair from Lab 3.
        for index in range(EXPECTED_PAIRS):
            digest.update(encode({"pair_id": index}) + b"\n")
        count = EXPECTED_PAIRS
        source = "deterministic-demo"
    if count != EXPECTED_PAIRS:
        raise ValueError(f"pair count {count} does not match EXPECTED_PAIRS={EXPECTED_PAIRS}")
    return Dataset(count, digest.hexdigest(), source)


class Coordinator:
    def __init__(self) -> None:
        self.zk = KazooClient(hosts=os.getenv("ZK_HOSTS", "localhost:2181"), timeout=SESSION_TIMEOUT)
        self.session_lost = False
        self.stop_requested = False
        self.dataset = load_dataset()

    def state_listener(self, state: KazooState) -> None:
        LOG.info("session state=%s", state)
        if state == KazooState.LOST:
            self.session_lost = True

    def start(self) -> None:
        self.zk.add_listener(self.state_listener)
        self.zk.start(timeout=30)
        self.zk.ensure_path(ROOT)
        self.zk.ensure_path(ELECTION)
        self.zk.ensure_path(PUBLICATIONS)
        try:
            self.zk.create(EPOCH, b"0")
        except NodeExistsError:
            pass
        try:
            # A stable pointer is created before calculation. Accepted writes
            # are setData operations, so two unfenced publications end at v2.
            self.zk.create(RESULT, b"{}")
        except NodeExistsError:
            pass
        LOG.info(
            "ready session_timeout=%.1fs fencing=%d pairs=%d digest=%s source=%s",
            SESSION_TIMEOUT,
            FENCING,
            self.dataset.count,
            self.dataset.digest,
            self.dataset.source,
        )
        while not self.stop_requested:
            self.session_lost = False
            LOG.info("waiting for leadership")
            try:
                self.zk.Election(ELECTION, identifier=INSTANCE).run(self.lead)
            except Exception:
                LOG.exception("election cycle failed")
                time.sleep(1)

    def acquire_epoch(self) -> tuple[int, int]:
        while True:
            raw, stat = self.zk.get(EPOCH)
            epoch = int(raw) + 1
            try:
                new_stat = self.zk.set(EPOCH, str(epoch).encode(), version=stat.version)
                return epoch, new_stat.version
            except BadVersionError:
                continue

    def read_checkpoint(self) -> int:
        if not self.zk.exists(CHECKPOINT):
            return 0
        raw, _ = self.zk.get(CHECKPOINT)
        data = decode(raw)
        if data.get("run_id") != RUN_ID:
            return 0
        return min(int(data["next_unit"]), WORK_UNITS)

    def write_checkpoint(self, next_unit: int, epoch: int) -> None:
        payload = encode({"run_id": RUN_ID, "next_unit": next_unit, "epoch": epoch, "writer": INSTANCE})
        if self.zk.exists(CHECKPOINT):
            self.zk.set(CHECKPOINT, payload)
        else:
            try:
                self.zk.create(CHECKPOINT, payload)
            except NodeExistsError:
                self.zk.set(CHECKPOINT, payload)

    def lead(self) -> None:
        epoch, epoch_version = self.acquire_epoch()
        started = time.monotonic()
        LOG.info("became leader epoch=%d epoch_version=%d", epoch, epoch_version)
        next_unit = self.read_checkpoint()
        LOG.info("resumed from checkpoint next_unit=%d/%d", next_unit, WORK_UNITS)
        for unit in range(next_unit, WORK_UNITS):
            # Deliberately finish the in-flight critical section after session loss.
            # This models a process that cannot prove it is still the leader.
            time.sleep(UNIT_DELAY)
            try:
                self.write_checkpoint(unit + 1, epoch)
            except Exception as exc:
                LOG.warning("checkpoint unavailable unit=%d error=%s", unit + 1, type(exc).__name__)
        result = {
            "run_id": RUN_ID,
            "writer": INSTANCE,
            "epoch": epoch,
            "unique_pairs": self.dataset.count,
            "sha256": self.dataset.digest,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
        self.publish(result)
        # One process instance participates in exactly one run. Without this,
        # Election.run() returns after the callback and the sole survivor could
        # immediately elect itself again and republish the completed result.
        self.stop_requested = True

    def publish(self, result: dict) -> None:
        # The result recipient performs the fencing check. ZooKeeper only stores
        # monotonically increasing epoch metadata; it cannot infer app semantics.
        current_epoch = int(self.zk.get(EPOCH)[0])
        if FENCING and result["epoch"] != current_epoch:
            LOG.error(
                "BadVersionError stale result rejected result_epoch=%d current_epoch=%d",
                result["epoch"],
                current_epoch,
            )
            return
        payload = encode(result)
        stat = self.zk.set(RESULT, payload)
        self.zk.create(f"{PUBLICATIONS}/item-", payload, sequence=True)
        LOG.info(
            "wrote result epoch=%d pointer_version=%d unique_pairs=%d sha256=%s",
            result["epoch"], stat.version, result["unique_pairs"], result["sha256"],
        )

    def close(self, *_: object) -> None:
        self.stop_requested = True
        self.zk.stop()
        self.zk.close()


def main() -> None:
    coordinator = Coordinator()
    signal.signal(signal.SIGTERM, coordinator.close)
    signal.signal(signal.SIGINT, coordinator.close)
    try:
        coordinator.start()
    finally:
        coordinator.close()


if __name__ == "__main__":
    main()
