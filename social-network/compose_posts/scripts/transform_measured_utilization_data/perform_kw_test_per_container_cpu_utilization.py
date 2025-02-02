import json
import csv
import os
import glob
from datetime import datetime, timezone
import re
from scipy.stats import kruskal

input_base_dir = '../../compose_posts'
container_pid_mapping_csv_dir = '../../compose_posts' 
output_base_dir = '../../compose_posts/transformed_data_kw_test'
os.makedirs(output_base_dir, exist_ok=True)

servers = ["gl2", "gl5", "gl6"]
containers_to_be_excluded = [
    'docker-compose', 'monitoring_prometheus', 'scaphandre', 'registry', 'nginx-web-server', 'media-frontend'
]
regex_pattern_to_filter_container_names = re.compile(r"^sn_([^\.]+)")

kruskal_wallis_csv_path = os.path.join(output_base_dir, 'kruskal_wallis_test_results_cpu_utilization.csv')

for i in range(1, 11):
    # Iterate through each server in servers
    for server in servers:
        input_dir = os.path.join(input_base_dir, str(i), "system_cpu_data")
        json_file_pattern = os.path.join(input_dir, f'per_container_cpu_usage_{server}_*.json')
        json_files = glob.glob(json_file_pattern)

        if not json_files:
            print(f"No JSON files found for server {server} in iteration {i}. Skipping...")
            continue
        
        if (server == 'gl2'):
            server_name = "GreenLab-STF"
        else:
            server_name = server
        output_dir = os.path.join(output_base_dir, server_name, "cpu_util_data_per_container")
        os.makedirs(output_dir, exist_ok=True)
        
        for json_file_path in json_files:
            with open(json_file_path, 'r') as f:
                data = json.load(f)

            service_data = {}
            nginx_data = []
            server_name = "GreenLab-STF" if server == "gl2" else server
            container_mapping_file = os.path.join(container_pid_mapping_csv_dir, f"container_pids_{server_name}.csv")
            
            if not os.path.exists(container_mapping_file):
                print(f"Container PID mapping file for {server_name} not found. Skipping...")
                continue

            with open(container_mapping_file, "r") as csv_file:
                container_pid_mapping = list(csv.DictReader(csv_file))
            
            for result in data["data"]["result"]:
                pid_in_prometheus_data = result["metric"].get("pid", "")
                custom_label = result["metric"].get("custom_label", "")
                
                for row in container_pid_mapping:
                    container_name = row["container_name"]
                    pid = row["pid"]
                    match = regex_pattern_to_filter_container_names.match(container_name)
                    
                    if match:
                        filtered_container_name = match.group(1)
                    elif custom_label == 'nginx_cpu':
                        filtered_container_name = 'nginx'
                    else:
                        filtered_container_name = container_name
                    
                    # Ignore 'nginx-web-server'
                    if filtered_container_name == 'nginx-web-server':
                        continue
                    
                    if custom_label == 'nginx_cpu':
                        for timestamp, value in result["values"]:
                            formatted_timestamp = datetime.fromtimestamp(float(timestamp), timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                            nginx_data.append([formatted_timestamp, 'nginx', float(value), pid_in_prometheus_data])
                        break
                    
                    if any(exclude in container_name for exclude in containers_to_be_excluded):
                        continue
                    
                    if pid == pid_in_prometheus_data:
                        if filtered_container_name not in service_data:
                            service_data[filtered_container_name] = []
                        
                        for timestamp, value in result["values"]:
                            formatted_timestamp = datetime.fromtimestamp(float(timestamp), timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                            service_data[filtered_container_name].append([formatted_timestamp, filtered_container_name, float(value), pid_in_prometheus_data])
                        break

            for service, records in service_data.items():
                service_output_dir = os.path.join(output_dir, service)
                os.makedirs(service_output_dir, exist_ok=True)
                csv_file_path = os.path.join(output_dir, service,f"cpu_usage_output_{service}_it_{i}.csv")
                with open(csv_file_path, 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow(["timestamp", "container", "cpu_usage", "pid"])
                    csv_writer.writerows(records)
            
            if nginx_data:
                service_output_dir = os.path.join(output_dir, "nginx")
                os.makedirs(service_output_dir, exist_ok=True)
                nginx_csv_path = os.path.join(output_dir, "nginx", f"cpu_usage_output_nginx_it_{i}.csv")
                with open(nginx_csv_path, 'w', newline='') as nginx_file:
                    csv_writer = csv.writer(nginx_file)
                    csv_writer.writerow(["timestamp", "container", "cpu_usage", "pid"])
                    csv_writer.writerows(nginx_data)

# Perform Kruskal-Wallis test per container across iterations
for server in servers:
    if (server == "gl2"):
        server_name = 'GreenLab-STF'
    else:
        server_name = server
    for container_name in os.listdir(os.path.join(output_base_dir, server_name, "cpu_util_data_per_container")):
        container_dir = os.path.join(output_base_dir, server_name, "cpu_util_data_per_container", container_name)
        cpu_usage_across_iterations = []

        for i in range(1, 11): 
            csv_file_path = os.path.join(container_dir, f"cpu_usage_output_{container_name}_it_{i}.csv")
            if os.path.exists(csv_file_path):
                with open(csv_file_path, 'r') as csvfile:
                    csv_reader = csv.reader(csvfile)
                    next(csv_reader)
                    cpu_usage = [float(row[2]) for row in csv_reader]
                    cpu_usage_across_iterations.append(cpu_usage)
        
        # Perform Kruskal-Wallis test if data from all iterations is collected
        if len(cpu_usage_across_iterations) == 10:
            kruskal_result = kruskal(*cpu_usage_across_iterations)
            print(f"Kruskal-Wallis Test for Container: {container_name} on Server: {server}")
            print(f"P-value: {kruskal_result.pvalue}")
            print("-" * 40)

            with open(kruskal_wallis_csv_path, 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([server, container_name, kruskal_result.pvalue])

print("Kruskal-Wallis test results have been written successfully.")
