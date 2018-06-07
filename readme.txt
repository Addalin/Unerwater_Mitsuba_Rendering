---------------------------------------------------------------
# List of commands to run before operating mitsuba simulation # 
---------------------------------------------------------------

---------------------------------------------------------------
#             Set paths in your local .bashrc file            #
---------------------------------------------------------------
# Set the Mitsuba installation paths
source "/home/**username**/Mitsuba/setpath.sh"

# Set the Mitsuba Simulation Folder paths
export MITSUBA_SIM = " /home/**username**/mitsuba_sim/"
export MITSUBA_PATH="/home/**username**/Mitsuba/dist"
export MITSUBA_RESULTS="/home/**username**/mitsuba_sim/mitsuba_results/sim_results"


---------------------------------------------------------------
#                      update mitsuba code                    #
---------------------------------------------------------------
cd $MITSUBA_SIM
git pull 

---->
# if not working delete $MITSUBA_SIM and do : 
cd ..
rm -r $MITSUBA_SIM
git clone https://github.com/Addalin/mitsuba_sim.git
cd $MITSUBA_SIM
<----

---------------------------------------------------------------
#                    update configurations                    #
1. create mitsuba_sim_results folder (as saved in environment path !)
2. update: sim_config.yml : scene : bg / cloud , nRuns : 2 
3. update: hetvol.xml : cloud_water_green.vol / cubic_water_green.vol
4. update: sensorName in main_mitsuba_sim.py
5. update: results_log.csv

---------------------------------------------------------------

mkdir mitsuba_sim_results
pico sim_config.yml
pico 3D_models/hetvol/mitsuba/hetvol.xml
pico main_mitsuba_sim.py
aws s3 sync . "s3://addaline-data/mitsuba_sim_results/resolution 2464 X 2056" --exclude="*" --include="results_log.csv" --include="s3://addaline-data/mitsuba_sim_results/resolution 2464 X 2056/output*.txt"
mv ./resolution 2464 X 2056/results_log.csv .
rm -r ./resolution 2464 X 2056/

---------------------------------------------------------------
#                     run simulation                          #
---------------------------------------------------------------
python main_mitsuba_sim.py |& tee -a output_machineType_sensorType_date.txt
