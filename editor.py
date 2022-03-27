import sys
import sqlite3
import datetime
from random import randint

connection = None
cursor = None

def getValidInteger(low, high, message=""):
    if message == "":
        choice = input("Enter a number between " + str(low) + " and " + str(high) + ": ")
    else:
        choice = input(message)
    valid = False
    while not valid:
        try:
            choice = int(choice)
            if choice < low or choice > high:
                raise ValueError
        except ValueError:
            choice = input("Invalid Input. Try again: ")
        else:
            valid = True
    return choice

def add_movie(database):
    connection = sqlite3.connect(database)  # establish connection to database
    cursor = connection.cursor()

    unique_mid = False
    mid = input("Enter a movie ID: ")
    while not unique_mid:
        cursor.execute("select count(*) from movies where mid=:mid", {"mid": mid})
        row = cursor.fetchone()
        if row[0] > 0:
            mid = input("Movie ID already exists!  Try a unique id: ")
        else:
            unique_mid = True
    movie_name = input("Enter title of the movie: ")
    year = input("Enter year of release: ")
    runtime = input("Enter runtime (mins): ")
    cursor.execute("insert into movies values (:mid,:title,:year,:runtime)",
                   {"mid": mid, "title": movie_name, "year": year, "runtime": runtime})
    connection.commit()

    while True:
        # print("-" * 15)
        print("Just click enter to stop adding cast members.")
        pid = input("Enter cast member ID: ")
        if pid == "":
            break
        cursor.execute("select name, birthYear from moviePeople where pid=:pid", {"pid": pid})
        row = cursor.fetchone()
        if row is not None:
            print("Data found in records for entered ID: " + row[0] + " born in " + str(row[1]))
            choice_add = getValidInteger(0, 1,
                                         "Do you want to add this person to the cast? Enter 1 for yes and 0 for no: ")
            if choice_add == 1:
                role = input("Enter cast member role: ")
                cursor.execute("insert into casts values (:mid,:pid,:role)", {"mid": mid, "pid": pid, "role": role})
                connection.commit()
                print("Successfully added " + row[0] + " to the cast")
            else:
                print("Skipped adding " + row[0] + " to the cast")
        else:
            choice_add = getValidInteger(0, 1,
                                         "No movie person with the entered ID exists. Enter 1 to add one or 0 to pass: ")
            if choice_add == 1:
                name = input("Enter name of the movie person: ")
                birth_year = input("Enter birth year of the movie person: ")
                role = input("Enter cast member role: ")
                cursor.execute("insert into moviePeople values (:pid, :name, :birth_year)",
                               {"pid": pid, "name": name, "birth_year": birth_year})
                cursor.execute("insert into casts values (:mid,:pid,:role)", {"mid": mid, "pid": pid, "role": role})
                connection.commit()
                print("New movie person successfully added to the cast")
            else:
                print("Skipped adding new movie person.")
    print("New movie successfully added!")
    print("-" * 15)


def update_recommendation(database):
    connection = sqlite3.connect(database)  # establish connection to database
    cursor = connection.cursor()

    updateQuery = '''
    select mv1, mv2, case when rt.score is null then 0 else rt.score end as score , case when rT.score is null then 'no' else 'yes' end as present
    from ((select distinct m1.mid as mv1, m2.mid as mv2, count(distinct w1.cid)
           from movies m1,
                movies m2,
                sessions s1
                    left join watch w1 on s1.sid = w1.sid and s1.cid = w1.cid,
                sessions s2
                    left join watch w2 on s2.sid = w2.sid and s2.cid = w2.cid
           where JULIANDAY('now') - JULIANDAY(s1.sdate) <= :day
             and JULIANDAY('now') - JULIANDAY(s2.sdate) <= :day
             and m1.mid = w1.mid
             and w1.duration * 2 >= m1.runtime
             and m2.mid = w2.mid
             and w2.duration * 2 >= m2.runtime
             and w1.cid = w2.cid
             and m1.mid != m2.mid
           group by m1.mid, m2.mid
           order by count(distinct w1.cid) desc) mT
             left outer join (
        select r.watched as r1, r.recommended r2, r.score as score
        from recommendations r
    ) rT on mv1 = r1 and mv2 = r2)
    '''
    validInput = False
    while not validInput:
        validInput = True
        userOption = input("Type a for annual\nType m for monthly\nType e for all time\n")
        if userOption not  in 'ame':
            validInput = False
        if userOption.lower() == 'a':
            cursor.execute(updateQuery,{'day':365})
        elif userOption.lower() == 'm':
            cursor.execute(updateQuery, {'day': 30})
        elif userOption.lower() == 'e':
            cursor.execute(updateQuery, {'day': 999999})
        else:
            validInput = False
            print('Please enter a valid input')
    result = cursor.fetchall()
    if(len(result)>0):
        print(result)
    else:
        print('No results found')    