#StockCard

import ticker_data as td
import numpy as np

class StockCard:
    ###
    ## All Cards will be (5x4) market days long (fuck weeks n months)
    ## 
    ## at starting with dn(tick) then some stock specifics 
    ## each dn(tick) will be
    ## ohlv 
    ## [ [d0tick[0], d0tick[1], d0tick[2], d0tick[3]],
    ##   [d1tick[0], d1tick[1], d1tick[2], d1tick[3]],
    ##   [d2tick[0], d2tick[1], d2tick[2], d2tick[3]],
    ##   [d3tick[0], d3tick[1], d3tick[2], d3tick[3]],
    ##   [time[0],   time[1],   weekday,   yrday    ],
    ##   [marketick, date[0],   date[1],   date[2]  ] ]
    ##
    ## in total (5x4x75 = 1500 mt)x(6x4) =shape(1500, 6, 4)= 36000*32 bits = 144 KB
    ## 
    ###         
         
    def __init__(self, sym, datetime):
        self.sym = sym
        self.date = datetime
        self.MAT = np.zeros((1500, 6, 4), dtype='float32')


    #@deprecated
    #we will be using linear and not week fashion listing
    def _inputD0tick(self, se_arr):
        s_mkt = se_arr[-1].market_tick
        soff = (4-self.date.weekday())*75

        j = len(se_arr)-1
        i = soff + s_mkt - se_arr[j].market_tick
        

        while i < 1500 and j>=0:
            self.MAT[i][0] = np.array(\
                (se_arr[j].open, se_arr[j].high, se_arr[j].low, se_arr[j].vol),\
                dtype='float32')
            self.MAT[i][4] = np.array(\
                (se_arr[j].datetime.hour, se_arr[j].datetime.minute,\
                 se_arr[j].datetime.isoweekday(),\
                 se_arr[j].datetime.timetuple()[-2]),\
                dtype='float32')
            self.MAT[i][5] = np.array(\
                (se_arr[j].market_tick, se_arr[j].datetime.year,\
                 se_arr[j].datetime.month, se_arr[j].datetime.day),\
                dtype='float32')

            j -= 1
            i = soff + s_mkt - se_arr[j].market_tick

    def inputD0tick(self, se_arr):
        s_mkt = se_arr[-1].market_tick
        soff = 0 #linear listing

        j = len(se_arr)-1
        i = soff + s_mkt - se_arr[j].market_tick
        

        while i < 1500 and j>=0:
            self.MAT[i][0] = np.array(\
                (se_arr[j].open, se_arr[j].high, se_arr[j].low, se_arr[j].vol),\
                dtype='float32')
            self.MAT[i][4] = np.array(\
                (se_arr[j].datetime.hour, se_arr[j].datetime.minute,\
                 se_arr[j].datetime.isoweekday(),\
                 se_arr[j].datetime.timetuple()[-2]),\
                dtype='float32')
            self.MAT[i][5] = np.array(\
                (se_arr[j].market_tick, se_arr[j].datetime.year,\
                 se_arr[j].datetime.month, se_arr[j].datetime.day),\
                dtype='float32')

            j -= 1
            i = soff + s_mkt - se_arr[j].market_tick


    def computeDntick(self):
        #D1
        self.MAT[1:-1, 1] = (self.MAT[0:-2, 0] - self.MAT[2:, 0])/2

        #D2
        self.MAT[1:-1, 2] = (self.MAT[0:-2, 0] - 2*self.MAT[1:-1, 0]\
                                  + self.MAT[2:, 0])/4

        #interpolate D1
        self.MAT[0][1] = self.MAT[1][1] + self.MAT[1][2]*1
        self.MAT[-1][1] = self.MAT[-2][1] + self.MAT[-2][2]*1

        #D3                
        self.MAT[1:-1, 3, 0:] = (self.MAT[0:-2, 1] - 2*self.MAT[1:-1, 1]\
                                  + self.MAT[2:, 1])/4

        #interpolate D2
        self.MAT[0][2] = self.MAT[1][2] + self.MAT[1][3]*1
        self.MAT[-1][2] = self.MAT[-2][2] + self.MAT[-2][3]*1

        #interpolate D3
        self.MAT[0][3] = self.MAT[1][3] + (self.MAT[2][3] - self.MAT[3][3])
        self.MAT[-1][3] = self.MAT[-2][3] + (self.MAT[-3][3] - self.MAT[-4][3])

    def MAT2filetxt(self):
        txt = ""
        mftxt = "{:.2f} {:.2f} {:.2f} {} "+\
                "{:.5f} {:.5f} {:.5f} {:.3f} "+\
                "{:.5f} {:.5f} {:.5f} {:.4f} "+\
                "{:.5f} {:.5f} {:.5f} {:.4f} \t"
        dftxt = "{} {} {} {} \t"+\
                "{} {} {} {}\n"
        
        for i in range(1500):        
            txt += mftxt.format(*self.MAT[i][0:4].reshape((16)))\
                   + dftxt.format(*self.MAT[i][4:].reshape(8).astype('int32'))
            
            if (i+1)%75 == 0:
                txt += '\n'

        return txt[0:-2]
    
    def filetxt2MAT(self, txt):
        txt = txt.replace("\n\n", '\n').replace(' \t', ' ')
        txt = txt.splitlines()
        txt = [ t.split(' ') for t in txt ]

        toMAT = np.array(txt, dtype='float32')

        if toMAT.shape[0] != 1500 or toMAT.shape[1] != 24:
            print(">>> corrupt [filetxt] filetxt2MAT() [FAIL:shape{}]".format(toMAT.shape))
            return 1

        self.MAT = toMAT.reshape((1500, 6, 4))
        return 0       

    def MAT2D(self):
        ## shape (120, 300)
        mat2d = np.zeros((20*6, 75*4), dtype='float32')
        
        for i in range(0, 1500):
            mat2d[int(i/75)*6:int(i/75)*6+6, (i%75)*4:(i%75)*4+4] = self.MAT[i]

        return mat2d

    def MAT2Linear(self):
        ## shape (1500, 24)
        mat2l = np.zeros((1500, 24), dtype='float32')
        
        for i in range(0, 1500):
            mat2l[i] = self.MAT[i].flatten()
        
        return mat2l

    def MAT2Image(self):
        img = np.ndarray((75*5*4, 20*6, 3), dtype='uint8')
        
        '''
        price_fac = (np.maximum(self.MAT[0:, 1, 1]) - np.average(self.MAT[0:, 1, 2]))
        vol_fac =
        deriv_fac =
        mkt_fac =
        hr_fac =
        min_fac =
        weekday_fac =
        day_fac =
        month_fac =
        yr_fac =
        yrday_fac =
        
        for i in range(1500):
            
        '''
        pass



