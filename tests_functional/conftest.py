"""
pytest configuration file
"""
import pytest

def pytest_addoption(parser):
    parser.addoption("--url", action="store", default="https://varapp-dev.vital-it.ch", help="Varapp URL")

@pytest.fixture(scope="class")
def url(request):
    opt = request.config.getoption("--url")
    request.cls.URL = opt

#@pytest.fixture(scope="class")
#def browser(request):
#    opt = request.config.getoption("--browser")
#    request.cls.BROWSER = opt.lower()
