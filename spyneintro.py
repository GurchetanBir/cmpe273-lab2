import json
from spyne import ServiceBase, rpc, Iterable, Application, Unicode, Float
from spyne.protocol.http import HttpRpc
from spyne.protocol.json import JsonDocument
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
import urllib2
import re
from collections import Counter
from address import AddressParser
import time


class FindCrime(ServiceBase):
    @rpc(Unicode, Float, Float, Float, _returns=Iterable(Unicode))
    def checkcrime(ctx, lat, lon, radius, key):

        baseurl = "http://api.spotcrime.com/crimes.jason?"
        response = urllib2.urlopen("%slat=%s&lon=%s&radius=%s&key=." % (baseurl, lat, lon, radius))
        jsondata = json.load(response)
        #yield response

        totalcrimes = 0
        crime_type_count = {}
        addresslist = []
        timelist = []
        mostdangerous = []
# get all the components of the dictionary----------------------------

        for i in jsondata["crimes"]:
            if not i["type"] in crime_type_count:
                crime_type_count[str(i["type"])] = 1
            else:
                crime_type_count[str(i["type"])] += 1
            totalcrimes += 1
        for i in range(totalcrimes):
            newdict = jsondata['crimes'][i]
            addressdict = newdict['address']

            timedict = newdict['date']

            timelist.append(timedict)

            addresslist.append(addressdict)
        #print addresslist



# split the timelist#  ------------------------------------------------------------
        timelisttimes=[]
        timelist2 = [] #it is a list of strings of times
        for i in timelist:
            x = i.split(" ")
            y = x[1] + x[2]
            timelist2.append(y)
        #print timelist2


#get time in ranges

        am12to3=0
        am3to6=0
        am6to9=0
        am9to12=0
        pm12to3=0
        pm3to6=0
        pm6to9=0
        pm9to12=0

        for i in timelist2:
            date_object = time.strptime(i,'%I:%M%p').tm_hour
            date_object2 = time.strptime(i, '%I:%M%p').tm_min
            minutes=(date_object*60)+date_object2
            #print minutes


            if(minutes>=1 and minutes<=180):
                am12to3 +=1
            elif(minutes>=181 and minutes<=360):
                am3to6 +=1
            elif (minutes >=361 and minutes <=540):
                am6to9 += 1
            elif (minutes >=541 and minutes <=720):
                am9to12 += 1
            elif (minutes >=721 and minutes <=900):
                pm12to3 += 1
            elif (minutes >=901 and minutes <=1080):
                pm3to6 += 1
            elif (minutes >=1081and minutes <=1260):
                pm6to9 += 1
            elif (minutes >=1261 and minutes <=1440or minutes == 0):
                pm9to12 += 1

        event_time_count = {"12:01am-3am": am12to3,
                            "3:01am-6am":am3to6,
                            "6:01am-9am":am6to9,
                            "9:01am-12noon":am9to12,
                            "12:01pm-3pm":pm12to3,
                            "3:01pm-6pm":pm3to6,
                            "6:01pm-9pm":pm6to9,
                            "9:01pm-12midnight":pm9to12}





#list [] will save all the intersections oof streets where crime has happened------------------
        list = []
        for i in addresslist:
            intersections = re.findall("[\w.\s]{1,20}&[\w.\s]{1,20}", i)
            list.append(intersections)
        #print list





#all addresses have alla the addresses in individual--------------------
        alladdresses = []
        for i in list:
            before = re.compile(r"&(.*)")
            matches = re.findall(before, ''.join(i))
            alladdresses.append(matches)
            after = re.compile(r"(.*)&")
            matches2 = re.findall(after, ''.join(i))
            alladdresses.append(matches2)

        list2 = [x for x in alladdresses if x != []]  # remove []
        #print list2, len(list2)



# list 2 has all the individual addresses so chanage elements into string--------------
        list3 = []
        for i in list2:
            addinstr = ''.join(i)
            list3.append(addinstr)
        #print list3,len(list3)
#lis 3  has the streets of intersection in string in list---------------


#merge both the lists and
        mergelists = list3 + addresslist
        #print mergelists,len(mergelists)
        for i in mergelists:
            if re.findall("[\w.\s*]{1,20}&[\w.\s*]{1,20}", i):
                mergelists.remove(i)
        for i in mergelists:
                if re.findall("[\w.\s*]{1,20}&[\w.\s*]{1,20}", i):
                    mergelists.remove(i)
        #print mergelists,len(mergelists)

# covert address format into street format-------------------------------------------------
        allstreets = []  # it will give all addresses in street format streets
        ap = AddressParser()

        for i in mergelists:
            address = ap.parse_address(i)
            x = "{} {} {}".format(address.street_prefix, address.street, address.street_suffix)
            allstreets.append(x)
        #print x



# convert into dict with corresponding value as total occurence for address-----------------------
        countsaddress = dict()
        for i in allstreets:
            countsaddress[i] = countsaddress.get(i, 0) + 1
        #print countsaddress


# convert into dict with corresponding value as total occurence for time-----------------------
        countstime = dict()
        for i in timelist2:
            countstime[i] = countstime.get(i, 0) + 1
        #print  countstime

#find the most dangrous steeet by sortinng and getting  top 3-----------------------------------

        top3 = Counter(countsaddress)
        top3.most_common()
        #print top3.most_common()



#now gwt the top 3------------------------------------------------------------------------------
        for key, value in top3.most_common(3):
            mostdangerous.append(key)



#finall print=======================================================
        final_dict={"total_crime":totalcrimes,"the_most_dangerous_streets":mostdangerous,"crime_type_count":crime_type_count,"event_time_count":event_time_count}
        yield final_dict


application = Application([FindCrime],
                          tns='snype.example.hello',
                          in_protocol=HttpRpc(validator='soft'),
                          out_protocol=JsonDocument())

if __name__ == "__main__":
    app = WsgiApplication(application)
    server = make_server('0.0.0.0', 8000, app)
    server.serve_forever()
