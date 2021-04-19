
import os
import unittest
import sys

from cortx.utils.conf_store import Conf

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)).replace(
    "sspl_test", "low-level/framework"
)
sys.path.append(PROJECT_ROOT)
from base.conf_upgrade import ConfUpgrade


class TestConfUpgrade(unittest.TestCase):

    def setUp(self):
        base_config = "low-level/files/opt/seagate/sspl/conf/sspl.conf.LR2.yaml"
        base_config = os.path.dirname(os.path.abspath(__file__)).replace(
                                      "sspl_test", base_config)
        base_config_url = f"yaml://{base_config}"
        self.existing_config = "/tmp/existing.conf"
        self.new_config = "/tmp/new.conf"
        self.merged_config = "/tmp/merged.conf"
        with open(self.existing_config, "w"):
            pass
        with open(self.new_config, "w"):
            pass
        self.existing_config_url = f"yaml://{self.existing_config}"
        self.new_config_url = f"yaml://{self.new_config}"
        self.merged_config_url = f"yaml://{self.merged_config}"
        Conf.load("base", base_config_url)
        Conf.load("existing", self.existing_config_url)
        Conf.load("new", self.new_config_url)
        # Delete below keys to get clean config
        Conf.delete("base", "CHANGED")
        Conf.delete("base", "OBSOLETE")
        # Create exising and new config file from base file
        Conf.copy("base", "existing")
        Conf.copy("base", "new")
        Conf.save("existing")
        Conf.save("new")

    def test_new_key_should_be_added_in_config(self):
        # Add new key in new config file
        Conf.set("existing", "FOO>bar", "spam")
        Conf.save("existing")
        Conf.set("new", "FOO>bar", "spam")
        Conf.set("new", "FOO>eggs", "ham")
        Conf.set("new", "BAZ>bar", "spam")
        Conf.save("new")
        conf_upgrade = ConfUpgrade(self.existing_config_url,
                                   self.new_config_url,
                                   self.merged_config_url)
        conf_upgrade.upgrade()
        Conf.load("merged", self.merged_config_url)
        self.assertIsNotNone(Conf.get("merged", "FOO>eggs"))
        self.assertIsNotNone(Conf.get("merged", "BAZ>bar"))
        self.assertEqual(Conf.get("new", "FOO>eggs"),
                         Conf.get("merged", "FOO>eggs"))
        self.assertEqual(Conf.get("new", "BAZ>bar"),
                         Conf.get("merged", "BAZ>bar"))
        for key in Conf.get_keys("existing", key_index=False):
            self.assertIn(key, Conf.get_keys("merged", key_index=False))

    def test_changed_key_should_be_replaced_in_config(self):
        Conf.set("existing", "FOO>bar", "spam")
        Conf.save("existing")
        Conf.set("new", "FOOBAR>bar", "spam")
        Conf.set("new", "CHANGED[0]>FOO", "FOOBAR")
        Conf.save("new")
        conf_upgrade = ConfUpgrade(self.existing_config_url,
                                   self.new_config_url,
                                   self.merged_config_url)
        conf_upgrade.upgrade()
        Conf.load("merged", self.merged_config_url)
        self.assertIsNone(Conf.get("merged", "FOO"))
        self.assertIsNotNone(Conf.get("merged", "FOOBAR"))
        self.assertEqual(Conf.get("existing", "FOO>bar"),
                         Conf.get("merged", "FOOBAR>bar"))

    def test_multilevel_changed_key_should_be_replaced_in_config(self):
        Conf.set("existing", "FOO", {"bar": "qux", "eggs": "ham"})
        Conf.save("existing")
        Conf.set("new", "FOOBAR", {"baz": "spam", "eggs": "ham"})
        Conf.delete("new", "FOO")
        Conf.set("new", "CHANGED[0]>FOO>bar", "FOOBAR>baz")
        Conf.save("new")
        conf_upgrade = ConfUpgrade(self.existing_config_url,
                                   self.new_config_url,
                                   self.merged_config_url)
        conf_upgrade.upgrade()
        Conf.load("merged", self.merged_config_url)
        self.assertIsNone(Conf.get("merged", "FOO"))
        self.assertIsNotNone(Conf.get("merged", "FOOBAR"))
        self.assertIsNotNone(Conf.get("merged", "FOOBAR>baz"))
        self.assertEqual(Conf.get("existing", "FOO>bar"),
                         Conf.get("merged", "FOOBAR>baz"))

    def test_obsolete_key_should_be_present_in_config(self):
        Conf.set("existing", "FOO", {"bar": "qux", "eggs": "ham"})
        Conf.save("existing")
        Conf.set("new", "FOO", {"bar": "qux", "eggs": "ham"})
        Conf.set("new", "OBSOLETE[0]", "FOO>bar")
        Conf.save("new")
        conf_upgrade = ConfUpgrade(self.existing_config_url,
                                   self.new_config_url,
                                   self.merged_config_url)
        conf_upgrade.upgrade()
        Conf.load("merged", self.merged_config_url)
        self.assertIsNotNone(Conf.get("merged", "FOO>bar"))

    def test_removed_key_should_be_absent_in_config(self):
        Conf.set("existing", "FOO", {"bar": "qux", "eggs": "ham"})
        Conf.set("existing", "OBSOLETE[0]", "FOO>bar")
        Conf.save("existing")
        Conf.set("new", "FOO", {"eggs": "ham"})
        Conf.save("new")
        conf_upgrade = ConfUpgrade(self.existing_config_url,
                                   self.new_config_url,
                                   self.merged_config_url)
        conf_upgrade.upgrade()
        Conf.load("merged", self.merged_config_url)
        self.assertIsNone(Conf.get("merged", "FOO>bar"))

    def tearDown(self):
        os.remove(self.existing_config)
        os.remove(self.new_config)
        os.remove(self.merged_config)
        Conf._conf = None


if __name__ == '__main__':
    unittest.main()
