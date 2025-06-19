from radolan_hdf5 import RadolanHdf5Products
from poi2RadolanHdf5RvMap import poi2RadolanHdf5RvMap
from radolan import RadolanProducts
from poi2RadolanRvMap import poi2RadolanRvMap
plz='15378'
data = RadolanProducts.getRvData('file:./testdata/DE1200_RV2506151820.tar.bz2',{poi2RadolanRvMap[plz]})
data_hdf5 = RadolanHdf5Products.getRvData('file:./testdata/composite_rv_20250615_1820.tar',{poi2RadolanHdf5RvMap[plz]})

print(data['timestamp'])
print(data_hdf5['timestamp'],"\n")

for i in range(len(data['forecasts'])):
    print(data['forecasts'][i]['forecast'],data_hdf5['forecasts'][i]['forecast'], next(iter(data['forecasts'][i]['values'].values())), next(iter(data_hdf5['forecasts'][i]['values'].values())),next(iter(data_hdf5['forecasts'][i]['values'].values()))- next(iter(data['forecasts'][i]['values'].values())))
