# 1) Imports
import xarray as xr
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.interpolate import interp1d
from scipy import stats
import math
import os
import dask
from dask.diagnostics import ProgressBar
import gc

# Ativando barra de progresso para monitorar a operação
pbar = ProgressBar()
pbar.register()

# 2) Functions
def ds_calib_to_frame(ds):
    df = ds.to_dataframe()
    df = df.reset_index()
    df = df[["time", "VAR_2T"]]
    percentil_95 = np.percentile(ds["VAR_2T"], 95)
    print(percentil_95)
    df.set_index("time", inplace = True)
    
    return df

def ds_prev_to_frame(ds):
    df_prev = ds.to_dataframe()
    df_prev = df_prev.reset_index()
    df_prev = df_prev[["time", "t2m", "r"]]

    df_prev.set_index("time", inplace = True)
    df_prev = df_prev.sort_index()

    return df_prev

def caulculate_xhwi(df_calib, df_prev):
    temps = df_calib['VAR_2T'].values
    #Function for calculate the percentil of a x's temperature
    def calculate_percentil(x):
        return stats.percentileofscore(temps, x)
    
    # Applying the function for each value in df_prev
    df_prev['Target'] = df_prev['t2m'].map(calculate_percentil)
    #Tme/tpe
    df_prev["tpe"] = df_prev["Target"] - 95
    df_prev.loc[df_prev["Target"] - 95 <= 0, "tpe"] = 0
    
    #Coef
    df_prev["Coef"] = ((np.exp(df_prev["tpe"])) * (df_prev["r"])) / (1000)
    
    #Heatwave index
    df_prev["XHWI"] = ((df_prev["Coef"]) - (0.001)) / (14.84)
    #Se tpe == 0, o índice não deve ser calculado
    df_prev.loc[df_prev["tpe"] == 0, "XHWI"] = 0
    df_prev.loc[df_prev["t2m"] <= 32, "XHWI"] = 0
    #Se HWI <= 0.001, não contar como ondas de calor, portanto, HWI é transformado em zero.
    df_prev.loc[df_prev["XHWI"] <= 0.001, "XHWI"] = 0
    
    return df_prev

def diary_ind_prod(path):
    df = pd.read_csv(path)
    df.reset_index()
    df.set_index("time", inplace=True)
    df.index = pd.to_datetime(df.index)
    
    # Grouping the data by day and calculating the sum of the index values
    diary_sum = df.resample('D')['XHWI'].sum()
    # Calculating the total number of hours the index is non-zero for each day
    non_zero_hours = df['XHWI'].apply(lambda x: 1 if x != 0 else 0).resample('D').sum()
    ind_prod = diary_sum * non_zero_hours
    
    t2m = df.resample("D")["t2m"].max()
    r = df.resample("D")["r"].mean()
    
    diary_sum.name = 'diary_sum'
    non_zero_hours.name = 'non_zero_hours'
    ind_prod.name = 'Ind_Prod'

    df_I = pd.concat([t2m, r, diary_sum, non_zero_hours, ind_prod], axis=1)

    return df_I

def monthly_ind_prod(path):
    df = pd.read_csv(path)
    df.reset_index()
    df.set_index("time", inplace=True)
    df.index = pd.to_datetime(df.index)
    
    # Grouping the data by day and calculating the sum of the index values
    diary_sum = df.resample('D')['XHWI'].sum()
    # Calculating the total number of hours the index is non-zero for each day
    non_zero_hours = df['XHWI'].apply(lambda x: 1 if x != 0 else 0).resample('D').sum()
    ind_prod = diary_sum * non_zero_hours
    
    t2m = df.resample("D")["t2m"].max()
    r = df.resample("D")["r"].mean()
    
    diary_sum.name = 'diary_sum'
    non_zero_hours.name = 'non_zero_hours'
    ind_prod.name = 'Ind_Prod'

    df_I = pd.concat([t2m, r, diary_sum, non_zero_hours, ind_prod], axis=1)

    t2m = df_I.resample("MS")["t2m"].max()
    r = df_I.resample("MS")["r"].mean()
    ind_prod_sum = df_I.resample('MS')['Ind_Prod'].sum()
    ind_prod_sum.name = "Ind_Prod_monthly_sum"

    xhwi = pd.concat([t2m, r, ind_prod_sum], axis=1)
    xhwi = xhwi.dropna(how="any")

    return xhwi

