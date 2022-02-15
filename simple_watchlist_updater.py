proj_name = 'simple watchlist updater'
proj_version = '2021-05-27-15:23'


print("\n\t\t{}\n\t\t{}".format(proj_name, proj_version))
print("\n\nloading modules ..", end='', flush=True)
import os
print(" ..", end='', flush=True)
import numpy as np
print(" ..", end='', flush=True)
import time
print(" ..", end='', flush=True)
import datetime as dt
print(" ..", end='', flush=True)
import yfinance as yf
print(" ..", end='', flush=True)
from multiprocessing.pool import ThreadPool
print(" ..", end='', flush=True)
from collections import deque
print(" ..\nWELCOME\n", flush=True)

data_avblty = { '1m7d':7, '5m2m':59, '15m6m':59, '1h12m':729, '1d2y':9000}

database_files = [['1m7d', '1m', 7], ['5m2m', '5m', 60],\
                  ['15m6m', '15m', 180], ['1h12m', '1h', 360],\
                  ['1d2y', '1d', 720]]

def getDownloadDates(curr, prev = None):
    currdate = dt.date(curr[0], curr[1], curr[2])
    if currdate.weekday() == 6:
        currdate = currdate - dt.timedelta(1)
    
    if prev:
        prevdate = dt.date(int(prev[0]), int(prev[1]), int(prev[2]))
        ddays = currdate - prevdate
        ddays = ddays.days
        if ddays < 1:
            return None
    
    dates = dict()
    for dbf in database_files:
        if not prev:
            ddays = dbf[2]
        
        startdate = currdate - dt.timedelta(min(ddays, data_avblty[dbf[0]]))
        dates[dbf[0]] = [startdate.isoformat(), currdate.isoformat()]
        #dates[dbf[0]] = ['2021-08-02', '2021-08-07']
        #dates[dbf[0]][1] = '2021-08-07'

    return dates

## PARALLEL TASKS::
def taskhis(sym, dbfile, dates):
    #with yf.Ticker(sym) as ticker:
    if True:
        ticker = yf.Ticker(sym)
        his = ticker.history(interval = dbfile[1],\
                            start  = dates[dbfile[0]][0],\
                            end    = dates[dbfile[0]][1],\
                            )

    return his, dbfile

def taskinfo(sym, dbfile):
    class INFO:
        def __init__(self, data):
            self.data = data
            if len(data) > 10:
                self.empty = False
            else:
                self.empty = True

            ct = time.localtime()
            self.cttxt = 'info_{}-{}-{}_{}'.format(ct.tm_year,\
                                      ct.tm_mon, ct.tm_mday,\
                                      ct.tm_hour*3600
                                    +ct.tm_min*60
                                    +ct.tm_sec)
                
        def to_file(self, fn, mode='a+'):
            infotxt = self.cttxt + ',' + str(self.data)[1:-1]
            with open(fn, 'a+') as f:
                f.write(infotxt)

    info_d =  yf.Ticker(sym).info
    info = INFO(info_d)

    return info, dbfile
## ##

def download(sym, dates):
    print("\n\t>>> starting download :: ", sym)
    data=[]

    ##TODO : IMPLIMENT PLXZ
    wd_name = {0:'MON', 1:'TUE', 2:'WED', 3:'THR',\
               4:'FRI', 5:'SAT', 6:'SUN'}
    
    nthreads = 8
    pool = ThreadPool(processes = nthreads)
    pending = []

    #Applying Parallel
    for dbfile in database_files:
        #print("\t>>> >> applying   ", dbfile[0], dates[dbfile[0]])
        task = pool.apply_async(taskhis, (sym, dbfile, dates) )
        pending.append(task)
    

    #fetching parallel
    while len(pending) > 0:
        for i in range(len(pending)):
            if pending[i].ready():
                his, dbfile = pending.pop(i).get()

                print("\t>>> >> downloaded   ", dbfile[0],'\t', dates[dbfile[0]], end='')
                if not his.empty:
                    data.append([sym, dbfile[0],\
                                 dates[dbfile[0]][0], dates[dbfile[0]][1],\
                                 his, not his.empty])
                    print(' [pass]')
                else:
                    print(' [FAIL]')

                break

    return data



def approxT(s_clock_t, n_rem, avg_t=[0,0]):
    n_clock_t = time.time()
    clock_t = n_clock_t - s_clock_t

    if avg_t[1] == 0:
        avg_t = [clock_t, 0]
    else:
        avg_t[0] = avg_t[0]*0.6 + (n_clock_t - avg_t[1])*0.4
    avg_t[1] = n_clock_t
    
    clock_d = [n_clock_t, int(clock_t/60), int(clock_t)%60,\
               int(avg_t[0]*(n_rem)/60), int(avg_t[0]*(n_rem))%60, avg_t]

    return clock_d

