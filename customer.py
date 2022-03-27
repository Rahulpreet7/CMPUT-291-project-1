import sys
import sqlite3
import datetime
from random import randint
from collections import Counter

connection = None
cursor = None

sid = 0

def start_session(database, cid):
    global sid
    connection = sqlite3.connect(database) # establish connection to database
    cursor = connection.cursor()

    insert_session_query = '''    INSERT INTO sessions values
                                (:sid, :cid, :sdate, :duration);
                                '''
    sdate = str(datetime.date.today())
    while True:     
        sid = randint(0, 9999)
        cursor.execute("SELECT * FROM sessions where sid=?;", (sid,))
        found = cursor.fetchone()
        if not found:   
            break
        
    duration = 'NULL'
    cursor.execute(insert_session_query, {"sid": sid, "cid": cid, "sdate": sdate, "duration": duration})
    connection.commit()
    
    return sid

def search_movies(database, cid):  #DONE
    global sid
    connection = sqlite3.connect(database) # establish connection to database
    cursor = connection.cursor()
    
    print("Search for movies")
    keys = input("Enter keyword(s): ")
    keywords = keys.split()
    tables = []
    for keyword in keywords:
        cursor.execute('''SELECT DISTINCT
                        m.title,
                        m.year,
                        m.runtime
                    FROM
                        movies m
                        INNER JOIN casts c
                        ON m.mid = c.mid
                        INNER JOIN moviePeople mp
                        ON c.pid = mp.pid
                    WHERE
                        m.title LIKE :keyword COLLATE NOCASE
                        OR c.role LIKE :keyword COLLATE NOCASE
                        OR mp.name LIKE :keyword COLLATE NOCASE''', {"keyword": '%' + keyword + '%'})
        rows = cursor.fetchall()  # getting a table of matching movies for each keyword
        tables += rows  # adding results of each keyword to tables
    counter = Counter(tables).most_common()  # sort in decreasing order of matching keywords
    
    total = len(counter)
    
    if total>5:
        printed = 1
        
        for j in range (5):
            print(j+1,'.', counter[j][0][0] +" " + str(counter[j][0][1]) +" "+ str(counter[j][0][2]))
            printed+=1
        more = input("Do you want to see more results? (y/n)")
        printed += 5
        
        if more.lower() == 'y':
            for i in range(5,len(counter)):
                print(i+1,'.', counter[i][0][0] +" " + str(counter[i][0][1]) +" "+ str(counter[i][0][2]))
        else:
            print("Displayed all.")
    else:
        for i in range(len(counter)):
            print(i+1,'.', counter[i][0][0] +" " + str(counter[i][0][1]) +" "+ str(counter[i][0][2]))
                
    movie_option = int(input("Which movie do you want to watch?"))
    print("\nYou selected to watch the following movie. \n")
    print(counter[movie_option-1][0][0] +" " + str(counter[movie_option-1][0][1]) +" "+ str(counter[movie_option-1][0][2]))
        
    new_option = int(input("(1) to select a cast member and follow it, OR (2) to start watching the movie."))
    
    if new_option == 1:
        # call follow func
        movie_name = counter[movie_option-1][0][0]
        cursor.execute('''SELECT mp.pid, mp.name, m.mid from moviePeople mp, casts c, movies m WHERE mp.pid = c.pid AND m.mid = c.mid AND m.title = ?''',(movie_name,))
        count = 1
        data = cursor.fetchall()
        print("\n")
        for actor in data:
            
            print(count, actor[1])
            count+=1
        actor_option = int(input("Which cast member do you want to follow?"))
        
        print(cid)
        print(data[actor_option-1][0])

        cursor.execute("""INSERT INTO follows(cid,pid) VALUES (?,?);""", (cid,data[actor_option-1][0],))
        
        connection.commit()
                    
        print("You have followed.".format(data[actor_option-1][0]))
        

        
    elif new_option == 2:
        movie_name = counter[movie_option-1][0][0]
        cursor.execute('''SELECT m.mid from movies m WHERE m.title = ?''',(movie_name,))
        
        data = cursor.fetchone()        
        print(data)
        movie_mid = data[0]
        
        
        start_movie(database,cid, sid, movie_mid)
        
def start_movie(database,cid, sid, mid):
    # watch(sid, cid, mid, duration)
    connection = sqlite3.connect(database) # establish connection to database
    cursor = connection.cursor()

    check_watch = '''
        SELECT * 
        FROM watch 
        WHERE cid=:cid
            AND sid=:sid 
            AND duration<0;
        '''
    if cursor.execute(check_watch, {'sid':sid, 'cid':cid}).fetchone():
        print("You are already watching a movie!. Please end that movie first")
        return

    current = datetime.datetime.now()
    duration = int(current.strftime("%Y%m%d%H%M%S"))
    duration = -duration

    start_watching = '''
        INSERT INTO watch VALUES (:sid, :cid, :mid, :dur);
    '''
    cursor.execute(start_watching, {'sid':sid, 'cid':cid, 'mid':mid, 'dur':duration})
    connection.commit()

    return

def end_movies(database, cid, sid):
    
    connection = sqlite3.connect(database) # establish connection to database
    cursor = connection.cursor()    

    movie_watching = '''
        SELECT w.mid, w.duration
        FROM watch w
        WHERE lower(w.sid) = :sid AND lower(w.cid) = :cid AND w.duration < 0;
    '''
    mid, dur = 0,0
    checkR = cursor.execute(movie_watching, {"sid":sid, "cid":cid}).fetchone()
    if not checkR:
        print('you are watching nothing.')
        return
    else:
        mid, dur = checkR


    dur = str(-dur)
    dt_start = datetime.strptime(dur, "%Y%m%d%H%M%S") 
    dt_current = datetime.now()
    watch_dur = (dt_current - dt_start).total_seconds()//60

    update_watch = """
        UPDATE watch
        SET duration = :dur
        WHERE lower(cid) = :cid AND lower(sid) = :sid AND mid = :mid AND duration<0;
    """
    cursor.execute(update_watch, {"dur": watch_dur, "cid": cid, "sid": sid, "mid":mid})
    connection.commit()

    return

def end_session(database, cid, sid):
    
    connection = sqlite3.connect(database) # establish connection to database
    cursor = connection.cursor()
    
    end_movies(database,cid, sid)

    # CLOSE SESSION AFTER CLOSING THE MOVIE
    find_session = '''
        SELECT s.sdate
        FROM sessions s
        WHERE lower(s.sid) = :sid AND lower(s.cid) = :cid
    '''
    s_date  = cursor.execute(find_session, {"sid":sid, "cid":cid}).fetchone()
    if not s_date:
        return
    s_date = s_date[0]
    dt_start = datetime.strptime(s_date, "%d/%m/%y %H:%M:%S")
    dt_current = datetime.now()
    duration = (dt_current - dt_start).total_seconds()//60

    update_session = """
        UPDATE sessions
        SET duration = :dur
        WHERE lower(cid) = :cid AND lower(sid) = :sid;
    """
    cursor.execute(update_session, {"dur": duration, "cid": cid, "sid": sid})
    connection.commit()
    
