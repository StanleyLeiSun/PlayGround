import json
from pprint import pprint

#json_file='a.json' 
json_file=r'd:\tempwork\temp\part-00000'

json_data=open(json_file)
out_file = open(r"d:\tempwork\temp\russell_out.txt", mode='w')

lines = json_data.readlines()

for l in lines:
    data = json.loads(l)
    cluster_id = data[:1][0]
    for i in data[1:][0][:30]:
        item_url = i[0]
        item_score = float(i[1])
        if item_score > 0.5:
            out_file.write("{0}\t{1}\t{2}\n".format(cluster_id, item_url, item_score))

json_data.close()
out_file.close()