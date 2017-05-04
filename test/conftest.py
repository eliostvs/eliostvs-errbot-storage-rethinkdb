def pytest_addoption(parser):
    parser.addoption("--port", type=int, help="RethinkDB port")
