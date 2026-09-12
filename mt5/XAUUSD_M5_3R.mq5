//+------------------------------------------------------------------+
//|  XAUUSD_M5_3R.mq5                                                |
//|  Momentum displacement -> limit pullback -> fixed 3:1            |
//|                                                                  |
//|  Line-for-line mirror of xauusd/strategy.py. If you change one,  |
//|  change the other in the same commit, or you are live-trading a  |
//|  strategy you never backtested.                                  |
//|                                                                  |
//|  Decisions are made ONCE per closed M5 bar, using bar index 1     |
//|  (the last CLOSED bar). Never index 0. Index 0 is the future.     |
//+------------------------------------------------------------------+
#property copyright "XAUUSD M5 3R"
#property version   "1.00"

#include <Trade\SymbolInfo.mqh>

//--- reward:risk ----------------------------------------------------
input group             "=== Reward : Risk ==="
input double InpRR              = 3.0;    // Reward:risk (the ask: 3.0)

input group             "=== Displacement trigger ==="
input int    InpBreakoutLB      = 20;     // Close beyond extreme of N prior bars
input double InpMinLegATR       = 1.0;    // Min impulse leg, x ATR
input double InpMaxLegATR       = 6.0;    // Max impulse leg, x ATR

input group             "=== Limit entry ==="
input double InpRetrace         = 0.382;  // Limit depth into the leg
input bool   InpEmaConfluence   = true;   // Pull limit to EMA when deeper
input int    InpEmaPullback     = 21;     // Pullback EMA period

input group             "=== Stop ==="
input double InpSLBufferATR     = 0.30;   // Stop buffer beyond leg origin, x ATR
input double InpMinRATR         = 0.50;   // Min stop distance, x ATR
input double InpMaxRATR         = 2.50;   // Max stop distance, x ATR

input group             "=== Regime filters ==="
input int    InpEmaFast         = 21;
input int    InpEmaSlow         = 50;
input int    InpHtfEma          = 21;     // EMA period on H1
input bool   InpRequireHtf      = true;   // Require H1 trend agreement
input int    InpAtrPeriod       = 14;
input int    InpAtrPctWindow    = 480;    // Lookback for the volatility band
input double InpAtrPctFloor     = 0.30;   // Reject dead tape below this pct
input double InpAtrPctCap       = 0.97;   // Reject news spikes above this pct

input group             "=== Order lifecycle ==="
input int    InpExpireBars      = 12;     // Cancel unfilled limits after N bars
input double InpInvalidateFrac  = 0.10;   // Cancel if close re-enters leg origin

input group             "=== Sessions (UTC) ==="
input int    InpServerGmtOffset = 0;      // Broker server time minus UTC, in hours
input string InpSession1        = "07:00-11:00";  // London
input string InpSession2        = "12:30-16:30";  // NY overlap
input string InpForceFlat       = "20:00";        // Flat by this time
input int    InpFridayCutoffH   = 16;     // No new risk after this hour on Friday

input group             "=== Risk ==="
input double InpRiskPct         = 0.5;    // Risk per trade, % of equity
input int    InpMaxTradesPerDay = 4;
input double InpDailyLossStopR  = 2.0;    // Stand down after -N R on the day
input double InpMoveSLToBEatR   = 0.0;    // 0 = off. Pure 3:1 as designed.
input double InpMaxSpread       = 0.60;   // Skip if spread (USD/oz) is wider
input long   InpMagic           = 20240503;

//--- state ----------------------------------------------------------
int      hAtr = INVALID_HANDLE;
int      hEmaFast = INVALID_HANDLE, hEmaSlow = INVALID_HANDLE, hEmaPull = INVALID_HANDLE;
int      hEmaHtf = INVALID_HANDLE;
datetime lastBarTime = 0;
datetime dayStamp = 0;
int      tradesToday = 0;
double   realisedRToday = 0.0;
double   pointValuePerLot = 0.0;
CSymbolInfo sym;

struct Window { int from; int to; bool ok; };   // minutes from UTC midnight
Window   sess1, sess2;
int      flatMinute = 20 * 60;