###
## BIG FUCKIN CHANGE BIG FUCKIN CHANGE - make data range for [ohlc](not v) for d0-5 LAARRGGEE (better nn performance )- 202110112322
###
###
## 20211007 SCC WILL INCLUDES CLOSE VALUE !!!IMP!!!
###
def makeSCC(SE, no_vol=False):
    SC = np.zeros((len(SE), 24+4), dtype='float32')


    # input dn0
    if no_vol:
        SC[:,0:5] = [ [ se.open, se.high, se.low, se.close,se.close*1000] for se in SE ]
    else:
        SC[:,0:5] = [ [ se.open, se.high, se.low, se.close,  se.vol] for se in SE ]
    SC[:,0:4] =  SC[:,0:4] * 10**3

    # compute dn
    #----------------------------

    #D1
    SC[1:-1, 5:10] = (SC[2:, 0:5] - SC[0:-2, 0:5])/2

    #D2
    SC[2:-2, 10:15] = (SC[0:-4, 0:5] -2*SC[2:-2, 0:5] + SC[4:, 0:5])/4
    
    #interpolate D1
    # [ a b c d e ]
    # a1 = b1 - b2 = b1 - ( c2 - c3 ) = b1 - ( c2 - ~(d2 - c2) ) = b1 - ~( 2*c2 - d2 )
    SC[0][5:10] = SC[1][5:10] - ( 2*SC[2][10:15] - SC[3][10:15] )
    SC[-1][5:10] = SC[-2][5:10] + ( 2*SC[-3][10:15] - SC[-4][10:15] )

    
    #D3
    SC[2:-2, 15:20] = (SC[0:-4, 5:10] - 2*SC[2:-2, 5:10] + SC[4:, 5:10])/4


    #interpolate D3 (simple addition)
    SC[ 0][15:20] = SC[ 2][15:20] + (SC[ 2][15:20] - SC[ 4][15:20]) 
    SC[ 1][15:20] = SC[ 2][15:20] + (SC[ 2][15:20] - SC[ 5][15:20])
    SC[-2][15:20] = SC[-3][15:20] + (SC[-3][15:20] - SC[-4][15:20])
    SC[-1][15:20] = SC[-3][15:20] + (SC[-3][15:20] - SC[-5][15:20])


    #interpolate D2 (using D3)
    SC[ 1][10:15] = SC[ 2][10:15] - ( 2*SC[ 3][15:20] - SC[ 4][15:20] )
    SC[-2][10:15] = SC[-3][10:15] + ( 2*SC[-4][15:20] - SC[-5][15:20] )

    SC[ 0][10:15] = SC[ 1][10:15] - ( 2*SC[ 2][15:20] - SC[ 3][15:20] )
    SC[-1][10:15] = SC[-2][10:15] + ( 2*SC[-3][15:20] - SC[-4][15:20] )
    

        # compute dn complete
    #----------------------------

    ## [ [d0tick[0], d0tick[1], d0tick[2], d0tick[3], d0tick[4]]
    ##   [d1tick[0], d1tick[1], d1tick[2], d1tick[3], d1tick[4]]
    ##   [d2tick[0], d2tick[1], d2tick[2], d2tick[3], d2tick[4]]
    ##   [d3tick[0], d3tick[1], d3tick[2], d3tick[3], d3tick[4]]
    ##   [time[0],   time[1],   weekday,   yrday               ],
    ##   [marketick, date[0],   date[1],   date[2]             ] ]

    SC[:, 20:28] =\
          [ [ se.datetime.hour, se.datetime.minute,\
              se.datetime.isoweekday(), se.datetime.timetuple()[-2],\
              se.market_tick, se.datetime.year,\
              se.datetime.month, se.datetime.day] for se in SE ]

    ###
    ## BIG FUCKIN CHANGE BIG FUCKIN CHANGE - make data range for [ohlc](not v) for d0-5 LAARRGGEE (better nn performance )- 202110112322
    ###


    '''
    #FOR [OHLC]
    #D0
    SC[:, 0:5-1]   *= 10**3
    #D1
    SC[:, 5:10-1]  *= 5*10**5
    #D2
    SC[:, 10:15-1] *= 10**6
    #D3
    SC[:, 15:20-1] *= 10**6

    #FOR [V]
    #D0
    SC[:, 4]  *= 1
    #D1
    SC[:, 9]  *= 1
    #D2
    SC[:, 14] *= 1
    #D3
    SC[:, 19] *= 10

    '''
    
    
    return SC

