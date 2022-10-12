from nwbinspector.testing import load_testing_config, update_testing_config


def test_update_testing_config():
    test_key = "LOCAL_PATH"
    test_value = "/a/new/path/"

    initial_testing_config = load_testing_config()
    try:
        update_testing_config(key=test_key, value=test_value)
        updated_testing_config = load_testing_config()
    finally:
        # Restore
        update_testing_config(key=test_key, value=initial_testing_config[test_key])

    assert updated_testing_config[test_key] != initial_testing_config[test_key]
    assert updated_testing_config[test_key] == test_value
