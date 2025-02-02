import numpy as np
import matplotlib.pyplot as plt
import csv
import json
import os
from collections import deque
import math
import pandas as pd
from server_ctmc import CTMCCPUUtilizationSimulator
import argparse
from scipy.stats import pearsonr
import re

class CPUSimulation:
    def __init__(self, duration, idle_time, ramp_up_duration, burst_duration, burst_arrival_rate, steady_arrival_rate, service_time_range, num_cores, jobs, time_step, max_service_time_variation, container_name, idling_arrival_rate):
        self.duration = duration
        self.idle_time = idle_time
        self.ramp_up_duration = ramp_up_duration
        self.burst_duration = burst_duration
        self.burst_arrival_rate = burst_arrival_rate
        self.steady_arrival_rate = steady_arrival_rate
        self.service_time_range = service_time_range
        self.num_cores = num_cores
        self.time_step = time_step
        self.time_points = int(duration / time_step)
        self.time = np.arange(0, duration, time_step)
        self.cpu_utilization = np.zeros(self.time_points)
        self.queue = deque()
        self.jobs = jobs
        self.max_service_time_variation = max_service_time_variation
        self.decay_time = decay_time
        self.container_name = container_name
        self.idling_arrival_rate = idling_arrival_rate
    
    #Simulate CPU utilization for a Docker container with explicit queuing behavior.
    def simulate(self):
        for t in range(self.time_points):
            # Current arrival rate is varied on the basis of the performance test scenario
            if t < self.idle_time:
                current_arrival_rate = idling_arrival_rate
            elif t < self.idle_time + self.burst_duration:
                current_arrival_rate = self.burst_arrival_rate
            elif t < self.idle_time + self.burst_duration + self.ramp_up_duration:
                current_arrival_rate = self.steady_arrival_rate
            else:
                # Gradually tapering off arrival rate instead of abruptly cutting to zero using an exponential distribution
                decay_rate = self.decay_time
                current_arrival_rate = max(
                0,
                self.steady_arrival_rate * math.exp(-decay_rate * (t - (self.idle_time + self.burst_duration + self.ramp_up_duration)))
                )

            # Generate arrivals using Poisson distribution
            arrivals = np.random.poisson(current_arrival_rate * self.time_step)
            for _ in range(arrivals):
                if self.jobs:
                    for container_job in self.jobs.values():
                        avg_service_time = float(container_job['avg_service_time'])
                        api_call_count = int(container_job['api_call_count'])
                        job_service_time = avg_service_time * api_call_count
                        raw_service_time = np.random.exponential(job_service_time)
                        variation_factor = np.random.uniform(1 - self.max_service_time_variation, 1 + self.max_service_time_variation)
                        raw_service_time *= variation_factor
                        self.queue.append(raw_service_time)
                else:
                    service_time = np.random.uniform(*self.service_time_range)
                    self.queue.append(service_time)

            # Process jobs in the queue
            for _ in range(self.num_cores):
                if self.queue:
                    job = self.queue.popleft()
                    if job > self.time_step:
                        remaining_service_time = job - self.time_step
                        self.queue.appendleft(remaining_service_time)
                        self.cpu_utilization[t] += self.time_step / self.num_cores
                    else:
                        self.cpu_utilization[t] += job / self.num_cores

        # Clip CPU utilization to range [0, 100] to avoid unrealistic values
        self.cpu_utilization = np.clip(self.cpu_utilization * 100, 0, 100)
        return self.time, self.cpu_utilization

    def aggregate_and_save_to_csv(self, time, data, interval, file_name):
        """
        Aggregate the data and save it to a CSV file.
        """
        aggregated_time = []
        aggregated_data = []
        for i in range(0, len(time), interval):
            aggregated_time.append(time[i])
            aggregated_data.append(np.mean(data[i:i + interval]))

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_name), exist_ok=True)

        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time (s)', 'CPU Utilization (%)'])
            writer.writerows(zip(aggregated_time, aggregated_data))

        return np.array(aggregated_time), np.array(aggregated_data)

    def plot(self, aggregated_time, aggregated_cpu_utilization, plot_file_name):
        """
        Plot the CPU utilization over time and save to the file.
        """
        plt.figure(figsize=(10, 5))
        plt.plot(aggregated_time, aggregated_cpu_utilization, label='CPU Utilization', color='blue')
        plt.axhline(100, color='red', linestyle='--', label='Max Utilization (100%)')
        plt.title('CPU Utilization of a Docker Container (With Idle Time, Burst Mode, and Cooldown)')
        plt.xlabel('Time (s)')
        plt.ylabel('CPU Utilization (%)')
        plt.ylim(0, max(aggregated_cpu_utilization) * 1.2)
        plt.legend()
        plt.grid()
        plt.tight_layout()

        # Save the plot to the file
        plt.savefig(plot_file_name)
        plt.close()