//+------------------------------------------------------------------+
int OnInit()
{
   if(!sym.Name(_Symbol))
   {
      Print("FATAL: cannot bind symbol ", _Symbol);
      return INIT_FAILED;
   }
   sym.RefreshRates();

   if(Period() != PERIOD_M5)
      Print("WARNING: designed for M5. Current chart is ", EnumToString((ENUM_TIMEFRAMES)Period()),
            " - the logic still runs on M5 series data, but attach it to M5 to avoid confusion.");

   hAtr     = iATR(_Symbol, PERIOD_M5, InpAtrPeriod);
   hEmaFast = iMA(_Symbol, PERIOD_M5, InpEmaFast, 0, MODE_EMA, PRICE_CLOSE);
   hEmaSlow = iMA(_Symbol, PERIOD_M5, InpEmaSlow, 0, MODE_EMA, PRICE_CLOSE);
   hEmaPull = iMA(_Symbol, PERIOD_M5, InpEmaPullback, 0, MODE_EMA, PRICE_CLOSE);
   hEmaHtf  = iMA(_Symbol, PERIOD_H1, InpHtfEma, 0, MODE_EMA, PRICE_CLOSE);

   if(hAtr == INVALID_HANDLE || hEmaFast == INVALID_HANDLE || hEmaSlow == INVALID_HANDLE ||
      hEmaPull == INVALID_HANDLE || hEmaHtf == INVALID_HANDLE)
   {
      Print("FATAL: indicator handle creation failed");
      return INIT_FAILED;
   }

   if(InpRR <= 0 || InpRetrace <= 0 || InpRetrace >= 1 || InpMinRATR <= 0 ||
      InpMaxRATR <= InpMinRATR || InpMinLegATR <= 0 || InpMaxLegATR <= InpMinLegATR ||
      InpExpireBars < 1 || InpAtrPctFloor < 0 || InpAtrPctCap > 1 || InpAtrPctFloor >= InpAtrPctCap)
   {
      Print("FATAL: inconsistent inputs - refusing to trade a config that cannot work");
      return INIT_PARAMETERS_INCORRECT;
   }

   sess1 = ParseWindow(InpSession1);
   sess2 = ParseWindow(InpSession2);
   if(!sess1.ok && !sess2.ok)
   {
      Print("FATAL: no valid session window");
      return INIT_PARAMETERS_INCORRECT;
   }
   flatMinute = ParseMinute(InpForceFlat, 20 * 60);

   // value of a 1.00 USD/oz move for 1.00 lot
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0 || tickValue <= 0)
   {
      Print("FATAL: broker reports tick size ", tickSize, " tick value ", tickValue);
      return INIT_FAILED;
   }
   pointValuePerLot = tickValue / tickSize;
   PrintFormat("init ok | 1.00 USD/oz move = %.2f USD per lot | breakeven WR at %.1f:1 = %.1f%%",
               pointValuePerLot, InpRR, 100.0 / (1.0 + InpRR));
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   IndicatorRelease(hAtr);
   IndicatorRelease(hEmaFast);
   IndicatorRelease(hEmaSlow);
   IndicatorRelease(hEmaPull);
   IndicatorRelease(hEmaHtf);
}

//+------------------------------------------------------------------+
//| One decision per closed bar. Ticks in between only manage risk.  |
//+------------------------------------------------------------------+
void OnTick()
{
   RollDay();
   ManageOpenPositions();      // break-even + flat-time, every tick
   datetime t0 = iTime(_Symbol, PERIOD_M5, 0);
   if(t0 == lastBarTime)
      return;
   lastBarTime = t0;

   CancelStaleOrders();        // once per bar is enough
   if(HasOpenPosition() || HasPendingOrder())
      return;
   if(tradesToday >= InpMaxTradesPerDay)
      return;
   if(realisedRToday <= -MathAbs(InpDailyLossStopR))
      return;
   EvaluateSignal();
}

