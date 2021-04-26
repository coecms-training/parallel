#!/g/data/hh5/public/apps/nci_scripts/python-analysis3
# Copyright 2021 Scott Wales
# author: Scott Wales <scott.wales@unimelb.edu.au>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import climtas.nci
import xarray
import pandas
import numpy
import time
import dask
import climtas
import os


def test_load(path, variable, chunks, isel=None):
    with xarray.open_mfdataset(
        path, combine="nested", concat_dim="time", chunks=chunks
    ) as ds:
        var = ds[variable]
        if isel is not None:
            var = var.isel(**isel)

        out = os.path.join(os.environ['TMPDIR'],'sample.nc')

        start = time.perf_counter()
        daily = climtas.blocked_resample(var, time=24).mean()
        climatology = climtas.blocked_groupby(daily, time='dayofyear').mean()
        climtas.io.to_netcdf_throttled(climatology, out)
        duration = time.perf_counter() - start

    data_size = var.nbytes
    chunk_size = numpy.prod([c[0] for c in var.chunks]) * var.dtype.itemsize
    nchunks = var.data.npartitions

    print(
        f"{dask.utils.format_bytes(data_size/duration)}/s - {dask.utils.format_bytes(data_size)} loaded in {nchunks} chunks (~ {dask.utils.format_bytes(chunk_size)})"
    )

    return {"duration": duration, "data_size": data_size, "chunk_size": chunk_size}


def test_load_chunks(path, variable, chunk_list, iterations=1, isel=None):

    with xarray.open_mfdataset(path, combine="nested", concat_dim="time") as ds:
        var = ds[variable]
        c = dict(zip(var.dims, var.encoding["chunksizes"]))
        print(f"Native chunks - {c}")

    result = []
    for n in range(iterations):
        for c in chunk_list:
            r = test_load(path, variable, c, isel=isel)
            r.update(c)
            result.append(r)

    return pandas.DataFrame(result).sort_values("duration")


if __name__ == '__main__':
    c = climtas.nci.GadiClient()

    workers = len(c.cluster.workers)
    threads = c.cluster.workers[0].nthreads

    path = "/g/data/rt52/era5/single-levels/reanalysis/2t/200*/2t_era5_oper_sfc_*.nc"
    var = 't2m'

    # Warm the cache
    xarray.open_mfdataset(path, {"latitude": 91, "longitude": 180})[var].mean().load()

    df = test_load_chunks(
        path,
        var,
        chunk_list = [
            {"latitude": 91,   "longitude": 180//2},
            {"latitude": 91,   "longitude": 180},
            {"latitude": 91,   "longitude": 180*2},
            {"latitude": 91*2, "longitude": 180},
            {"latitude": 91*2, "longitude": 180*2},
        ],
    )

    df['workers'] = workers
    df['threads'] = threads

    logfile = 'era5_t2_climatology.csv'

    try:
        prev = pandas.read_csv(logfile)
        df = pandas.concat([prev, df])
    except FileNotFoundError:
        pass

    df.to_csv(logfile, index=False)
