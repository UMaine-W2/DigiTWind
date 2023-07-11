# Copyright 2023 - Yuksel Rudy Alkarem

from dash import Dash

class Retina(Dash):
    def __init__(self, channels, pdata, vdata):
        super().__init__()

        self.channels = channels
        self.pdata    = pdata
        self.vdata    = vdata