//+------------------------------------------------------------------+
//| Signal on bar 1 (last CLOSED bar)                                |
//+------------------------------------------------------------------+
void EvaluateSignal()
{
   int need = MathMax(InpAtrPctWindow + InpAtrPeriod + 5, InpEmaSlow * 3);
   if(Bars(_Symbol, PERIOD_M5) < need)
      return;

   datetime sigTime = iTime(_Symbol, PERIOD_M5, 1);
   int minute = UtcMinuteOfDay(sigTime);
   if(!InSession(minute))
      return;

   MqlDateTime dt;
   TimeToStruct(ToUtc(sigTime), dt);
   if(dt.day_of_week == 5 && dt.hour >= InpFridayCutoffH)
      return;

   if(!sym.RefreshRates())
      return;
   double spread = sym.Ask() - sym.Bid();
   if(spread > InpMaxSpread)
   {
      PrintFormat("skip: spread %.2f > cap %.2f", spread, InpMaxSpread);
      return;
   }

   double atrBuf[];
   if(CopyBuffer(hAtr, 0, 1, InpAtrPctWindow, atrBuf) < InpAtrPctWindow)
      return;
   double atr = atrBuf[InpAtrPctWindow - 1];   // most recent closed bar
   if(atr <= 0)
      return;

   // volatility band: too quiet and 3R is unreachable, too wild and you were
   // the last liquidity before the reversal
   double floorAtr = Percentile(atrBuf, InpAtrPctFloor);
   double capAtr   = Percentile(atrBuf, InpAtrPctCap);
   if(atr < floorAtr || atr > capAtr)
      return;

   double ef[], es[], ep[], eh[];
   if(CopyBuffer(hEmaFast, 0, 1, 1, ef) < 1) return;
   if(CopyBuffer(hEmaSlow, 0, 1, 1, es) < 1) return;
   if(CopyBuffer(hEmaPull, 0, 1, 1, ep) < 1) return;
   if(CopyBuffer(hEmaHtf,  0, 1, 2, eh) < 2) return;   // [0]=older, [1]=last closed H1

   double closeSig = iClose(_Symbol, PERIOD_M5, 1);
   double htfClose = iClose(_Symbol, PERIOD_H1, 1);     // last CLOSED H1 bar
   double htfEma = eh[1], htfEmaPrev = eh[0];
   int htfBias = 0;
   if(htfClose > htfEma && htfEma >= htfEmaPrev) htfBias = 1;
   else if(htfClose < htfEma && htfEma <= htfEmaPrev) htfBias = -1;

   // extreme of the InpBreakoutLB bars BEFORE the signal bar
   int iHi = iHighest(_Symbol, PERIOD_M5, MODE_HIGH, InpBreakoutLB, 2);
   int iLo = iLowest(_Symbol, PERIOD_M5, MODE_LOW, InpBreakoutLB, 2);
   if(iHi < 0 || iLo < 0)
      return;
   double priorHigh = iHigh(_Symbol, PERIOD_M5, iHi);
   double priorLow  = iLow(_Symbol, PERIOD_M5, iLo);

   bool longOk  = (closeSig > priorHigh) && (ef[0] > es[0]) && (!InpRequireHtf || htfBias > 0);
   bool shortOk = (closeSig < priorLow)  && (ef[0] < es[0]) && (!InpRequireHtf || htfBias < 0);
   if(longOk == shortOk)
      return;

   // leg origin includes the signal bar itself
   int oLo = iLowest(_Symbol, PERIOD_M5, MODE_LOW, InpBreakoutLB + 1, 1);
   int oHi = iHighest(_Symbol, PERIOD_M5, MODE_HIGH, InpBreakoutLB + 1, 1);
   double origin = longOk ? iLow(_Symbol, PERIOD_M5, oLo) : iHigh(_Symbol, PERIOD_M5, oHi);
   double leg = MathAbs(closeSig - origin);
   if(leg < InpMinLegATR * atr || leg > InpMaxLegATR * atr)
      return;

   double entry, sl;
   if(longOk)
   {
      entry = closeSig - InpRetrace * leg;
      if(InpEmaConfluence && ep[0] > origin && ep[0] < entry)
         entry = ep[0];                        // deeper entry = smaller R = reachable 3R
      entry = MathMax(entry, origin + 0.05 * leg);
      sl = origin - InpSLBufferATR * atr;
   }
   else
   {
      entry = closeSig + InpRetrace * leg;
      if(InpEmaConfluence && ep[0] < origin && ep[0] > entry)
         entry = ep[0];
      entry = MathMin(entry, origin - 0.05 * leg);
      sl = origin + InpSLBufferATR * atr;
   }

   double r = longOk ? (entry - sl) : (sl - entry);
   if(r <= 0 || r < InpMinRATR * atr || r > InpMaxRATR * atr)
      return;
   double tp = longOk ? entry + InpRR * r : entry - InpRR * r;

   // Never place a limit on the wrong side of the market: that is a market
   // order in a costume, and it destroys the risk geometry the whole edge
   // rests on. MT5 rule: buy limit below Ask, sell limit above Bid, and
   // outside the broker's freeze distance.
   double freeze = (double)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL) * _Point;
   if(longOk && entry >= sym.Ask() - freeze)
   { Print("skip: long limit not safely below the ask"); return; }
   if(!longOk && entry <= sym.Bid() + freeze)
   { Print("skip: short limit not safely above the bid"); return; }

   double stopsLevel = (double)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
   if(MathAbs(entry - sl) < stopsLevel || MathAbs(tp - entry) < stopsLevel)
   {
      Print("skip: broker minimum stop distance exceeds our geometry");
      return;
   }

   double lots = LotsForRisk(r);
   if(lots <= 0)
   {
      Print("skip: smallest tradable lot would exceed the risk budget");
      return;
   }
   PlaceLimit(longOk, NormalizePrice(entry), NormalizePrice(sl), NormalizePrice(tp), lots, r, atr, origin, leg);
}

