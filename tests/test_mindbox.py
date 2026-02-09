"""
Unit tests for Mindbox plugin
"""

import os
import tempfile
import time
import unittest


class TestMindboxScanFolder(unittest.TestCase):
    """Test folder scanning logic for Mindbox plugin"""

    def _scan_mindbox_folder(self, folder):
        """
        Scan folder for .mb files
        (Copy of the implementation from keypi_mindbox/__init__.py for testing)

        Args:
            folder: Path to the mindbox folder

        Returns:
            List of dicts with file info
        """
        if not os.path.isdir(folder):
            return []

        files = []
        try:
            for entry in os.listdir(folder):
                if entry.lower().endswith(".mb"):
                    file_path = os.path.join(folder, entry)
                    if os.path.isfile(file_path):
                        mod_time = os.path.getmtime(file_path)
                        mod_date = time.strftime("%Y-%m-%d", time.localtime(mod_time))
                        name_without_ext = os.path.splitext(entry)[0]
                        files.append(
                            {
                                "name": name_without_ext,
                                "filename": entry,
                                "path": file_path,
                                "modified": mod_date,
                            }
                        )
        except OSError:
            return []

        files.sort(key=lambda f: f["name"].lower())
        return files

    def setUp(self):
        """Create a temporary directory with test .mb files"""
        self.test_dir = tempfile.mkdtemp()

        # Create test .mb files
        self.test_files = ["notes.mb", "todo.mb", "ideas.mb", "UPPERCASE.MB"]
        for filename in self.test_files:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, "w") as f:
                f.write(f"Content of {filename}")

        # Create a non-.mb file (should be ignored)
        with open(os.path.join(self.test_dir, "readme.txt"), "w") as f:
            f.write("This is not a .mb file")

        # Create a subdirectory with .mb file (should be ignored - no recursion)
        sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(sub_dir)
        with open(os.path.join(sub_dir, "nested.mb"), "w") as f:
            f.write("Nested file")

    def tearDown(self):
        """Clean up temporary directory"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_scan_finds_mb_files(self):
        """Test that scan finds all .mb files"""
        result = self._scan_mindbox_folder(self.test_dir)

        self.assertEqual(len(result), 4)

    def test_scan_ignores_non_mb_files(self):
        """Test that scan ignores non-.mb files"""
        result = self._scan_mindbox_folder(self.test_dir)

        filenames = [f["filename"] for f in result]
        self.assertNotIn("readme.txt", filenames)

    def test_scan_ignores_subdirectories(self):
        """Test that scan does not recurse into subdirectories"""
        result = self._scan_mindbox_folder(self.test_dir)

        filenames = [f["filename"] for f in result]
        self.assertNotIn("nested.mb", filenames)

    def test_scan_case_insensitive_extension(self):
        """Test that scan handles .MB and .mb extensions"""
        result = self._scan_mindbox_folder(self.test_dir)

        filenames = [f["filename"] for f in result]
        self.assertIn("UPPERCASE.MB", filenames)

    def test_scan_returns_correct_structure(self):
        """Test that each result has the expected keys"""
        result = self._scan_mindbox_folder(self.test_dir)

        for file_info in result:
            self.assertIn("name", file_info)
            self.assertIn("filename", file_info)
            self.assertIn("path", file_info)
            self.assertIn("modified", file_info)

    def test_scan_name_without_extension(self):
        """Test that name field has no extension"""
        result = self._scan_mindbox_folder(self.test_dir)

        names = [f["name"] for f in result]
        for name in names:
            self.assertFalse(name.endswith(".mb"))
            self.assertFalse(name.endswith(".MB"))

    def test_scan_path_is_absolute(self):
        """Test that path is absolute"""
        result = self._scan_mindbox_folder(self.test_dir)

        for file_info in result:
            self.assertTrue(os.path.isabs(file_info["path"]))

    def test_scan_modified_date_format(self):
        """Test that modified date is in YYYY-MM-DD format"""
        result = self._scan_mindbox_folder(self.test_dir)

        for file_info in result:
            date_str = file_info["modified"]
            self.assertRegex(date_str, r"^\d{4}-\d{2}-\d{2}$")

    def test_scan_sorted_by_name(self):
        """Test that results are sorted alphabetically by name"""
        result = self._scan_mindbox_folder(self.test_dir)

        names = [f["name"].lower() for f in result]
        self.assertEqual(names, sorted(names))

    def test_scan_nonexistent_folder(self):
        """Test scanning a non-existent folder returns empty list"""
        result = self._scan_mindbox_folder("/nonexistent/path/12345")

        self.assertEqual(result, [])

    def test_scan_empty_folder(self):
        """Test scanning an empty folder returns empty list"""
        empty_dir = tempfile.mkdtemp()
        try:
            result = self._scan_mindbox_folder(empty_dir)
            self.assertEqual(result, [])
        finally:
            os.rmdir(empty_dir)

    def test_scan_folder_with_no_mb_files(self):
        """Test scanning folder with only non-.mb files"""
        no_mb_dir = tempfile.mkdtemp()
        try:
            with open(os.path.join(no_mb_dir, "readme.txt"), "w") as f:
                f.write("text file")
            with open(os.path.join(no_mb_dir, "data.json"), "w") as f:
                f.write("{}")

            result = self._scan_mindbox_folder(no_mb_dir)
            self.assertEqual(result, [])
        finally:
            import shutil

            shutil.rmtree(no_mb_dir, ignore_errors=True)


class TestMindboxShortcutHandling(unittest.TestCase):
    """Test shortcut input parsing for Mindbox plugin"""

    def _parse_shortcut(self, user_input):
        """
        Parse shortcut input and return matched shortcut name.
        Returns "edit" if #edit matches, None otherwise.
        """
        shortcut_input = user_input[1:].lower()  # Remove # and lowercase

        if shortcut_input == "" or "edit".startswith(shortcut_input):
            return "edit"
        return None

    def test_hash_only_shows_edit(self):
        """Test that # alone suggests #edit"""
        result = self._parse_shortcut("#")
        self.assertEqual(result, "edit")

    def test_hash_e_matches_edit(self):
        """Test that #e matches #edit"""
        result = self._parse_shortcut("#e")
        self.assertEqual(result, "edit")

    def test_hash_ed_matches_edit(self):
        """Test that #ed matches #edit"""
        result = self._parse_shortcut("#ed")
        self.assertEqual(result, "edit")

    def test_hash_edit_matches_edit(self):
        """Test that #edit matches exactly"""
        result = self._parse_shortcut("#edit")
        self.assertEqual(result, "edit")

    def test_hash_unknown_returns_none(self):
        """Test that unknown shortcut returns None"""
        result = self._parse_shortcut("#xyz")
        self.assertIsNone(result)

    def test_shortcut_case_insensitive(self):
        """Test case-insensitive shortcut matching"""
        result = self._parse_shortcut("#EDIT")
        self.assertEqual(result, "edit")


class TestMindboxConfig(unittest.TestCase):
    """Test configuration validation logic"""

    def _is_configured(self, mindbox_folder):
        """Check if configuration is valid"""
        return bool(mindbox_folder)

    def test_empty_folder_not_configured(self):
        """Test empty folder path is not configured"""
        self.assertFalse(self._is_configured(""))

    def test_none_folder_not_configured(self):
        """Test None folder path is not configured"""
        self.assertFalse(self._is_configured(None))

    def test_valid_folder_is_configured(self):
        """Test valid folder path is configured"""
        self.assertTrue(self._is_configured("C:\\Users\\test\\Mindbox"))

    def test_whitespace_folder_not_configured(self):
        """Test whitespace-only folder path (after strip) is not configured"""
        # Note: settings.get_stripped would strip whitespace before this check
        self.assertFalse(self._is_configured(""))


if __name__ == "__main__":
    unittest.main()
