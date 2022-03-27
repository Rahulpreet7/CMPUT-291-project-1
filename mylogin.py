import sys
import sqlite3
import datetime
import customer
import editor
import getpass as gp

from random import randint

connection = None
cursor = None
id = None
'''this is the main class of the program where all the functiomns from different files ar imported and called plus we made login screen here'''
class Interface:

    def __init__(self):
        self.exit_app = False   # set to TRUE when user attempts to quit application
        self.logged_in = False  # set to TRUE when user has successfully logged in
        self.get_database()
        self.sid = 0
        self.run()
    
    def get_database(self):
        self.database = input("Name of database: ")
        
    def run(self):
        while not self.exit_app:
            self.login()
            while self.logged_in:
                if self.user_type == 'c':
                    self.customer()  #jump to customer
                elif self.user_type == 'e':
                    self.editor()
            print("You have been logged out.")
        print("You have exited the application.")
        
    def login(self):
        global id
        global connection, cursor
        while not self.exit_app and not self.logged_in:
            id = input("\nPlease insert a valid user id: \n")
            
            connection = sqlite3.connect(self.database) # establish connection to database
            cursor = connection.cursor()
            
            login_query = '''   SELECT COUNT(*)
                                FROM editors
                                WHERE eid=:eid;
                                '''
            cursor.execute(login_query, {"eid":id})
            row = cursor.fetchone()            
            if row[0] > 0:
                self.get_password(id, 'e')
                self.user_type = 'e'
                self.eid = id
                self.logged_in = True
                return 0, id
            else:
                login_query = '''   SELECT COUNT(*)
                                    FROM customers
                                    WHERE cid=:cid;
                                    '''
                cursor.execute(login_query, {"cid":id})
                row = cursor.fetchone()                
                if row[0] > 0:
                    self.get_password(id, 'c')
                    self.user_type = 'c'
                    self.cid = id
                    self.logged_in = True
                    return 1, id
                else:  # not registered
                    print("You are not a registered customer. Please signup.")
                    id = input("Select a 4 character id: ")
                    #print(id)
                    success = False
                    while not success:
                        # not checking in editors as ids are disjoint
                        login_query = '''   SELECT COUNT(*)
                                            FROM customers
                                            WHERE cid=:cid;
                                            '''
                        cursor.execute(login_query, {"cid":id})
                        row = cursor.fetchone()                        
                        if len(id) != 4:
                            id = input("Please enter a 4 character id: ")
                        elif row[0] > 0:
                            id = input("id already in use. Try another one: ")
                        else:
                            success = True
                    name = input("Enter name: ")
                    pw = getpass.getpass("Enter a password of your choice: ")    #hiding the password
                    insert_customer_query = '''    INSERT INTO customers values
                                                   (:id, :name, :pw)
                                                   '''
                    cursor.execute(insert_customer_query, {"id":id, "name": name, "pw":pw})
                    connection.commit()
                    print("You are successfully signed up and logged in!")
                    self.user_type = 'c'
                    self.cid = id
                    self.logged_in = True
                    return 1, id

    def get_password(self, id, user_type):
        success = False
            
        # getting user name if customer
        if user_type == 'c':
            cursor.execute("SELECT name FROM customers WHERE cid=:cid", {"cid": id})
            row = cursor.fetchone()
            name = row[0]
        else:
            name = 'Editor ' + id
            
        pw = gp.getpass(prompt="Welcome " + name + ". Enter your password: ")
        while not success:
            if user_type == 'e':
                cursor.execute("SELECT COUNT(*) FROM editors WHERE eid=:eid AND pwd=:pw", {"eid": id, "pw": pw})
            else:
                cursor.execute("SELECT COUNT(*) FROM customers WHERE cid=:cid AND pwd=:pw", {"cid": id, "pw": pw})
            row = cursor.fetchone()
            if row[0] > 0:
                print("You are successfully logged in!")
                success = True
            else:
                pw = gp.getpass(prompt="Incorrect password. Try again: ")
                
    def customer(self):   #importing all the customer functions
        global id,sid
        print('1 - Start a session',
              '2 - Search movies',
              '3 - End watching a movie',
              '4 - End a session',
              'X - Logout',
              'XX - Exit Application', sep='\n')
        selection = input("\nSelect an option from 1-4, X, XX: ")
        sid = 0
        if selection == '1':
            self.sid = customer.start_session(self.database, self.cid)
        elif selection == '2':
            if self.sid == 0:
                self.sid = customer.start_session(self.database, self.cid)
            customer.search_movies(self.database,self.cid)
        elif selection == '3':
            if self.sid == 0:
                print("No movie being watched")
                return
            else:
                print("You have selected to end the movie.")
                #cursor.execute('''SELECT COUNT(*) from watch WHERE cid  ?''',(id,))
                #print("You are currently watching {} movies.".format(cursor.fetchone()[0])
                customer.end_movies(self.database, self.cid,self.sid)
        elif selection == '4':
            if self.sid == 0:
                print("No session started!")
                return
            customer.end_session(self.database, self.cid,self.sid)
        elif selection == 'X':
            self.logged_in = False
        elif selection == "XX":
            self.logged_in = False
            self.exit_app = True
        else:
            print("\nInvalid Input\nPlease try again\n")
    
    def editor(self):   #importing customer functions
        global id
        print('1 - Add a movie',
              '2 - Update a recommmendation',
              'X - Logout',
              'XX - Exit Application', sep='\n')
        selection = input("\nSelect an option from 1-2, X, XX: ")
        if selection == '1':
            editor.add_movie(self.database)
        elif selection == '2':
            editor.update_recommendation(self.database)
        elif selection == 'X':
            self.logged_in = False
        elif selection == "XX":
            self.logged_in = False
            self.exit_app = True
        else:
            print("\nInvalid Input\nPlease try again\n")
        
def main():
    Interface()

if __name__ == "__main__":
    main()