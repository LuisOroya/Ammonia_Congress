"""Single source of truth for Python-side pipeline settings."""
SELECTED_K = 9
K_VALUES = tuple(range(5, 16))
PV_WIND_ROUND_DECIMALS = 3   # upward to 0.001 MW
H2_STORAGE_ROUND_KG = 1      # upward to 1 kg
THREADS = 16
PWL_SEGMENTS = 6