# 3) Processing Data
# 3.1) Brasilian Capitals
BR_cities_dict = {
                  "Curitiba": [-49.266873, -25.434657], 
                  "Porto Alegre": [-51.121873, -29.973011],
                  "Florianópolis": [-48.5489, -27.594514],
                  "Vitória": [-40.37522, -20.342443], 
                  "Belo Horizonte": [-43.966878, -19.914189], 
                  "Rio de Janeiro": [-43.39112, -22.864019],
                  "São Paulo": [-46.637177, -23.560714], 
                  "Rio Branco": [-67.82702, -9.970123],
                  "Macapá": [-51.093464, 0.032312],
                  "Manaus": [-59.983923, -3.067863], 
                  "Belém": [-48.456545, -1.435312], 
                  "Porto Velho": [-63.869757,  -8.766493],
                  "Boa Vista": [-60.70358, 2.820423],
                  "Palmas": [-48.322951, -10.223291],
                  "Goiânia": [-49.262223, -16.685239],
                  "Cuiabá": [-56.091689, -15.597807],
                  "Campo Grande": [-54.616175, -20.461428],
                  "Maceió": [-35.724432, -9.647983],
                  "Salvador": [-38.484514, -12.984535],
                  "Fortaleza": [-38.556329, -3.780144],
                  "São Luís": [-44.259858, -2.548971],
                  "João Pessoa": [-34.862597, -7.150461],
                  "Recife": [-34.942075, -8.048461],
                  "Teresina": [-42.79097, -5.087195],
                  "Natal": [-35.25804, -5.757555],
                  "Aracaju": [-37.087555, -10.90724],
                  "Brasília": [-47.89463, -15.800849]
                  }

# 3.2) Rio de Janeiro Cities
RJ_cities_dict = {
                  "Itaperuna": [-41.893713, -21.201246], 
                  "Nova Friburgo": [-42.533413, -22.287768],
                  "Petrópolis": [-43.179508, -22.512088],
                  "Campos dos Goytacazes": [-41.317154, -21.758101], 
                  "Cabo Frio": [-42.042666, -22.882395], 
                  "Paraíba do Sul": [-43.291892, -22.160876],
                  "Resende": [-44.46126, -22.469065], 
                  "Angra dos Reis": [-44.296176, -22.973831],
                  "Niterói_litoral": [-43., -23.],
                  "Niterói_interior": [-43., -22.75], 
                  "São Gonçalo": [-42.975174, -22.818852], 
                  "Duque de Caxias": [-43.264504,  -22.757002],
                  "Rio de Janeiro": [-43.39112, -22.864019]
                  }

# 4) Open Files
# 4.1) Calibration
# The original upstream calibration file is not included in this repository.
path_t2m_calib = "data/raw/era5/upstream/temp_max_Brazil_1961-1990.nc"
ds_t2m_calib_total = xr.open_dataset(path_t2m_calib)
ds_t2m_calib_total

# Formating longitude
ds_t2m_calib_total.coords["longitude"] = (ds_t2m_calib_total.coords["longitude"] + 180) % 360 - 180 #Colocar o formato da longitude de -180 a 180
ds_t2m_calib_total = ds_t2m_calib_total.sortby(ds_t2m_calib_total.longitude)

# 4.2) Prediction
#Prediction period
#Openfiles
path_t2m_prev = "data/raw/era5/upstream/zarr_store_t2m_br_1950-2023"
path_r_prev = "data/raw/era5/upstream/zarr_store_humidity_br_1950-2023"

# 
ds_t2m_prev_zarr = xr.open_zarr(path_t2m_prev)
ds_r_prev_zarr = xr.open_zarr(path_r_prev)

# 5) Main
# 5.1) Path for Results
pth_result = "data/raw/era5/capitals"

