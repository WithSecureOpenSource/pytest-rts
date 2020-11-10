import pytest
from pytest_rts.utils import git


@pytest.mark.parametrize(
    "changes, expected",
    [
        ([("changes/car/shift_2_forward.txt", "src/car.py")], ["src/car.py"]),
        ([], []),
        (
            [
                ("changes/car/shift_2_forward.txt", "src/car.py"),
                ("changes/shop/change_get_price.txt", "src/shop.py"),
            ],
            ["src/car.py", "src/shop.py"],
        ),
    ],
)
def test_changed_files_current(changes, expected, helper):
    for c in changes:
        change = c[0]
        filename = c[1]
        helper.change_file(change, filename)
    assert git.changed_files_current() == expected


@pytest.mark.parametrize(
    "diff_file, real_changed_lines, real_line_updates",
    [
        (
            "fake_diff_data/1.txt",
            [
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
            ],
            [
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
            ],
        ),
        ("fake_diff_data/2.txt", [83, 240], [(83, 0), (240, 1)]),
        ("fake_diff_data/3.txt", [16, 24], [(16, 3), (24, 4)]),
    ],
)
def test_get_test_lines_and_update_lines_fake_change(
    diff_file, real_changed_lines, real_line_updates
):
    with open(diff_file, "r") as f:
        diff = f.read()

    lines_changed, line_updates, _ = git.get_test_lines_and_update_lines(diff)

    assert lines_changed == real_changed_lines
    assert line_updates == real_line_updates


def test_get_test_lines_and_update_lines_real_change(helper):
    helper.change_file("changes/car/line_shifts_middle.txt", "src/car.py")
    diff = git.file_diff_data_current("src/car.py")
    changed_lines, line_updates, _ = git.get_test_lines_and_update_lines(diff)
    assert changed_lines == [11, 17]
    assert line_updates == [(11, 2), (17, 5)]