//+------------------------------------------------------------------+
bool PlaceLimit(const bool isLong, const double entry, const double sl, const double tp,
                const double lots, const double r, const double atr,
                const double origin, const double leg)
{
   MqlTradeRequest req;  ZeroMemory(req);
   MqlTradeResult  res;  ZeroMemory(res);

   req.action       = TRADE_ACTION_PENDING;
   req.symbol       = _Symbol;
   req.volume       = lots;
   req.type         = isLong ? ORDER_TYPE_BUY_LIMIT : ORDER_TYPE_SELL_LIMIT;
   req.price        = entry;
   req.sl           = sl;
   req.tp           = tp;
   req.magic        = InpMagic;
   req.deviation    = 10;
   // Prefer a broker-side expiry so a dropped connection cannot leave a stale
   // limit resting for hours. Fall back to GTC + our own bar-count cancel when
   // the broker does not support timed expiry.
   long expMode = SymbolInfoInteger(_Symbol, SYMBOL_EXPIRATION_MODE);
   if((expMode & SYMBOL_EXPIRATION_SPECIFIED) != 0)
   {
      req.type_time  = ORDER_TIME_SPECIFIED;
      req.expiration = iTime(_Symbol, PERIOD_M5, 0) + InpExpireBars * 5 * 60;
   }
   else
   {
      req.type_time  = ORDER_TIME_GTC;   // CancelStaleOrders() enforces the expiry
   }
   req.type_filling = PickFilling();
   // stash the invalidation level in the comment so CancelStaleOrders can read
   // it back without any external state to lose on restart
   req.comment      = StringFormat("3R|%s|%.2f",
                        isLong ? "L" : "S",
                        isLong ? origin + InpInvalidateFrac * leg
                               : origin - InpInvalidateFrac * leg);

   if(!OrderSend(req, res) || (res.retcode != TRADE_RETCODE_DONE && res.retcode != TRADE_RETCODE_PLACED))
   {
      PrintFormat("OrderSend failed: retcode=%d %s", res.retcode, res.comment);
      return false;
   }
   PrintFormat("%s LIMIT %.2f lots @ %.2f | SL %.2f | TP %.2f | R=%.2f (%.2f ATR) | expires %s",
               isLong ? "BUY" : "SELL", lots, entry, sl, tp, r, r / atr,
               TimeToString(req.expiration, TIME_MINUTES));
   return true;
}

