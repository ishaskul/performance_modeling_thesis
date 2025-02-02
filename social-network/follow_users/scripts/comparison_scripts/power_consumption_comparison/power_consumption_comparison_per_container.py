import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np
import os

power_consumption_data_path = '../../../follow_users_final_run/1/transformed_data/power_consumption_data_per_container'
estimated_data_path = '../../../estimations/estimated_power_consumption'
output_dir = '../../../estimations/plots/power_consumption_comparison_plots'
os.makedirs(output_dir, exist_ok=True)
servers = ['gl2', 'gl5', 'gl6']
containers = [
    'home-timeline-redis', 'nginx', 'post-storage-memcached', 'url-shorten-mongodb',
    'user-mongodb', 'user-service', 'user-timeline-redis', 'user-timeline-service',
    'cassandra','compose-post-service','home-timeline-service','jaeger-agent','media-memcached',
    'media-mongodb','post-storage-mongodb','post-storage-service','social-graph-service','url-shorten-service'
    ,'user-memcached','jaeger-collector','jaeger-query','media-service','social-graph-mongodb','social-graph-redis'
    ,'text-service','unique-id-service','url-shorten-memcached','user-mention-service','user-timeline-mongodb'
]
error = []


for server in servers:
    for container in containers:
        try:
            actual_data_path = f"{power_consumption_data_path}/{server}/{container}.csv"
            if not os.path.exists(actual_data_path):
                continue

            actual_data = pd.read_csv(actual_data_path)
            actual_data['timestamp'] = pd.to_datetime(actual_data['timestamp'], errors='coerce')
            actual_data = actual_data.dropna(subset=['timestamp'])
            actual_data['time_sec'] = (actual_data['timestamp'] - actual_data['timestamp'].iloc[0]).dt.total_seconds()
            actual_data['interval'] = (actual_data['time_sec'] // 15) * 15
            actual_grouped = actual_data.groupby('interval')['power_consumption'].mean().reset_index()
            actual_grouped.columns = ['Time (s)', 'power_consumption']

            estimated_data_path_container = f"{estimated_data_path}/{server}/{container}.csv"
            if not os.path.exists(estimated_data_path_container):
                continue

            estimated_data = pd.read_csv(estimated_data_path_container)
            max_time_actual = actual_grouped['Time (s)'].max()
            max_time_estimated = estimated_data['Time (s)'].max()
            max_time = min(max_time_actual, max_time_estimated)
            actual_grouped = actual_grouped[actual_grouped['Time (s)'] <= max_time]
            estimated_data = estimated_data[estimated_data['Time (s)'] <= max_time]

            merged_data = pd.merge(actual_grouped, estimated_data, on='Time (s)', suffixes=('_actual', '_estimated'))

            mse = mean_squared_error(merged_data['power_consumption_actual'], merged_data['power_consumption_estimated'])
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(merged_data['power_consumption_actual'], merged_data['power_consumption_estimated'])

            plt.figure(figsize=(10, 6))
            plt.plot(merged_data['Time (s)'], merged_data['power_consumption_actual'], label='Actual Power Consumption', marker='o')
            plt.plot(merged_data['Time (s)'], merged_data['power_consumption_estimated'], label='Estimated Power Consumption', color='green')
            plt.xlabel('Time (s)')
            plt.ylabel('Power Consumption (W)')
            plt.title(f'Power Consumption: Actual vs. Estimated {server} - {container}')
            plt.legend()
            plt.grid(True)

            plot_file_name = f"{output_dir}/{server}_{container}_power_consumption_comparison.png"
            plt.savefig(plot_file_name)
            plt.close()

            print(f"Metrics for {server} - {container}:")
            print(f'Mean Squared Error: {mse}')
            print(f'Root Mean Squared Error: {rmse}')
            print(f'Mean Absolute Error: {mae}')
            print("-" * 50)
            
            error.append({
                'server': server,
                'container': container,
                'MSE': mse,
                'RMSE': rmse,
                'MAE': mae
            })

        except Exception as e:
            print(f"Error processing {server}/{container}: {e}")

error_log_df = pd.DataFrame(error)
error_log_df.to_csv(f"{estimated_data_path}/power_consumption_error_metrics.csv", index=False)