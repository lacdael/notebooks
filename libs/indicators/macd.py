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
from .indicator import Indicator 
from .indicator import parse_risk_reward 
from .indicator import calculate_stop_loss
from .indicator import calculate_take_profit

"""
                          xxxxxxxxx                        
                      xxxxx        xxxx                    
                    xxx                 x  xx    xxxx      
                  xxx                  xxxx                
                 xx              xxxx      xx              
               xxx        xxx   xx           xxx           
              x      xx  xx                    xxx         
xxxx  xxx   xxxxx  xxx                           xxx       
        xxx                                                
      xx                                                   
    xx                                                     
   x                                                       
"""

SLOW_LINE = "EMA26";  # EMA12
FAST_LINE = "EMA12";  # EMA12


class MACD( Indicator ):

    STATE_GOLD_WITHIN_FAIT = 0;
    STATE_GOLD_WITHOUT_FAIT = 1;
    STATE_GOLD_WITHIN_ASSET = 2;
    STATE_BELOW_STOPLOSS_ASSET = 3;
    STATE_ABOVE_TAKE_PROFIT_ASSET = 4;
    STATE_HIT_GOLD_FAIT = 5;
    STATE_DEATH_WITHIN_FAIT = 6;
    STATE_DEATH_WITHOUT_FAIT = 7;
    STATE_DEATH_WITHIN_ASSET = 8;
    STATE_DEATH_WITHOUT_ASSET = 9;
    STATE_HIT_DEATH_WITH_ASSET = 10;


    _cache = {};
    _plotData = [
        {"key": FAST_LINE,"color":"lime"},
        {"key": SLOW_LINE,"color":"red"},
    ];
    _threshold = 0.1;
    _pair = [];
    _logger = None;

    def _open_long_trade(self, entry_price):
        stop = calculate_stop_loss( self._stop_loss, entry_price)
        take_profit = calculate_take_profit( self._stop_loss, self._risk_reward_multiple, entry_price)
        self._cache["take_profit"] = take_profit;
        self._cache["stop_loss"] = stop;

    def __init__( self, store=None, threshold=0.1, pair=[], stopLoss=-1.0, riskReward="1:2" ):
        if len(pair) == 0:
            raise Exception("Pair is empty");
        if store:
            self._cache = store;
        else:
            self._cache = {"holding":pair[0]};
        self._logger = logging.getLogger('trades')
        self._stop_loss = abs( stopLoss);
        self._risk_reward_multiple = parse_risk_reward( riskReward)
        self._threshold = threshold;
        self._pair = pair;

    "@override"
    def getPlotData( self ):
        return self._plotData;

    "@override"
    def prep( self, df ):
        self._cache = {"holding":self._pair[0]};
        # Fast EMA
        df[ FAST_LINE ] = df['close'].ewm(span=12, adjust=False).mean()

        # Slow EMA
        df[ SLOW_LINE  ] = df['close'].ewm(span=26, adjust=False).mean()
        
        self._cache["take_profit"] = 0;
        self._cache["stop_loss"] = 0;
        self._cache["AvSlowLessThanFast"] = self._isAvSlowLessThanFast( df , 0 );
        self._cache["goldenCross"] = {
                "close" : df.iloc[0]["close"],
                "open" : df.iloc[0]["close"],
                "time"  : str( df.iloc[0].name ) 
        };
        self._cache["deathCross"] = { 
                "close" : df.iloc[0]["close"],
                "open" : df.iloc[0]["close"],
                "time"  : str( df.iloc[0].name ) 
        };
               
    def _isAvSlowLessThanFast( self, df , i ):
        return df[ FAST_LINE ].iloc[i] >= df[ SLOW_LINE ].iloc[i];

    "@override"
    def getStates( self ):
        return [
            self.STATE_GOLD_WITHIN_FAIT,
            self.STATE_GOLD_WITHOUT_FAIT,
            self.STATE_GOLD_WITHIN_ASSET,
            self.STATE_BELOW_STOPLOSS_ASSET,
            self.STATE_ABOVE_TAKE_PROFIT_ASSET,
            self.STATE_HIT_GOLD_FAIT,

            self.STATE_DEATH_WITHIN_FAIT,
            self.STATE_DEATH_WITHOUT_FAIT,
            self.STATE_DEATH_WITHIN_ASSET,
            self.STATE_DEATH_WITHOUT_ASSET,
            self.STATE_HIT_DEATH_WITH_ASSET
        ];

    def _priceInStopLossTakeProfit( self, price ):
        return ( price <= self._cache["take_profit"] and price >= self._cache["stop_loss"]);



    def _indicator_golden_cross(self, df, i):
        if i == 0:
            self._cache["crossHit"] = False
            return

        prev_fast = df[ FAST_LINE ].iloc[i-1]
        prev_slow = df[ SLOW_LINE ].iloc[i-1]
        curr_fast = df[ FAST_LINE ].iloc[i]
        curr_slow = df[ SLOW_LINE ].iloc[i]

        self._cache["crossHit"] = False
        # Golden cross
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            self._cache["crossHit"] = True
            self._cache["AvSlowLessThanFast"] = True
            self._cache["goldenCross"] = {
                "time": str(df.iloc[i].name),
                "open": df["open"].iloc[i],
                "close": df["close"].iloc[i],
                "volume": df["volume"].iloc[i],
            }
        # Death cross
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            self._cache["crossHit"] = True
            self._cache["AvSlowLessThanFast"] = False
            self._cache["deathCross"] = {
                "time": str(df.iloc[i].name),
                "open": df["open"].iloc[i],
                "close": df["close"].iloc[i],
                "volume": df["volume"].iloc[i],
            }



    def getReward(self, action, df, i):
        try:
            # Reward constants
            OK = 0.1
            NO = -0.5
            YES = 1
            DIAMOND = 3
            GOLD = 2
            BAD = -1
            TERRIBLE = -3

            state = self.getState(df, i)

            # Reward lookup table: { state: { action: reward } }
            R = {
                # ---------------- FIAT STATES ----------------
                self.STATE_GOLD_WITHIN_FAIT: {Indicator.BUY: YES,Indicator.SELL: TERRIBLE,Indicator.HOLD: 0},
                self.STATE_GOLD_WITHOUT_FAIT: {Indicator.BUY: YES,Indicator.SELL: TERRIBLE,Indicator.HOLD: 0},
                self.STATE_HIT_GOLD_FAIT: {Indicator.BUY: DIAMOND,Indicator.SELL: TERRIBLE,Indicator.HOLD: 0},
                self.STATE_DEATH_WITHIN_FAIT: {Indicator.BUY: TERRIBLE,Indicator.SELL: TERRIBLE,Indicator.HOLD: 0},
                self.STATE_DEATH_WITHOUT_FAIT: {Indicator.BUY: TERRIBLE, Indicator.SELL: TERRIBLE,Indicator.HOLD: 0,},
                # ---------------- ASSET NORMAL RANGE ----------------
                self.STATE_GOLD_WITHIN_ASSET: {Indicator.BUY: TERRIBLE,Indicator.SELL: NO,Indicator.HOLD: OK, },
                self.STATE_DEATH_WITHIN_ASSET: {Indicator.BUY: TERRIBLE,Indicator.SELL: NO,Indicator.HOLD: OK, },
                self.STATE_DEATH_WITHOUT_ASSET: {Indicator.BUY: TERRIBLE,Indicator.SELL: NO,Indicator.HOLD: OK},
                # ---------------- TAKE PROFIT ----------------
                self.STATE_ABOVE_TAKE_PROFIT_ASSET:{ Indicator.BUY: TERRIBLE,Indicator.SELL: DIAMOND,Indicator.HOLD: OK},
                # ---------------- STOP LOSS ----------------
                self.STATE_BELOW_STOPLOSS_ASSET:{ Indicator.BUY: TERRIBLE,Indicator.SELL: GOLD,Indicator.HOLD: BAD},
                # ---------------- DEATH CROSS HIT IN ASSET ----------------
                self.STATE_HIT_DEATH_WITH_ASSET:{ Indicator.BUY: TERRIBLE, Indicator.SELL: DIAMOND,Indicator.HOLD: OK },
            }
            return R.get(state, {}).get(action, 0)

        except:
            traceback.print_exc()
            return 0


    def getReward_old(self, action, df, i):

        golden = self._cache["AvSlowLessThanFast"]
        holding_fiat = (self._cache["holding"] == self._pair[0])

        price = (df.iloc[i]["close"] + df.iloc[i]["open"]) / 2
        in_range = self._priceInStopLossTakeProfit(price)

        # ---------------- FIAT ----------------
        if holding_fiat:

            if action == Indicator.BUY:
                return 0.5 if golden else -0.5

            if action == Indicator.SELL:
                return -0.2  # mild penalty

            return 0  # HOLD

        # ---------------- IN TRADE ----------------
        else:

            # Take Profit
            if price >= self._cache["take_profit"]:
                if action == Indicator.SELL:
                    return 1.0
                if action == Indicator.HOLD:
                    return 0.2
                return -0.5

            # Stop Loss
            if price <= self._cache["stop_loss"]:
                if action == Indicator.HOLD:
                    return -1.0
                if action == Indicator.SELL:
                    return -0.2
                return -0.5

            # Normal trade zone
            if action == Indicator.HOLD:
                return 0.1

            if action == Indicator.SELL:
                return -0.3

            if action == Indicator.BUY:
                return -0.5

        return 0




    "@override"
    def getState(self, df, i):
        try:
            goldenCross = self._cache["AvSlowLessThanFast"]
            price = (df.iloc[i]["close"] + df.iloc[i]["open"]) / 2
            in_range = self._priceInStopLossTakeProfit(price)

            holding_fiat = (self._cache["holding"] == self._pair[0])
            holding_asset = (self._cache["holding"] == self._pair[1])

            if holding_asset and not in_range:
                if price >= self._cache["take_profit"]:
                    return self.STATE_ABOVE_TAKE_PROFIT_ASSET
                if price <= self._cache["stop_loss"]:
                    return self.STATE_BELOW_STOPLOSS_ASSET

            # --------------------------
            # GOLDEN CROSS STATES
            # --------------------------
            if goldenCross:
                if holding_fiat:
                    if self._cache["crossHit"]:
                        return self.STATE_HIT_GOLD_FAIT
                    if in_range:
                        return self.STATE_GOLD_WITHIN_FAIT
                    else:
                        return self.STATE_GOLD_WITHOUT_FAIT
                elif holding_asset:
                    if in_range:
                        return self.STATE_GOLD_WITHIN_ASSET

            # --------------------------
            # DEATH CROSS STATES
            # --------------------------
            else:
                if holding_fiat:
                    if in_range:
                        return self.STATE_DEATH_WITHIN_FAIT
                    else:
                        return self.STATE_DEATH_WITHOUT_FAIT
                elif holding_asset:
                    if self._cache["crossHit"]:
                        return self.STATE_HIT_DEATH_WITH_ASSET
                    if in_range:
                        return self.STATE_DEATH_WITHIN_ASSET
                    else:
                        return self.STATE_DEATH_WITHOUT_ASSET

            # Fallback (should never happen)
            return 0

        except:
            traceback.print_exc()
            return 0



    "@override"
    def buy( self, price ):
        self._cache["entry"] = price # buy asset
        self._cache["holding"] = self._pair[1] # buy asset
        self._open_long_trade( price )
    
    "@override"
    def sell( self, price ):
        self._cache["holding"] = self._pair[0] # fait
    
    "@override"
    def work( self, df, i ):
        self._indicator_golden_cross( df , i );

