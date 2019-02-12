from pyspark import SparkConf
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from pyspark.sql.functions import to_timestamp
import sys
import time
import math
from operator import add
import logging
sys.path.append('/app/htm')
import settings
import htmCircle


conf = SparkConf()
conf.setMaster('spark://spark-master:7077')
conf.setAppName('spark-basic')
sc = SparkContext(conf=conf)
sc.addPyFile("/app/htm/htmCircle.py") 
sc.addPyFile("/app/htm/_htmCircle.so") 

point = [336.14, 0.13]

properties = {
    'user'    : settings.DB_USER,
    'password': settings.DB_PASS,
    'host'    : 'jdbc:mysql://' + settings.DB_HOST +':3306',
    'database': settings.DB_NAME,
    'driver': 'com.mysql.jdbc.Driver',
    'url' : 'jdbc:mysql://' + settings.DB_HOST +':3306/' + settings.DB_NAME
}

working_directory = '/app/'


def distance(ra1, de1, ra2, de2):
    dra = (ra1 - ra2)*math.cos(de1*math.pi/180)
    dde = (de1 - de2)
    return math.sqrt(dra*dra + dde*dde)


spark = SparkSession \
    .builder \
    .appName('pyspark_demo_app') \
    .config('spark.driver.extraClassPath',
            working_directory + 'mysql-connector-java-8.0.13.jar') \
	    .master("local[*]") \
    .getOrCreate() 


def get_crossmatch_where_clause(cone ,wl_radius):	

    cone_id  = cone.cone_id
    name     = cone.name
    myRA     = cone["ra"]
    myDecl   = cone.decl
    print(myRA)
    print(myDecl)
    subClause = htmCircle.htmCircleRegion(16, myRA, myDecl, wl_radius)
    subClause = subClause.replace('htm16ID', 'htm16').replace('where', '')
    return subClause
    #return  df.select('*').filter(subClause).rdd.map(lambda p : filter_hits(p, wl_radius, myRA, myDecl, wl_id, cone_id, name)).collect()  
    #query3 = 'SELECT * FROM objects WHERE htm16 ' + subClause[14: -2]
    #query_results3 = spark.sql(query3)
    #return query_results3.rdd.map(lambda p: filter_hits(p, wl_radius, myRA, myDecl, wl_id, cone_id, name)).collect()


def filter_hits(row, wl_radius, myRA, myDecl, wl_id, cone_id, name):

    objectId = row['objectId']
    ndethist = row['ncand']
    arcsec = 3600*distance(myRA, myDecl, row['ramean'], row['decmean'])

    if arcsec <= wl_radius:
        return {
                'wl_id':wl_id,
                'cone_id':cone_id,
                'name':name,
                'objectId':objectId,
                'ndethist':ndethist,
                'arcsec':arcsec
        }
    else :
        return None


def run_watchlist(wl_id, delete_old=True):

    newhitlist = []

    df1 = spark.read \
        .format('jdbc') \
        .option('driver', properties['driver']) \
        .option('url', properties['url']) \
        .option('user', properties['user']) \
        .option('password', properties['password']) \
        .option('dbtable', 'watchlists') \
        .load()

    df1.createOrReplaceTempView("watchlists")

    # get information about the watchlist we are running
    # query = 'SELECT name,radius FROM watchlists WHERE wl_id=%d' % wl_id
    # query_results = spark.sql(query)
    # watchlists = query_results.rdd.map(lambda p: {'name' : p.name, 'radius' : p.radius}).collect()
    watchlists = df1.select(["name", "radius"]).filter(df1.wl_id == wl_id).collect()

    for watchlist in watchlists:
        wl_name   = watchlist['name']
        wl_radius = watchlist['radius']

    print ("Running Watchlist '%s' at radius %.1f" % (wl_name, wl_radius))

    # make a list of all the hits to return it
    newhitlist = []
	
    df2 = spark.read \
        .format('jdbc') \
        .option('driver', properties['driver']) \
        .option('url', properties['url']) \
        .option('user', properties['user']) \
        .option('password', properties['password']) \
        .option('dbtable', 'watchlist_cones') \
        .load()

    df2.createOrReplaceTempView("watchlist_cones")
    
    # get all the cones and run them
    #query2 = 'SELECT cone_id,name,ra,decl FROM watchlist_cones WHERE wl_id=%d' % wl_id	
    #query_results2 = spark.sql(query2)
    #cones = query_results2.rdd.map(lambda p: {'cone_id' : p.cone_id, 'name' : p.name, 'ra' : p.ra, 'decl' : p.decl })
  
    cones = df2.select(["cone_id","name", "ra", "decl"]).filter(df2.wl_id == wl_id).collect()

    df4 = spark.read \
        .format('jdbc') \
        .option('driver', properties['driver']) \
        .option('url', properties['url']) \
        .option('user', properties['user']) \
        .option('password', properties['password']) \
        .option('dbtable', 'objects') \
        .load() 

    df4.createOrReplaceTempView("objects")

    #newhitlist = df4.select(["*"]).filter(get_crossmatch_where_clause(df2, wl_radius))
    print(df4.count())
    newhitlist = [df4.count()]
    # newhitlist = cones.reduceByKey(lambda x : cone_crossmatch(x, wl_radius)).collect() 

    
    #newhitlist = query_results2.rdd.map(lambda p : cone_crossmatch(p, wl_radius)).collect()
    for cone in cones:
        newhitlist.append(df4.select(["*"]).filter(get_crossmatch_where_clause(cone, wl_radius)).collect())


    newhitlist = [i for i in newhitlist if i != []]
    return newhitlist


wl_id = 35
start = time. time()
hitlist = run_watchlist(wl_id)
print('Found %d matches' % len(hitlist))
print (hitlist)
end = time. time()
print("Time taken: " + str(end - start) + " seconds")


