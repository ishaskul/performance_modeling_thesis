import os
import json
import glob
import csv
data_dir_name = "buy_books_final"

source_dir_path = f"../{data_dir_name}/1/service_time_data"
with open("buy-books-scenario-per-service-job-details.json", 'r') as json_file:
    jobs_per_service_data = json.load(json_file)

with open("./avg_service_time_details.csv", mode='w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["server", "service_name", "job", "avg_service_time"])

def process_scraped_data(scraped_data, service_name, job, server, csv_file_path):
    result = scraped_data.get("data", {}).get("result", [])
    values = result[0]["values"]
    
    # Filter out the "NaN" values and calculate the average of the valid numbers
    valid_values = [float(value[1]) for value in values if value[1] != "NaN" and value[1] != "+Inf"]
    
    if valid_values:
        avg_service_time = sum(valid_values) / len(valid_values)
    else:
        avg_service_time = 0 
    
    avg_service_time = round(avg_service_time, 4)

    with open(csv_file_path, mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([server, service_name, job, avg_service_time])

def calculate_avg_mysql_arrival_rate_for_msqlserver():
    file_pattern = "../buy_books_final/1/arrival_rates_data/scraped_arrival_rates_all_servers_*.json"
    matching_files = glob.glob(file_pattern)
    
    arrival_rate_data_path = matching_files[0]
    label = "mysql_server_arrival_rate"
    
    with open(arrival_rate_data_path, 'r') as json_file:
        arrival_data = json.load(json_file)
    
    results_array = arrival_data.get("data", {}).get("result", [])
    avg_arrival_rate = 0
    
    for result in results_array:
        if result.get("metric", {}).get("custom_label") == label:
            arrival_rates = result.get("values", [])
            valid_values = [float(rate[1]) for rate in arrival_rates if rate[1] != "NaN" and rate[1] != "+Inf"]
            
            if valid_values:
                avg_arrival_rate = sum(valid_values) / len(valid_values)
            break
    
    avg_arrival_rate = round(avg_arrival_rate, 4)
    print("my_sql_server_avg_arrival_rate: ", avg_arrival_rate)
    return avg_arrival_rate

def calculate_avg_mysql_cpu_utilization():
    file_pattern = "../buy_books_final/1/system_cpu_data/per_container_cpu_usage_gl2_*.json"
    matching_files = glob.glob(file_pattern)
    cpu_data_path = matching_files[0]  # Assuming you want the first matching file
    
    with open(cpu_data_path, 'r') as json_file:
        cpu_data = json.load(json_file)
    
    results_array = cpu_data.get("data", {}).get("result", [])
    avg_cpu_utilization = 0
    
    for result in results_array:
        cmdline = result.get("metric", {}).get("cmdline", "")
        if "mysqld" in cmdline:
            cpu_values = result.get("values", [])
            valid_values = [float(value[1]) for value in cpu_values if value[1] != "NaN" and value[1] != "+Inf"]
            
            if valid_values:
                avg_cpu_utilization = sum(valid_values) / len(valid_values)
            break
    
    avg_cpu_utilization = round(avg_cpu_utilization, 4)
    print("my_sql_server_avg_cpu_utilization: ", avg_cpu_utilization)
    return avg_cpu_utilization

def calculate_mysql_service_time(arrival_rate, cpu_utilization):
    service_time = cpu_utilization / arrival_rate
    with open("./avg_service_time_details.csv", mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["gl2", "mysqld", None, service_time])
    return round(service_time, 4)

def calculate_avg_arrival_rate_for_gateway_server():
    file_pattern = "../buy_books_final/1/arrival_rates_data/scraped_arrival_rates_all_servers_*.json"
    matching_files = glob.glob(file_pattern)
    
    arrival_rate_data_path = matching_files[0]
    gateway_server_address = "145.108.225.7:8765"
    
    with open(arrival_rate_data_path, 'r') as json_file:
        arrival_data = json.load(json_file)
    
    results_array = arrival_data.get("data", {}).get("result", [])
    avg_arrival_rate = 0
    
    for result in results_array:
        if result.get("metric", {}).get("instance") == gateway_server_address:
            arrival_rates = result.get("values", [])
            valid_values = [float(rate[1]) for rate in arrival_rates if rate[1] != "NaN" and rate[1] != "+Inf"]
            
            if valid_values:
                avg_arrival_rate = sum(valid_values) / len(valid_values)
            break
    
    avg_arrival_rate = round(avg_arrival_rate, 4)
    print("gateway_server_avg_arrival_rate: ", avg_arrival_rate)
    return avg_arrival_rate

def calculate_avg_gateway_server_cpu_utilization_per_replica():
    file_pattern = "../buy_books_final/1/system_cpu_data/per_container_cpu_usage_gl2_*.json"
    matching_files = glob.glob(file_pattern)
    cpu_data_path = matching_files[0]
    
    with open(cpu_data_path, 'r') as json_file:
        cpu_data = json.load(json_file)
    
    results_array = cpu_data.get("data", {}).get("result", [])
    avg_cpu_utilization = 0
    
    for result in results_array:
        cmdline = result.get("metric", {}).get("cmdline", "")
        if "gateway-server" in cmdline:
            cpu_values = result.get("values", [])
            valid_values = [float(value[1]) for value in cpu_values if value[1] != "NaN" and value[1] != "+Inf"]
            
            if valid_values:
                avg_cpu_utilization = sum(valid_values) / len(valid_values)
            break
    
    avg_cpu_utilization = round(avg_cpu_utilization, 4)
    print("my_sql_server_avg_cpu_utilization: ", avg_cpu_utilization)
    return avg_cpu_utilization

def calculate_avg_gateway_server_cpu_utilization_per_replica():
    file_pattern = "../buy_books_final/1/system_cpu_data/per_container_cpu_usage_gl2_*.json"
    matching_files = glob.glob(file_pattern)
    avg_cpu_util_per_replica = {}
    counter = 0

    for cpu_data_path in matching_files:
        with open(cpu_data_path, 'r') as json_file:
            cpu_data = json.load(json_file)

        results_array = cpu_data.get("data", {}).get("result", [])

        for result in results_array:
            cmdline = result.get("metric", {}).get("cmdline", "")
            if "gateway-server" in cmdline:
                pid = result.get("metric", {}).get("pid")
                cpu_values = result.get("values", [])
                valid_values = [float(value[1]) for value in cpu_values if value[1] != "NaN" and value[1] != "+Inf"]

                if valid_values:
                    avg_cpu_utilization = sum(valid_values) / len(valid_values)
                    avg_cpu_utilization = round(avg_cpu_utilization, 4)
                    counter += 1  # Increment counter after finding a valid replica
                    avg_cpu_util_per_replica[f"gateway-server_replica_{counter}"] = {
                        "pid": pid,
                        "avg_cpu_util": avg_cpu_utilization
                    }

    print("avg_cpu_util_per_replica: ", avg_cpu_util_per_replica)
    return avg_cpu_util_per_replica

def calculate_service_times_for_gateway_server_replicas(arrival_rate_for_api_gateway, cpu_utilization_dict):
    arrival_rate_per_replica = arrival_rate_for_api_gateway / 3
    service_times = {}

    for replica_name, replica_data in cpu_utilization_dict.items():
        cpu_utilization = replica_data['avg_cpu_util']
        service_time = cpu_utilization / arrival_rate_per_replica 
        service_times[replica_name] = round(service_time, 4)

        with open("./avg_service_time_details.csv", mode='a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['gl2', replica_name, None, service_time])

    return service_times

servers = ["gl2", "gl5", "gl6"]
for server in servers:
    server_dir_path = os.path.join(source_dir_path, server)
                        
    # Iterate over services in service_details JSON
    for service_name, service_info in jobs_per_service_data.items():
        port_number = service_info.get("port_number")
        jobs = service_info.get("jobs", [])
                        
        for job in jobs:
            #print(f"  - {job}")
            scraped_job_data_path = os.path.join(server_dir_path, f"{service_name}_{job}_*.json")
            scraped_job_data_for_specific_job = glob.glob(scraped_job_data_path)
            file_path = scraped_job_data_for_specific_job[0]
            with open(file_path, 'r') as file:
                 scraped_data = json.load(file)
                 process_scraped_data(scraped_data, service_name, job, server, "./avg_service_time_details.csv")

calculate_mysql_service_time(calculate_avg_mysql_arrival_rate_for_msqlserver(), calculate_avg_mysql_cpu_utilization())
arrival_rate_for_api_gateway = calculate_avg_arrival_rate_for_gateway_server()
avg_cpu_utilization_per_replica = calculate_avg_gateway_server_cpu_utilization_per_replica()
calculate_service_times_for_gateway_server_replicas(arrival_rate_for_api_gateway, avg_cpu_utilization_per_replica)