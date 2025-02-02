import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np
import os

cpu_data_path = './social-network/compose_posts/compose_posts/1/transformed_data/cpu_util_data_per_container'
estimated_data_path = './social-network/compose_posts/estimations/estimated_cpu_data'
output_dir = './social-network/compose_posts/estimations/plots/cpu_comparison_plots'

os.makedirs(output_dir, exist_ok=True)

error_log = []

servers = ['gl2', 'gl5', 'gl6']
containers = [
    'home-timeline-redis', 'nginx', 'post-storage-memcached', 'url-shorten-mongodb',
    'user-mongodb', 'user-service', 'user-timeline-redis', 'user-timeline-service',
    'cassandra','compose-post-service','home-timeline-service','jaeger-agent','media-memcached',
    'media-mongodb','post-storage-mongodb','post-storage-service','social-graph-service','url-shorten-service'
    ,'user-memcached','jaeger-collector','jaeger-query','media-service','social-graph-mongodb','social-graph-redis'
    ,'text-service','unique-id-service','url-shorten-memcached','user-mention-service','user-timeline-mongodb'
]

# Loop through each server and container
for server in servers:
    for container in containers:
        try:
            actual_data_path = f"{cpu_data_path}/{server}/{container}.csv"
            if not os.path.exists(actual_data_path):
                continue 

            cpu_data = pd.read_csv(actual_data_path)

            # Ensure 'timestamp' column is datetime
            cpu_data['timestamp'] = pd.to_datetime(cpu_data['timestamp'], errors='coerce')

            cpu_data = cpu_data.dropna(subset=['timestamp'])
            cpu_data['time_sec'] = (cpu_data['timestamp'] - cpu_data['timestamp'].iloc[0]).dt.total_seconds()
            
            # Group into 15-second intervals
            cpu_data['interval'] = (cpu_data['time_sec'] // 15) * 15
            grouped = cpu_data.groupby('interval')['cpu_usage'].mean().reset_index()
            grouped.columns = ['Time (s)', 'CPU Utilization (%)']

            estimated_data_path_container = f"{estimated_data_path}/{server}/{container}.csv"
            if not os.path.exists(estimated_data_path_container):
                print(f"Warning: Estimated data file for {server}/{container} not found at {estimated_data_path_container}")
                continue

            estimated_cpu_data = pd.read_csv(estimated_data_path_container)

            max_time_actual = grouped['Time (s)'].max()
            max_time_estimated = estimated_cpu_data['Time (s)'].max()
            max_time = min(max_time_actual, max_time_estimated)

            grouped = grouped[grouped['Time (s)'] <= max_time]
            estimated_cpu_data = estimated_cpu_data[estimated_cpu_data['Time (s)'] <= max_time]

            merged_data = pd.merge(grouped, estimated_cpu_data, on='Time (s)', suffixes=('_actual', '_estimated'))

            mse = mean_squared_error(merged_data['CPU Utilization (%)_actual'], merged_data['CPU Utilization (%)_estimated'])
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(merged_data['CPU Utilization (%)_actual'], merged_data['CPU Utilization (%)_estimated'])

            error_log.append({
                'Server': server,
                'Container': container,
                'Mean Squared Error': mse,
                'Root Mean Squared Error': rmse,
                'Mean Absolute Error': mae
            })

            # Plot the comparison
            plt.figure(figsize=(10, 6))
            plt.plot(grouped['Time (s)'], grouped['CPU Utilization (%)'], label='Actual CPU Utilization', marker='o')
            plt.plot(estimated_cpu_data['Time (s)'], estimated_cpu_data['CPU Utilization (%)'], label='Estimated CPU Utilization', color='red')
            plt.xlabel('Time (s)')
            plt.ylabel('CPU Utilization (%)')
            plt.title(f'CPU Utilization: Actual vs. Estimated {server} - {container}')
            plt.legend()
            plt.grid(True)

            plot_file_name = f"{output_dir}/{server}_{container}_cpu_comparison.png"
            plt.savefig(plot_file_name)
            plt.close()

            print(f"Metrics for {server} - {container}:")
            print(f'Mean Squared Error: {mse}')
            print(f'Root Mean Squared Error: {rmse}')
            print(f'Mean Absolute Error: {mae}')
            print("-" * 50)

        except Exception as e:
            print(f"Error processing {server}/{container}: {e}")

error_log_df = pd.DataFrame(error_log)
csv_file_path = f"{estimated_data_path}/cpu_utilization_error_metrics.csv"
error_log_df.to_csv(csv_file_path, index=False)

print(f"Error metrics saved to {csv_file_path}")
