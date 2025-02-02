import csv
import os
import glob
import sys
import json
from datetime import datetime
import re
import csv
import pandas as pd
from scipy.stats import kruskal, shapiro, f_oneway
import matplotlib.pyplot as plt
import scipy.stats as stats

def transform_system_cpu_data_per_server_per_iteration(input_base_dir,output_base_dir, system_cpu_output_path ):
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)
    for i in range(1, 4):
        input_dir = os.path.join(input_base_dir, str(i), system_cpu_output_path)
        for machine in green_lab_machines:
            file_pattern = os.path.join(input_dir, f'cpu_usage_output_{machine}_*.txt')
            files = glob.glob(file_pattern)
            for input_file in files:
                output_file = os.path.join(output_base_dir, machine, system_cpu_output_path, f'cpu_usage_output_{machine}_it_{i}.csv')
                with open(input_file, 'r') as file:
                    lines = file.readlines()

                headers = ["Time", "CPU", "user", "nice", "system", "iowait", "steal", "idle"]

                output_dir = os.path.dirname(output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                with open(output_file, 'w', newline='') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerow(headers)

                    for line in lines:
                        splitted_line = line.split()
                        if(machine == 'gl5' or machine == 'gl6'):
                            if len(splitted_line) == 9 and not line.startswith("Average:") and "idle" not in line:
                                if 'PM' in splitted_line or 'AM' in splitted_line:
                                    new_time = f"{splitted_line[0]} {splitted_line[1]}"
                                    converted_time_24h = datetime.strptime(new_time, "%I:%M:%S %p").strftime("%H:%M:%S")
                                    new_splitted_line = [converted_time_24h, splitted_line[2], splitted_line[3], splitted_line[4], splitted_line[5], splitted_line[6], splitted_line[7], splitted_line[8]]
                                    csvwriter.writerow(new_splitted_line)
                                else:
                                    csvwriter.writerow(splitted_line)
                        else:
                            if len(splitted_line) == 8 and not line.startswith("Average:") and "idle" not in line:
                                if 'PM' in splitted_line or 'AM' in splitted_line:
                                    new_time = f"{splitted_line[0]} {splitted_line[1]}"
                                    converted_time_24h = datetime.strptime(new_time, "%I:%M:%S %p").strftime("%H:%M:%S")
                                    new_splitted_line = [converted_time_24h, splitted_line[2], splitted_line[3], splitted_line[4], splitted_line[5], splitted_line[6], splitted_line[7], splitted_line[8]]
                                    csvwriter.writerow(new_splitted_line)
                                else:
                                    csvwriter.writerow(splitted_line)

def transform_system_power_consumption_data_per_server_per_iteration(input_base_dir, output_base_dir, system_power_consumption_output_path):
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)
    for i in range(1, 4):
        input_dir = os.path.join(input_base_dir, str(i), system_power_consumption_output_path)
        for machine in green_lab_machines:
            file_pattern = os.path.join(input_dir, f'powerstat_output_{machine}_*.txt')
            files = glob.glob(file_pattern)
            for input_file in files:
                output_file = os.path.join(output_base_dir, machine, system_power_consumption_output_path, f'power_consumption_output_{machine}_it_{i}.csv')
                with open(input_file, 'r') as file:
                    lines = file.readlines()

                headers = ["Time", "Watts"]

                output_dir = os.path.dirname(output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                with open(output_file, 'w', newline='') as csvfile:
                    csvwriter = csv.writer(csvfile)
                    csvwriter.writerow(headers)

                    for line in lines:
                        # Ignore lines which are not the readings
                        if any(keyword in line for keyword in ['Running for', 'Power measurements', '--------', 'Average', 'GeoMean', 'StdDev', 'Minimum', 'Maximum', 'Summary', 'Note', 'These readings','Time','Watts']):
                            continue
                        splitted_line = line.split()                        
                        if len(splitted_line) >= 13:
                            time = splitted_line[0]
                            watts = splitted_line[12]
                            csvwriter.writerow([time, watts])

def convert_timestamp(unix_timestamp):
    dt_object = datetime.utcfromtimestamp(unix_timestamp)
    return dt_object.strftime('%Y-%m-%d %H:%M:%S')

def generate_pid_conatiner_name_mapping_from_data(input_base_dir, resource_util_output_path, resource_type):
    input_dir = os.path.join(input_base_dir, "1", resource_util_output_path)
    container_pid_mapping = {}
    for machine in green_lab_machines:
        # Determine the correct machine name
        if machine == 'GreenLab-STF':
            machine_name = 'gl2'
        else:
            machine_name = machine
        container_pid_mapping[machine_name] = {}
        file_pattern = os.path.join(input_dir, f'per_container_{resource_type}_{machine_name}_*.json')
        files = glob.glob(file_pattern)

        for input_file in files:
            with open(input_file, 'r') as json_file:
                data = json.load(json_file)
                for prometheus_result in data['data']['result']:
                    metric_info = prometheus_result['metric']
                    cmdline = metric_info.get("cmdline")
                    pid = metric_info.get("pid")
                    
                    if "prometheus.yml" in cmdline:
                        container_name_prefix = "prometheus"
                    elif "scaphandreprometheus" in cmdline:
                        container_name_prefix = "scaphandre"
                    elif "consulagent" in cmdline:
                        container_name_prefix = "consul"
                    elif re.search(r'-jar\/([^\/]+)\.jar$', cmdline):
                        regex_query_matching = re.search(r'-jar\/([^\/]+)\.jar$', cmdline)
                        container_name_prefix = regex_query_matching.group(1)
                    elif "telegraf" in cmdline:
                        container_name_prefix = "telegraf"
                    elif "chronograf" in cmdline:
                        container_name_prefix = "chronograf"
                    elif "kapacitord" in cmdline:
                        container_name_prefix = "kapacitord"
                    elif "influxd" in cmdline:
                        container_name_prefix = "influxd"
                    elif "registry" in cmdline:
                        container_name_prefix = "registry"
                    elif "trueorg.springframework.boot.loader.launch.PropertiesLauncher" in cmdline:
                        container_name_prefix = "zipkin"      
                    elif "max_connections=3000000" in cmdline:
                        container_name_prefix = "mysql"                 
                    else:
                        continue

                    # Generate an iterative identifier if multiple replicas are present
                    count = 1
                    container_name = f"{container_name_prefix}_replica_{count}"
                    existing_containers = [value for value in container_pid_mapping[machine_name].values()]
                    while container_name in existing_containers:
                        count += 1
                        container_name = f"{container_name_prefix}_replica_{count}"

                    container_pid_mapping[machine_name][pid] = container_name

    return container_pid_mapping


def transform_per_container_resource_util_per_server(input_base_dir, output_base_dir, resource_util_output_path):
    if ("power_consumption_data" in resource_util_output_path ):
        resource_type = "power_consumption"
    else:
        resource_type = "cpu_usage"
    container_pid_mapping = generate_pid_conatiner_name_mapping_from_data(input_base_dir,resource_util_output_path, resource_type )
    for i in range(1, 4):
        input_dir = os.path.join(input_base_dir, str(i), resource_util_output_path)
        # Loop through each server machine
        for machine in green_lab_machines:
            if(machine == 'GreenLab-STF'):
                machine_name = 'gl2'
            else:
                machine_name = machine
            file_pattern = os.path.join(input_dir, f'per_container_{resource_type}_{machine_name}_*.json')
            files = glob.glob(file_pattern)
            
            if not files:
                print(f"No files found for {machine_name} in {input_dir}")
                continue

            for input_file in files:
                with open(input_file, 'r') as json_file:
                    data = json.load(json_file)

                    for prometheus_result in data['data']['result']:
                        metric_info = prometheus_result['metric']
                        values = prometheus_result['values']
                        for timestamp, utilization in values:
                             formatted_timestamp = convert_timestamp(int(timestamp))
                             pid = metric_info.get("pid")
                             container_name = container_pid_mapping[machine_name].get(pid)
                             csv_row = {
                                    "timestamp": formatted_timestamp,
                                    "container": container_name,
                                    f"{resource_type}": utilization,
                                    "pid": pid
                                    }
                
                             csv_headers = ["timestamp", "container", f"{resource_type}", "pid"]
                             outputPathForPerContainerCSVs = f'{output_base_dir}/{machine}/per_container_data/{container_name}'
                             if not os.path.exists(outputPathForPerContainerCSVs):
                                os.makedirs(outputPathForPerContainerCSVs)
                             csv_file_path = os.path.join(outputPathForPerContainerCSVs, f'{resource_type}_output_{container_name}_it_{i}.csv')
                             with open(csv_file_path, 'a', newline='') as csv_file:
                                writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
                                if csv_file.tell() == 0:  # Only write headers if file is empty
                                    writer.writeheader()
                                writer.writerow(csv_row)

def calculate_cpu_utilization_from_idle_time(output_base_dir, servers):
    for server in servers:
        system_cpu_utilization_data_folder = os.path.join(output_base_dir, server, "system_cpu_data")
        for i in range(1, 4):
            cpu_util_csv_file_path = os.path.join(system_cpu_utilization_data_folder, f"cpu_usage_output_{server}_it_{i}.csv")
            df = pd.read_csv(cpu_util_csv_file_path)  # corrected the variable name here as well
            df['cpu_utilization'] = (100 - df['idle']).round(2)
            df.to_csv(cpu_util_csv_file_path, index=False)

def perform_kruskal_wallis_test_on_total_system_cpu_util_data(output_base_dir, servers):
    result_csv_path = os.path.join(output_base_dir, 'kruskal_wallis_test_results_cpu_utilization.csv')
    with open(result_csv_path, 'w', newline='') as result_csv_file:
        csv_writer = csv.writer(result_csv_file)
        csv_writer.writerow(["server_name", "container_name", "p-value"])
        for server in servers:
            all_iterations_data = []
            system_cpu_utilization_data_folder = os.path.join(output_base_dir, server, "system_cpu_data")
            for i in range(1, 4):
                cpu_util_csv_file_path = os.path.join(system_cpu_utilization_data_folder, f"cpu_usage_output_{server}_it_{i}.csv")
                df = pd.read_csv(cpu_util_csv_file_path)
                cpu_utilization_data = df['cpu_utilization']
                all_iterations_data.append(cpu_utilization_data)

            kruskal_result = kruskal(*all_iterations_data)
            
            csv_writer.writerow([server, "", kruskal_result.pvalue])
            print(f"KW Test Result for Total System CPU Utilization Data: {server}")
            print(f"P-value: {kruskal_result.pvalue}")
            print("-" * 40)

def perform_kruskal_wallis_test_on_total_power_consumption_data(output_base_dir, servers):
    result_csv_path = os.path.join(output_base_dir, 'kruskal_wallis_test_results_power_consumption.csv')
    with open(result_csv_path, 'w', newline='') as result_csv_file:
        csv_writer = csv.writer(result_csv_file)
        csv_writer.writerow(["server_name", "container_name", "p-value"])
        for server in servers:
            all_iterations_data = []
            power_consumption_data_folder = os.path.join(output_base_dir, server, "power_consumption_data")
            for i in range(1, 4):
                power_consumption_csv_file_path = os.path.join(power_consumption_data_folder, f"power_consumption_output_{server}_it_{i}.csv")
                df = pd.read_csv(power_consumption_csv_file_path)
                power_consumption_data = df['Watts']
                all_iterations_data.append(power_consumption_data)

            kruskal_result = kruskal(*all_iterations_data)
            csv_writer.writerow([server, "", kruskal_result.pvalue])
            print(f"KW Test Result for Total System Power Consumption Data: {server}")
            print(f"P-value: {kruskal_result.pvalue}")
            print("-" * 40)


if len(sys.argv) < 2:
    print("Please specify the scenario name: python3 data_transformer.py <scenario-name> e.g. buy_books")
    sys.exit(1)
green_lab_machines = ['GreenLab-STF', 'gl5', 'gl6']
scenario = sys.argv[1]
input_base_dir = f'../../buy_books_final'
output_base_dir = f'../../buy_books_final/transformed_data_kw_test'
system_cpu_output_path = 'system_cpu_data'
system_power_consumption_output_path = 'power_consumption_data'

transform_system_cpu_data_per_server_per_iteration(input_base_dir,output_base_dir, system_cpu_output_path)
calculate_cpu_utilization_from_idle_time(output_base_dir, green_lab_machines)
transform_system_power_consumption_data_per_server_per_iteration(input_base_dir,output_base_dir, system_power_consumption_output_path)
perform_kruskal_wallis_test_on_total_system_cpu_util_data(output_base_dir,green_lab_machines)
perform_kruskal_wallis_test_on_total_power_consumption_data(output_base_dir,green_lab_machines)