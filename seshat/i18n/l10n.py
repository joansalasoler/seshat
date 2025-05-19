# -*- coding: utf-8 -*-

# Seshat: AI powered command palette
# Copyright (C) 2025 Joan Sala <contact@joansala.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, locale


def setup_locale(text_domain: str, locale_path: str) -> None:
    """Set up localization for the application."""

    language = locale.getdefaultlocale()[0] or "en"
    locale.setlocale(locale.LC_ALL, '')

    if os.path.isdir(locale_path):
        os.environ['LOCPATH'] = locale_path

    if 'LANG' not in os.environ or not os.environ['LANG']:
        os.environ['LANG'] = language

    if 'LOCPATH' not in os.environ or not os.environ['LOCPATH']:
        locale_path = f'{ sys.base_prefix }/share/locale'
        os.environ['LOCPATH'] = locale_path

    locale.bind_textdomain_codeset(text_domain, 'utf-8')
    locale.bindtextdomain(text_domain, locale_path)
    locale.textdomain(text_domain)
