# This file is a part of IntelOwl https://github.com/intelowlproject/IntelOwl
# See the file 'LICENSE' for copying permission.

import logging
from subprocess import DEVNULL, PIPE, Popen

from celery.exceptions import SoftTimeLimitExceeded

from api_app.analyzers_manager.classes import FileAnalyzer
from api_app.exceptions import AnalyzerRunException

logger = logging.getLogger(__name__)


class SignatureInfo(FileAnalyzer):
    def run(self):
        p = None
        results = {
            "checksum_mismatch": False,
            "no_signature": False,
            "verified": False,
            "corrupted": False,
        }
        try:
            command = ["osslsigncode", "verify", self.filepath]
            p = Popen(command, stdin=DEVNULL, stdout=PIPE, stderr=PIPE)
            (out, err) = p.communicate()
            output = out.decode()

            if p.returncode == 1 and "MISMATCH" in output:
                results["checksum_mismatch"] = True
            elif p.returncode != 0:
                raise AnalyzerRunException(
                    f"osslsigncode return code is {p.returncode}. Error: {err}"
                )

            if not output:
                raise AnalyzerRunException("osslsigncode gave no output?")

            if "No signature found" in output:
                results["no_signature"] = True
            if "Signature verification: ok" in output:
                results["verified"] = True
            if "Corrupt PE file" in output:
                results["corrupted"] = True
        except SoftTimeLimitExceeded as exc:
            self._handle_exception(exc)
            if p:
                p.kill()

        return results
