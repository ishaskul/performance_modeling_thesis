if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <app> <scenario_name>"
    exit 1
fi

app=$1
scenario_name=$2
rm -r ./${app}/${scenario_name}/estimations/estimated_cpu_data
rm -r ./${app}/${scenario_name}/estimations/estimated_power_consumption
rm -r ./${app}/${scenario_name}/estimations/plots

echo "Cleanup for ${app} - ${scenario_name} complete."