############################
'''
def DEPRECATED_makeSCC(SE):
    SC = np.zeros((len(SE), 24), dtype='float32')


    # input dn0
    SC[:,0:4] = [ [ se.open, se.high, se.low, se.vol] for se in SE ]

    # compute dn
    #----------------------------

    #D1
    SC[1:-1, 4:8] = (SC[2:, 0:4] - SC[0:-2, 0:4])/2

    #D2
    SC[2:-2, 8:12] = (SC[0:-4, 0:4] -2*SC[2:-2, 0:4] + SC[4:, 0:4])/4
    
    #interpolate D1
    # [ a b c d e ]
    # a1 = b1 - b2 = b1 - ( c2 - c3 ) = b1 - ( c2 - ~(d2 - c2) ) = b1 - ~( 2*c2 - d2 )
    SC[0][4:8] = SC[1][4:8] - ( 2*SC[2][8:12] - SC[3][8:12] )
    SC[-1][4:8] = SC[-2][4:8] + ( 2*SC[-3][8:12] - SC[-4][8:12] )

    
    #D3
    SC[2:-2, 12:16] = (SC[0:-4, 4:8] - 2*SC[2:-2, 4:8] + SC[4:, 4:8])/4


    #interpolate D3 (simple addition)
    SC[ 0][12:16] = SC[ 2][12:16] + (SC[ 2][12:16] - SC[ 4][12:16]) 
    SC[ 1][12:16] = SC[ 2][12:16] + (SC[ 2][12:16] - SC[ 5][12:16])
    SC[-2][12:16] = SC[-3][12:16] + (SC[-3][12:16] - SC[-4][12:16])
    SC[-1][12:16] = SC[-3][12:16] + (SC[-3][12:16] - SC[-5][12:16])


    #interpolate D2 (using D3)
    SC[ 1][8:12] = SC[ 2][8:12] - ( 2*SC[ 3][12:16] - SC[ 4][12:16] )
    SC[-2][8:12] = SC[-3][8:12] + ( 2*SC[-4][12:16] - SC[-5][12:16] )

    SC[ 0][8:12] = SC[ 1][8:12] - ( 2*SC[ 2][12:16] - SC[ 3][12:16] )
    SC[-1][8:12] = SC[-2][8:12] + ( 2*SC[-3][12:16] - SC[-4][12:16] )
    

        # compute dn complete
    #----------------------------

    ## [ [d0tick[0], d0tick[1], d0tick[2], d0tick[3]],
    ##   [d1tick[0], d1tick[1], d1tick[2], d1tick[3]],
    ##   [d2tick[0], d2tick[1], d2tick[2], d2tick[3]],
    ##   [d3tick[0], d3tick[1], d3tick[2], d3tick[3]],
    ##   [time[0],   time[1],   weekday,   yrday    ],
    ##   [marketick, date[0],   date[1],   date[2]  ] ]

    SC[:, 16:24] =\
          [ [ se.datetime.hour, se.datetime.minute,\
              se.datetime.isoweekday(), se.datetime.timetuple()[-2],\
              se.market_tick, se.datetime.year,\
              se.datetime.month, se.datetime.day] for se in SE ]

    return SC
#################'''

    
def SCC2filetxt(SC, s, linear = 1):
    txt = ""
    mftxt = "{:.2f} {:.2f} {:.2f} {:.2f} {} "+\
            "{:.5f} {:.5f} {:.5f} {:.5f} {:.3f} "+\
            "{:.5f} {:.5f} {:.5f} {:.5f} {:.4f} "+\
            "{:.5f} {:.5f} {:.5f} {:.5f} {:.4f} \t"
    
    dftxt = "{} {} {} {} \t"+\
            "{} {} {} {}\n"
    if linear:
        dftxt = dftxt[:-1] + ' '

    #txt = [ mftxt.format(*_sc[0:16])\
    #        + dftxt.format(*_sc[16:].astype('int32')) \
    #        for _sc in SC[s-1500+1:s+1] ]

    
    for i in range(s-1500-1, s-1):        
        txt += mftxt.format(*SC[i, 0:16+4])\
                + dftxt.format(*SC[i, 16+4:].astype('int32'))
            
        if (i+2)%75 == 0:
            txt += '\n'

    return txt[0:-1]

