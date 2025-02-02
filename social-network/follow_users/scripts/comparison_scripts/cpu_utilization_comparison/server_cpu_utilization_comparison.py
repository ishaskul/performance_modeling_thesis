import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np
import os

server_cpu_utilization_path = './social-network/follow_users/follow_users_final_run/1/transformed_data/server_level_res_utilization_data'
estimated_data_path = './social-network/follow_users/estimations/estimated_cpu_data'
output_dir = './social-network/follow_users/estimations/plots/cpu_comparison_plots'
errors_csv_path = f'{estimated_data_path}/cpu_utilization_error_metrics.csv'

os.makedirs(output_dir, exist_ok=True)

error_log = []

servers = ['gl2', 'gl5', 'gl6']
for server in servers:
    if(server == 'gl2'):
          server_name = 'GreenLab-STF'
    else:
          server_name = server
    actual_data_path = f"{server_cpu_utilization_path}/{server_name}/system_cpu_data/cpu_usage_output_{server_name}_it_1.csv"
    cpu_data = pd.read_csv(actual_data_path)
    cpu_data['Time'] = pd.to_datetime(cpu_data['Time'], format='%H:%M:%S', errors='coerce').dt.time
    cpu_data = cpu_data.dropna(subset=['Time'])
    cpu_data['time_sec'] = (pd.to_timedelta(cpu_data['Time'].apply(str)) - pd.to_timedelta(str(cpu_data['Time'].iloc[0]))).dt.total_seconds()
    cpu_data['interval'] = (cpu_data['time_sec'] // 15) * 15
    grouped = cpu_data.groupby('interval')['cpu_utilization'].mean().reset_index()
    grouped.columns = ['Time (s)', 'CPU Utilization (%)']

    estimated_data_path_container = f"{estimated_data_path}/{server}/aggregated_cpu_utilization.csv"
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
                'Container': '',
                'Mean Squared Error': mse,
                'Root Mean Squared Error': rmse,
                'Mean Absolute Error': mae
            })

    plt.figure(figsize=(10, 6))
    plt.plot(grouped['Time (s)'], grouped['CPU Utilization (%)'], label='Actual CPU Utilization', marker='o')
    plt.plot(estimated_cpu_data['Time (s)'], estimated_cpu_data['CPU Utilization (%)'], label='Estimated CPU Utilization', color='red')
    plt.xlabel('Time (s)')
    plt.ylabel('CPU Utilization (%)')
    plt.title(f'Server CPU Utilization: Actual vs. Estimated {server}')
    plt.legend()
    plt.grid(True)

    plot_file_name = f"{output_dir}/{server}_cpu_comparison.png"
    plt.savefig(plot_file_name)
    plt.close()

    print(f"Metrics for {server}")
    print(f'Mean Squared Error: {mse}')
    print(f'Root Mean Squared Error: {rmse}')
    print(f'Mean Absolute Error: {mae}')
    print("-" * 50)

error_log_df = pd.DataFrame(error_log)
csv_file_path = f"{estimated_data_path}/cpu_utilization_error_metrics.csv"
error_log_df.to_csv(csv_file_path, mode='a', header=not os.path.exists(csv_file_path), index=False)
print(f"Error metrics saved to {csv_file_path}")