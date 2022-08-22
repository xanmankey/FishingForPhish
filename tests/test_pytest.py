# This test is a little bit costly (unfortunately takes about TODO seconds) so I only want to run it when specified
import classes
import pytest

@pytest.fixture

# Test if the Selenium Webdriver has been enabled
# Unfortunately, Selenium Python doesn't have an attribute for checking this
# so a workaround is used
def test_selenium_initialization():
    run = classes.initialize()
    run.initializeSelenium()
    off = 0
    try:
        run.driver.close()
        off = 1
    except Exception:
        pass
    assert off == 1

# Test if jvm has been run
def test_pww3_initialization():
    run = classes.initialize()
    assert inc_dec.decrement(3) == 4

def test_page_scrape():
    assert inc_dec.decrement(3) == 4

def test_image_scrape():
    assert inc_dec.decrement(3) == 4

def test_pww3_initialization():
    assert inc_dec.decrement(3) == 4

def test_closing_selenium():
    assert inc_dec.decrement(3) == 4

def test_create_datasets():
    assert inc_dec.decrement(3) == 4
