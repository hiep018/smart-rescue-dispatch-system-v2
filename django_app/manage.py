#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks."""

    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        'attendance_system.settings'
    )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Không thể import Django. Hãy kiểm tra Django đã được cài "
            "và Python Interpreter đang chọn đúng môi trường."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()