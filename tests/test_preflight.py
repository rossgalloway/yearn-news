import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import preflight
import utils


class FetchJsonDataTests(unittest.TestCase):
    def test_fetch_json_data_retries_then_returns_decoded_payload(self) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok": true}'

        with (
            patch("utils.urlopen", side_effect=[URLError("temporary"), response]) as mocked_urlopen,
            patch("utils.time.sleep") as mocked_sleep,
        ):
            result = utils.fetch_json_data(
                "https://example.com/data",
                source="Example API",
                timeout=3.0,
                retries=1,
            )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(mocked_urlopen.call_count, 2)
        mocked_urlopen.assert_called_with("https://example.com/data", timeout=3.0)
        mocked_sleep.assert_called_once_with(0.5)

    def test_fetch_json_data_raises_source_aware_error_after_retries(self) -> None:
        with (
            patch("utils.urlopen", side_effect=URLError("offline")),
            patch("utils.time.sleep"),
        ):
            with self.assertRaisesRegex(utils.DataSourceError, "Example API"):
                utils.fetch_json_data(
                    "https://example.com/data",
                    source="Example API",
                    retries=1,
                )

    def test_fetch_json_rejects_non_object_payloads(self) -> None:
        with patch("utils.fetch_json_data", return_value=[{"value": 1}]):
            with self.assertRaisesRegex(utils.DataSourceError, "received list"):
                utils.fetch_json("https://example.com/data", source="Example API")


class PreflightTests(unittest.TestCase):
    def test_check_rpc_uses_chain_id_as_the_connectivity_probe(self) -> None:
        web3 = MagicMock()
        web3.eth.chain_id = 1

        with (
            patch.dict(utils.CHAINS["mainnet"], {"rpc": "https://example.invalid"}),
            patch("preflight.get_web3", return_value=web3),
        ):
            result = preflight.check_rpc("mainnet", required=True)

        self.assertEqual(result.status, "ready")
        self.assertIn("chain ID 1", result.detail)
        web3.is_connected.assert_not_called()

    def test_main_fails_when_a_required_check_is_unavailable(self) -> None:
        results = [
            preflight.CheckResult("required", "unavailable", "offline", True),
            preflight.CheckResult("optional", "ready", "connected", False),
        ]

        with patch("preflight.run_checks", return_value=results), patch("builtins.print"):
            exit_code = preflight.main()

        self.assertEqual(exit_code, 1)

    def test_main_allows_optional_failures(self) -> None:
        results = [
            preflight.CheckResult("required", "ready", "connected", True),
            preflight.CheckResult("optional", "unavailable", "offline", False),
        ]

        with patch("preflight.run_checks", return_value=results), patch("builtins.print"):
            exit_code = preflight.main()

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
