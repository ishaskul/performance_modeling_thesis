import numpy as np
import pandas as pd

class CTMCCPUUtilizationSimulator:
    def __init__(self, transition_matrix, overhead_ranges, num_cores):
        self.transition_matrix = transition_matrix
        self.overhead_ranges = overhead_ranges
        self.num_cores = num_cores
    
    #Simulate CPU overhead with smoothening
    def get_smoothed_overhead(self, current_state, prev_overhead):
        min_overhead, max_overhead = self.overhead_ranges[current_state]
        if max_overhead <= 0:
            overhead = np.random.uniform(min_overhead, max_overhead)
        else:
            scale = (max_overhead - min_overhead) / 2
            base_overhead = np.random.exponential(scale)
            overhead = min_overhead + base_overhead
            overhead = np.clip(overhead, min_overhead, max_overhead)
        if prev_overhead is not None:
            smoothing_factor = 0.2
            overhead = smoothing_factor * prev_overhead + (1 - smoothing_factor) * overhead
        return overhead

        #Simulate CPU utilization using a CTMC model.
        #:return: Simulated CPU utilization values
    def simulate_ctmc(self, duration, idle_time, ramp_up_duration, burst_duration,
                      burst_arrival_rate, steady_arrival_rate, cpu_utilization_when_idle, time_step=15):
        num_states = len(self.overhead_ranges)
        current_state = 0
        prev_overhead = None
        cpu_utilization = []

        for t in range(0, duration + 1, time_step):
            if t < idle_time:
                cpu_utilization.append(cpu_utilization_when_idle)
                continue
            elif t < idle_time + burst_duration:
                current_arrival_rate = burst_arrival_rate
            elif t < idle_time + burst_duration + ramp_up_duration:
                current_arrival_rate = steady_arrival_rate
            else:
                current_arrival_rate = 0

            overhead = self.get_smoothed_overhead(current_state, prev_overhead)
            prev_overhead = overhead

            # Update state based on transition probabilities
            current_row = self.transition_matrix[current_state]
            probs = np.clip(current_row * time_step + np.eye(num_states)[current_state], 0, 1)
            next_state = np.random.choice(range(num_states), p=probs / probs.sum())
            current_state = next_state
            # Calculate CPU utilization using Little's Law and normalize by number of cores
            cpu_utilization_value = (current_arrival_rate * overhead) / self.num_cores
            cpu_utilization.append(cpu_utilization_value)

        return np.array(cpu_utilization)

    #Refine CPU utilization by combining existing data with CTMC simulation.
    def refine_cpu_utilization(self, microservice_cpu_csv, duration, idle_time, 
                               ramp_up_duration, burst_duration, burst_arrival_rate, 
                               steady_arrival_rate, cpu_utilization_when_idle):
        df = pd.read_csv(microservice_cpu_csv)

        csv_time_points = df['Time (s)'].values
        time_step = csv_time_points[1] - csv_time_points[0]

        # Simulate CTMC
        simulated_cpu_utilization = self.simulate_ctmc(
            duration, idle_time, ramp_up_duration, burst_duration, 
            burst_arrival_rate, steady_arrival_rate, cpu_utilization_when_idle, time_step=time_step
        )

        if len(simulated_cpu_utilization) != len(df):
            raise ValueError("Simulated CPU utilization length does not match the CSV data length.")

        df['refined_cpu'] = np.clip(df['CPU Utilization (%)'] + simulated_cpu_utilization, 0, 100)

        return df