def fix_source:
  .source
  | join("")
  | gsub("\\\\n"; "\n")
  | gsub("\\\\\\\""; "\"")
  | gsub("\\\\\\{"; "{")
  | gsub("\\\\\\}"; "}")
  | gsub("ROOT = DATA_DIRBRAZIL_PATH"; "ROOT = DATA_DIR\n\nBRAZIL_PATH")
  | gsub("        return str\\(ERA5_MONTHLY_DIR"; "    return str(ERA5_MONTHLY_DIR")
  | gsub("base_path = str\\(ERA5_CAPITALS_DIR\\)"; "base_path = str(ERA5_MONTHLY_DIR)")
  | gsub("base_path,\n                        capital,\n                        f\"\\{capital\\}_heatwave_ERA5_diary.parquet\""; "ERA5_DAILY_DIR,\n                        capital,\n                        f\"{capital}_heatwave_ERA5_diary.parquet\"")
  | gsub("return str\\(ERA5_MONTHLY_DIR / city_dir_name / f\"\\{city_dir_name\\}_heatwave_ERA5_monthly.parquet\"\\)"; "    return str(ERA5_MONTHLY_DIR / city_dir_name / f\"{city_dir_name}_heatwave_ERA5_monthly.parquet\")")
  | gsub("ROOT = Path\\(\n    \"DATA_DIR\"\n\\)"; "ROOT = DATA_DIR")
  | gsub("XHWI_PATH = \\(\n    ROOT\n    / \"Indices_ondas_calor/\"\n      \"xhwi_era5_1950-2024_br_monthly_ind_prod_oficial\\.nc\"\n\\)"; "XHWI_PATH = XHWI_NETCDF")
  | gsub("OUTPUT_FILE = \\(\n    \"PROJECT_ROOT/\"\n    \"Artigo1/plot_full_maps\\.png\"\n\\)"; "OUTPUT_FILE = str(RESULTS_DIR / \"hazard_maps\" / \"plot_full_maps.png\")")
  | gsub("OUTPUT_FILE = \\(\n    \"PROJECT_ROOT/\"\n    \"Artigo1/zoom_p3risk_maps\\.png\"\n\\)"; "OUTPUT_FILE = str(RESULTS_DIR / \"risk_maps\" / \"zoom_p3risk_maps.png\")")
  | split("\n")
  | map(if startswith("        return str(ERA5_MONTHLY_DIR") then sub("^        "; "    ") else . end)
  | join("\n")
  | split("\n")
  | map(. + "\n");

.cells |= map(select((.source | join("")) | contains("user.upper()") | not))
| .cells |= map(if .cell_type == "code" then .source = (fix_source) else . end)
