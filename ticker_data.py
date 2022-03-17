import datetime as dt
import numpy as np

def getList(fn, delimit='\n'):
    l= []
    
    with open(fn, 'r') as f:
        txt = f.read()
        if txt == '':
            return []

        #for sp in split:
        #   l = [ i.split(delimit) for i in l ]
        #while len(l) == 1:
        #    l = l[0]

        l = txt.split(delimit)

    return l

class StockEvent:
    def __init__(self, datetime, open_, high_, low_, close_, vol_ = 0, symbol='#UNDEF#', OVERIDE_MKT = None):
        #accepted format datetime.date
        self.datetime = datetime

        #float values
        self.open = float(open_)
        self.high = float(high_)
        self.low  = float(low_)
        self.close= float(close_)
        self.vol  = float(vol_)

        self.symbol = symbol
        if OVERIDE_MKT is not None:
            self.market_tick = OVERIDE_MKT
        else:
            self.market_tick = getMarketTick(self.datetime)    

    def priceMove(self):
        return self.close - self.open

    def OVERIDE_mtk(mtk):
        self.market_tick = mkt
        
    def __str__(self):
        #print([self.datetime, [self.market_tick, self.open, self.high, self.low, self.close, self.vol],\
        #       self.symbol])
        return str([self.datetime.isoformat(),\
                    [self.market_tick, self.open, self.high, self.low, self.close, self.vol],\
                    self.symbol])

def DEPRECATED_searchRedundancy(se, v=0):
    red_idx = []
    for i in range(len(se)-1):
        if se[i].market_tick >= se[i+1].market_tick:
            if v:
                print(i, se[i], se[i+1])
            red_idx.append(i)
        if v and i%30:
            print(">> searched {:.2f}%".format(i*100/len(se)))

    return red_idx

def removeRedundancy(se, red_idx=[]):
    #se.sort(key = lambda x : x.market_tick)

    i = 1
    while i < len(se):
        if se[i-1].market_tick == se[i].market_tick:
            se.pop(i)
        else:
            i += 1

    return se

def fillholes(se):
    i = 1
    while i < len(se):
        if se[i-1].market_tick +1 != se[i].market_tick:
            l = [ StockEvent(dt.datetime(1,1,1), 0,0,0,0,0,'', i) for i in range(se[i-1].market_tick +1, se[i].market_tick) ]
            se = se[:i] + l + se[i:]

        i += 1
    return se



def DEPRECATED_removeRedundancy(se, red_idx=[]):
    if len(red_idx) == 0:
        red_idx = searchRedundancy(se)

    mark = []
    todel = []
    for ridx in red_idx:
        for x in range(ridx, 0, -1):
            td = se[x].datetime - se[ridx+1].datetime
            if td.total_seconds == 0:
                mark.append([x, ridx+1])

    for s in mark:
        for i in range(s[0], s[1]):
            td = se[i].datetime - se[s[1]+i].datetime
            if td.total_seconds == 0:
                todel.append()

    todel.sort()
    todel.reverse()
    for i in range(len(todel)):
        if todel[i] in todel[i+1:]:
            continue
        se.pop(i)

def DEPRECATED_findHoles(se):
    for i in range(1, len(se)):
        diff = se[i].market_tick - se[i-1].market_tick
        if diff>1:
            print(">> se[{}] - se[{}] :: mt-diff = {}-{}"\
                  .format(i, i-1, se[i].market_tick, diff))

holidays = []
def getPrecHoli(date):
    #update local/fetch holiday list
    global holidays
    if not holidays.__len__():
        with open('L:/dev/st_nn/holidays_frm.csv', 'r') as f:
            txt = f.read()

        data = [ t.split(' ') for t in txt.split('\n') ]
        
        holidays = []
        for d in data:
            event = ''
            for t in d[3:]:
                event += t
            
            holidays.append([ dt.date( int(d[0]), int(d[1]), int(d[2])), event ])

    for i in range(holidays.__len__()):
        ddays = holidays[i][0]-date
        if ddays.days < 0:
            continue
        return i #one less

    return holidays.__len__()

def getMarketTick(date):
        ''' NSE was established in 1992
            so we will start all stock clock tickers from
            1992 MAR 02 Mon 09:00:00

            BUT BUT
            there are holidays and database for holidays exsist only since 2011 JAN 03 MON
            so ... ticker start from
            2011 JAN 03 09 15
        '''

        ddays = date - dt.datetime(2011, 1, 3, 0, 0, 0)

        p_hdays =  getPrecHoli(date.date())
        nweekdays = 5*int(ddays.days/7) # JAN03 is MON

        total_days = nweekdays - p_hdays + min(5, date.weekday()) ##iso == 1st se is mkt_tick = 0
        
        #5min granularity for each day from 09:15 to 15:30 == 6hr 15min == 6*60/5 +15/5 == 75
        market_tick = total_days*75
        
        if date.weekday() < 5:
            minutes = date.hour*60 + date.minute
            market_tick += int(max(0, min(15*60+30, minutes) - (9*60+15))/5)

        #print("total_days:", total_days, "weekday:", date.weekday())
        return int(market_tick)

##FUCKD_UP
def getTickDate(market_tick):
        ''' NSE was established in 1992
            so we will start all stock clock tickers from
            1992 MAR 02 Mon 09:00:00

            BUT BUT
            there are holidays and database for holidays exsist only since 2011 JAN 03 MON
            so ... ticker start from
            2011 JAN 01 
        '''
        p_hdays =  getPrecHoli(date)
        
        d = int(market_tick/75) + p_hdays
        hr = 9 + int((market_tick%75)/12)
        m = 15+((market_tick%75)%12)*5

        date = dt.datetime(2011, 1, 3, 0, 0, 0)\
               + dt.timedelta(days=d + p_hdays, hours=hr, minutes=m)

        #date = dt.timedelta(

        p_hdays =  getPrecHoli(date)
        nweekdays = 5*int(ddays.days/7)

        total_days = nweekdays - p_hdays + date.isoweekday()

        #5min granularity for each day from 09:15 to 15:30 == 6hr 15min == 6*60/5 +15/5 == 75
        market_tick = total_days*75 + (date.hour-9)*12 + int((date.minute - 15)/5)

        return int(market_tick)

def EXTRACT(fn):
    symbol = fn.split('/')[-1].split('_')[0]
    
    #get raw data
    lines = getList(fn)
    data = [ l.split(',') for l in lines ]


    #clean data
    data_signature = data.pop(0)

    i = -1
    while i < data.__len__()-1:
        i+=1
        delete = False

        if data[i].__len__() < 2:
            data.pop(i)
            i-=1
            continue
        
        for j in range(1, data[i].__len__()):
            p = data[i][j]
            if p == '' or p.isalpha():
                delete = True
                break

        if delete:
            data.pop(i)
            i-=1

    #start object gen
    SE = []
    for d in data:
        sdt = [ d[0].split(' ')[0].split('-'),\
                     d[0].split(' ')[1].split('+')[0].split(':') ]

        if not sdt[0].__len__() == 3 or not sdt[1].__len__() == 3 :
            print('>> corrupt data'+fn)
        

        for i in range(2):
            for j in range(3):
                sdt[i][j] = int( sdt[i][j] )
        
                
        sdt = dt.datetime(sdt[0][0], sdt[0][1], sdt[0][2], sdt[1][0], sdt[1][1], sdt[1][2])

        SE.append(StockEvent(sdt, d[1], d[2], d[3], d[4], d[5], symbol))

    SE.sort(key = lambda x : x.market_tick)
    SE = removeRedundancy(SE)
    SE = fillholes(SE)

    return SE                         


