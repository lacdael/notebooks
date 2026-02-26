from datetime import datetime 
import pandas as pd
import numpy as np
import pprint
import os
import json
import glob
import logging
import time
import traceback


def parse_risk_reward( rr_string):
    #Convert '1:2' into 2.0
    risk, reward = rr_string.split(":")
    return float(reward) / float(risk)

def calculate_stop_loss( stop_loss_percent, entry_price):
    #Calculate stop loss for a long trade
    return entry_price * (1 - stop_loss_percent / 100)

def calculate_take_profit( stop_loss_percent, risk_reward_multiple, entry_price):
    #Calculate take profit using R:R
    reward_percent = stop_loss_percent * risk_reward_multiple
    return entry_price * (1 + reward_percent / 100)


class Indicator:
    
    def getPlotData( self ) : raise NotImplementedError
    def prep( self , df ) : raise NotImplementedError
    def work( self , df, ptr ) : raise NotImplementedError
    def getStates( self ) : raise NotImplementedError
    def getReward( self, action, df, i) : raise NotImplementedError
    def getState( self, df, i ) : raise NotImplementedError
    def buy( self, price ) : raise NotImplementedError
    def sell( self, price ) : raise NotImplementedError

    HOLD = 0
    BUY = 1
    SELL = 2

    OK = 0.1;
    NO = -0.5
    STUPID = -1
    YES = 1
    BAD = -2
    GOLD = 2
