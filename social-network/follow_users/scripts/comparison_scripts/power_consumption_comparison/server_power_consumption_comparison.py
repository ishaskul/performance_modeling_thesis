import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np
import os

server_utilization_path = './social-network/follow_users/follow_users_final_run/1/transformed_data/server_level_res_utilization_data'
estimated_data_path = './social-network/follow_users/estimations/estimated_power_consumption'
output_dir = './social-network/follow_users/estimations/plots/power_consumption_comparison_plots'

os.makedirs(output_dir, exist_ok=True)

servers = ['gl2', 'gl5', 'gl6']

error_log = []

for server in servers:
    if server == 'gl2':
        server_name = 'GreenLab-STF'
    else:
        server_name = server

    actual_data_path = f"{server_utilization_path}/{server_name}/power_consumption_data/power_consumption_output_{server_name}_it_1.csv"
    power_consumption_data = pd.read_csv(actual_data_path)
    power_consumption_data['Time'] = pd.to_datetime(
        power_consumption_data['Time'], format='%H:%M:%S', errors='coerce'
    ).dt.time
    power_consumption_data = power_consumption_data.dropna(subset=['Time'])
    power_consumption_data['time_sec'] = (
        pd.to_timedelta(power_consumption_data['Time'].apply(str))
        - pd.to_timedelta(str(power_consumption_data['Time'].iloc[0]))
    ).dt.total_seconds()
    power_consumption_data['interval'] = (power_consumption_data['time_sec'] // 15) * 15
    grouped = power_consumption_data.groupby('interval')['Watts'].mean().reset_index()
    grouped.columns = ['Time (s)', 'Actual Power Consumption (W)']

    estimated_data_path_container = f"{estimated_data_path}/{server}/estimated_server_power_consumption.csv"
    estimated_power_consumption_data = pd.read_csv(estimated_data_path_container)
    estimated_power_consumption_data.columns = ['Time (s)', 'Estimated Power Consumption (W)']

    max_time_actual = grouped['Time (s)'].max()
    max_time_estimated = estimated_power_consumption_data['Time (s)'].max()
    max_time = min(max_time_actual, max_time_estimated)
    grouped = grouped[grouped['Time (s)'] <= max_time]
    estimated_power_consumption_data = estimated_power_consumption_data[estimated_power_consumption_data['Time (s)'] <= max_time]
    merged_data = pd.merge(
        grouped, estimated_power_consumption_data, on='Time (s)', how='inner'
    )

    mse = mean_squared_error(
        merged_data['Actual Power Consumption (W)'], merged_data['Estimated Power Consumption (W)']
    )
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(
        merged_data['Actual Power Consumption (W)'], merged_data['Estimated Power Consumption (W)']
    )

    # Calculate energy consumption using the trapezoidal rule
    time_diff = np.diff(merged_data['Time (s)'])
    energy_actual = np.trapezoid(merged_data['Actual Power Consumption (W)'], merged_data['Time (s)'])
    energy_estimated = np.trapezoid(merged_data['Estimated Power Consumption (W)'], merged_data['Time (s)'])

    
    # Calculate error percentage for energy
    energy_error_percentage = abs(energy_actual - energy_estimated) / energy_actual * 100

    plt.figure(figsize=(10, 6))
    plt.plot(
        merged_data['Time (s)'], merged_data['Actual Power Consumption (W)'],
        label='Actual Power Consumption', marker='o'
    )
    plt.plot(
        merged_data['Time (s)'], merged_data['Estimated Power Consumption (W)'],
        label='Estimated Power Consumption', color='red'
    )
    plt.xlabel('Time (s)')
    plt.ylabel('Power Consumption (W)')
    plt.title(f'Power Consumption: Actual vs. Estimated ({server_name})')
    plt.legend()
    plt.grid(True)

    plot_file_name = f"{output_dir}/{server}_power_comparison.png"
    plt.savefig(plot_file_name)
    plt.close()

    print(f"Metrics for {server_name}")
    print(f'Mean Squared Error: {mse}')
    print(f'Root Mean Squared Error: {rmse}')
    print(f'Mean Absolute Error: {mae}')
    print(f'Energy Consumption Actual (Joules): {energy_actual}')
    print(f'Energy Consumption Estimated (Joules): {energy_estimated}')
    print(f'Error Percentage (%): {energy_error_percentage}')
    print("-" * 50)

    error_log.append({
        'server': server_name,
        'container': '',
        'MSE': mse,
        'RMSE': rmse,
        'MAE': mae,
        'Energy_Consumption_Actual (Joules)': energy_actual,
        'Energy_Consumption_Estimated (Joules)': energy_estimated,
        'Error_Percentage (%)': energy_error_percentage
    })

error_log_df = pd.DataFrame(error_log)
csv_file_path = f"{estimated_data_path}/power_consumption_error_metrics_with_percentage.csv"
error_log_df.to_csv(csv_file_path, mode='a', header=not os.path.exists(csv_file_path), index=False)