//+------------------------------------------------------------------+
//| Cancel stale, invalidated or out-of-session orders.              |
//| Dead money is worse than a loss: it also blocks the next setup.  |
//+------------------------------------------------------------------+
void CancelStaleOrders()
{
   double prevClose = iClose(_Symbol, PERIOD_M5, 1);
   int minute = UtcMinuteOfDay(iTime(_Symbol, PERIOD_M5, 0));
   bool sessionOver = (minute >= flatMinute) || !InSession(minute);

   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(ticket == 0) continue;
      if(!OrderSelect(ticket)) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      if(OrderGetInteger(ORDER_MAGIC) != InpMagic) continue;

      bool kill = sessionOver;
      string reason = "session";
      if(!kill)
      {
         // enforce the expiry ourselves too, in case the broker took the order
         // as GTC (see PlaceLimit) - a stale limit is worse than no limit
         datetime placed = (datetime)OrderGetInteger(ORDER_TIME_SETUP);
         if(TimeCurrent() - placed > InpExpireBars * 5 * 60)
         {
            kill = true;
            reason = "expired";
         }
      }
      if(!kill)
      {
         string cm = OrderGetString(ORDER_COMMENT);
         string parts[];
         if(StringSplit(cm, '|', parts) == 3)
         {
            bool isLong = (parts[1] == "L");
            double invalidate = StringToDouble(parts[2]);
            if(( isLong && prevClose < invalidate) || (!isLong && prevClose > invalidate))
            {
               kill = true;
               reason = "structure broken";
            }
         }
      }
      if(kill)
      {
         MqlTradeRequest req; ZeroMemory(req);
         MqlTradeResult  res; ZeroMemory(res);
         req.action = TRADE_ACTION_REMOVE;
         req.order  = ticket;
         if(OrderSend(req, res))
            PrintFormat("cancelled #%I64u (%s)", ticket, reason);
      }
   }
}

//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   int minute = UtcMinuteOfDay(TimeCurrent());
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;

      long type   = PositionGetInteger(POSITION_TYPE);
      double entry = PositionGetDouble(POSITION_PRICE_OPEN);
      double sl    = PositionGetDouble(POSITION_SL);
      double tp    = PositionGetDouble(POSITION_TP);
      bool isLong  = (type == POSITION_TYPE_BUY);

      if(minute >= flatMinute)
      {
         ClosePosition(ticket, "flat-time");
         continue;
      }
      if(InpMoveSLToBEatR > 0 && sl != 0 && MathAbs(sl - entry) > _Point)
      {
         double r = MathAbs(entry - sl);
         double price = isLong ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                               : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         double progress = isLong ? (price - entry) / r : (entry - price) / r;
         if(progress >= InpMoveSLToBEatR)
            ModifyStop(ticket, NormalizePrice(entry), tp);
      }
   }
}

bool ClosePosition(const ulong ticket, const string why)
{
   if(!PositionSelectByTicket(ticket)) return false;
   MqlTradeRequest req; ZeroMemory(req);
   MqlTradeResult  res; ZeroMemory(res);
   req.action    = TRADE_ACTION_DEAL;
   req.position  = ticket;
   req.symbol    = _Symbol;
   req.volume    = PositionGetDouble(POSITION_VOLUME);
   req.magic     = InpMagic;
   req.deviation = 20;
   req.type      = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
                     ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   req.price     = (req.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                                                 : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   req.type_filling = PickFilling();
   bool ok = OrderSend(req, res) &&
             (res.retcode == TRADE_RETCODE_DONE || res.retcode == TRADE_RETCODE_PLACED);
   PrintFormat("close #%I64u (%s) -> %s retcode=%d", ticket, why, ok ? "ok" : "FAILED", res.retcode);
   return ok;
}

bool ModifyStop(const ulong ticket, const double sl, const double tp)
{
   MqlTradeRequest req; ZeroMemory(req);
   MqlTradeResult  res; ZeroMemory(res);
   req.action   = TRADE_ACTION_SLTP;
   req.position = ticket;
   req.symbol   = _Symbol;
   req.sl       = sl;
   req.tp       = tp;
   return OrderSend(req, res) && res.retcode == TRADE_RETCODE_DONE;
}

//+------------------------------------------------------------------+
//| Track realised R per day so the daily loss stop is real          |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) != _Symbol) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != InpMagic) return;

   long entryType = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   if(entryType == DEAL_ENTRY_IN)
   {
      tradesToday++;
      return;
   }
   if(entryType == DEAL_ENTRY_OUT || entryType == DEAL_ENTRY_INOUT)
   {
      double profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT)
                    + HistoryDealGetDouble(trans.deal, DEAL_COMMISSION)
                    + HistoryDealGetDouble(trans.deal, DEAL_SWAP);
      double riskUsd = AccountInfoDouble(ACCOUNT_EQUITY) * InpRiskPct / 100.0;
      if(riskUsd > 0)
         realisedRToday += profit / riskUsd;
      PrintFormat("closed deal profit %.2f -> day R %.2f (cap %.1f)",
                  profit, realisedRToday, -MathAbs(InpDailyLossStopR));
   }
}

