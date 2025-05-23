import argparse
import json
import logging
import os
import pathlib
import sys
import time
import typing


JsonWorkRequest = object
JsonWorkResponse = object


class Worker:
    """Synchronous, serial persistent worker."""

    def __init__(self, instream: "typing.TextIO", outstream: "typing.TextIO"):
        self._instream = instream
        self._outstream = outstream
        self._logger = logging.getLogger("worker")
        self._logger.info("starting worker")

    def run(self) -> None:
        try:
            while True:
                request = None
                try:
                    request = self._get_next_request()
                    if request is None:
                        self._logger.info("Empty request: exiting")
                        break
                    response = self._process_request(request)
                    if response:
                        self._send_response(response)
                except Exception:
                    self._logger.exception("Unhandled error: request=%s", request)
                    output = (
                        f"Unhandled error:\nRequest: {request}\n"
                        + traceback.format_exc()
                    )
                    request_id = 0 if not request else request.get("requestId", 0)
                    self._send_response(
                        {
                            "exitCode": 3,
                            "output": output,
                            "requestId": request_id,
                        }
                    )
        finally:
            self._logger.info("Worker shutting down")

    def _get_next_request(self) -> "object | None":
        line = self._instream.readline()
        if not line:
            return None
        return json.loads(line)

    def _process_request(self, request: "JsonWorkRequest") -> "JsonWorkResponse | None":
        if request.get("cancel"):
            return None
        work()
        response = {
            "requestId": request.get("requestId", 0),
            "exitCode": 0,
        }
        return response

    def _send_response(self, response: "JsonWorkResponse") -> None:
        self._outstream.write(json.dumps(response) + "\n")
        self._outstream.flush()


def work():
    with open("work.txt", "w") as f:
        f.write(int(time.time()))


def main(args: "list[str]") -> int:
    if "--persistent_worker" in args:
        Worker(sys.stdin, sys.stdout).run()
    else:
        work()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