def aggregate_server_cpu_utilization(base_dir, servers):
    aggregated_data = {}

    for server in servers:
        server_dir = os.path.join(base_dir, server)
        if not os.path.exists(server_dir):
            print(f"Directory {server_dir} does not exist. Skipping.")
            continue

        server_cpu_data = None

        # Iterate over all CSV files in the server directory
        for csv_file in os.listdir(server_dir):
            if csv_file.endswith('.csv'):
                csv_path = os.path.join(server_dir, csv_file)
                container_data = pd.read_csv(csv_path)

                # Check if this is the first container's data being added
                if server_cpu_data is None:
                    server_cpu_data = container_data.copy()
                else:
                    server_cpu_data = server_cpu_data.merge(
                        container_data, on="Time (s)", how="outer", suffixes=('', '_other')
                    ).fillna(0)
                    server_cpu_data['CPU Utilization (%)'] += server_cpu_data.pop('CPU Utilization (%)_other')

        if server_cpu_data is not None:
            server_cpu_data['CPU Utilization (%)'] = server_cpu_data['CPU Utilization (%)'].clip(upper=100) #capping cpu utilization to a maximum of 100%
            aggregated_data[server] = server_cpu_data
            aggregated_csv_path = os.path.join(base_dir, f"{server}/aggregated_cpu_utilization.csv")
            server_cpu_data.to_csv(aggregated_csv_path, index=False)

    return aggregated_data

def plot_server_cpu_utilization(base_dir, servers):
    plt.figure(figsize=(12, 6))
    
    for server in servers:
        file_path = f"{base_dir}/{server}/aggregated_cpu_utilization.csv"
        data = pd.read_csv(file_path)
        plt.plot(data['Time (s)'], data['CPU Utilization (%)'], label=f"{server}", linewidth=1.5)
    
    plt.ylim(0, 110)
    plt.yticks(range(0, 111, 10))
    plt.title("CPU Utilization for Servers", fontsize=14, weight='bold')
    plt.xlabel("Time (s)", fontsize=12)
    plt.ylabel("CPU Utilization (%)", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{base_dir}/cpu_utilization_plot.png", dpi=300)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Accept arguments")
    parser.add_argument('--app', type=str, required=True, help="Name of the app for which you are running the experiment")
    parser.add_argument('--scenario_name', type=str, required=True, help="Name of the scenario that you are executing")
        
    return parser.parse_args()

args = parse_arguments()
app = args.app
scenario_name = args.scenario_name

with open(f'./{app}/{scenario_name}/model-config.json', 'r') as f:
    containers_config = json.load(f)

simulations = {}