if __name__ == '__main__':
    if not os.path.isfile('./watchlist.txt'):
        print(">> watchlist file does not exit. please create txt file"+\
              "with line separated ticker symbols and try again.")
        input(">> Press ENTER to exit")
        exit(1)
        

    print(">> reading watchlist\n\n")
    with open('./watchlist.txt', 'r') as wlf:
        wl = wlf.read()
    wl = [ [ x.upper()+'.NS' for x in y.split(' ')] for y in wl.split('\n')]

    null_err_wl = []
    date_err_wl = []
    download_err_wl = []

    s_clock_t = time.time()
    cdt = [0,0,0,0,0,[0,0]]
    
    for tk in wl:
        ##
        cdt = approxT(s_clock_t, len(wl) - wl.index(tk), cdt[5])
        #tk = wl[i]
        print(">>> updating ticker item :: ", tk, '[', wl.index(tk)+1, '/', len(wl), '] [ +'+str(cdt[1])+':'+str(cdt[2])+' / -'+str(cdt[3])+':'+str(cdt[4])+' ]') 
        if tk == None or tk == [] or tk == ['']:
            print("  > corrupt ticker item. Please"+\
                  " maintain no empty newline in watchlist\n\n")
            null_err_wl.append(wl.index(tk))
            continue
            

        
        #find dir and updlist
        print("\t>>> checking log")
        updlogf = './'+tk[0]+'/'+tk[0]+'_updatelog.txt'

        if not os.path.isdir('./'+tk[0]):
            os.mkdir('./'+tk[0])
            os.mkdir('./'+tk[0]+'/dump')
            llog = ['']
        else:
            updlog = open(updlogf, 'r')
            llog = updlog.read().split('\n')
            updlog.close()
        


        #get time period of download
        currtime = time.localtime()
        
        if llog[-1]:
            print("\t>>> last update ::", llog[-1])
            download_dates = getDownloadDates(currtime, llog[-1].split(' '))
        else:
            print("\t>>> no logs found :: fresh data download")
            download_dates = getDownloadDates(currtime)

        if download_dates == None:
            print("\t>>> update date period too small or negative.")
            print("  > ticker NOT updated or Already updated.\n\n")
            date_err_wl.append([wl.index(tk), tk, llog[-1]])
            continue

        '''
        markpass = 1 
        with open('./'+tk[0]+'/STOCKCARDS/'+tk[0]+'_STOCKCARD_2021_07_16.txt', 'r') as f:
            if '0 0 0 0' in f.read():
                markpass = 0

        if markpass:
            print('>> [MAERK PASS]')
            continue
        '''        

        data = download(tk[0], download_dates)

        if not data or not len(data) >= 5:
            print("\t>>> No data downloaded/stored.")
            print("  > ticker NOT updated or ticker symbol does not exist."+\
                  "please check yahoo finance symbol list.\n\n")
            download_err_wl.append([wl.index(tk), tk, llog[-1]])
            continue
        
        print("\n\t>>> download complete. Dumping data")
        #create dumpfile
        for d in data:
            ct = time.localtime()
            fn = './'+d[0]+'/'+'dump'+'/'+\
                 'dump_{}_{}_{}-{}-{}_{}.csv'.format(d[0],d[1], ct.tm_year,\
                                                    ct.tm_mon, ct.tm_mday,\
                                                    ct.tm_hour*3600
                                                    +ct.tm_min*60
                                                    +ct.tm_sec)

            d[4].to_csv(fn, mode='w')
            #print("\t>>> >> dumpfile created : ", fn)


        print("\n\t>>> UPDATING DATABASE FILES")
        #append to dbfiles
        for d in data:
            ct = time.localtime()
            fn = './'+d[0]+'/'+d[0]+'_'+d[1]+'.csv'


            d[4].to_csv(fn, mode='a+')
            #print("\t>>> >> database file updated :\t", fn)


        #update updfile
        log_ts = ''
        for i in range(time.struct_time.n_sequence_fields):
            log_ts += str(currtime[i])+' '
        
        with open(updlogf, 'a+') as updlog:
            updlog.write('\n'+log_ts[:-1])

        #finished
        print("\n  > ticker updated :: "+updlog.name+' :: '+ log_ts + '\n\n')

    
        


    print("<< WATCHLIST UPDATE COMPLETE >>\n\n Errors::")

    if len(null_err_wl):
        print(">> Following [nul_err_wl] errors found in watchlist file, at line no.(s):")
        for i in range(len(null_err_wl)):
            print(null_err_wl[i], '\t', end='')
            if not i%5:
                print('')
        print('\n')

    if len(date_err_wl):
        print(">> [date_err_wl] errors occured for following symbols:")
        for i in date_err_wl:
            print('  >>> ', i[0], i[1][0])
        
        print('\n')

    if len(download_err_wl):
        print(">> [download_err_wl] errors occured for following symbols:")
        for i in download_err_wl:
            print('  >>> ', i[0], i[1][0], '/t', i[2])
        
        print('\n')
    
        
    input(">> Press ENTER to exit")
    

###########################################################################
    
#deprecated
def _download(sym, dates):
    print("\n\t>>> starting download :: ", sym)

    ticker = yf.Ticker(sym)
    data = []
    for dbfile in database_files:
        print("\t>>> >> downloading   ", dbfile[0], dates[dbfile[0]])
        his = ticker.history(interval = dbfile[1],\
                             start  = dates[dbfile[0]][0],\
                             end    = dates[dbfile[0]][1])
        if not his.empty:
            data.append([sym, dbfile[0],\
                         dates[dbfile[0]][0], dates[dbfile[0]][1],\
                         his, not his.empty])

    return data

    

    
        
        

    
