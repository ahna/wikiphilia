import pymysql
import sys
#import app
	


# DATABASE SETTINGS
configFileName="/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/app/settings/development.cfg"
file = open(configFileName, 'r')
content = file.read()
file.close()
paths = content.split("\n") #split it into lines
for path in paths:
    p = path.split(" = ")
    if p[0] == 'DEBUG':
        debug = p[1]
    elif p[0] == 'DATABASE_HOST':
        host = p[1].replace('"','')
    elif p[0] == 'DATABASE_PORT':
        port = int(p[1])
    elif p[0] == 'DATABASE_USER':
        user = p[1].replace('"','')
    elif p[0] == 'DATABASE_PASSWORD':
        passwd = p[1].replace('"','')
    elif p[0] == 'DATABASE_DB':
        dbname = p[1].replace('"','')
       
    
#conn = conDB(passwd='wikiscore123',host='insight.cw33openpoo6.us-west-2.rds.amazonaws.com', port=3306, user='agirshick', dbname='insight')
    
# Returns MySQL database connection
# with parameter set in .cfg file
def conDB(passwd=passwd,host=host, port=port, user=user, dbname=db):
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