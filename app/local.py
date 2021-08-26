#!/usr/bin/env python
import os
import sys

import dotenv

if __name__ == "__main__":
    dotenv.read_dotenv("../.env")
    dotenv.read_dotenv("../.env.local", override=True)

    from django.core.management import execute_from_command_line

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    execute_from_command_line(sys.argv)