for server, containers in containers_config.items():
    for container, container_data in containers.items():
        if container == 'p_idle' or container == 'p_max' or container == 'ctmc_transition_matrix' or container == 'ctmc_service_time_overhead_ranges' or  container == 'duration' or container == 'idle_time' or container == 'ramp_up_duration' or container == 'burst_duration' or container == 'burst_arrival_rate' or container == 'steady_arrival_rate'  or container == 'cpu_utilization_when_idle' or container == 'num_cores' or container == 'alpha' or container == 'beta':
            continue
        # Extracting from model config file
        duration = container_data['duration']
        idle_time = container_data['idle_time']
        ramp_up_duration = container_data['ramp_up_duration']
        burst_duration = container_data['burst_duration']
        burst_arrival_rate = container_data['burst_arrival_rate']
        steady_arrival_rate = container_data['steady_arrival_rate']
        service_time_range = container_data['service_time_range']
        num_cores = containers_config[server]['num_cores']
        time_step = container_data.get('time_step', 1)
        jobs = container_data.get('jobs', {})
        max_service_time_variation = container_data['max_service_time_variation']
        decay_time = container_data['decay_time']
        idling_arrival_rate = container_data.get('idling_arrival_rate', 0)
        simulations[container] = CPUSimulation(
            duration + 1, idle_time, ramp_up_duration, burst_duration, burst_arrival_rate, steady_arrival_rate,
            service_time_range, num_cores, jobs, time_step, max_service_time_variation, container, idling_arrival_rate
        )

        # Run queuing network simulation
        time, cpu_utilization = simulations[container].simulate() 

        # Aggregate data and save to CSV
        aggregation_interval = 15
        csv_file_name = f"{app}/{scenario_name}/estimations/estimated_cpu_data/{server}/{container}.csv"
        aggregated_time, aggregated_cpu_utilization = simulations[container].aggregate_and_save_to_csv(time, cpu_utilization, aggregation_interval, csv_file_name)

        # Plot the results
        plot_file_name = f"{app}/{scenario_name}/estimations/estimated_cpu_data/{server}/{container}_cpu_utilization.png"
        simulations[container].plot(aggregated_time, aggregated_cpu_utilization, plot_file_name)

def estimate_per_container_power_consumption(estimated_cpu_data, containers_config, output_dir):
    correlation_results = []
    
    for server, containers in containers_config.items():
        server_dir = os.path.join(estimated_cpu_data, server)
        server_output_dir = os.path.join(output_dir, server)
        os.makedirs(server_output_dir, exist_ok=True)
        
        for container, container_data in containers.items():
            if container in ['p_idle', 'p_max', 'ctmc_transition_matrix', 'ctmc_service_time_overhead_ranges', 
                             'duration', 'idle_time', 'ramp_up_duration', 'burst_duration', 
                             'burst_arrival_rate', 'steady_arrival_rate', 'cpu_utilization_when_idle', 
                             'num_cores','alpha','beta']:
                continue
            
            container_file = os.path.join(server_dir, f"{container}.csv")
            df = pd.read_csv(container_file)
            p_idle = container_data['p_idle']
            p_max = containers_config[server]['p_max']
            
            # Calculate power consumption
            df['power_consumption'] = p_idle + (p_max - p_idle) * (df['CPU Utilization (%)'] / 100)
            
            output_file = os.path.join(server_output_dir, f"{container}.csv")
            df_output = df[['Time (s)', 'CPU Utilization (%)', 'power_consumption']].copy()
            df_output.to_csv(output_file, index=False)
            
            pearson_coefficient, p_value = pearsonr(df_output['CPU Utilization (%)'], df_output['power_consumption'])
            correlation_results.append({
                'Server': server,
                'Container': container,
                'Pearson_Coefficient': pearson_coefficient,
                'P-Value': p_value
            })
            
            # Plot power consumption
            aggregated_time = df_output['Time (s)'].values
            aggregated_power_consumption = df_output['power_consumption'].values
            plt.figure(figsize=(10, 5))
            plt.plot(aggregated_time, aggregated_power_consumption, label='Power Consumption', color='green')
            plt.title(f'Power Consumption of {container}')
            plt.xlabel('Time (s)')
            plt.ylabel('Power Consumption (W)')
            plt.grid()
            plt.tight_layout()
            plot_file_name = os.path.join(server_output_dir, f"{container}_power_consumption.png")
            plt.savefig(plot_file_name)
            plt.close()
    
    correlation_df = pd.DataFrame(correlation_results)
    correlation_file = os.path.join(output_dir, 'cpu_power_correlation_results.csv')
    correlation_df.to_csv(correlation_file, index=False)