# 5.2) Calculation and saving Xtreme Heatwave Index
#for key, values in RJ_cities_dict.items():
#    print(f"\n____A Cidade é {key}____\n")
#
#    # Open Calibration Data 
#    ds_calib = ds_t2m_calib_total.sel(longitude=values[0], latitude=values[1], method="nearest")
#
#    ## Training Period - default is:
#    per = ["1960-01-01T00:00:00.000000000", "1990-12-31T23:00:00.000000000"]
#    ds_calib = ds_calib.sel(time = slice(per[0], per[1]))
#
#    ## Daily Maximum Temperature - In that case we already have:
#    ### ds_calib = ds_calib.resample(time='D').max(dim='time')
#
#    ## Monthly xarray datasets
#    month_ds = [ds_calib.sel(time=(ds_calib['time.month'] == i)) for i in range(1,13)] #Armazenando o dataset de cada mês na lista month_ds
#    
#    ## Monthly dataframes
#    list_df = [ds_calib_to_frame(ds) for ds in month_ds]
#    
#    # Open Prediction Data
#    ds_t2m_prev = ds_t2m_prev_zarr.sel(longitude=values[0], latitude=values[1], method="nearest")
#    ds_r_prev = ds_r_prev_zarr.sel(longitude=values[0], latitude=values[1], method="nearest")
#
#    # Grouping in One Dataset
#    ds_prev = ds_t2m_prev
#    ds_prev["r"] = ds_r_prev["r"]
#
#    # Prediction Period
#    per_prev = ["1950-01-01T00:00:00.000000000", "2024-09-30T23:00:00.000000000"]
#    ds_prev = ds_prev.sel(time=slice(per_prev[0], per_prev[1]))
#
#    # Bump in Memory the selecting data
#    print("Iniciando leitura total do dado selecionado")
#    ds_prev = ds_prev.compute()
#    print("Finalizando leitura total do dado selecionado")
#
#    month_ds_prev = [ds_prev.sel(time=(ds_prev['time.month'] == i)) for i in range(1,13)] #Armazenando o dataset de cada mês na lista month_ds_prev
#
#    # TimeSeries of Prediction
#    print("Iniciando ds_prev_to_frame")
#    list_df_prev = [ds_prev_to_frame(ds_prev) for ds_prev in month_ds_prev]
#    print("Finalizando ds_prev_to_frame")
#    
#    #Calculate Xtreme Heatwave Index
#    print("Iniciando caulculate_xhwi")
#    list_df_xhwi = [caulculate_xhwi(df_calib, df_prev) for df_calib, df_prev in zip(list_df, list_df_prev)]
#    print("Finalizando caulculate_xhwi")
#
#    # Saving Data
#    for index, df_xhwi in enumerate(list_df_xhwi):
#        if not os.path.exists(f"{pth_result}/{key}"):
#            os.makedirs(f"{pth_result}/{key}")
#        print(f"Iniciando salvamento do csv do mês {index+1}")
#        df_xhwi.to_csv(f"{pth_result}/{key}/{key}_heatwave_ERA5_month_{index+1}.csv")
#        print(f"Finalizando salvamento do csv do mês {index+1}")
#        #df.to_excel(f"{pth_result}/{city}_heatwave_ERA5_month_{i+1}.xlsx")
#
#    # Calculating Diary Ind_Prod
#    list_diary_ind_prod = [diary_ind_prod(f"{pth_result}/{key}/{key}_heatwave_ERA5_month_{i}.csv") for i in range(1, 13)]
#    
#    Ind_diary_Prod = pd.concat(list_diary_ind_prod)
#    Ind_diary_Prod.dropna(how="any", inplace=True)
#    Ind_diary_Prod.index = pd.to_datetime(Ind_diary_Prod.index)
#    Ind_diary_Prod.sort_index(inplace=True)
#    print("Iniciando salvamento do Ind_Prod diário")
#    Ind_diary_Prod.to_csv(f"{pth_result}/{key}/{key}_Diary_Ind_Prod_t2m_MAX.csv")
#    print("Finalizando salvamento do Ind_Prod diário")
#
#    # Calculating Monthly Ind_Prod
#    list_monthly_ind_prod = [monthly_ind_prod(f"{pth_result}/{key}/{key}_heatwave_ERA5_month_{i}.csv") for i in range(1, 13)]
#    
#    Ind_monthly_Prod = pd.concat(list_monthly_ind_prod)
#    Ind_monthly_Prod.index = pd.to_datetime(Ind_monthly_Prod.index)
#    Ind_monthly_Prod.sort_index(inplace=True)
#    print("Iniciando salvamento do Ind_Prod mensal")
#    Ind_monthly_Prod.to_csv(f"{pth_result}/{key}/{key}_Monthly_Ind_Prod.csv")
#    print("Finalizando salvamento do Ind_Prod mensal")
#
#    # Cleaning Memory
#    del ds_calib, ds_prev, ds_t2m_prev, ds_r_prev, list_df, list_df_prev, list_df_xhwi
#    del Ind_diary_Prod, Ind_monthly_Prod, list_diary_ind_prod, list_monthly_ind_prod
#
#    gc.collect()

