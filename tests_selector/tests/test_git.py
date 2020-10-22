from tests_selector.utils import git


def test_changed_files_current_no_change():
    assert git.changed_files_current() == []


def test_changed_files_current_one_change():
    with open("./src/car.py", "r") as f:
        lines = f.readlines()
        lines[6] = "abcd\n"

    with open("./src/car.py", "w") as f:
        for line in lines:
            f.write(line)

    assert git.changed_files_current() == ["src/car.py"]


def test_get_test_lines_and_update_lines1():
    with open("./fake_diff_data/1.txt", "r") as f:
        diff = f.read()

    lines, updates, _ = git.get_test_lines_and_update_lines(diff)

    real_lines = [
        23,
        29,
        30,
        34,
        35,
        36,
        38,
        40,
        50,
        59,
        67,
        72,
        83,
        91,
        100,
        109,
        119,
        135,
        145,
        161,
        171,
        181,
        190,
        199,
        210,
        219,
        228,
        238,
    ]

    real_updates = [
        (23, 2),
        (29, 4),
        (30, 5),
        (34, 6),
        (35, 7),
        (36, 8),
        (38, 9),
        (40, 10),
        (50, 12),
        (59, 13),
        (67, 15),
        (72, 16),
        (83, 17),
        (91, 18),
        (100, 19),
        (109, 20),
        (119, 22),
        (135, 23),
        (145, 25),
        (161, 26),
        (171, 27),
        (181, 28),
        (190, 29),
        (199, 30),
        (210, 31),
        (219, 32),
        (228, 33),
        (238, 34),
    ]

    assert lines == real_lines
    assert updates == real_updates


def test_get_test_lines_and_update_lines2():
    with open("./fake_diff_data/2.txt", "r") as f:
        diff = f.read()

    lines, updates, _ = git.get_test_lines_and_update_lines(diff)
    real_lines = [83, 240]
    real_updates = [(83, 0), (240, 1)]

    assert lines == real_lines
    assert updates == real_updates


def test_get_test_lines_and_update_lines3():
    with open("./fake_diff_data/3.txt", "r") as f:
        diff = f.read()

    lines, updates, _ = git.get_test_lines_and_update_lines(diff)
    real_lines = [16, 24]
    real_updates = [(16, 3), (24, 4)]

    assert lines == real_lines
    assert updates == real_updates


def test_get_test_lines_and_update_lines4():
    with open("./src/car.py", "r") as f:
        lines = f.readlines()
        lines[11] = lines[11].strip() + "+1\n"
        lines[15] = lines[15] + "\n\n"
        lines[21] = "        if True:\n"

    with open("./src/car.py", "w") as f:
        for line in lines:
            f.write(line)

    diff = git.file_diff_data_current("src/car.py", ".")
    lines, updates, _ = git.get_test_lines_and_update_lines(diff)
    real_lines = [12, 16, 22]
    real_updates = [(12, 0), (16, 2), (22, 2)]

    assert lines == real_lines
    assert updates == real_updates