def estimate_power_consumption_over_all_servers_over_time(estimated_cpu_data_dir, containers_config, output_dir):
    correlation_results_file = os.path.join(output_dir, "cpu_power_correlation_results.csv")
    correlation_results = []
    currently_executing_scenario = re.search(r"/([^/]+)/estimations/estimated_cpu_data$", estimated_cpu_data_dir)
    for server, containers in containers_config.items():
        server_dir = os.path.join(estimated_cpu_data_dir, server)
        server_output_dir = os.path.join(output_dir, server)
        os.makedirs(server_output_dir, exist_ok=True)
        server_cpu_utilization_file = os.path.join(server_dir, f"refined_cpu_utilization_{server}.csv")
        df = pd.read_csv(server_cpu_utilization_file)
        p_idle = containers_config[server]['p_idle']
        p_max = containers_config[server]['p_max']
        if (scenario_name in ['follow_users','buy_books'] and server in ['gl5','gl6']):
            print("In non-linear")
            alpha = containers_config[server]['alpha']
            beta = containers_config[server]['beta']
            df['power_consumption'] = p_idle + (p_max - p_idle) * alpha * (df['refined_cpu'] / 100) ** beta
        else:    
            df['power_consumption'] = p_idle + (p_max - p_idle) * (df['refined_cpu'] / 100)
        output_file = os.path.join(server_output_dir, f"estimated_server_power_consumption.csv")
        df_output = df[['Time (s)', 'power_consumption']].copy()
        df_output.to_csv(output_file, index=False)
        pearson_coefficient, p_value = pearsonr(df['refined_cpu'], df['power_consumption'])
        correlation_results.append({
            "Server": server,
            "Container": "",
            "Pearson_Coefficient": pearson_coefficient,
            "P-Value": p_value
        })
    
    correlation_df = pd.DataFrame(correlation_results)
    correlation_df.to_csv(correlation_results_file, mode='a', header=False, index=False)

def plot_server_power_consumption(base_dir, servers):
    plt.figure(figsize=(12, 6))
    
    for server in servers:
        file_path = f"{base_dir}/{server}/estimated_server_power_consumption.csv"
        data = pd.read_csv(file_path)
        plt.plot(data['Time (s)'], data['power_consumption'], label=f"{server}", linewidth=1.5)
    
    plt.title("Power Consumption Across All Servers Over Time", fontsize=14, weight='bold')
    plt.xlabel("Time (s)", fontsize=12)
    plt.ylabel("Power Consumption (W)", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{base_dir}/power_consumption_plot.png", dpi=300)

def run_ctmc():
    for server, containers in containers_config.items():
        transition_matrix = np.array(containers_config[server]["ctmc_transition_matrix"])
        service_time_overhead_ranges = [tuple(range_pair) for range_pair in containers_config[server]["ctmc_service_time_overhead_ranges"]] 
        no_of_cores = containers_config[server]["num_cores"]

        simulate_per_server_cpu_utilization_overhead = CTMCCPUUtilizationSimulator(
        transition_matrix, service_time_overhead_ranges, no_of_cores
        )
        
        refined_server_cpu_utilization = simulate_per_server_cpu_utilization_overhead.refine_cpu_utilization(
        f"./{app}/{scenario_name}/estimations/estimated_cpu_data/{server}/aggregated_cpu_utilization.csv", 
        duration=containers_config[server]["duration"], 
        idle_time=containers_config[server]["idle_time"], 
        ramp_up_duration=containers_config[server]["ramp_up_duration"],
        burst_duration=containers_config[server]["burst_duration"], 
        burst_arrival_rate=containers_config[server]["burst_arrival_rate"], 
        steady_arrival_rate=containers_config[server]["steady_arrival_rate"],
        cpu_utilization_when_idle = containers_config[server]["cpu_utilization_when_idle"],
         )
        refined_server_cpu_utilization.to_csv(f"./{app}/{scenario_name}/estimations/estimated_cpu_data/{server}/refined_cpu_utilization_{server}.csv", index=False)
        #print(refined_server_cpu_utilization.head())

base_dir = f"./{app}/{scenario_name}/estimations/estimated_cpu_data"
servers = ['gl2', 'gl5', 'gl6']
aggregated_server_data = aggregate_server_cpu_utilization(base_dir, servers)
plot_server_cpu_utilization(base_dir, servers)
run_ctmc()
estimate_per_container_power_consumption(base_dir, containers_config, f"./{app}/{scenario_name}/estimations/estimated_power_consumption")
estimate_power_consumption_over_all_servers_over_time(base_dir, containers_config, f"./{app}/{scenario_name}/estimations/estimated_power_consumption" )
plot_server_power_consumption(f"./{app}/{scenario_name}/estimations/estimated_power_consumption", servers)