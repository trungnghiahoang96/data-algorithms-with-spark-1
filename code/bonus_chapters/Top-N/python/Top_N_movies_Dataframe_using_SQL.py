from __future__ import print_function 
import sys 
import csv
import pandas as pd
from pyspark.sql import SparkSession 

#------------------------------------
#------------------------------------
# Authors:
#   Mahmoud Parsian (https://github.com/mahmoudparsian/)
#   Krishna Sai Tejaswini Kambhampati (https://github.com/Tejaswini-popuri/)
#------------------------------------
#------------------------------------
# create a dictionary{(movie_id, movie_name)}
def create_dict(movies):
  movies_dict = {}
  with open(movies, mode='r') as movies_file:
    reader = csv.reader(movies_file)
    movies_dict = {rows[0]:rows[1] for rows in reader}
  #
  return movies_dict
#end-def
#------------------------------------

# make sure we have 5 parameters
if len(sys.argv) != 5:  
  print("Usage: <prog> <N> <ratings> <movies> <rating_threshold>", file=sys.stderr)
  exit(-1)

# define Top-N
N = int(sys.argv[1])
print("N=", N)

# define ratings input path
# each rating record: userId,movieId,rating,timestamp
ratings = sys.argv[2]  
print("ratings=", ratings)

# define movies input path
# each movies record: movieId,title,genres
movies = sys.argv[3]  
print("movies=", movies)

# if a rating is less than rating_threshold,
# then that record will be dropped
# if you do not want to drop any records, then set rating_threshold = 0
rating_threshold = float(sys.argv[4])
print("rating_threshold=", rating_threshold)

# create an instance of SparkSession
spark = SparkSession.builder.getOrCreate()

# read ratings and create RDD[String]
df = spark.read.load(ratings,format = 'csv', header=True)
print("Dataframe Schema: ")
df.printSchema()
print("df.show(10): ")
df.show(10, truncate=False)
print("df.count(): ", df.count())       

#If a given record has missing values then that record is dropped from all calculations
filtered_df = df.filter(df.userId.isNotNull()|df.movieId.isNotNull() |df.rating.isNotNull())

#Convert dataframe to relational table
filtered_df.createOrReplaceTempView('movie_reviews_table')

#Find the top 10 movies watched more frequently using SQL
# top N
topN_movies_df = spark.sql('select movieId, count(userId) as no_of_times_movie_seen from movie_reviews_table group by movieId order by count(userId) DESC limit ' + str(N))
topN_movies_df.show(10, truncate=False)

# action 'take()' helps to limit the number of rows to get
# Returns the first N (5, 10, ...) rows as a list of Row (pyspark.sql.Row)
topN_movies = topN_movies_df.take(N)
 
#creating a data frame
movies_df = pd.read_csv(movies)
print(movies_df.head())

for col in movies_df.columns:
  print(col)

#create a dictionary{(movie_id, movie_name)}
movies_dict = create_dict(movies)

#add a movie name to top N (5, 10, ...) list:
topN_with_names = []
for row in topN_movies:
  if (row.movieId in movies_dict):
    topN_with_names.append((row.movieId, row.no_of_times_movie_seen, movies_dict[row.movieId]))
  else:
    topN_with_names.append((row.movieId, row.no_of_times_movie_seen, None))

print("topN_with_names=", topN_with_names)
    
# done!
spark.stop()