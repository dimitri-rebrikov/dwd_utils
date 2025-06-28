from radolan_hdf5 import RadolanHdf5Products
from poi2RadolanHdf5RvMap import poi2RadolanHdf5RvMap
from radolan import RadolanProducts
from poi2RadolanRvMap import poi2RadolanRvMap
plz='70597'
xy_hdf5 = poi2RadolanHdf5RvMap[plz]
print("hdf5", xy_hdf5)
xy_old = (xy_hdf5[0], 1199-xy_hdf5[1])
print("old", xy_old)

data_hdf5 = RadolanHdf5Products.getRvData('file:./testdata/composite_rv_20250615_1820.tar',{(xy_hdf5[0], xy_hdf5[1], xy_hdf5[0], xy_hdf5[1])})
data_old = RadolanProducts.getRvData('file:./testdata/DE1200_RV2506151820.tar.bz2',{(xy_old[0], xy_old[1], xy_old[0], xy_old[1])})

print("hdf5", data_hdf5['timestamp'])
print("old", data_old['timestamp'])

for i in range(len(data_hdf5['forecasts'])):
    print("hdf5",data_hdf5['forecasts'][i]['forecast'], next(iter(data_hdf5['forecasts'][i]['values'].values())))
    print("hdf5",data_old['forecasts'][i]['forecast'], next(iter(data_old['forecasts'][i]['values'].values())))
    print(next(iter(data_hdf5['forecasts'][i]['values'].values()))- next(iter(data_old['forecasts'][i]['values'].values())))
