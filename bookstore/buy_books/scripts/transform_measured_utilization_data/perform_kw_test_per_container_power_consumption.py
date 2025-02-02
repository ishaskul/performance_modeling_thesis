import json
import csv
import os
import glob
from datetime import datetime
from scipy.stats import kruskal

input_base_dir = '../../buy_books_final'
output_base_dir = '../../buy_books_final/transformed_data_kw_test'


os.makedirs(output_base_dir, exist_ok=True)


relevant_services = [
    "account-service", "billing-service", "catalog-service",
    "payment-service", "order-service", "gateway-server", "mysqld"
]


servers = ["gl2", "gl5", "gl6"]


for i in range(1, 4):  
    for server in servers:
        input_dir = os.path.join(input_base_dir, str(i), "power_consumption_data")
        json_file_pattern = os.path.join(input_dir, f'per_container_power_consumption_{server}_*.json')
        json_files = glob.glob(json_file_pattern)

        for json_file_path in json_files:
            if(server == "gl2"):
                server_nam = "GreenLab-STF"
            else:
                server_nam = server
            output_dir = os.path.join(output_base_dir, server_nam, f"power_consumption_data_per_container")
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
                        
                        # Initialize service data if not already
                        if container_name not in service_data:
                            service_data[container_name] = []
                        for timestamp, value in result["values"]:
                            # Convert timestamp (epoch) to the desired format
                            formatted_timestamp = datetime.utcfromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                            service_data[container_name].append([formatted_timestamp, container_name, float(value), result["metric"]["pid"]])
                        break

            for container_name, records in service_data.items():
                if(server == "gl2"):
                    server_name = "GreenLab-STF"
                else:
                    server_name = server
                outputPathForPerContainerCSVs = os.path.join(output_base_dir, server_name, "power_consumption_data_per_container", container_name)
                os.makedirs(outputPathForPerContainerCSVs, exist_ok=True)

                csv_file_path = os.path.join(outputPathForPerContainerCSVs, f"power_consumption_output_{container_name}_it_{i}.csv")
                with open(csv_file_path, 'w', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow(["timestamp", "container", "power_consumption", "pid"])
                    csv_writer.writerows(records)


green_lab_machines = ['GreenLab-STF', 'gl5', 'gl6']
# performing KW test
kruskal_wallis_csv_path = os.path.join(output_base_dir, 'kruskal_wallis_test_results_power_consumption.csv')
for server in green_lab_machines:
    for container_name in os.listdir(os.path.join(output_base_dir, server, "power_consumption_data_per_container")):
        container_dir = os.path.join(output_base_dir, server, "power_consumption_data_per_container", container_name)
        power_consumption_across_iterations = []

        # Collect data from every iteration
        for i in range(1, 4):
            csv_file_path = os.path.join(container_dir, f"power_consumption_output_{container_name}_it_{i}.csv")
            if os.path.exists(csv_file_path):
                with open(csv_file_path, 'r') as csvfile:
                    csv_reader = csv.reader(csvfile)
                    next(csv_reader)  # Skip the header row
                    power_consumption = [float(row[2]) for row in csv_reader]
                    power_consumption_across_iterations.append(power_consumption)
        
        if len(power_consumption_across_iterations) == 3: 
            kruskal_result = kruskal(*power_consumption_across_iterations)
            print(f"Kruskal-Wallis Test for Container: {container_name} on Server: {server}")
            print(f"P-value: {kruskal_result.pvalue}")
            print("-" * 40)
            with open(kruskal_wallis_csv_path, 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([server, container_name, kruskal_result.pvalue])

print("Kruskal-Wallis Test performed successfully for all containers and servers.")
