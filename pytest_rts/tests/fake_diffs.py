"""Fake diff strings for tests"""

FAKE_DIFF_1 = """diff --git a/start.py b/start.py
index 8b05226..010a132 100644
--- a/start.py
+++ b/start.py
@@ -23,0 +24,2 @@ from helper import (
+
+
@@ -29,0 +32,2 @@ def git_diff_data(filename,commithash1,commithash2):
+
+
@@ -30,0 +35 @@ def git_diff_data(filename,commithash1,commithash2):
+
@@ -34,0 +40 @@ def tests_from_changed_testfiles(files,commithash1,commithash2):
+
@@ -35,0 +42 @@ def tests_from_changed_testfiles(files,commithash1,commithash2):
+
@@ -36,0 +44 @@ def tests_from_changed_testfiles(files,commithash1,commithash2):
+
@@ -38,0 +47 @@ def tests_from_changed_testfiles(files,commithash1,commithash2):
+
@@ -40,0 +50 @@ def tests_from_changed_testfiles(files,commithash1,commithash2):
+
@@ -50,0 +61,2 @@ def tests_from_changed_testfiles(files,commithash1,commithash2):
+
+
@@ -59,0 +72 @@ def tests_from_changed_sourcefiles(files,commithash1,commithash2):
+
@@ -67,0 +81,2 @@ def tests_from_changed_sourcefiles(files,commithash1,commithash2):
+
+
@@ -72,0 +88 @@ def tests_from_changes(commithash1,commithash2):
+
@@ -83,0 +100 @@ def read_newly_added_tests():
+
@@ -91,0 +109 @@ def read_newly_added_tests():
+
@@ -100,0 +119 @@ def split_changes(commit1,commit2):
+
@@ -109,0 +129 @@ def split_changes(commit1,commit2):
+
@@ -119,0 +140,2 @@ def file_changes_between_commits(commit1, commit2):
+
+
@@ -135,0 +158 @@ def run_tests_and_update(test_set,update_tuple):
+
@@ -145,0 +169,2 @@ def commits_test():
+
+
@@ -161,0 +187 @@ def commits_test():
+
@@ -171,0 +198 @@ def random_remove_test(iterations):
+
@@ -181,0 +209 @@ def random_remove_test(iterations):
+
@@ -190,0 +219 @@ def random_remove_test(iterations):
+
@@ -199,0 +229 @@ def random_remove_test(iterations):
+
@@ -210,0 +241 @@ def random_remove_test(iterations):
+
@@ -219,0 +251 @@ def random_remove_test(iterations):
+
@@ -228,0 +261 @@ def main():
+
@@ -238,0 +272 @@ def main():
+    
"""

FAKE_DIFF_2 = """diff --git a/start.py b/start.py
index 8b05226..58b5c2d 100644
--- a/start.py
+++ b/start.py
@@ -83 +83 @@ def read_newly_added_tests():
-    conn = sqlite3.connect('example.db')
+    conn = sqlite3.connect('example.db2')
@@ -240,0 +241 @@ if __name__ == '__main__':
+    
"""

FAKE_DIFF_3 = """@@ -16 +12,4 @@ fakefakefakefake
@@ -24,0 +234 @@\n@@ 34,3 34,6 @@ 12312553214,,2344-123 gitqr @ oqjwd @
@@ 13,4 22 @@
"""
