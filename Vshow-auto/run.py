import pytest
import os
from send_email import zipDir, send_email
import sys
import subprocess
import time
import signal
import logging


if __name__ == '__main__':
    pytest.main(["-sq", "--clean-alluredir", "--alluredir=./vshow_auto_report/allure-results"])
    os.system("allure generate ./vshow_auto_report/allure-results/ -o ./vshow_auto_report/allure-report/ --clean")
    # zipDir()
    # send_email()
