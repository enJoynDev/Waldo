import drift as D
import run_experiments as E
import run_trial as R


def test_condition_list_has_the_expected_size_and_no_duplicates():
    conditions = E.build_conditions()
    assert len(conditions) == 810  # 5 modes x 5 drifts x 30 seeds + 2 noise levels x 30 seeds
    assert len(set(conditions)) == len(conditions)


def test_row_has_exactly_the_documented_columns(world):
    row = E.run_one(world, 3, ("B1", 0.005, 0.0, 0))
    assert list(row) == E.COLUMNS
    assert row["run_id"] == 3


def test_row_matches_a_direct_run(world):
    row = E.run_one(world, 0, ("B2", 0.005, 0.0, 4))
    direct = R.run_trial(world, "B2", 4, D.make_params(d_eps=0.005))
    for key in ("final_lat_err", "final_head_err_deg", "max_lat_err", "dist_travelled"):
        assert row[key] == direct[key]
