import json
import csv
import os
import glob
from datetime import datetime, timezone
import re

input_dir = '../../follow_users_final_run/1/power_consumption_data'
container_pid_mapping_csv_dir = '../../follow_users_final_run' 
output_base_dir = '../../follow_users_final_run/1/transformed_data/power_consumption_data_per_container'
os.makedirs(output_base_dir, exist_ok=True)

servers = ["gl2", "gl5", "gl6"]
containers_to_be_excluded = [
    'docker-compose', 'monitoring_prometheus', 'scaphandre', 'registry', 'nginx-web-server','media-frontend'
]
regex_pattern_to_filter_container_names = re.compile(r"^sn_([^\.]+)")

for server in servers:
    json_file_pattern = os.path.join(input_dir, f'per_container_power_consumption_{server}_*.json')
    json_files = glob.glob(json_file_pattern)
    if not json_files:
        print(f"No JSON files found for server {server}. Skipping...")
        continue
    
    output_dir = os.path.join(output_base_dir, server)
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
                elif custom_label == 'nginx_power_consumption':
                    filtered_container_name = 'nginx'
                else:
                    filtered_container_name = container_name
                
                # Ignore 'nginx-web-server'
                if filtered_container_name == 'nginx-web-server':
                    continue
                
                if custom_label == 'nginx_power_consumption':
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
            csv_file_path = os.path.join(output_dir, f"{service}.csv")
            with open(csv_file_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["timestamp", "container", "power_consumption", "pid"])
                csv_writer.writerows(records)
        
        if nginx_data:
            nginx_csv_path = os.path.join(output_dir, "nginx.csv")
            with open(nginx_csv_path, 'w', newline='') as nginx_file:
                csv_writer = csv.writer(nginx_file)
                csv_writer.writerow(["timestamp", "container", "power_consumption", "pid"])
                csv_writer.writerows(nginx_data)

print("CSV files created successfully for all servers.")