//+------------------------------------------------------------------+
//| helpers                                                          |
//+------------------------------------------------------------------+
double LotsForRisk(const double rPrice)
{
   if(rPrice <= 0 || pointValuePerLot <= 0) return 0.0;
   double riskUsd = AccountInfoDouble(ACCOUNT_EQUITY) * InpRiskPct / 100.0;
   double raw = riskUsd / (rPrice * pointValuePerLot);

   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step <= 0) step = 0.01;

   double lots = MathFloor(raw / step) * step;   // round DOWN, always
   lots = NormalizeDouble(lots, 2);
   if(lots < minL) return 0.0;                   // skip beats over-risking
   return MathMin(lots, maxL);
}

double NormalizePrice(const double price)
{
   double tick = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick <= 0) return NormalizeDouble(price, _Digits);
   return NormalizeDouble(MathRound(price / tick) * tick, _Digits);
}

ENUM_ORDER_TYPE_FILLING PickFilling()
{
   long modes = SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if((modes & SYMBOL_FILLING_FOK) != 0) return ORDER_FILLING_FOK;
   if((modes & SYMBOL_FILLING_IOC) != 0) return ORDER_FILLING_IOC;
   return ORDER_FILLING_RETURN;
}

double Percentile(const double &values[], const double pct)
{
   int n = ArraySize(values);
   if(n <= 0) return 0.0;
   double copy[];
   ArrayResize(copy, n);
   ArrayCopy(copy, values);
   ArraySort(copy);
   double pos = pct * (n - 1);
   int lo = (int)MathFloor(pos);
   int hi = MathMin(lo + 1, n - 1);
   return copy[lo] + (copy[hi] - copy[lo]) * (pos - lo);
}

datetime ToUtc(const datetime serverTime)
{
   return serverTime - (datetime)(InpServerGmtOffset * 3600);
}

int UtcMinuteOfDay(const datetime serverTime)
{
   MqlDateTime dt;
   TimeToStruct(ToUtc(serverTime), dt);
   return dt.hour * 60 + dt.min;
}

bool InSession(const int minute)
{
   if(sess1.ok && minute >= sess1.from && minute < sess1.to) return true;
   if(sess2.ok && minute >= sess2.from && minute < sess2.to) return true;
   return false;
}

int ParseMinute(const string hhmm, const int fallback)
{
   string p[];
   if(StringSplit(hhmm, ':', p) != 2) return fallback;
   int h = (int)StringToInteger(p[0]);
   int m = (int)StringToInteger(p[1]);
   if(h < 0 || h > 24 || m < 0 || m > 59) return fallback;
   return h * 60 + m;
}

Window ParseWindow(const string spec)
{
   Window w; w.from = 0; w.to = 0; w.ok = false;
   string p[];
   if(StringSplit(spec, '-', p) != 2) return w;
   w.from = ParseMinute(p[0], -1);
   w.to   = ParseMinute(p[1], -1);
   w.ok   = (w.from >= 0 && w.to > w.from && w.to <= 24 * 60);
   return w;
}

bool HasOpenPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(t == 0 || !PositionSelectByTicket(t)) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagic)
         return true;
   }
   return false;
}

bool HasPendingOrder()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong t = OrderGetTicket(i);
      if(t == 0 || !OrderSelect(t)) continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol &&
         OrderGetInteger(ORDER_MAGIC) == InpMagic)
         return true;
   }
   return false;
}

void RollDay()
{
   MqlDateTime dt;
   TimeToStruct(ToUtc(TimeCurrent()), dt);
   datetime stamp = (datetime)(dt.year * 10000 + dt.mon * 100 + dt.day);
   if(stamp != dayStamp)
   {
      dayStamp = stamp;
      tradesToday = 0;
      realisedRToday = 0.0;
   }
}
//+------------------------------------------------------------------+
