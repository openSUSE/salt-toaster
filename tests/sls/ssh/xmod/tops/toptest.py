# -*- coding: utf-8 -*-
__virtualname__ = 'toptest'


def __virtual__():
    return __virtualname__


def top(**kwargs):
    return {"base": ['custom_top']}
