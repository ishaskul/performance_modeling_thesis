import json
import csv
import os
import glob
from datetime import datetime

input_dir = '../../buy_books_final/1/power_consumption_data'
output_base_dir = '../../buy_books_final/1/transformed_data/power_consumption_data_per_container'

os.makedirs(output_base_dir, exist_ok=True)

relevant_services = [
    "account-service", "billing-service", "catalog-service",
    "payment-service", "order-service", "gateway-server","mysqld"
]

servers = ["gl2", "gl5", "gl6"]

for server in servers:
    json_file_pattern = os.path.join(input_dir, f'per_container_power_consumption_{server}_*.json')
    json_files = glob.glob(json_file_pattern)
    
    for json_file_path in json_files:
        output_dir = os.path.join(output_base_dir, server)
        os.makedirs(output_dir, exist_ok=True)
        
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        service_data = {}
        gateway_server_counter = 1

        for result in data["data"]["result"]:
            cmdline = result["metric"].get("cmdline", "")
            
            for service in relevant_services:
                if service in cmdline:
                    # Special handling for gateway-server
                    if service == "gateway-server":
                        container_name = f"gateway-server_replica_{gateway_server_counter}"
                        gateway_server_counter += 1
                    elif service == "docker-entrypoint.sh":
                        container_name = "mysqld"
                    else:
                        container_name = service
                    
                    if container_name not in service_data:
                        service_data[container_name] = []
                    
                    for timestamp, value in result["values"]:
                        # Convert timestamp (epoch) to the desired format
                        formatted_timestamp = datetime.utcfromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                        service_data[container_name].append([formatted_timestamp, container_name, float(value), result["metric"]["pid"]])
                    break

        for service, records in service_data.items():
            csv_file_path = os.path.join(output_dir, f"{service}.csv")
            with open(csv_file_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["timestamp", "container", "power_consumption", "pid"])
                csv_writer.writerows(records)

print("CSV files created successfully for all servers.")