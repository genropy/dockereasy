#!/usr/bin/env python
# encoding: utf-8
from gnr.app.gnrdbo import GnrDboTable, GnrDboPackage

class Package(GnrDboPackage):
    def config_attributes(self):
        return dict(sqlschema='docker',
                    comment='docker',
                    name_short='docker',
                    name_long='docker',
                    name_full='docker',
                    _syspackage=True)
                    

class Table(GnrDboTable):
    pass