# A Queuing Network and Continuous Time Markov Chain based Hybrid Model that is capable of estimating the CPU Utilization, Power Consumption and Energy Consumption values for microservices-based applications deployed in a distributed setting

### Setup
- Navicate to the project directory and run the following command to setup virtual environment for python locally and install all the required dependencies required to run this model :
  
```bash
python3 setup_venv.py
```
- Activate the virtual environment by running :
 
```bash
source .venv/bin/activate
```

### How to run the model ? 
- Run the following bash script to run the model as well as all the data analysis scripts that will generate all the required comparison plots and error metrics
   
```bash
./run_model_and_analysis_scripts.sh <app_name> <user_scenario_name>
```
Where, valid combinations for app_name and user_scenario_name are : 
| App Name        | User Scenario Name  |
|----------------|--------------------|
| bookstore      | buy_books          |
| social_network | compose_posts      |
| social_network | follow_users       |


### Overview of Replication Package
This replication package is structured as follows:

```
    /
    .
    |--- ./model_cpu_utilization.py                                                                 Main simulation file for the Queuing Network and Continuous Time Markov Chain (CTMC) combined performance model
    |--- ./server_ctmc.py                                                                           The File with contains the main implementation of the CTMC
    |--- ./run_model_and_analysis_scripts.sh                                                        Simple shell script that runs the model and the data analysis scripts to get the prediction plots of the model
    |--- ./run_clean_up.sh                                                                          shell script that clears all the data estimated data based on the application name passed to it
    |--- ./setup_venv.py                                                                            This script when triggered creates a virtual python environment locally and install all the required dependencies required for the project
    |--- ./requirements.txt                                                                         Contains the list of dependencies to be installed
    |--- ./bookstore/buy_books/estimations/estimated_cpu_data                                       Contains the csv files and plots for the per container, per server CPU Utilization estimations done by the model for  bookstore buy_books scenario
    |--- ./bookstore/buy_books/estimations/estimated_power_consumption                              Contains the csv files and plots for the per container, per server Power  estimations done by the model for  bookstore buy_books scenario
    |--- ./bookstore/buy_books/estimations/plots/cpu_comparison_plots                               Contains the PNG image files for the comparisomn plots generated by the model for CPU Utilization estimations for  bookstore buy_books scenario
    |--- ./bookstore/buy_books/estimations/plots/power_consumption_comparison_plots                 Contains the PNG image files for the comparisomn plots generated by the model for power consumption  estimations for social-network buy_books scenario
    |--- ./social-network/compose_posts/estimations/estimated_cpu_data                              Contains the csv files and plots for the per container, per server CPU Utilization estimations done by the model for  social-network compose_posts scenario and error metric csv files
    |--- ./social-network/compose_posts/estimations/estimated_power_consumption                     Contains the csv files and plots for the per container, per server Power  estimations done by the model for  social-network compose_posts scenario and error metric csv files
    |--- ./social-network/compose_posts/estimations/plots/cpu_comparison_plots                      Contains the PNG image files for the comparisomn plots generated by the model for CPU Utilization estimations for  social-network compose_posts scenario 
    |--- ./social-network/compose_posts/estimations/plots/power_consumption_comparison_plots        Contains the PNG image files for the comparisomn plots generated by the model for power consumption  estimations for social-network compose_posts scenario
    |--- ./social-network/follow_users/estimations/estimated_cpu_data                              Contains the csv files and plots for the per container, per server CPU Utilization estimations done by the model for  social-network follow_users scenario and error metric csv files
    |--- ./social-network/follow_users/estimations/estimated_power_consumption                     Contains the csv files and plots for the per container, per server Power  estimations done by the model for  social-network follow_users scenario and error metric csv files
    |--- ./social-network/follow_users/estimations/plots/cpu_comparison_plots                      Contains the PNG image files for the comparisomn plots generated by the model for CPU Utilization estimations for  social-network follow_users scenario 
    |--- ./social-network/follow_users/estimations/plots/power_consumption_comparison_plots        Contains the PNG image files for the comparisomn plots generated by the model for power consumption  estimations for social-network follow_users scenario
    |--- ./social-network/compose_posts/model-config.json                                           Compost posts scenarin configuration file which is directly used in the performance model
    |--- ./social-network/follow_users/model-config.json                                            follow users scenarin configuration file which is directly used in the performance model  
    |--- ./buy_books/buy_books/model-config.json                                            follow users scenarin configuration file which is directly used in the performance model


### Abstract Representation of a single server within the Performance Model
![Alt text](./images/performance_mode_abstraction.jpg)
