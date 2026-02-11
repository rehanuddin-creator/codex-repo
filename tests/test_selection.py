import unittest
from unittest.mock import patch

from auto_software_installer import (
    RequestValidationError,
    _config_from_payload,
    install_from_payload,
    parse_selection,
    resolve_software_list,
)


class SelectionTests(unittest.TestCase):
    def test_parse_selection_keeps_order_and_unique(self):
        self.assertEqual(parse_selection("1,3,1,2", 4), [1, 3, 2])

    def test_parse_selection_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            parse_selection("0", 3)

    def test_resolve_software_list_removes_duplicates(self):
        self.assertEqual(
            resolve_software_list("git,curl,git"),
            ["git", "curl"],
        )

    def test_resolve_software_list_rejects_unknown(self):
        with self.assertRaises(ValueError):
            resolve_software_list("git,unknown")


class CloudFunctionPayloadTests(unittest.TestCase):
    def test_config_from_payload_requires_single_auth_method(self):
        with self.assertRaises(RequestValidationError):
            _config_from_payload(
                {
                    "host": "10.0.0.1",
                    "username": "ubuntu",
                    "password": "x",
                    "key_file": "/tmp/id_rsa",
                    "software": ["git"],
                }
            )

    def test_config_from_payload_validates_software(self):
        with self.assertRaises(RequestValidationError):
            _config_from_payload(
                {
                    "host": "10.0.0.1",
                    "username": "ubuntu",
                    "password": "x",
                    "software": ["unknown"],
                }
            )

    def test_install_from_payload_success(self):
        payload = {
            "host": "10.0.0.1",
            "username": "ubuntu",
            "password": "secret",
            "software": ["git", "curl"],
        }

        with patch("auto_software_installer.RemoteInstaller") as installer_cls:
            installer = installer_cls.return_value
            response = install_from_payload(payload)

            installer.connect.assert_called_once()
            installer.install.assert_called_once_with(["git", "curl"])
            installer.close.assert_called_once()
            self.assertEqual(response["status"], "success")
            self.assertEqual(response["installed"], ["git", "curl"])


if __name__ == "__main__":
    unittest.main()