def filetxt2SCC(txt, s=-1):
    txt = txt.replace("\n\n", '\n').replace(' \t', ' ')
    txt = txt.splitlines()
    txt = list(filter(('').__ne__, txt))
    txt = [ t.split(' ') for t in txt ]

    toMAT = np.array(txt, dtype='float32')

    if toMAT.shape[1] != 24+4:
        print(">>> corrupt [filetxt] filetxt2MAT() [FAIL:shape{}]".format(toMAT.shape))
        return 1

    #@deprecated
    #SCC = toMAT.reshape((1500, 6, 4))
    SCC = toMAT.reshape(-1, 24+4) ##NEW UPDATE TO INCLUDE se.CLOSE
    
    return SCC
    







        
            

        
            
    
            

        

if __name__ == '__main__':
    import os
    import datetime as dt
    import time
    import tqdm
    from multiprocessing.pool import ThreadPool
    
    stdb= './Stock_Database/'
    
    if not os.path.isfile(stdb+'watchlist.txt'):
        print(">> watchlist file does not exit. please create txt file"+\
              "with line separated ticker symbols and try again.")
        input(">> Press ENTER to exit")
        exit(1)
        

    print(">> reading watchlist\n\n")    
    with open(stdb+'watchlist.txt', 'r') as wlf:
        wl = wlf.read()
    wl = [ [ x.upper()+'.NS' for x in y.split(' ')] for y in wl.split('\n')]

    null_err_wl = []



    


    print('>> watchlist size ::', len(wl))
    s_wl = max(0, int(input('>> set watchlist work range: start = ')))
    e_wl = min(len(wl), int(input('>> set watchlist work range: end   = ')))
    print('\n\n>> starting iter ...')

    #def_start = 75*5*4
    def_start = td.getMarketTick(dt.datetime(2021, 5, 26))

    
    for tk in wl[s_wl:e_wl]:
        print(">>> ticker item :: ", tk, '[', wl.index(tk)+1, '/', len(wl), ']') 
        if tk == None or tk == [] or tk == ['']:
            print("  > corrupt ticker item. Please"+\
                  " maintain no empty newline in watchlist\n\n")
            null_err_wl.append(wl.index(tk))
            continue

        #we fuck with 5m2m first
        dataf = stdb+tk[0]+'/'+tk[0]+'_5m2m.csv'
        

        SE = td.EXTRACT(dataf)

        ###
        ### CREATING ALL POSSIBLE (OLD) CARDS
        ###

        print(SE[0])

        start = def_start - SE[0].market_tick
        sym = SE[0].symbol

        if not os.path.isdir(stdb+tk[0]+'/'+'STOCKCARDS'):
            os.mkdir(stdb+tk[0]+'/'+'STOCKCARDS')

        ########TODO POINT 20210806
        #SE.reverse()
        SCC = makeSCC(SE[0: len(SE)])

        
        for i in tqdm.tqdm(range(start, len(SCC), 75), desc='Generating Cards...'):
            ##RAW##SC = StockCard(sym, SE[i].datetime)
            #SC.inputD0tick(SE[0:i+1])
            #SC.computeDntick()
            
            cardf = stdb+tk[0]+'/'+'STOCKCARDS'+'/'+tk[0]+\
                    '_STOCKCARD_{}.txt'.format(SE[i].datetime.isoformat()\
                                               .split('T')[0].replace('-', '_'))
            
            ftxt = SCC2filetxt(SCC, i, linear=0)#-75-1)
            with open(cardf, 'w') as f:
                f.write(ftxt)

            f.close()


        #update updfile
        currtime = time.localtime()
        updlogf = stdb+tk[0]+'/'+'STOCKCARDS/'+tk[0]+'_updatelog.txt'
        
        log_ts = ''
        for i in range(time.struct_time.n_sequence_fields):
            log_ts += str(currtime[i])+' '
        
        with open(updlogf, 'w') as updlog:
            updlog.write('\n'+log_ts[:-1])

        #finished
        print("\n  > ticker stockcard updated :: "+updlog.name+' :: '+ log_ts + '\n\n')


        

        '''##Implimenting parrallel
        nthreads = 8
        pool = ThreadPool(processes = nthreads)
        pending = []

        def work(SE, i):
            SC = StockCard(sym, SE[i].datetime)
            
            SC.inputD0tick(SE[0:i+1])
            SC.computeDntick()
            
            cardf = stdb+tk[0]+'/'+'STOCKCARDS'+'/'+tk[0]+\
                    '_STOCKCARD_{}.txt'.format(SE[i].datetime.isoformat()\
                                               .split('T')[0].replace('-', '_'))
            
            ftxt = SC.MAT2filetxt()
            with open(cardf, 'w') as f:
                f.write(ftxt)

            f.close()

            
        
        for i in tqdm.tqdm(range(start, len(SE)), desc='Generating Cards...'):
            while True:
                if len(pending) >= nthreads:
                    if pending[0].ready():
                        pending.pop(0)
                        break
                else:
                    break

            task = pool.apply_async(work, (SE, i))
            pending.append(task)

        '''

            
            
            
