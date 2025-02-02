#!/bin/bash
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <app> <scenario_name>"
    exit 1
fi

app=$1
scenario_name=$2

# Run the queuing network and ctmc hybrid model
echo "Running performance model"
python3 model_cpu_utilization.py --app "$app" --scenario_name "$scenario_name"

# Run analysis scripts for cpu utilization
echo "Running CPU Utilization Comparison Scripts..."
python3 ./"$app"/"$scenario_name"/scripts/comparison_scripts/cpu_utilization_comparison/cpu_utilization_comparision_per_container.py
python3 ./"$app"/"$scenario_name"/scripts/comparison_scripts/cpu_utilization_comparison/server_cpu_utilization_comparison.py
python3 ./"$app"/"$scenario_name"/scripts/comparison_scripts/cpu_utilization_comparison/get_server_comparison_plots_after_ctmc_refinement.py

# Run analysis scripts for energy and power consumption
echo "Running Power Consumption Comparison Scripts..."
python3 ./"$app"/"$scenario_name"/scripts/comparison_scripts/power_consumption_comparison/power_consumption_comparison_per_container_with_energy_calculations.py
python3 ./"$app"/"$scenario_name"/scripts/comparison_scripts/power_consumption_comparison/server_power_consumption_comparison.py

echo "All tasks completed"
