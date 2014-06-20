import pymysql
import sys
#import app
	
# Returns MySQL database connection
def conDB(passwd='wikiscore123',host='localhost', port=3306, user='root', dbname='wikimeta'):
    try:
        con = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=dbname)
        print("Opened database " + dbname)
    
    except pymysql.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)

    return con


def curDB(conn):
 	return conn.cursor()
	
def closeDB(conn):
	curDB(conn).close()
	conn.commit()
	conn.close()
	print "Closed database " + conn.db