for key, values in BR_cities_dict.items():
    print(f"\n____A Cidade é {key}____\n")

    # Open Calibration Data 
    ds_calib = ds_t2m_calib_total.sel(longitude=values[0], latitude=values[1], method="nearest")

    ## Training Period - default is:
    per = ["1961-01-01T00:00:00.000000000", "1990-12-31T23:00:00.000000000"]
    ds_calib = ds_calib.sel(time = slice(per[0], per[1]))

    ## Daily Maximum Temperature - In that case we already have:
    ### ds_calib = ds_calib.resample(time='D').max(dim='time')

    ## Monthly xarray datasets
    month_ds = [ds_calib.sel(time=(ds_calib['time.month'] == i)) for i in range(1,13)] #Armazenando o dataset de cada mês na lista month_ds
    
    ## Monthly dataframes
    list_df = [ds_calib_to_frame(ds) for ds in month_ds]
    
    # Open Prediction Data
    ds_t2m_prev = ds_t2m_prev_zarr.sel(longitude=values[0], latitude=values[1], method="nearest")
    ds_r_prev = ds_r_prev_zarr.sel(longitude=values[0], latitude=values[1], method="nearest")

    # Grouping in One Dataset
    ds_prev = ds_t2m_prev
    ds_prev["r"] = ds_r_prev["r"]

    # Prediction Period
    per_prev = ["1950-01-01T00:00:00.000000000", "2023-12-31T23:00:00.000000000"]
    ds_prev = ds_prev.sel(time=slice(per_prev[0], per_prev[1]))

    # Bump in Memory the selecting data
    print("Iniciando leitura total do dado selecionado")
    ds_prev = ds_prev.compute()
    print("Finalizando leitura total do dado selecionado")

    month_ds_prev = [ds_prev.sel(time=(ds_prev['time.month'] == i)) for i in range(1,13)] #Armazenando o dataset de cada mês na lista month_ds_prev

    # TimeSeries of Prediction
    print("Iniciando ds_prev_to_frame")
    list_df_prev = [ds_prev_to_frame(ds_prev) for ds_prev in month_ds_prev]
    print("Finalizando ds_prev_to_frame")
    
    #Calculate Xtreme Heatwave Index
    print("Iniciando caulculate_xhwi")
    list_df_xhwi = [caulculate_xhwi(df_calib, df_prev) for df_calib, df_prev in zip(list_df, list_df_prev)]
    print("Finalizando caulculate_xhwi")

    # Saving Data
    for index, df_xhwi in enumerate(list_df_xhwi):
        if not os.path.exists(f"{pth_result}/{key}"):
            os.makedirs(f"{pth_result}/{key}")
        print(f"Iniciando salvamento do csv do mês {index+1}")
        df_xhwi.to_csv(f"{pth_result}/{key}/{key}_heatwave_ERA5_month_{index+1}.csv")
        print(f"Finalizando salvamento do csv do mês {index+1}")
        #df.to_excel(f"{pth_result}/{city}_heatwave_ERA5_month_{i+1}.xlsx")

    # Calculating Diary Ind_Prod
    list_diary_ind_prod = [diary_ind_prod(f"{pth_result}/{key}/{key}_heatwave_ERA5_month_{i}.csv") for i in range(1, 13)]
    
    Ind_diary_Prod = pd.concat(list_diary_ind_prod)
    Ind_diary_Prod.dropna(how="any", inplace=True)
    Ind_diary_Prod.index = pd.to_datetime(Ind_diary_Prod.index)
    Ind_diary_Prod.sort_index(inplace=True)
    print("Iniciando salvamento do Ind_Prod diário")
    Ind_diary_Prod.to_csv(f"{pth_result}/{key}/{key}_Diary_Ind_Prod_t2m_MAX.csv")
    print("Finalizando salvamento do Ind_Prod diário")

    # Calculating Monthly Ind_Prod
    list_monthly_ind_prod = [monthly_ind_prod(f"{pth_result}/{key}/{key}_heatwave_ERA5_month_{i}.csv") for i in range(1, 13)]
    
    Ind_monthly_Prod = pd.concat(list_monthly_ind_prod)
    Ind_monthly_Prod.index = pd.to_datetime(Ind_monthly_Prod.index)
    Ind_monthly_Prod.sort_index(inplace=True)
    print("Iniciando salvamento do Ind_Prod mensal")
    Ind_monthly_Prod.to_csv(f"{pth_result}/{key}/{key}_Monthly_Ind_Prod.csv")
    print("Finalizando salvamento do Ind_Prod mensal")

    # Cleaning Memory
    #del ds_calib, ds_prev, ds_t2m_prev, ds_r_prev, list_df, list_df_prev, list_df_xhwi
    #del Ind_diary_Prod, Ind_monthly_Prod, list_diary_ind_prod, list_monthly_ind_prod#

    #gc.collect()
