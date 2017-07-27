import redis

r = redis.Redis(host='127.0.0.1', port='6379')
print r

print "CLEANING REDIS"
print "=============="

print "Display all keys first"
for k in sorted(r.keys('meal*')):
    print " - "+ k

raw_input("Press ENTER to continue with key deletion ")

for k in r.keys('meal*'):
    print " - removing ... " + k
    r.delete(k)

r.set("total_calories", 0)

print "Now it should be empty"
for k in r.keys('meal*'):
    print " - "+ k
print ""

##############################
print "The current value of the -counter_meal- counter is " + str(r.get("counter_meal"))
raw_input("Press ENTER to reset it to zero ")
print r.set("counter_meal","0")

print "The current value of the -caloriecount- counter is " + str(r.get("caloriecount"))
raw_input("Press ENTER to reset it to zero ")
print r.set("caloriecount","0")


